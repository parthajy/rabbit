"""
LLM interface for Rabbit.

Wraps the fine-tuned Qwen 2.5 32B model (v2.0+) with signal-aware generation.
Uses Unsloth's FastLanguageModel to load the LoRA adapter on top of the
4-bit base automatically.

This is LoRA-only shipping — the repo on HuggingFace is the adapter and
Unsloth resolves the base model via adapter_config.json.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from rabbit.core.signals import SYSTEM_PROMPTS, SIGNAL_PREFIXES, SIGNAL_SETTINGS


class RabbitLLM:
    """Interface to the Rabbit v2.0 fine-tuned model (Qwen 2.5 32B + LoRA)."""

    def __init__(
        self,
        model_path: str = "reattend/rabbit-v2.0",
        max_seq_length: int = 2048,
        hf_token: str = "",
    ):
        self.model_path = model_path
        self.max_seq_length = max_seq_length
        self.hf_token = hf_token or os.environ.get("HF_TOKEN", "")
        self.model = None
        self.tokenizer = None
        self._loaded = False

    def load(self):
        """Load the model and tokenizer via Unsloth.

        Unsloth's from_pretrained handles the LoRA-on-top-of-4bit-base case
        automatically by reading adapter_config.json from the repo.
        """
        if self._loaded:
            return

        from unsloth import FastLanguageModel

        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_path,
            max_seq_length=self.max_seq_length,
            dtype=None,  # auto (bf16 on A100/H100, fp16 on L4)
            load_in_4bit=True,
            token=self.hf_token or None,
        )
        # 2x faster inference, disables training-only code paths
        FastLanguageModel.for_inference(self.model)
        self._loaded = True

    def generate(
        self,
        signal: str,
        content: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a response for a given signal."""
        import torch

        self.load()

        settings = SIGNAL_SETTINGS.get(signal, {"max_tokens": 512, "temperature": 0.1})
        max_tokens = max_tokens or settings["max_tokens"]
        temperature = temperature if temperature is not None else settings["temperature"]

        system_prompt = SYSTEM_PROMPTS.get(signal, SYSTEM_PROMPTS["answer"])
        prefix = SIGNAL_PREFIXES.get(signal, "[ANSWER]")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{prefix} {content}"},
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self.model.device)

        input_len = inputs.shape[-1]

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs,
                max_new_tokens=max_tokens,
                temperature=max(temperature, 0.01),
                do_sample=temperature > 0.01,
                use_cache=True,
            )

        raw = self.tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        return _clean_output(raw, signal)

    def generate_raw(
        self,
        system_prompt: str | None,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> str:
        """Raw passthrough generation — used by /v1/raw endpoint.

        No signal prefix, no cleaning. The caller supplies their own system
        prompt (or None) and user prompt verbatim.
        """
        import torch

        self.load()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self.model.device)

        input_len = inputs.shape[-1]

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs,
                max_new_tokens=min(max_tokens, 4096),
                temperature=max(temperature, 0.01),
                do_sample=temperature > 0.01,
                use_cache=True,
            )

        return self.tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()

    def generate_batch(self, tasks: list[tuple[str, str]]) -> list[str]:
        """Generate responses for multiple signal+content pairs sequentially."""
        return [self.generate(signal, content) for signal, content in tasks]


# ── JSON cleaning helpers ──────────────────────────────────────────────────

_JSON_SIGNALS = {
    "extract",
    "faithful_extract",
    "triage",
    "importance",
    "link",
    "ambient",
    "lint",
    "clean_json",
}


def _clean_output(text: str, signal: str) -> str:
    """Post-process model output."""
    # Strip markdown code blocks
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # For JSON signals, extract valid JSON
    if signal in _JSON_SIGNALS:
        match = re.search(r"\{[\s\S]*\}", text)
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
        match = re.search(r"\{[\s\S]*\}", text or "")
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}
