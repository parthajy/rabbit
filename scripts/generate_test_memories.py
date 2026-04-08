"""
Generate 5,000 realistic organizational memories for a single fictional company.
These simulate 6 months of a 50-person startup's communication.
Used for: stress testing Rabbit, A/B comparison, and future v1.5 training.

Usage:
    OPENAI_API_KEY=sk-xxx python3.13 scripts/generate_test_memories.py
"""

import json
import os
import random
import time
from pathlib import Path

from openai import OpenAI, RateLimitError

OUTPUT_DIR = Path("data/test_memories")
MODEL = "gpt-4o-mini"

# ONE company, consistent characters, evolving story over 6 months
COMPANY = {
    "name": "NexusAI",
    "industry": "AI-powered customer success platform for SaaS companies",
    "size": "50 people, Series A ($4M), 18 months old",
    "hq": "Bangalore, India with remote team in US",
    "teams": {
        "leadership": ["Arjun Mehta (CEO/Founder)", "Priya Krishnamurthy (CTO/Co-founder)", "David Chen (VP Sales, US)", "Nandita Rao (VP Product)"],
        "engineering": ["Karthik Iyer (Backend Lead)", "Ananya Sharma (Frontend Lead)", "Rohan Gupta (ML Engineer)", "Sneha Pillai (DevOps)", "Jake Morrison (Senior Backend, US)", "Pooja Nair (QA Lead)", "Aditya Venkatesh (Junior Dev)", "Meera Desai (Junior Dev)"],
        "product": ["Amit Patel (Product Manager)", "Kavitha Sundaram (UX Designer)", "Ritu Joshi (Product Analyst)"],
        "sales": ["Jayesh Bhatt (Account Executive)", "Ritika Malhotra (SDR)", "Tom Bradley (Enterprise AE, US)", "Sandeep Kumar (Solutions Engineer)"],
        "cs": ["Deepa Raghavan (CS Lead)", "Viraj Mehta (CSM)", "Ankita Singh (CSM)"],
        "ops": ["Rekha Srinivasan (HR/Ops)", "Sunil Nambiar (Finance)"],
    },
    "clients": ["Acme SaaS ($120K ARR)", "TechCorp ($85K ARR)", "DataFlow ($200K ARR, largest client)", "StartupGrid ($45K ARR)", "CloudBase ($60K ARR)", "Momentum ($30K ARR, new)", "Enterprise One ($350K, in negotiation)"],
    "projects": ["Platform v3.0 (major rewrite)", "Enterprise SSO", "AI Health Score (ML-powered churn prediction)", "Self-serve onboarding", "Mobile app MVP", "SOC2 compliance"],
    "timeline": "October 2025 — March 2026",
}

MEMORY_TYPES = {
    "meeting_transcript": 1500,
    "email_thread": 1200,
    "slack_message": 800,
    "standup_note": 600,
    "decision_log": 400,
    "calendar_event": 300,
    "voice_memo_transcript": 200,
}

MONTH_CONTEXTS = {
    "October 2025": "Q4 push. DataFlow threatening to churn. Platform v3.0 kickoff. Hiring 3 engineers.",
    "November 2025": "DataFlow saved with custom feature. SOC2 audit started. Jake frustrated with codebase. Series A investors want growth numbers.",
    "December 2025": "Holiday slowdown. Year-end review. Revenue $1.8M ARR. Enterprise One first contact. Team morale mixed — some burnout.",
    "January 2026": "New year planning. OKRs set. AI Health Score v1 shipped. Enterprise One demo went well. Hired 2 junior devs.",
    "February 2026": "Enterprise One negotiation intense. Platform v3.0 delayed. Frontend team blocked on design. David pushing for faster sales cycle.",
    "March 2026": "Enterprise One signed at $350K! Platform v3.0 shipped (2 weeks late). Jake gave notice. Team celebration then panic about Jake leaving.",
}


def generate_batch(client, memory_type, month, context, count=20):
    teams_str = "\n".join(f"  {team}: {', '.join(members)}" for team, members in COMPANY["teams"].items())

    prompt = f"""Generate {count} realistic {memory_type.replace('_', ' ')} memories for this company:

COMPANY: {COMPANY['name']} — {COMPANY['industry']}
Size: {COMPANY['size']}
HQ: {COMPANY['hq']}

TEAMS:
{teams_str}

CLIENTS: {', '.join(COMPANY['clients'])}
PROJECTS: {', '.join(COMPANY['projects'])}

MONTH: {month}
CONTEXT: {context}

Generate {count} {memory_type.replace('_', ' ')}s as JSONL. Each line:
{{
  "type": "{memory_type}",
  "date": "YYYY-MM-DD",
  "title": "Short descriptive title",
  "content": "The full text of the memory as it would naturally appear",
  "participants": ["Person 1", "Person 2"],
  "source": "{memory_type}"
}}

RULES:
- Use EXACT names from the team list. Never invent names.
- Make it realistic — include casual language, abbreviations, incomplete thoughts
- Include mundane stuff (50%) AND important decisions (30%) AND conflicts/tensions (20%)
- Reference specific clients, projects, and deadlines
- Show evolution — decisions get revisited, priorities shift, people disagree
- Include cross-references: "as we discussed in last week's meeting", "per Priya's email"
- Vary length: some are 2 lines (Slack), some are 500 words (meeting transcripts)
- Output ONLY valid JSONL."""

    try:
        response = client.chat.completions.create(
            model=MODEL, max_tokens=4096, timeout=120,
            messages=[
                {"role": "system", "content": "Generate realistic organizational memories as JSONL. Output ONLY valid JSON lines. Use exact names provided."},
                {"role": "user", "content": prompt},
            ],
        )
        memories = []
        text = response.choices[0].message.content or ""
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("```"):
                continue
            try:
                obj = json.loads(line)
                if "content" in obj and "type" in obj:
                    memories.append(obj)
            except json.JSONDecodeError:
                continue
        return memories
    except RateLimitError:
        time.sleep(30)
        return []
    except Exception as e:
        print(f"    Error: {e}")
        time.sleep(5)
        return []


def run():
    import concurrent.futures

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outfile = OUTPUT_DIR / "nexusai_memories.jsonl"

    existing = 0
    if outfile.exists():
        with open(outfile) as f:
            existing = sum(1 for line in f if line.strip())

    total_target = sum(MEMORY_TYPES.values())
    remaining = total_target - existing

    print(f"\n{'='*60}")
    print(f"  NEXUSAI — Realistic Memory Generator")
    print(f"  Company: {COMPANY['name']}")
    print(f"  Target: {total_target} memories (existing: {existing})")
    print(f"  Types: {len(MEMORY_TYPES)} | Months: {len(MONTH_CONTEXTS)}")
    print(f"{'='*60}\n")

    if remaining <= 0:
        print("  Already at target!")
        return

    months = list(MONTH_CONTEXTS.items())
    generated = 0
    batch_num = 0

    for memory_type, type_target in MEMORY_TYPES.items():
        type_generated = 0
        per_month = type_target // len(months)

        print(f"  Generating {memory_type}: {type_target} total ({per_month}/month)")

        for month, context in months:
            month_generated = 0
            while month_generated < per_month:
                batch_size = min(20, per_month - month_generated)
                memories = generate_batch(client, memory_type, month, context, batch_size)

                if memories:
                    with open(outfile, "a") as f:
                        for mem in memories:
                            f.write(json.dumps(mem, ensure_ascii=False) + "\n")
                    month_generated += len(memories)
                    type_generated += len(memories)
                    generated += len(memories)

                batch_num += 1
                if batch_num % 10 == 0:
                    print(f"    [{memory_type}] {type_generated}/{type_target} (total: {existing + generated})")

                time.sleep(0.2)

        print(f"  [{memory_type}] DONE: {type_generated}")

    print(f"\n{'='*60}")
    print(f"  COMPLETE! Total memories: {existing + generated}")
    with open(outfile) as f:
        final = sum(1 for line in f if line.strip())
    print(f"  File: {outfile} ({final} lines)")

    # Stats
    types = {}
    with open(outfile) as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                t = obj.get("type", "unknown")
                types[t] = types.get(t, 0) + 1
    print(f"  Breakdown:")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
