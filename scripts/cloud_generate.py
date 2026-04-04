"""
Rabbit — Cloud Synthetic Data Generator
Runs on RunPod CPU pod. Generates 50K training examples across all 10 tasks.
Results are saved to /workspace/rabbit/data/synthetic/ and pushed to GitHub.

Usage (on RunPod):
    OPENAI_API_KEY=sk-xxx python scripts/cloud_generate.py
"""

import json
import os
import random
import time
import subprocess
from pathlib import Path

from openai import OpenAI, RateLimitError

# ── Config ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("data/synthetic")
MODEL = "gpt-4o-mini"

# How many examples per task
TASK_TARGETS = {
    "answer": 10000,
    "expand": 6000,
    "multiturn": 5000,
    "dontknow": 4000,
    "extract": 5000,
    "triage": 5000,
    "summarize": 4000,
    "intent": 4000,
    "sentiment": 4000,
    "importance": 3000,
}

UNIVERSES = [
    {
        "name": "NovaPay (Fintech, 35 people)",
        "industry": "Digital payments and lending platform for small businesses",
        "cast": ["Vikram (CEO)", "Ananya (CTO)", "Rohan (Product Lead)", "Meera (Design Head)",
                 "Arjun (Backend Lead)", "Priya (Data Science)", "Karthik (DevOps)", "Sneha (QA)",
                 "Aditya (Sales VP)", "Nisha (Customer Success)"],
        "projects": ["UPI integration for merchants", "Credit scoring ML model",
                     "KYC automation pipeline", "Merchant onboarding redesign"],
    },
    {
        "name": "EduSpark (EdTech, 25 people)",
        "industry": "AI-powered adaptive learning platform for K-12",
        "cast": ["Rahul (Founder/CEO)", "Divya (CTO)", "Amit (Content Head)", "Kavitha (Product)",
                 "Suresh (ML Engineer)", "Lakshmi (Frontend)", "Ravi (Backend)", "Sunita (QA)",
                 "Deepak (Partnerships)", "Anjali (Operations)"],
        "projects": ["Adaptive quiz engine", "Parent dashboard rollout",
                     "School district pilot (500 students)", "Content localization (Hindi, Tamil)"],
    },
    {
        "name": "HealthBridge (HealthTech, 40 people)",
        "industry": "Telemedicine and health records platform",
        "cast": ["Dr. Sanjay (CEO)", "Pooja (CTO)", "Manish (Product)", "Rekha (Compliance)",
                 "Nikhil (Backend)", "Shreya (Frontend)", "Varun (ML)", "Geeta (QA)",
                 "Rajesh (Sales)", "Komal (Customer Success)"],
        "projects": ["Video consultation v2", "HIPAA compliance audit",
                     "AI symptom checker", "Insurance claims integration"],
    },
    {
        "name": "BuildRight (Construction Tech, 20 people)",
        "industry": "Project management and IoT for construction sites",
        "cast": ["Sameer (CEO)", "Nandini (CTO)", "Prasad (Product)", "Asha (Design)",
                 "Vishal (IoT Engineer)", "Ramesh (Backend)", "Pallavi (Frontend)",
                 "Sunil (Field Ops)", "Bharti (Finance)", "Ganesh (Sales)"],
        "projects": ["Site safety monitoring IoT", "Vendor payment automation",
                     "Blueprint digitization AI", "Worker attendance tracking"],
    },
    {
        "name": "CraftOS (Dev Tools, 20 people)",
        "industry": "AI code review and development workflow automation",
        "cast": ["Ankit (Founder/CEO)", "Maya (CTO)", "Sahil (ML Lead)", "Diya (Product)",
                 "Nitin (Backend)", "Pooja (Frontend)", "Tarun (DevRel)", "Aditi (QA)",
                 "Rajan (Sales)", "Shreyas (Infrastructure)"],
        "projects": ["AI review accuracy improvement", "VS Code extension v2",
                     "Enterprise SSO integration", "Usage-based pricing migration"],
    },
    {
        "name": "GreenFleet (CleanTech, 30 people)",
        "industry": "Electric vehicle fleet management and charging",
        "cast": ["Arun (CEO)", "Smita (CTO)", "Vivek (Hardware Lead)", "Preeti (Product)",
                 "Mahesh (Backend)", "Swati (Data Science)", "Kunal (Mobile)", "Rita (Operations)",
                 "Siddharth (Partnerships)", "Jaya (Finance)"],
        "projects": ["Route optimization ML", "Charging station network expansion",
                     "Fleet analytics dashboard", "Government subsidy compliance"],
    },
    {
        "name": "LegalMind (LegalTech, 15 people)",
        "industry": "AI-powered contract analysis and legal research",
        "cast": ["Adv. Sharma (CEO)", "Tanya (CTO)", "Mohit (ML Lead)", "Vandana (Product)",
                 "Gaurav (Backend)", "Ritu (Frontend)", "Alok (Data)", "Meenakshi (Legal Ops)",
                 "Harsh (Sales)", "Poonam (Customer Success)"],
        "projects": ["Contract clause extraction", "Legal precedent search engine",
                     "Due diligence automation", "Multi-language contract support"],
    },
    {
        "name": "FoodChain (Supply Chain, 45 people)",
        "industry": "Farm-to-restaurant supply chain and logistics",
        "cast": ["Kishore (CEO)", "Neha (CTO)", "Prakash (Logistics Head)", "Swapna (Product)",
                 "Ajay (Backend)", "Bhavna (Data)", "Tushar (Mobile)", "Shalini (Operations)",
                 "Dinesh (Procurement)", "Kavya (Quality)"],
        "projects": ["Cold chain monitoring IoT", "Demand forecasting ML",
                     "Farmer onboarding app", "Restaurant inventory integration"],
    },
    {
        "name": "TravelMind (Travel Tech, 50 people)",
        "industry": "AI-powered corporate travel management",
        "cast": ["Arun (CEO)", "Pallavi (CTO)", "Mandar (Product Head)", "Swapnil (Backend Lead)",
                 "Ritika (Frontend Lead)", "Jayesh (Sales VP)", "Ankita (ML Engineer)",
                 "Viraj (Operations)", "Deepa (Finance)", "Sandeep (Customer Success)"],
        "projects": ["Smart itinerary builder", "Expense reconciliation automation",
                     "Hotel negotiation AI", "Travel policy compliance engine"],
    },
    {
        "name": "CloudNest (SaaS, 60 people)",
        "industry": "Multi-tenant cloud infrastructure management",
        "cast": ["Srinivas (CEO)", "Aparna (CTO)", "Venkat (Platform Lead)", "Lavanya (Product)",
                 "Chandra (SRE Lead)", "Bharat (Security)", "Padma (Frontend)", "Mohan (Backend)",
                 "Sushma (Sales)", "Girish (Solutions Architect)"],
        "projects": ["Multi-cloud cost optimizer", "Kubernetes auto-scaling v2",
                     "SOC2 compliance automation", "Self-serve enterprise onboarding"],
    },
]

# Task instructions (shortened for cloud script)
TASK_INSTRUCTIONS = {
    "intent": """Generate intent classification examples.
- "input": a natural question about organizational memory
- "output": exactly ONE word: factual | entity | temporal | synthesis | actions | history | aggregation""",

    "extract": """Generate entity extraction examples from organizational content.
- "input": raw text (meeting, email, Slack, standup, note, calendar, CRM)
- "output": JSON with keys: people, organizations, decisions, action_items, dates, topics""",

    "triage": """Generate classification examples for organizational content.
- "input": raw text from any source
- "output": JSON with keys: type (meeting/email/note/standup/conversation/calendar/decision), summary, tags""",

    "expand": """Generate query expansion examples.
- "input": vague/short user query (2-5 words, casual, abbreviated)
- "output": expanded precise search query that captures likely intent""",

    "answer": """Generate CONVERSATIONAL Q&A examples over 5-7 retrieved memories.
- "input": "Question: [question]\\nMemories: [1] source, date — content [2]...[3]...[4]...[5]..."
- "output": Rich conversational answer in this format:

[2-4 paragraph narrative. Tell a STORY. Add INSIGHT. Use "What's interesting is...", "This suggests...", "The pattern here is...". Cite as [1][2] etc.]

Sources:
[1] Source Type, Date — Brief description
[2] Source Type, Date — Brief description

Follow-up questions:
→ Relevant follow-up question
→ Another question
→ Deeper reasoning question

Rules: Sound like a smart colleague. NO markdown. Always include Sources and Follow-up sections.""",

    "summarize": """Generate standalone summary examples.
- "input": raw text from any organizational source
- "output": rich 2-4 sentence summary capturing essence, decisions, and action items""",

    "sentiment": """Generate sentiment classification examples.
- "input": organizational text (meeting, email, Slack, standup)
- "output": exactly ONE word: positive | negative | neutral | tense | urgent""",

    "importance": """Generate importance scoring examples.
- "input": organizational text
- "output": JSON with "score" (1-5) and "reason" (one sentence)
Scores: 5=company-changing, 4=team-level, 3=regular+decisions, 2=routine, 1=noise""",

    "multiturn": """Generate multi-turn conversation examples.
- "input": "Turn 1 Question: [q1]\\nTurn 1 Answer: [a1 with citations]\\nMemories: [1]...[2]...[3]...\\nTurn 2 Question: [follow-up]"
- "output": Conversational answer building on Turn 1. Include Sources and Follow-up questions sections.
Follow-ups should be natural: "Tell me more about...", "When was that?", "Who disagreed?".""",

    "dontknow": """Generate examples where memories DON'T fully answer the question.
- "input": "Question: [question]\\nMemories: [1]...[2]...[3]..."
- "output": Honest response that:
  1. Says what IS known from memories
  2. States what's MISSING
  3. Suggests where to find it
Include Sources and Follow-up questions. NEVER make up info.""",
}


def generate_batch(client, task, universe, count=25):
    """Generate a batch of examples for a task."""
    uni = universe
    prompt = f"""You are generating training data for Rabbit, an AI model for organizational memory.

Organization: {uni['name']}
Industry: {uni['industry']}
People: {', '.join(uni['cast'])}
Projects: {', '.join(uni['projects'])}

TASK: {task.upper()}
{TASK_INSTRUCTIONS[task]}

Generate {count} diverse examples as JSONL. Each line: {{"input": "...", "output": "..."}}
Use the organization's people, projects, and context. Make it realistic.
Output ONLY valid JSONL lines, nothing else."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            timeout=120,
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
    """Generate examples for a single task. Runs in its own thread."""
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
    lock = __import__('threading').Lock()

    while generated < remaining:
        universe = random.choice(UNIVERSES)
        batch_size = min(25, remaining - generated)

        examples = generate_batch(client, task, universe, batch_size)

        if examples:
            with lock:
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

    total_target = sum(TASK_TARGETS.values())

    print(f"\n{'='*60}")
    print(f"  RABBIT — Cloud Data Generator (PARALLEL)")
    print(f"  Target: {total_target:,} examples across {len(TASK_TARGETS)} tasks")
    print(f"  Running {len(TASK_TARGETS)} tasks in parallel")
    print(f"{'='*60}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {}
        for task, target in TASK_TARGETS.items():
            futures[executor.submit(generate_task, client, task, target)] = task

        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                count = future.result()
                print(f"  >> {task} completed: {count}")
            except Exception as e:
                print(f"  >> {task} FAILED: {e}")

    print(f"\n{'='*60}")
    print(f"  RABBIT — Generation Complete!")
    print(f"{'='*60}")

    # Show final counts
    print(f"\n  Final counts:")
    for task in TASK_TARGETS:
        outfile = OUTPUT_DIR / f"{task}_synthetic.jsonl"
        if outfile.exists():
            with open(outfile) as f:
                count = sum(1 for line in f if line.strip())
            print(f"    {task:15s} {count:>8,}")

    # Try to push to git
    print(f"\n  Pushing to GitHub...")
    try:
        subprocess.run(["git", "add", "data/synthetic/"], check=True)
        subprocess.run(["git", "commit", "-m", "Cloud-generated synthetic data (50K batch)"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("  Pushed to GitHub!")
    except Exception as e:
        print(f"  Git push failed: {e}")
        print("  Data is saved locally at data/synthetic/")


if __name__ == "__main__":
    run()
