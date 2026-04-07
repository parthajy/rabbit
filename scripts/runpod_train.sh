#!/bin/bash
# ============================================================
#  RABBIT v1 — RunPod Training Script
#  Paste this entire script into the RunPod terminal.
#  Then close your laptop. Come back in ~45 min.
# ============================================================

set -e
echo "=========================================="
echo "  RABBIT v1 — Starting Training Pipeline"
echo "=========================================="

# ── Step 1: Install dependencies ──
echo ""
echo "[1/6] Installing dependencies..."
pip install -q unsloth
pip install -q --no-deps trl peft accelerate bitsandbytes datasets

# ── Step 2: Download training data from GitHub ──
echo ""
echo "[2/6] Downloading training data..."
cd /workspace
git clone https://github.com/parthajy/rabbit.git
cd rabbit

# Create filtered data directory and download from the repo
# (filtered data is gitignored, so we need to upload it)
mkdir -p data/filtered

# ── Step 3: Check if data exists, if not create from seeds ──
echo ""
echo "[3/6] Preparing training data..."

# Write the training script inline
cat > /workspace/train_rabbit.py << 'TRAINSCRIPT'
import json
import torch
from pathlib import Path
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# ── Config ──
DATA_DIR = Path("/workspace/rabbit/data/filtered")
OUTPUT_PATH = "/workspace/rabbit-v1"
GGUF_PATH = "/workspace/rabbit-v1-gguf"
BASE_MODEL = "unsloth/Phi-3.5-mini-instruct"
MAX_SEQ_LENGTH = 2048

TASKS = ["intent", "extract", "triage", "expand", "answer", "summarize", "sentiment", "importance"]

TASK_PREFIXES = {
    "intent": "[INTENT]",
    "extract": "[EXTRACT]",
    "triage": "[TRIAGE]",
    "expand": "[EXPAND]",
    "answer": "[ANSWER]",
    "summarize": "[SUMMARIZE]",
    "sentiment": "[SENTIMENT]",
    "importance": "[IMPORTANCE]",
}

TASK_SYSTEM_PROMPTS = {
    "intent": "You are Rabbit, Reattend's memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand": "You are Rabbit, Reattend's memory AI. Expand the user's vague query into a precise, comprehensive search query that captures their likely intent.",
    "answer": "You are Rabbit, Reattend's memory AI. Answer the user's question using the provided memory context. Use citations [1][2][3] to reference sources. Do not use markdown formatting.",
    "summarize": "You are Rabbit, Reattend's memory AI. Generate a rich 2-4 sentence standalone summary of the given content. Capture the essence, key decisions, and action items.",
    "sentiment": "You are Rabbit, Reattend's memory AI. Classify the tone of the given content. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance": "You are Rabbit, Reattend's memory AI. Score the importance of the given content for organizational memory. Return a JSON object with keys: score (1-5) and reason (one sentence).",
}

# ── Load model ──
print("\n" + "="*60)
print("  RABBIT — Loading base model...")
print("="*60)

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
print(f"  Trainable: {trainable:,} / {total_params:,} ({trainable/total_params*100:.1f}%)")

# ── Load data ──
print("\n" + "="*60)
print("  RABBIT — Loading training data...")
print("="*60)

all_examples = []

for task in TASKS:
    filepath = DATA_DIR / f"{task}_filtered.jsonl"
    if not filepath.exists():
        print(f"  {task}: NOT FOUND — skipping")
        continue

    count = 0
    with open(filepath) as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line.strip())
            output = raw["output"]
            if isinstance(output, dict):
                output = json.dumps(output)

            example = {
                "conversations": [
                    {"role": "system", "content": TASK_SYSTEM_PROMPTS[task]},
                    {"role": "user", "content": f"{TASK_PREFIXES[task]} {raw['input']}"},
                    {"role": "assistant", "content": output},
                ]
            }
            all_examples.append(example)
            count += 1

    print(f"  {task}: {count} examples")

print(f"\n  Total: {len(all_examples)} training examples")

# ── Format ──
def format_chat(example):
    text = tokenizer.apply_chat_template(
        example["conversations"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}

dataset = Dataset.from_list(all_examples)
dataset = dataset.map(format_chat)
dataset = dataset.shuffle(seed=42)

split = dataset.train_test_split(test_size=0.05, seed=42)
print(f"  Train: {len(split['train']):,}")
print(f"  Eval:  {len(split['test']):,}")

# ── Train ──
print("\n" + "="*60)
print("  RABBIT — Starting training...")
print("="*60 + "\n")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=split["train"],
    eval_dataset=split["test"],
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    args=TrainingArguments(
        output_dir=OUTPUT_PATH,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=50,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=25,
        eval_strategy="steps",
        eval_steps=200,
        save_strategy="steps",
        save_steps=500,
        save_total_limit=3,
        report_to="none",
        optim="adamw_8bit",
    ),
)

trainer_stats = trainer.train()

print(f"\n{'='*60}")
print(f"  RABBIT — Training complete!")
print(f"  Total steps: {trainer_stats.global_step}")
print(f"  Training loss: {trainer_stats.training_loss:.4f}")
print(f"  Runtime: {trainer_stats.metrics['train_runtime']/60:.1f} minutes")
print(f"{'='*60}")

# ── Save ──
print("\n  Saving LoRA adapters...")
model.save_pretrained(OUTPUT_PATH)
tokenizer.save_pretrained(OUTPUT_PATH)

print("  Saving GGUF (4-bit quantized)...")
model.save_pretrained_gguf(GGUF_PATH, tokenizer, quantization_method="q4_k_m")

# ── Test ──
print(f"\n{'='*60}")
print(f"  RABBIT — Smoke test...")
print(f"{'='*60}")

FastLanguageModel.for_inference(model)

test_cases = [
    ("[INTENT]", "What did we discuss with Brian last week?"),
    ("[EXTRACT]", "Met with Sarah from Acme on Tuesday. She agreed to send the contract by Friday. Budget confirmed at $45,000."),
    ("[EXPAND]", "what about brian"),
    ("[SENTIMENT]", "This is frustrating. We discussed this three times and nothing has changed."),
    ("[ANSWER]", "Question: What did we decide about pricing?\nMemories: [1] Meeting Mar 15 — decided to go freemium. [2] Meeting Mar 22 — costs too high. [3] Meeting Mar 28 — reversed, going usage-based."),
]

for prefix, user_input in test_cases:
    task_name = prefix.strip("[]").lower()
    messages = [
        {"role": "system", "content": TASK_SYSTEM_PROMPTS[task_name]},
        {"role": "user", "content": f"{prefix} {user_input}"},
    ]

    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt",
    ).to("cuda")

    outputs = model.generate(input_ids=inputs, max_new_tokens=256, temperature=0.1, do_sample=True)
    response = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)

    print(f"\n  --- {prefix} ---")
    inp = user_input[:80] + "..." if len(user_input) > 80 else user_input
    print(f"  Input:  {inp}")
    print(f"  Output: {response}")

print(f"\n{'='*60}")
print(f"  RABBIT v1 — TRAINING COMPLETE!")
print(f"  LoRA model: {OUTPUT_PATH}")
print(f"  GGUF model: {GGUF_PATH}")
print(f"  Download the GGUF file to your machine.")
print(f"{'='*60}")
TRAINSCRIPT

echo ""
echo "[4/6] Training script ready."
echo ""
echo "=========================================="
echo "  IMPORTANT: Upload your training data!"
echo "=========================================="
echo ""
echo "  Before running training, upload your 8 filtered JSONL files"
echo "  to: /workspace/rabbit/data/filtered/"
echo ""
echo "  Files needed:"
echo "    - answer_filtered.jsonl"
echo "    - expand_filtered.jsonl"
echo "    - extract_filtered.jsonl"
echo "    - importance_filtered.jsonl"
echo "    - intent_filtered.jsonl"
echo "    - sentiment_filtered.jsonl"
echo "    - summarize_filtered.jsonl"
echo "    - triage_filtered.jsonl"
echo ""
echo "  Upload via Jupyter: navigate to rabbit/data/filtered/ and drag-drop files"
echo ""
echo "  Then run: python /workspace/train_rabbit.py"
echo ""
echo "=========================================="
