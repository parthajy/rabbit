"""
Rabbit v2.1 — Continue fine-tuning from v2.0 LoRA on Qwen 2.5 32B.

Adds 15.5K new examples (multi-turn, temporal, causal, meta-instructions,
plain answers) on top of the 82K v2.0 base = ~97.8K total.

Key change from v2.0:
  - Starts from v2.0 LoRA weights (not fresh base model)
  - Lower LR (5e-5 vs 1e-4) to avoid catastrophic forgetting
  - Longer seq length (4096 vs 2048) for multi-turn conversations

Hardware: 1x H100 80GB or 1x A100 80GB on RunPod
Time: ~8-12 hours
Cost: ~$20-35

Usage:
  export HF_TOKEN="your_hf_token"
  python scripts/finetune_v21.py
"""

import os
import json
import glob
from pathlib import Path

# ── Config ──────────────────────────────────────────────────
BASE_MODEL = "unsloth/Qwen2.5-32B-Instruct-bnb-4bit"
V20_ADAPTER = "reattend/rabbit-v2.0"
OUTPUT_DIR = "models/rabbit-v2.1"
HF_REPO = "reattend/rabbit-v2.1"

LORA_R = 32
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

EPOCHS = 1
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 16  # effective batch = 16
LEARNING_RATE = 5e-5  # lower than v2.0 to avoid forgetting
MAX_SEQ_LENGTH = 4096
WARMUP_RATIO = 0.05

# Signal-specific system prompts (same as v2.0 for backward compat)
SIGNAL_PROMPTS = {
    "[INTENT]": "You are Rabbit, a memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "[EXTRACT]": "You are Rabbit, a memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "[TRIAGE]": "You are Rabbit, a memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "[EXPAND]": "You are Rabbit, a memory AI. Expand the user's vague query into a precise, comprehensive search query.",
    "[ANSWER]": "You are Rabbit, a memory AI. Answer the user's question using their saved memories. Be specific, cite sources as [1][2], use plain English.",
    "[SUMMARIZE]": "You are Rabbit, a memory AI. Generate a rich 2-4 sentence standalone summary.",
    "[SENTIMENT]": "You are Rabbit, a memory AI. Classify the tone. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "[IMPORTANCE]": "You are Rabbit, a memory AI. Score the importance 1-5 with reason. Return JSON with keys: score and reason.",
    "[LINK]": "You are Rabbit, a memory AI. Determine which candidates are meaningfully related. Return JSON with a links array.",
    "[AMBIENT]": "You are Rabbit, a memory AI. Detect contradictions or forgotten commitments. Return JSON.",
}

# v2.1 new categories use the answer system prompt
V21_SYSTEM = "You are Rabbit, a memory AI. Answer the user's question using their saved memories. Be specific, cite sources as [1][2], use plain English. No markdown formatting except citations."


def load_training_data():
    """Load v2.0 base (82K) + v2.1 new (15K) data."""
    examples = []

    # v2.0 filtered data
    data_dir = Path("data/filtered")
    if data_dir.exists():
        for f in sorted(data_dir.glob("*.jsonl")):
            count = 0
            for line in open(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    examples.append(json.loads(line))
                    count += 1
                except json.JSONDecodeError:
                    continue
            print(f"  v2.0 {f.name}: {count}")

    # v2.1 new data
    v21_dir = Path("data/v2.1")
    if v21_dir.exists():
        for f in sorted(v21_dir.glob("*.jsonl")):
            count = 0
            for line in open(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    examples.append(json.loads(line))
                    count += 1
                except json.JSONDecodeError:
                    continue
            print(f"  v2.1 {f.name}: {count}")

    print(f"\nTotal: {len(examples)}")
    return examples


def format_for_chat(example):
    """Convert training format to Qwen chat messages."""
    if "messages" in example:
        return example["messages"]

    input_text = example.get("input", "")
    output_text = example.get("output", "")

    if not input_text or not output_text:
        return None

    # Detect signal from prefix (v2.0 data has [SIGNAL] prefixes)
    system = V21_SYSTEM
    for prefix, prompt in SIGNAL_PROMPTS.items():
        if input_text.startswith(prefix):
            system = prompt
            break

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": input_text},
        {"role": "assistant", "content": output_text},
    ]


def main():
    print("=" * 60)
    print("  Rabbit v2.1 — Fine-tuning from v2.0 LoRA")
    print("=" * 60)

    hf_token = os.environ.get("HF_TOKEN", "")

    # Load data
    print("\nLoading training data...")
    raw_examples = load_training_data()
    if not raw_examples:
        print("ERROR: No training data found")
        return

    # Convert to chat format — normalize all messages to exactly 3 roles
    # (system, user, assistant) so pyarrow doesn't choke on mixed struct shapes
    print("\nConverting to chat format...")
    chat_examples = []
    skipped = 0
    for ex in raw_examples:
        msgs = format_for_chat(ex)
        if not msgs or len(msgs) < 2:
            skipped += 1
            continue
        # Ensure exactly 3 messages: system, user, assistant
        if len(msgs) == 2:
            msgs = [{"role": "system", "content": V21_SYSTEM}] + msgs
        elif len(msgs) > 3:
            # Keep system + last user + last assistant
            msgs = [msgs[0], msgs[-2], msgs[-1]]
        # Validate roles
        if msgs[0]["role"] != "system":
            msgs = [{"role": "system", "content": V21_SYSTEM}] + msgs[:2]
        chat_examples.append({"messages": msgs[:3]})
    print(f"Chat-formatted: {len(chat_examples)} (skipped {skipped})")

    # Load base model
    print(f"\nLoading base model {BASE_MODEL}...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
        token=hf_token or None,
    )

    # Load v2.0 LoRA weights as starting point
    print(f"\nLoading v2.0 adapter from {V20_ADAPTER}...")
    from peft import PeftModel
    model = PeftModel.from_pretrained(
        model, V20_ADAPTER,
        token=hf_token or None,
        is_trainable=True,
    )
    print("v2.0 LoRA weights loaded — continuing training from here")

    # Prepare dataset — pre-tokenize to plain text to avoid pyarrow struct
    # issues with mixed message formats. SFTTrainer accepts a "text" column.
    print("\nPreparing dataset (pre-tokenizing to text)...")
    import random as _rand
    _rand.seed(42)
    _rand.shuffle(chat_examples)

    texts = []
    for ex in chat_examples:
        try:
            text = tokenizer.apply_chat_template(
                ex["messages"],
                tokenize=False,
                add_generation_prompt=False,
            )
            if text and len(text) > 50:
                texts.append({"text": text})
        except Exception:
            continue
    print(f"Pre-tokenized: {len(texts)} examples")

    split_idx = int(len(texts) * 0.98)
    from datasets import Dataset
    train_dataset = Dataset.from_list(texts[:split_idx])
    eval_dataset = Dataset.from_list(texts[split_idx:])
    print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

    # Train
    print(f"\nTraining config:")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Batch: {BATCH_SIZE} x {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION} effective")
    print(f"  LR: {LEARNING_RATE} (half of v2.0's 1e-4)")
    print(f"  Max seq: {MAX_SEQ_LENGTH}")

    from trl import SFTTrainer
    from transformers import TrainingArguments

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=TrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION,
            learning_rate=LEARNING_RATE,
            warmup_ratio=WARMUP_RATIO,
            bf16=True,
            logging_steps=50,
            eval_strategy="steps",
            eval_steps=500,
            save_strategy="steps",
            save_steps=1000,
            save_total_limit=3,
            report_to="none",
            seed=42,
            gradient_checkpointing=True,
        ),
        max_seq_length=MAX_SEQ_LENGTH,
    )

    print("\nTraining started...")
    trainer.train()

    # Save
    print(f"\nSaving LoRA adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Upload to HuggingFace
    if hf_token:
        print(f"\nUploading LoRA to {HF_REPO}...")
        model.push_to_hub(HF_REPO, token=hf_token)
        tokenizer.push_to_hub(HF_REPO, token=hf_token)
        print("Upload complete!")
    else:
        print("\nNo HF_TOKEN. Upload manually:")
        print(f"  huggingface-cli upload {HF_REPO} {OUTPUT_DIR}")

    print("\n" + "=" * 60)
    print("  v2.1 training complete!")
    print(f"  LoRA adapter: {OUTPUT_DIR}")
    print(f"  HuggingFace: {HF_REPO}")
    print("=" * 60)


if __name__ == "__main__":
    main()
