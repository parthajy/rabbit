import json, torch, os
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

print("Loading base model...")
base = AutoModelForCausalLM.from_pretrained("microsoft/Phi-3.5-mini-instruct", torch_dtype=torch.float16, device_map="auto")
tok = AutoTokenizer.from_pretrained("microsoft/Phi-3.5-mini-instruct")

print("Loading Rabbit LoRA...")
hf_token = os.environ.get("HF_TOKEN", "")
model = PeftModel.from_pretrained(base, "reattend/rabbit-v1", token=hf_token)
model.eval()

SP = {
    "intent": "You are Rabbit, Reattend's memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand": "You are Rabbit, Reattend's memory AI. Expand the user's vague query into a precise, comprehensive search query that captures their likely intent.",
    "answer": "You are Rabbit, Reattend's memory AI. Answer the user's question using the provided memory context. Use citations [1][2][3] to reference sources. Do not use markdown formatting.",
    "summarize": "You are Rabbit, Reattend's memory AI. Generate a rich 2-4 sentence standalone summary of the given content. Capture the essence, key decisions, and action items.",
    "sentiment": "You are Rabbit, Reattend's memory AI. Classify the tone of the given content. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance": "You are Rabbit, Reattend's memory AI. Score the importance of the given content for organizational memory. Return a JSON object with keys: score (1-5) and reason (one sentence).",
}

tests = [
    ("[INTENT]", "What did we discuss with Brian last week?"),
    ("[INTENT]", "Who is responsible for the API integration?"),
    ("[EXTRACT]", "Met with Sarah from Acme on Tuesday. She agreed to send the contract by Friday. Budget confirmed at 45000 dollars."),
    ("[TRIAGE]", "Quick sync with dev team. Jake will fix the auth bug by EOD. Maria is starting the dashboard redesign next sprint."),
    ("[EXPAND]", "what about brian"),
    ("[EXPAND]", "pricing stuff"),
    ("[SUMMARIZE]", "Board meeting recap: Revenue hit 2.1M ARR. Decided to raise Series A in Q3. Tom from Sequoia expressed interest. Need to prep deck by end of month."),
    ("[SENTIMENT]", "This is frustrating. We discussed this three times and nothing has changed. The deadline is tomorrow and we still dont have a plan."),
    ("[SENTIMENT]", "Great news! The pilot went really well and the client wants to expand to all departments."),
    ("[IMPORTANCE]", "Team standup: CSS fix deployed. Lunch order changed to Thai. Jenkins build is green."),
    ("[IMPORTANCE]", "Emergency: production database is down. All users affected. Revenue impact estimated at 50k per hour."),
    ("[ANSWER]", "Question: What did we decide about pricing?\nMemories: [1] Meeting Mar 15 decided to go freemium generous limits. [2] Meeting Mar 22 costs too high reconsidering. [3] Meeting Mar 28 reversed decision going usage-based."),
]

print("\n" + "=" * 60)
print("  RABBIT v1 TEST BENCH")
print("=" * 60)

for prefix, inp in tests:
    task = prefix.strip("[]").lower()
    msgs = [{"role": "system", "content": SP[task]}, {"role": "user", "content": f"{prefix} {inp}"}]
    inputs = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True).to(model.device)
    input_len = inputs["input_ids"].shape[-1]
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=256, temperature=0.1, do_sample=True)
    resp = tok.decode(out[0][input_len:], skip_special_tokens=True)
    print(f"\n--- {prefix} ---")
    print(f"In:  {inp[:80]}")
    print(f"Out: {resp}")

print("\n" + "=" * 60)
print("  TEST COMPLETE")
print("=" * 60)
