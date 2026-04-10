"""
LLM interface for Rabbit.

Wraps the fine-tuned Phi-3.5 model with signal-aware generation.
Handles model loading, inference, and output cleaning.
"""

from __future__ import annotations

import json
import re
from typing import Any

from rabbit.core.signals import SYSTEM_PROMPTS, SIGNAL_PREFIXES, SIGNAL_SETTINGS


class RabbitLLM:
    """Interface to the Rabbit fine-tuned model."""

    def __init__(self, model_path: str = "reattend/rabbit-v1.4-merged", device: str = "auto", hf_token: str = ""):
        self.model_path = model_path
        self.device = device
        self.hf_token = hf_token
        self.model = None
        self.tokenizer = None
        self._loaded = False

    def load(self):
        """Load the model and tokenizer."""
        if self._loaded:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_storage=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            quantization_config=bnb_config,
            device_map=self.device,
            token=self.hf_token or None,
            torch_dtype=torch.float16,
        )
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3.5-mini-instruct")
        self.model.eval()
        self._loaded = True

    def generate(self, signal: str, content: str, max_tokens: int | None = None, temperature: float | None = None) -> str:
        """Generate a response for a given signal."""
        import torch

        self.load()

        settings = SIGNAL_SETTINGS.get(signal, {"max_tokens": 512, "temperature": 0.1})
        max_tokens = max_tokens or settings["max_tokens"]
        temperature = temperature or settings["temperature"]

        system_prompt = SYSTEM_PROMPTS.get(signal, SYSTEM_PROMPTS["answer"])
        prefix = SIGNAL_PREFIXES.get(signal, "[ANSWER]")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{prefix} {content}"},
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            return_tensors="pt", return_dict=True,
        ).to(self.model.device)

        input_len = inputs["input_ids"].shape[-1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=max(temperature, 0.01),
                do_sample=temperature > 0.01,
            )

        raw = self.tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        return _clean_output(raw, signal)

    def generate_batch(self, tasks: list[tuple[str, str]]) -> list[str]:
        """Generate responses for multiple signal+content pairs sequentially.

        Args:
            tasks: List of (signal, content) tuples.

        Returns:
            List of response strings in the same order.
        """
        return [self.generate(signal, content) for signal, content in tasks]


def _clean_output(text: str, signal: str) -> str:
    """Post-process model output."""
    # Strip markdown code blocks
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    # For JSON signals, extract valid JSON
    if signal in ("extract", "triage", "importance", "link", "ambient"):
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                parsed = json.loads(match.group())
                text = json.dumps(parsed)
            except json.JSONDecodeError:
                pass

    return text


def parse_json_output(text: str) -> dict[str, Any]:
    """Parse a JSON string from model output, with fallback."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r'\{[\s\S]*\}', text or "")
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}
