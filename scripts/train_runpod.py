import json, torch
from pathlib import Path
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

DATA_DIR = Path("/workspace/rabbit/data/filtered")
OUTPUT_PATH = "/workspace/rabbit-v1"
GGUF_PATH = "/workspace/rabbit-v1-gguf"
TASKS = ["intent","extract","triage","expand","answer","summarize","sentiment","importance","multiturn","dontknow"]
TASK_PREFIXES = {"intent":"[INTENT]","extract":"[EXTRACT]","triage":"[TRIAGE]","expand":"[EXPAND]","answer":"[ANSWER]","summarize":"[SUMMARIZE]","sentiment":"[SENTIMENT]","importance":"[IMPORTANCE]","multiturn":"[ANSWER]","dontknow":"[ANSWER]"}
TASK_SYSTEM_PROMPTS = {
    "intent":"You are Rabbit, Reattend's memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract":"You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage":"You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand":"You are Rabbit, Reattend's memory AI. Expand the user's vague query into a precise, comprehensive search query that captures their likely intent.",
    "answer":"You are Rabbit, Reattend's memory AI. Answer the user's question conversationally using the provided memory context. Tell a story, provide insight, cite sources as [1][2][3]. Include a Sources section and suggest Follow-up questions. Do not use markdown.",
    "summarize":"You are Rabbit, Reattend's memory AI. Generate a rich 2-4 sentence standalone summary of the given content. Capture the essence, key decisions, and action items.",
    "sentiment":"You are Rabbit, Reattend's memory AI. Classify the tone of the given content. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance":"You are Rabbit, Reattend's memory AI. Score the importance of the given content for organizational memory. Return a JSON object with keys: score (1-5) and reason (one sentence).",
    "multiturn":"You are Rabbit, Reattend's memory AI. Continue the conversation using the provided memory context. Build on what was already discussed. Cite sources as [1][2][3]. Include Sources and Follow-up questions. Do not use markdown.",
    "dontknow":"You are Rabbit, Reattend's memory AI. Answer the user's question using the provided memory context. If the memories don't fully answer the question, be honest about what's missing and suggest where to find it. Cite sources as [1][2][3]. Do not use markdown.",
}

print("Loading model...")
model, tokenizer = FastLanguageModel.from_pretrained(model_name="unsloth/Phi-3.5-mini-instruct", max_seq_length=2048, dtype=None, load_in_4bit=True)
model = FastLanguageModel.get_peft_model(model, r=16, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"], lora_alpha=16, lora_dropout=0, bias="none", use_gradient_checkpointing="unsloth")

print("Loading data...")
all_examples = []
for task in TASKS:
    fp = DATA_DIR / f"{task}_filtered.jsonl"
    if not fp.exists():
        continue
    count = 0
    for line in open(fp):
        if not line.strip():
            continue
        raw = json.loads(line.strip())
        output = raw["output"]
        if isinstance(output, dict):
            output = json.dumps(output)
        all_examples.append({"conversations":[{"role":"system","content":TASK_SYSTEM_PROMPTS[task]},{"role":"user","content":f"{TASK_PREFIXES[task]} {raw['input']}"},{"role":"assistant","content":output}]})
        count += 1
    print(f"  {task}: {count}")
print(f"  Total: {len(all_examples)}")

def format_chat(ex):
    return {"text": tokenizer.apply_chat_template(ex["conversations"], tokenize=False, add_generation_prompt=False)}

dataset = Dataset.from_list(all_examples).map(format_chat).shuffle(seed=42)
split = dataset.train_test_split(test_size=0.05, seed=42)
print(f"  Train: {len(split['train'])} | Eval: {len(split['test'])}")

print("\nStarting training...")
trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=split["train"], eval_dataset=split["test"], dataset_text_field="text", max_seq_length=2048,
    args=TrainingArguments(output_dir=OUTPUT_PATH, per_device_train_batch_size=2, gradient_accumulation_steps=4, warmup_steps=50, num_train_epochs=3, learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(), bf16=torch.cuda.is_bf16_supported(), logging_steps=25, eval_strategy="steps", eval_steps=200, save_strategy="steps", save_steps=500, save_total_limit=3, report_to="none", optim="adamw_8bit"))
stats = trainer.train()
print(f"\nDONE! Loss: {stats.training_loss:.4f} | Time: {stats.metrics['train_runtime']/60:.1f} min")

print("Saving model...")
model.save_pretrained(OUTPUT_PATH)
tokenizer.save_pretrained(OUTPUT_PATH)
print("Saving GGUF...")
model.save_pretrained_gguf(GGUF_PATH, tokenizer, quantization_method="q4_k_m")

print("\nTesting...")
FastLanguageModel.for_inference(model)
for prefix, inp in [("[INTENT]","What did we discuss with Brian last week?"),("[EXTRACT]","Met with Sarah from Acme on Tuesday. Budget confirmed at $45k."),("[EXPAND]","what about brian"),("[SENTIMENT]","This is frustrating. Nothing has changed."),("[ANSWER]","Question: What about pricing?\nMemories: [1] Mar 15 - freemium. [2] Mar 22 - costs high. [3] Mar 28 - usage-based.")]:
    task_name = prefix.strip("[]").lower()
    msgs = [{"role":"system","content":TASK_SYSTEM_PROMPTS[task_name]},{"role":"user","content":f"{prefix} {inp}"}]
    ids = tokenizer.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
    out = model.generate(input_ids=ids, max_new_tokens=256, temperature=0.1, do_sample=True)
    print(f"\n  {prefix}: {inp[:60]}")
    print(f"  -> {tokenizer.decode(out[0][ids.shape[-1]:], skip_special_tokens=True)}")

print("\n" + "="*50)
print("RABBIT v1 COMPLETE!")
print(f"GGUF at: {GGUF_PATH}")
print("="*50)
