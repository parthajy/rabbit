"""
Rabbit v1.4 — Targeted training data generator
Focuses on: faithful extraction (no hallucination), clean JSON, better formatting.
Run on RunPod CPU pod.

Usage:
    OPENAI_API_KEY=sk-xxx python3.13 scripts/generate_v14_data.py
"""

import json
import os
import random
import time
from pathlib import Path

from openai import OpenAI, RateLimitError

OUTPUT_DIR = Path("data/synthetic")
MODEL = "gpt-4o-mini"

# 20K total: focused on quality gaps
TASK_TARGETS = {
    "faithful_extract": 8000,     # Was 3000, need more to kill hallucination
    "clean_json": 4000,           # Was 2000, need cleaner outputs
    "formatted_answer": 5000,     # Was 2809, need more bold + sources + followups
    "compile": 3000,              # Keep at 3000
}

UNIVERSES = [
    {"name": "NovaPay (Fintech, 35 people)", "industry": "Digital payments", "cast": ["Vikram (CEO)", "Ananya (CTO)", "Rohan (Product)", "Meera (Design)", "Arjun (Backend)", "Priya (Data Science)", "Karthik (DevOps)", "Sneha (QA)", "Aditya (Sales VP)", "Nisha (CS)"], "projects": ["UPI integration", "Credit scoring ML", "KYC automation", "Merchant onboarding"]},
    {"name": "EduSpark (EdTech, 25 people)", "industry": "AI learning platform", "cast": ["Rahul (CEO)", "Divya (CTO)", "Amit (Content)", "Kavitha (Product)", "Suresh (ML)", "Lakshmi (Frontend)", "Ravi (Backend)", "Sunita (QA)", "Deepak (Partnerships)", "Anjali (Ops)"], "projects": ["Adaptive quiz engine", "Parent dashboard", "School pilot", "Content localization"]},
    {"name": "HealthBridge (HealthTech, 40 people)", "industry": "Telemedicine", "cast": ["Dr. Sanjay (CEO)", "Pooja (CTO)", "Manish (Product)", "Rekha (Compliance)", "Nikhil (Backend)", "Shreya (Frontend)", "Varun (ML)", "Geeta (QA)", "Rajesh (Sales)", "Komal (CS)"], "projects": ["Video consultation v2", "HIPAA audit", "Symptom checker AI", "Insurance claims"]},
    {"name": "BuildRight (Construction Tech)", "industry": "Project management IoT", "cast": ["Sameer (CEO)", "Nandini (CTO)", "Prasad (Product)", "Asha (Design)", "Vishal (IoT)", "Ramesh (Backend)", "Pallavi (Frontend)", "Sunil (Field Ops)", "Bharti (Finance)", "Ganesh (Sales)"], "projects": ["Site safety IoT", "Vendor payments", "Blueprint AI", "Worker tracking"]},
    {"name": "LegalMind (LegalTech)", "industry": "AI contract analysis", "cast": ["Adv. Sharma (CEO)", "Tanya (CTO)", "Mohit (ML)", "Vandana (Product)", "Gaurav (Backend)", "Ritu (Frontend)", "Alok (Data)", "Meenakshi (Legal Ops)", "Harsh (Sales)", "Poonam (CS)"], "projects": ["Clause extraction", "Precedent search", "Due diligence", "Multi-language contracts"]},
    {"name": "FoodChain (Supply Chain, 45 people)", "industry": "Farm-to-restaurant logistics", "cast": ["Kishore (CEO)", "Neha (CTO)", "Prakash (Logistics)", "Swapna (Product)", "Ajay (Backend)", "Bhavna (Data)", "Tushar (Mobile)", "Shalini (Ops)", "Dinesh (Procurement)", "Kavya (Quality)"], "projects": ["Cold chain IoT", "Demand forecasting", "Farmer app", "Restaurant inventory"]},
    {"name": "CloudNest (SaaS, 60 people)", "industry": "Multi-tenant cloud infrastructure", "cast": ["Srinivas (CEO)", "Aparna (CTO)", "Venkat (Platform)", "Lavanya (Product)", "Chandra (SRE)", "Bharat (Security)", "Padma (Frontend)", "Mohan (Backend)", "Sushma (Sales)", "Girish (Solutions)"], "projects": ["Multi-cloud optimizer", "K8s autoscaling v2", "SOC2 automation", "Self-serve onboarding"]},
    {"name": "GreenFleet (CleanTech)", "industry": "EV fleet management", "cast": ["Arun (CEO)", "Smita (CTO)", "Vivek (Hardware)", "Preeti (Product)", "Mahesh (Backend)", "Swati (Data Science)", "Kunal (Mobile)", "Rita (Ops)", "Siddharth (Partnerships)", "Jaya (Finance)"], "projects": ["Route optimization", "Charging network", "Fleet analytics", "Govt subsidy compliance"]},
]

TASK_INSTRUCTIONS = {
    "faithful_extract": """Generate entity extraction examples where EXACT name reproduction is CRITICAL.
- "input": text with specific names, dollar amounts, dates, emails, companies
- "output": JSON {people, organizations, decisions, action_items, dates, topics}

CRITICAL RULES:
- Every name MUST appear EXACTLY as in input. "Sarah" = "Sarah", NEVER "Sara", "Sarcis", "Saroks"
- Every number EXACTLY as stated. "$45,000" stays "$45,000"
- Every date EXACTLY. "April 15" stays "April 15"
- Include TRICKY names: Priyanka, Sreejith, Venkataraman, Muhammad, Krzyzewski
- Include mixed formats: "$2.1M ARR", "Q2 2026", "v2.0.1"
- Output ONLY valid JSON. No markdown. No explanation.
- action_items should reference the EXACT person name from input, not invented names

WRONG: {"action_items": ["Saroks to send contract"]}
RIGHT: {"action_items": ["Sarah to send the contract by Friday"]}""",

    "clean_json": """Generate examples for JSON-output signals. Output MUST be PURE JSON.
Mix of extract, triage, importance, link, ambient.
- "output": ONLY valid JSON. Nothing before/after. No markdown. No explanation.

BAD: ```json\n{"score": 3}\n```
GOOD: {"score": 3}

BAD: {"links": [...]} This is because...
GOOD: {"links": [...]}""",

    "formatted_answer": """Generate conversational Q&A with PROPER formatting.
- "input": "Question: [q]\nMemories: [1] source, date — content [2]...[3]...[4]...[5]..."
- "output": MUST use this EXACT structure:

[2-4 paragraphs. Use **bold** for person names on first mention. Use **bold** for key decisions. Cite as [1][2]. Use reasoning: "What's interesting is...", "The pattern suggests...", "This indicates..."]

Sources:
[1] Source Type, Date — Description
[2] Source Type, Date — Description

Follow-up questions:
→ First question
→ Second question
→ Third question

MANDATORY: **bold** names, Sources: section, Follow-up questions: with →, minimum 300 words.""",

    "compile": """Generate COMPILE examples — updating wiki pages with new info.
- "input": "EXISTING PAGE:\n[current page]\n\nNEW MEMORY:\n[new info]"
- "output": Updated page merging new info. Format: Summary, Key People, Open Items, Recent Activity, Related Topics.
If new info contradicts existing, note: "Previously X, now Y (updated Apr 7)".""",
}


def generate_batch(client, task, universe, count=25):
    uni = universe
    prompt = f"""Generate training data for Rabbit AI.
Organization: {uni['name']} ({uni['industry']})
People: {', '.join(uni['cast'])}
Projects: {', '.join(uni['projects'])}

TASK: {task.upper()}
{TASK_INSTRUCTIONS[task]}

Generate {count} diverse examples as JSONL. Each line: {{"input": "...", "output": "..."}}
Output ONLY valid JSONL."""

    try:
        response = client.chat.completions.create(
            model=MODEL, max_tokens=4096, timeout=120,
            messages=[
                {"role": "system", "content": "Generate training data as JSONL. Output ONLY valid JSON lines."},
                {"role": "user", "content": prompt},
            ],
        )
        examples = []
        text = response.choices[0].message.content or ""
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("```"):
                continue
            try:
                obj = json.loads(line)
                if "input" in obj and "output" in obj:
                    examples.append(obj)
            except json.JSONDecodeError:
                continue
        return examples
    except RateLimitError:
        time.sleep(30)
        return []
    except Exception as e:
        print(f"    Error: {e}")
        time.sleep(5)
        return []


def generate_task(client, task, target):
    import threading
    outfile = OUTPUT_DIR / f"{task}_synthetic.jsonl"
    existing = 0
    if outfile.exists():
        with open(outfile) as f:
            existing = sum(1 for line in f if line.strip())
    remaining = target - existing
    if remaining <= 0:
        print(f"  {task}: already at {existing} (target: {target}) — skipping")
        return existing
    print(f"  Starting {task}: existing={existing}, target={target}, need={remaining}")
    generated = 0
    batch_num = 0
    while generated < remaining:
        universe = random.choice(UNIVERSES)
        examples = generate_batch(client, task, universe, 25)
        if examples:
            with open(outfile, "a") as f:
                for ex in examples:
                    f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            generated += len(examples)
            batch_num += 1
            if batch_num % 10 == 0:
                print(f"    [{task}] Batch {batch_num}: {existing + generated}/{target}")
        time.sleep(0.1)
    print(f"  [{task}] DONE — {existing + generated} total")
    return existing + generated


def run():
    import concurrent.futures
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    client = OpenAI(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  RABBIT v1.4 — Training Data Generator")
    print(f"  Target: {sum(TASK_TARGETS.values()):,} examples")
    print(f"{'='*60}\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(generate_task, client, task, target): task for task, target in TASK_TARGETS.items()}
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                count = future.result()
                print(f"  >> {task} completed: {count}")
            except Exception as e:
                print(f"  >> {task} FAILED: {e}")
    print(f"\n{'='*60}")
    print(f"  Generation Complete!")
    for task in TASK_TARGETS:
        outfile = OUTPUT_DIR / f"{task}_synthetic.jsonl"
        if outfile.exists():
            with open(outfile) as f:
                print(f"    {task}: {sum(1 for line in f if line.strip())}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
