"""
Rabbit — Fine-tuning Script
Fine-tunes Phi-3.5 Mini on all 5 Reattend tasks using Unsloth.

Usage (on RunPod A100):
    python scripts/finetune.py
    python scripts/finetune.py --base-model "unsloth/Phi-3.5-mini-instruct" --epochs 3
"""

import argparse
import json
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

FILTERED_DIR = Path("data/filtered")
OUTPUT_DIR = Path("models")

TASKS = ["intent", "extract", "triage", "expand", "answer", "summarize", "sentiment", "importance", "multiturn", "dontknow", "link", "ambient", "faithful_extract", "formatted_answer", "followup_answer", "clean_json", "compile", "lint", "compile_answer"]

# Task prefixes used in the prompt format
TASK_PREFIXES = {
    "intent": "[INTENT]",
    "extract": "[EXTRACT]",
    "triage": "[TRIAGE]",
    "expand": "[EXPAND]",
    "answer": "[ANSWER]",
    "summarize": "[SUMMARIZE]",
    "sentiment": "[SENTIMENT]",
    "importance": "[IMPORTANCE]",
    "multiturn": "[ANSWER]",
    "dontknow": "[ANSWER]",
    "link": "[LINK]",
    "ambient": "[AMBIENT]",
    "faithful_extract": "[EXTRACT]",
    "formatted_answer": "[ANSWER]",
    "followup_answer": "[ANSWER]",
    "clean_json": "[EXTRACT]",
    "compile": "[COMPILE]",
    "lint": "[LINT]",
    "compile_answer": "[COMPILE]",
}

TASK_SYSTEM_PROMPTS = {
    "intent": "You are Rabbit, Reattend's memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand": "You are Rabbit, Reattend's memory AI. Expand the user's vague query into a precise, comprehensive search query that captures their likely intent.",
    "answer": "You are Rabbit, Reattend's memory AI. Answer the user's question conversationally using the provided memory context. Tell a story, provide insight, cite sources as [1][2][3]. Include a Sources section and suggest Follow-up questions. Do not use markdown.",
    "summarize": "You are Rabbit, Reattend's memory AI. Generate a rich 2-4 sentence standalone summary of the given content. Capture the essence, key decisions, and action items.",
    "sentiment": "You are Rabbit, Reattend's memory AI. Classify the tone of the given content. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance": "You are Rabbit, Reattend's memory AI. Score the importance of the given content for organizational memory. Return a JSON object with keys: score (1-5) and reason (one sentence).",
    "multiturn": "You are Rabbit, Reattend's memory AI. Continue the conversation using the provided memory context. Build on what was already discussed. Cite sources as [1][2][3]. Include Sources and Follow-up questions. Do not use markdown.",
    "dontknow": "You are Rabbit, Reattend's memory AI. Answer the user's question using the provided memory context. If the memories don't fully answer the question, be honest about what's missing and suggest where to find it. Cite sources as [1][2][3]. Do not use markdown.",
    "link": "You are Rabbit, Reattend's memory AI. Given a source record and candidate records, determine which candidates are meaningfully related. Return a JSON object with a links array. Each link has: target_id, kind (same_topic/depends_on/contradicts/continuation_of/same_people/causes/temporal), weight (0-1), and explanation. Max 8 links. If no candidates are related, return {\"links\": []}.",
    "ambient": "You are Rabbit, Reattend's memory AI. You see what the user is currently doing (screen text) and related memories. Decide whether to alert them. Return JSON: {\"show\": false} if no alert needed. Or {\"show\": true, \"reason\": \"contradiction|forgotten_commitment|critical_context\", \"memory_indices\": [1,2], \"context\": \"one sentence explanation\"} if they need to know something. Only alert for genuine contradictions, forgotten commitments, or critical context. Do NOT alert for loose associations.",
    "faithful_extract": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics. CRITICAL: Reproduce every name, number, and date EXACTLY as it appears in the input. Never abbreviate, paraphrase, or alter proper nouns.",
    "formatted_answer": "You are Rabbit, Reattend's memory AI. Answer conversationally. Use **bold** for person names and key decisions. Cite inline as [1][2][3]. You MUST end with Sources: section and Follow-up questions: section (3 questions prefixed with →). Minimum 300 words.",
    "followup_answer": "You are Rabbit, Reattend's memory AI. Answer the question using memories. Always end with Follow-up questions: section containing exactly 3 questions prefixed with →. Questions must be specific, useful, and varied (factual, analytical, strategic).",
    "clean_json": "You are Rabbit, Reattend's memory AI. Extract structured information. Return ONLY valid JSON. No text before or after the JSON object. No markdown. No explanation.",
    "compile": "You are Rabbit, Reattend's memory AI. You maintain a living organizational wiki. Given an existing entity/topic page and a new memory, update the page by integrating the new information. Preserve valid existing info, add new details, note contradictions if any. Format: Summary, Key People, Open Items, Recent Activity, Related Topics.",
    "lint": "You are Rabbit, Reattend's memory AI. You audit the organizational knowledge base. Given an entity page and recent memories, detect issues. Return JSON with: contradictions (facts that conflict), stale_items (dates passed with no update), missing_links (entities mentioned without pages), suggested_actions (what to fix).",
    "compile_answer": "You are Rabbit, Reattend's memory AI. Convert a synthesized answer into a reusable wiki entry. Return JSON with: title (max 80 chars), content (wiki-style, not Q&A), category (decisions/projects/people/strategy/operations), source_ids, auto_update (true), keywords.",
}


# ── Data loading ────────────────────────────────────────────────────────────


def load_all_training_data() -> list[dict]:
    """Load and format all filtered data into chat-style training examples."""
    all_examples = []

    for task in TASKS:
        filtered_file = FILTERED_DIR / f"{task}_filtered.jsonl"
        if not filtered_file.exists():
            print(f"  Warning: {filtered_file} not found. Skipping {task}.")
            continue

        count = 0
        with open(filtered_file) as f:
            for line in f:
                if not line.strip():
                    continue
                raw = json.loads(line.strip())

                # Format as chat conversation
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

        print(f"  Loaded {count} examples for {task}")

    print(f"\n  Total training examples: {len(all_examples)}")
    return all_examples


# ── Fine-tuning ─────────────────────────────────────────────────────────────


def finetune(base_model: str, epochs: int, lr: float, batch_size: int):
    """Run fine-tuning with Unsloth."""

    # Import here so the script can show help without GPU deps
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import Dataset

    print(f"\n{'='*60}")
    print(f"  RABBIT — Fine-tuning")
    print(f"  Base model: {base_model}")
    print(f"  Epochs: {epochs}")
    print(f"  Learning rate: {lr}")
    print(f"{'='*60}")

    # Load model with Unsloth (2x faster, 60% less VRAM)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=2048,
        dtype=None,  # auto-detect
        load_in_4bit=True,
    )

    # Add LoRA adapters
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

    # Load data
    training_data = load_all_training_data()

    # Format for the tokenizer
    def format_chat(example):
        text = tokenizer.apply_chat_template(
            example["conversations"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    dataset = Dataset.from_list(training_data)
    dataset = dataset.map(format_chat)
    dataset = dataset.shuffle(seed=42)

    # Split: 95% train, 5% eval
    split = dataset.train_test_split(test_size=0.05, seed=42)

    # Training
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(OUTPUT_DIR / "rabbit-v1")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            output_dir=output_path,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=50,
            num_train_epochs=epochs,
            learning_rate=lr,
            fp16=True,
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=100,
            save_strategy="steps",
            save_steps=200,
            save_total_limit=3,
            report_to="none",
        ),
    )

    print("\n  Starting training...\n")
    trainer.train()

    # Save the fine-tuned model
    print(f"\n  Saving model to {output_path}...")
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    # Also save as GGUF for Ollama deployment
    gguf_path = str(OUTPUT_DIR / "rabbit-v1-q4")
    print(f"  Saving GGUF (4-bit quantized) to {gguf_path}...")
    model.save_pretrained_gguf(gguf_path, tokenizer, quantization_method="q4_k_m")

    print(f"\n{'='*60}")
    print(f"  RABBIT — Fine-tuning complete!")
    print(f"  Model saved to: {output_path}")
    print(f"  GGUF saved to: {gguf_path}")
    print(f"  Next step: python scripts/evaluate.py")
    print(f"{'='*60}")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Fine-tune Phi-3.5 Mini for Reattend memory tasks"
    )
    parser.add_argument(
        "--base-model",
        default="unsloth/Phi-3.5-mini-instruct",
        help="Base model to fine-tune (default: unsloth/Phi-3.5-mini-instruct)",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs (default: 3)")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate (default: 2e-4)")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size (default: 2)")

    args = parser.parse_args()
    finetune(args.base_model, args.epochs, args.lr, args.batch_size)


if __name__ == "__main__":
    main()
