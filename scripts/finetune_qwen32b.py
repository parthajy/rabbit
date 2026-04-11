"""
Rabbit v2.0 — Fine-tune Qwen 2.5 32B for Memory Infrastructure

Training setup:
  - Base: Qwen/Qwen2.5-32B-Instruct
  - Method: LoRA (r=32, alpha=32) via Unsloth
  - Data: ~108K examples (82K existing + 18K v1.5 fixes + 8K long examples)
  - Hardware: 2x A100 80GB on RunPod
  - Time: ~8-10 hours
  - Cost: ~$35-40

Usage:
  # On RunPod with 2x A100 80GB:
  pip install unsloth datasets trl transformers peft
  python scripts/finetune_qwen32b.py

Output:
  - LoRA adapter: models/rabbit-v2.0/
  - Merged model: models/rabbit-v2.0-merged/
  - Upload to HuggingFace: reattend/rabbit-v2.0
"""

import os
import json
import glob
from pathlib import Path

# ── Config ──────────────────────────────────────────────────
BASE_MODEL = "Qwen/Qwen2.5-32B-Instruct"
OUTPUT_DIR = "models/rabbit-v2.0"
MERGED_DIR = "models/rabbit-v2.0-merged"
HF_REPO = "reattend/rabbit-v2.0"

# LoRA config — r=32 for 32B model (more capacity than r=16 used for 3.8B)
LORA_R = 32
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

# Training config
EPOCHS = 2  # 2 epochs for larger model (less overfitting risk)
BATCH_SIZE = 2  # Per-device batch size (adjust based on VRAM)
GRADIENT_ACCUMULATION = 8  # Effective batch size = 2 * 8 * 2 GPUs = 32
LEARNING_RATE = 1e-4
MAX_SEQ_LENGTH = 4096  # Qwen supports 128K but we cap at 4K for training efficiency
WARMUP_RATIO = 0.05

# ── Load Data ───────────────────────────────────────────────
def load_training_data():
    """Load all filtered training data from data/filtered/ directory."""
    examples = []
    data_dir = Path("data/filtered")

    if not data_dir.exists():
        print(f"ERROR: {data_dir} not found. Run data generation scripts first.")
        return []

    for jsonl_file in sorted(data_dir.glob("*.jsonl")):
        with open(jsonl_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                    examples.append(ex)
                except json.JSONDecodeError:
                    continue
        print(f"  Loaded {jsonl_file.name}")

    # Also load long examples if available
    long_file = Path("data/synthetic/long_examples.jsonl")
    if long_file.exists():
        with open(long_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                    examples.append(ex)
                except json.JSONDecodeError:
                    continue
        print(f"  Loaded long_examples.jsonl")

    print(f"\nTotal training examples: {len(examples)}")
    return examples


def format_for_chat(example):
    """Convert our training format to Qwen chat format."""
    # Our format: {"input": "...", "output": "..."}
    # OR: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}

    if "messages" in example:
        return example["messages"]

    # Legacy format conversion
    input_text = example.get("input", "")
    output_text = example.get("output", "")

    if not input_text or not output_text:
        return None

    # Detect signal from prefix
    signal_prompts = {
        "[INTENT]": "You are Rabbit, a memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
        "[EXTRACT]": "You are Rabbit, a memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
        "[TRIAGE]": "You are Rabbit, a memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
        "[EXPAND]": "You are Rabbit, a memory AI. Expand the user's vague query into a precise, comprehensive search query.",
        "[ANSWER]": "You are Rabbit, a memory AI. Answer the user's question conversationally with citations.",
        "[SUMMARIZE]": "You are Rabbit, a memory AI. Generate a rich 2-4 sentence standalone summary.",
        "[SENTIMENT]": "You are Rabbit, a memory AI. Classify the tone. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
        "[IMPORTANCE]": "You are Rabbit, a memory AI. Score the importance 1-5 with reason. Return JSON with keys: score and reason.",
        "[LINK]": "You are Rabbit, a memory AI. Determine which candidates are meaningfully related. Return JSON with a links array.",
        "[AMBIENT]": "You are Rabbit, a memory AI. Detect contradictions or forgotten commitments. Return JSON.",
    }

    system = "You are Rabbit, a memory AI assistant."
    for prefix, prompt in signal_prompts.items():
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
    print("  Rabbit v2.0 — Fine-tuning Qwen 2.5 32B")
    print("=" * 60)

    # Load data
    print("\nLoading training data...")
    raw_examples = load_training_data()
    if not raw_examples:
        return

    # Convert to chat format
    print("Converting to chat format...")
    chat_examples = []
    for ex in raw_examples:
        msgs = format_for_chat(ex)
        if msgs:
            chat_examples.append({"messages": msgs})

    print(f"Chat-formatted examples: {len(chat_examples)}")

    # Load model with Unsloth
    print(f"\nLoading {BASE_MODEL} with Unsloth...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    print("Applying LoRA...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Prepare dataset
    print("Preparing dataset...")
    from datasets import Dataset

    def tokenize_fn(example):
        messages = example["messages"]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        return tokenizer(
            text,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding=False,
        )

    dataset = Dataset.from_list(chat_examples)
    dataset = dataset.shuffle(seed=42)

    # Split
    split = dataset.train_test_split(test_size=0.02, seed=42)
    train_dataset = split["train"]
    eval_dataset = split["test"]

    print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

    # Train
    print(f"\nStarting training...")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE} x {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION} effective")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Max sequence length: {MAX_SEQ_LENGTH}")

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
            fp16=True,
            logging_steps=50,
            eval_strategy="steps",
            eval_steps=500,
            save_strategy="steps",
            save_steps=1000,
            save_total_limit=3,
            report_to="none",
            seed=42,
        ),
        max_seq_length=MAX_SEQ_LENGTH,
    )

    print("\nTraining started...")
    trainer.train()

    # Save LoRA adapter
    print(f"\nSaving LoRA adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Merge and save full model (4-bit quantized)
    print(f"\nMerging to {MERGED_DIR}...")
    model.save_pretrained_merged(
        MERGED_DIR,
        tokenizer,
        save_method="merged_4bit",
    )

    # Upload to HuggingFace
    hf_token = os.environ.get("HF_TOKEN", "")
    if hf_token:
        print(f"\nUploading to HuggingFace: {HF_REPO}...")
        model.push_to_hub_merged(
            HF_REPO,
            tokenizer,
            save_method="merged_4bit",
            token=hf_token,
        )
        print("Upload complete!")
    else:
        print("\nNo HF_TOKEN set. Skipping upload. Upload manually:")
        print(f"  huggingface-cli upload {HF_REPO} {MERGED_DIR}")

    print("\n" + "=" * 60)
    print("  Training complete!")
    print(f"  LoRA adapter: {OUTPUT_DIR}")
    print(f"  Merged model: {MERGED_DIR}")
    print(f"  HuggingFace: {HF_REPO}")
    print("=" * 60)


if __name__ == "__main__":
    main()
