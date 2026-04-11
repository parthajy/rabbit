"""
Generate Rabbit v2.0 training data for Qwen 2.5 32B.

Creates ~50K NEW examples with longer, more complex inputs:
- Long extractions (1000-5000 word inputs)
- Multi-scope answers (individual, team, vertical, executive)
- Reasoning and suggestions
- Contradiction detection
- Knowledge compilation (wiki pages)
- Long triage/summarize

Uses OpenAI API (gpt-4o-mini) for generation.
Run two instances in parallel by splitting the work:
  python generate_v2_data.py --part 1  (runs first half)
  python generate_v2_data.py --part 2  (runs second half)

Output: data/synthetic/v2_*.jsonl
"""

import json
import os
import sys
import random
import time
import argparse
from pathlib import Path

API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

# ── Universes ──────────────────────────────────────────────
# Each universe is a fictional company with consistent characters
UNIVERSES = [
    {
        "company": "Meridian Health",
        "industry": "healthcare",
        "people": ["Dr. Ananya Rao", "James Chen", "Maria Santos", "David Park", "Lisa Okonkwo", "Dr. Raj Kapoor", "Sarah Mitchell", "Tom Nguyen"],
        "teams": ["Clinical", "Engineering", "Operations", "Compliance", "Product"],
        "projects": ["Patient Portal 2.0", "HIPAA Audit", "Telemedicine Expansion", "EMR Migration"],
        "topics": ["patient data", "FDA compliance", "clinical trials", "insurance integration"],
    },
    {
        "company": "Axion Finance",
        "industry": "fintech",
        "people": ["Priya Sharma", "Marcus Johnson", "Elena Volkov", "Kevin O'Brien", "Zara Ahmed", "Chris Wu", "Rachel Green", "Nathan Cole"],
        "teams": ["Risk", "Engineering", "Sales", "Compliance", "Product"],
        "projects": ["Basel III Implementation", "Mobile Banking v3", "KYC Automation", "Fraud Detection ML"],
        "topics": ["regulatory compliance", "transaction monitoring", "credit risk", "market volatility"],
    },
    {
        "company": "NovaTech Solutions",
        "industry": "enterprise SaaS",
        "people": ["Karan Mehta", "Sophie Anderson", "Diego Ramirez", "Fatima Al-Hassan", "Ben Thompson", "Yuki Tanaka", "Alex Rivera", "Nina Petrova"],
        "teams": ["Frontend", "Backend", "DevOps", "Design", "Sales", "Customer Success"],
        "projects": ["Platform v4 Migration", "Enterprise SSO", "Analytics Dashboard", "API Gateway v2"],
        "topics": ["microservices", "Kubernetes", "customer onboarding", "ARR growth", "churn reduction"],
    },
    {
        "company": "GreenPath Energy",
        "industry": "clean energy",
        "people": ["Arjun Reddy", "Clara Johansson", "Michael Obi", "Sana Khan", "Patrick Dubois", "Mei Lin", "Jack Morrison", "Amara Diallo"],
        "teams": ["R&D", "Operations", "Policy", "Engineering", "Finance"],
        "projects": ["Solar Grid Optimization", "Carbon Credit Platform", "Battery Storage Pilot", "Government Tender Q3"],
        "topics": ["renewable energy", "grid stability", "carbon offsets", "regulatory policy", "ESG reporting"],
    },
    {
        "company": "LexShield Legal",
        "industry": "legal tech",
        "people": ["Amanda Chen", "Robert Fitzgerald", "Deepa Nair", "Carlos Mendez", "Emily Watson", "Omar Hassan", "Victoria Lee", "Thomas Blake"],
        "teams": ["Litigation", "Corporate", "IP", "Engineering", "Operations"],
        "projects": ["Contract AI Review", "Case Management v2", "Compliance Tracker", "Client Portal"],
        "topics": ["contract review", "IP filings", "litigation strategy", "billing automation", "client confidentiality"],
    },
]

MEMORY_SOURCES = ["meeting", "email", "slack", "calendar", "document", "note", "voice_memo", "report"]

# ── API Call ───────────────────────────────────────────────

def call_api(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call OpenAI API."""
    import urllib.request

    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  API error: {e}")
        return ""


# ── Generators ─────────────────────────────────────────────

def generate_long_extract(universe: dict) -> dict | None:
    """Generate a long meeting/document with full extraction."""
    source = random.choice(["meeting transcript", "email thread", "project report", "slack thread"])
    num_people = random.randint(3, 6)
    people = random.sample(universe["people"], num_people)
    project = random.choice(universe["projects"])
    topic = random.choice(universe["topics"])

    prompt = f"""Generate a realistic {source} for {universe['company']} ({universe['industry']}).

Participants: {', '.join(people)}
Project: {project}
Topic: {topic}

Requirements:
- Must be 800-2000 words long
- Include at least {num_people} people speaking or mentioned
- Include at least 3 specific decisions made
- Include at least 4 action items with owners and deadlines
- Include at least 5 specific dates
- Include specific numbers (budgets, metrics, percentages)
- Feel realistic, not generic
- Include disagreements or tensions where natural

Write ONLY the raw transcript/content. No metadata or headers."""

    content = call_api("You are a corporate content simulator. Generate realistic organizational content.", prompt, max_tokens=3000)
    if not content or len(content) < 500:
        return None

    # Now generate the extraction
    extract_prompt = f"""Extract structured information from this {source}. Return ONLY valid JSON.

TEXT:
{content}

Return JSON with these exact keys:
- people: array of full names mentioned
- organizations: array of company/team names
- decisions: array of specific decisions made (quote them precisely)
- action_items: array of objects with "owner", "task", "due" keys
- dates: array of all dates mentioned
- topics: array of key topics discussed"""

    output = call_api("Return only valid JSON. No markdown.", extract_prompt, max_tokens=1500)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().strip("```json").strip("```"))
    except:
        return None

    return {
        "input": f"[EXTRACT] {content}",
        "output": json.dumps(parsed),
    }


def generate_long_triage(universe: dict) -> dict | None:
    """Generate long content with triage classification."""
    source = random.choice(MEMORY_SOURCES)
    people = random.sample(universe["people"], random.randint(2, 5))
    project = random.choice(universe["projects"])

    prompt = f"""Generate a realistic {source} from {universe['company']} ({universe['industry']}).
Involving: {', '.join(people)}
About: {project}
Length: 500-1500 words. Make it realistic and detailed."""

    content = call_api("Generate realistic corporate content.", prompt, max_tokens=2000)
    if not content or len(content) < 300:
        return None

    triage_prompt = f"""Classify this content. Return ONLY valid JSON with keys:
- type: one of "meeting", "decision", "note", "task", "idea", "insight", "context", "report"
- summary: 2-3 sentence summary capturing all key points
- tags: array of 4-8 relevant tags

Content:
{content}"""

    output = call_api("Return only valid JSON.", triage_prompt, max_tokens=500)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().strip("```json").strip("```"))
    except:
        return None

    return {
        "input": f"[TRIAGE] {content}",
        "output": json.dumps(parsed),
    }


def generate_reasoning_answer(universe: dict) -> dict | None:
    """Generate a reasoning/analysis question with multi-memory context."""
    people = random.sample(universe["people"], random.randint(3, 6))
    project = random.choice(universe["projects"])
    topic = random.choice(universe["topics"])

    # Generate 5-10 memory summaries as context
    num_memories = random.randint(5, 10)
    memories_prompt = f"""Generate {num_memories} realistic memory summaries for {universe['company']} about {project}.
Each should be 1-2 sentences, from different dates over the past 2 months.
Include decisions, action items, updates, and at least one contradiction.
People involved: {', '.join(people)}

Format each as: [N] Source, Date - Summary"""

    memories = call_api("Generate realistic organizational memory summaries.", memories_prompt, max_tokens=1500)
    if not memories:
        return None

    # Generate a reasoning question
    question_type = random.choice([
        f"Based on these meetings, what are the biggest risks to {project}?",
        f"What patterns do you see in how the team has handled {topic}?",
        f"Summarize the key decisions about {project} and suggest next steps",
        f"Are there any contradictions in what the team has said about {topic}?",
        f"What should {random.choice(people)} prioritize this week based on recent updates?",
        f"Give me an executive summary of {project} progress over the last month",
        f"What blockers keep recurring across these updates about {project}?",
    ])

    answer_prompt = f"""You are Rabbit, a memory AI. Answer this question using ONLY the provided memories.

Question: {question_type}

Memories:
{memories}

Requirements:
- Cite sources inline as [1][2][3]
- Use **bold** for key names and decisions
- Analyze patterns and connections across memories
- Provide actionable suggestions where appropriate
- Be specific, not generic
- End with:

Sources:
[1] Description
[2] Description

Follow-up questions:
-> Question 1
-> Question 2
-> Question 3"""

    answer = call_api("You are Rabbit, a memory AI that provides detailed analytical answers with citations.", answer_prompt, max_tokens=2000)
    if not answer:
        return None

    return {
        "input": f"[ANSWER] Question: {question_type}\n\nMemories:\n{memories}",
        "output": answer,
    }


def generate_contradiction(universe: dict) -> dict | None:
    """Generate contradiction detection example."""
    people = random.sample(universe["people"], 3)
    project = random.choice(universe["projects"])

    prompt = f"""Generate a scenario for {universe['company']} where current context contradicts a stored memory.

People: {', '.join(people)}
Project: {project}

Return ONLY valid JSON with:
- screen_context: what someone is currently saying/writing (1-2 sentences)
- memory_1: a related memory that contradicts the context (with date)
- memory_2: another related memory (may or may not contradict)
- expected_output: JSON with show (true), reason ("contradiction"), context (explanation), memory_indices (array)

Make the contradiction realistic - different dates, changed budgets, reversed decisions, etc."""

    output = call_api("Generate realistic organizational contradictions as JSON.", prompt, max_tokens=1000)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().strip("```json").strip("```"))
    except:
        return None

    ambient_input = f"Screen context: {parsed.get('screen_context', '')}\n\nRelated memories:\n[1] {parsed.get('memory_1', '')}\n[2] {parsed.get('memory_2', '')}"

    return {
        "input": f"[AMBIENT] {ambient_input}",
        "output": json.dumps(parsed.get("expected_output", {"show": True, "reason": "contradiction"})),
    }


def generate_compile(universe: dict) -> dict | None:
    """Generate knowledge compilation (wiki page) example."""
    entity_type = random.choice(["person", "project", "topic"])

    if entity_type == "person":
        entity = random.choice(universe["people"])
    elif entity_type == "project":
        entity = random.choice(universe["projects"])
    else:
        entity = random.choice(universe["topics"])

    num_memories = random.randint(6, 12)
    memories_prompt = f"""Generate {num_memories} realistic memory summaries about "{entity}" at {universe['company']}.
Each from different dates, covering different aspects (role, decisions, relationships, actions).
Format: [N] Source, Date - Summary"""

    memories = call_api("Generate diverse memory summaries.", memories_prompt, max_tokens=1500)
    if not memories:
        return None

    compile_prompt = f"""Compile everything known about "{entity}" into a structured wiki page.
Use ONLY the provided memories.

Memories:
{memories}

Format with **bold** headers, cite sources as [1][2], include:
- Overview/Role
- Key Decisions
- Relationships
- Recent Activity
- Open Items/Pending Actions"""

    wiki = call_api("You are Rabbit. Compile a knowledge page from memories.", compile_prompt, max_tokens=1500)
    if not wiki:
        return None

    return {
        "input": f"[ANSWER] Compile everything known about '{entity}' into a comprehensive wiki page.\n\nMemories:\n{memories}",
        "output": wiki,
    }


def generate_long_link(universe: dict) -> dict | None:
    """Generate memory linking example with multiple candidates."""
    people = random.sample(universe["people"], 4)
    project = random.choice(universe["projects"])

    prompt = f"""Generate a memory linking scenario for {universe['company']}.

Create:
1. A "source" memory (2-3 sentences about {project})
2. Five "candidate" memories, where:
   - 2 are strongly related (same_topic or continuation_of)
   - 1 contradicts the source
   - 2 are unrelated

People to mention: {', '.join(people)}

Return ONLY valid JSON with:
- source: the source memory text
- candidates: array of 5 objects with "id" (1-5) and "text"
- expected_links: array of objects with target_id, kind (same_topic/depends_on/contradicts/continuation_of/same_people/causes/supersedes), weight (0-1), explanation"""

    output = call_api("Generate memory linking scenarios as JSON.", prompt, max_tokens=1500)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().strip("```json").strip("```"))
    except:
        return None

    source_text = parsed.get("source", "")
    candidates = parsed.get("candidates", [])
    expected = parsed.get("expected_links", [])

    candidate_text = "\n".join([f"[{c['id']}] (id=mem_{c['id']}) {c['text']}" for c in candidates])

    return {
        "input": f"[LINK] Source: {source_text}\n\nCandidates:\n{candidate_text}",
        "output": json.dumps({"links": expected}),
    }


# ── Main ───────────────────────────────────────────────────

GENERATORS = {
    "long_extract": (generate_long_extract, 8000),
    "long_triage": (generate_long_triage, 5000),
    "reasoning_answer": (generate_reasoning_answer, 8000),
    "contradiction": (generate_contradiction, 3000),
    "compile": (generate_compile, 3000),
    "long_link": (generate_long_link, 3000),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, default=0, help="1 or 2 for parallel runs. 0 = all")
    parser.add_argument("--type", type=str, default="all", help="Specific type to generate")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine what to generate
    if args.type != "all":
        tasks = {args.type: GENERATORS[args.type]}
    elif args.part == 1:
        tasks = {k: v for i, (k, v) in enumerate(GENERATORS.items()) if i < 3}
    elif args.part == 2:
        tasks = {k: v for i, (k, v) in enumerate(GENERATORS.items()) if i >= 3}
    else:
        tasks = GENERATORS

    for task_name, (generator, target_count) in tasks.items():
        output_file = output_dir / f"v2_{task_name}.jsonl"
        existing = 0
        if output_file.exists():
            existing = sum(1 for _ in open(output_file))
            print(f"\n{task_name}: {existing} existing, need {target_count - existing} more")
        else:
            print(f"\n{task_name}: generating {target_count} examples")

        remaining = target_count - existing
        if remaining <= 0:
            print(f"  Already done!")
            continue

        success = 0
        failures = 0
        with open(output_file, "a") as f:
            for i in range(remaining):
                universe = random.choice(UNIVERSES)
                example = generator(universe)

                if example:
                    f.write(json.dumps(example) + "\n")
                    success += 1
                else:
                    failures += 1

                if (i + 1) % 50 == 0:
                    print(f"  {task_name}: {success}/{i+1} successful ({failures} failures)")
                    f.flush()

                # Rate limiting
                time.sleep(0.3)

        print(f"  {task_name}: DONE - {success} generated, {failures} failed")

    print("\nAll generation complete!")
    print("Run quality_filter.py to clean the data before training.")


if __name__ == "__main__":
    main()
