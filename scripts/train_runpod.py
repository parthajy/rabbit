import json, torch
from pathlib import Path
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

DATA_DIR = Path("/workspace/rabbit/data/filtered")
OUTPUT_PATH = "/workspace/rabbit-v1.3"
GGUF_PATH = "/workspace/rabbit-v1.3-gguf"
TASKS = ["intent","extract","triage","expand","answer","summarize","sentiment","importance","multiturn","dontknow","link","ambient","faithful_extract","formatted_answer","followup_answer","clean_json","compile","lint","compile_answer"]
TASK_PREFIXES = {"intent":"[INTENT]","extract":"[EXTRACT]","triage":"[TRIAGE]","expand":"[EXPAND]","answer":"[ANSWER]","summarize":"[SUMMARIZE]","sentiment":"[SENTIMENT]","importance":"[IMPORTANCE]","multiturn":"[ANSWER]","dontknow":"[ANSWER]","link":"[LINK]","ambient":"[AMBIENT]","faithful_extract":"[EXTRACT]","formatted_answer":"[ANSWER]","followup_answer":"[ANSWER]","clean_json":"[EXTRACT]","compile":"[COMPILE]","lint":"[LINT]","compile_answer":"[COMPILE]"}
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
    "link":"You are Rabbit, Reattend's memory AI. Given a source record and candidate records, determine which candidates are meaningfully related. Return JSON with a links array. Each link: target_id, kind (same_topic/depends_on/contradicts/continuation_of/same_people/causes/temporal), weight (0-1), explanation. Max 8 links. If none related, return {\"links\": []}.",
    "ambient":"You are Rabbit, Reattend's memory AI. You see what the user is doing (screen text) and related memories. Decide whether to alert. Return {\"show\": false} if no alert. Or {\"show\": true, \"reason\": \"contradiction|forgotten_commitment|critical_context\", \"memory_indices\": [1,2], \"context\": \"explanation\"} if they need to know. Only alert for genuine issues.",
    "faithful_extract":"You are Rabbit, Reattend's memory AI. Extract structured information. Return JSON with keys: people, organizations, decisions, action_items, dates, topics. CRITICAL: Reproduce every name, number, and date EXACTLY as in the input. Never alter proper nouns.",
    "formatted_answer":"You are Rabbit, Reattend's memory AI. Answer conversationally. Use **bold** for names and key decisions. Cite as [1][2][3]. MUST end with Sources: and Follow-up questions: (3 questions with →). Minimum 300 words.",
    "followup_answer":"You are Rabbit, Reattend's memory AI. Answer using memories. Always end with Follow-up questions: section with exactly 3 questions prefixed with →.",
    "clean_json":"You are Rabbit, Reattend's memory AI. Extract structured information. Return ONLY valid JSON. No text before or after. No markdown.",
    "compile":"You are Rabbit, Reattend's memory AI. Update an existing wiki page with new information. Preserve valid existing info, add new details, note contradictions. Format: Summary, Key People, Open Items, Recent Activity, Related Topics.",
    "lint":"You are Rabbit, Reattend's memory AI. Audit the knowledge base. Return JSON with: contradictions, stale_items, missing_links, suggested_actions.",
    "compile_answer":"You are Rabbit, Reattend's memory AI. Convert a synthesized answer into a wiki entry. Return JSON with: title, content, category, source_ids, auto_update, keywords.",
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

print("\nTesting...")
FastLanguageModel.for_inference(model)
test_cases = [
    ("[INTENT]","What did we discuss with Brian last week?"),
    ("[EXTRACT]","Met with Sarah from Acme on Tuesday. Budget confirmed at $45k."),
    ("[EXPAND]","what about brian"),
    ("[SENTIMENT]","This is frustrating. Nothing has changed."),
    ("[IMPORTANCE]","Emergency: production DB is down. Revenue impact $50k/hr."),
    ("[LINK]","SOURCE RECORD:\nTitle: Pricing decision reversed\nSummary: Team reversed freemium decision, moving to usage-based pricing due to cost concerns.\n\nCANDIDATES:\n1. [id-1] Freemium launch plan: Team discussed generous free tier limits and growth projections.\n2. [id-2] Q2 hiring plan: Engineering team needs 3 more backend devs.\n3. [id-3] Cost analysis from Finance: Monthly infrastructure costs 40% over budget with freemium model.\n4. [id-4] Customer feedback survey: Enterprise clients prefer predictable pricing.\n5. [id-5] Sprint planning: Next sprint focused on payment integration."),
    ("[AMBIENT]","SCREEN TEXT (from Gmail):\nHi Tom, confirming our meeting for October 15th to discuss the renewal at $45,000.\n\nRELATED MEMORIES:\n1. [meeting] Client call with Tom: Discussed renewal timeline, agreed on September 30th deadline.\n2. [email] Tom's email: Budget approved at $42,000 not $45,000.\n3. [note] Account notes: Tom prefers quarterly billing."),
    ("[ANSWER]","Question: What happened with the pricing decision?\nMemories: [1] Meeting Mar 15 - team decided on freemium with generous limits. [2] Email Mar 20 - Finance flagged costs as unsustainable. [3] Meeting Mar 22 - heated discussion about costs. [4] Slack Mar 25 - CEO asked for alternatives. [5] Meeting Mar 28 - reversed decision, going usage-based."),
]
for prefix, inp in test_cases:
    task_name = prefix.strip("[]").lower()
    msgs = [{"role":"system","content":TASK_SYSTEM_PROMPTS[task_name]},{"role":"user","content":f"{prefix} {inp}"}]
    ids = tokenizer.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
    out = model.generate(input_ids=ids, max_new_tokens=512, temperature=0.1, do_sample=True)
    print(f"\n  {prefix}: {inp[:80]}")
    print(f"  -> {tokenizer.decode(out[0][ids.shape[-1]:], skip_special_tokens=True)}")

print("\n" + "="*50)
print("RABBIT v1.3 COMPLETE!")
print(f"Model at: {OUTPUT_PATH}")
print("="*50)
