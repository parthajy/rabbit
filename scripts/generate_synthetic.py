"""
Rabbit — Synthetic Data Generator (Universe-Based)

Generates training data by creating fictional "organization universes" with:
- Consistent cast of characters (recurring names across meetings)
- Meeting sequences (follow-ups, decision evolution, contradictions)
- Realistic org dynamics (scope creep, priority shifts, implicit references)
- Diverse memory sources: meetings, Gmail, Slack, standups, calendar, notes, docs

This produces connected, realistic training data — not isolated random examples.

Usage:
    python scripts/generate_synthetic.py --count 5000
    python scripts/generate_synthetic.py --count 1000 --task intent
    python scripts/generate_synthetic.py --count 5000 --universes 10
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

from openai import OpenAI, RateLimitError

# ── Config ──────────────────────────────────────────────────────────────────

TASKS = ["intent", "extract", "triage", "expand", "answer"]
SEED_DIR = Path("seed")
OUTPUT_DIR = Path("data/synthetic")

MODEL = "gpt-4o-mini"  # Cost-effective for bulk generation
MAX_TOKENS = 4096

# ── Memory Source Types ─────────────────────────────────────────────────────

MEMORY_SOURCES = """
IMPORTANT: Generate examples from DIVERSE memory sources. Mix these across examples:

1. MEETING TRANSCRIPTS — formal and informal meetings, standups, 1:1s, all-hands
   Example: "Standup Mar 15. Rohit: API is 80% done. Sneha: blocked on design specs."

2. GMAIL / EMAIL — forwarded emails, reply chains, cold outreach, internal threads
   Example: "From: sarah@acme.co | Subject: Re: Q2 Contract | Hi, attaching the revised pricing..."

3. SLACK MESSAGES — channel messages, DMs, threads, reactions context
   Example: "#engineering — Karan: just pushed the fix for webhook drops. Vikram: 🎉 deploying now"

4. CALENDAR EVENTS — meeting titles, descriptions, attendee lists, rescheduled events
   Example: "Calendar: Product Review (rescheduled from Mon) | Mar 18 2-3pm | Priya, Rohit, Ananya"

5. NOTES / DOCS — personal notes, shared docs, decision logs, post-mortems
   Example: "Note to self: follow up with Amit about the ZyloTech pilot. They seemed hesitant on pricing."

6. STANDUP UPDATES — daily async standups, weekly updates, progress reports
   Example: "Farhan's weekly update: Finished cohort analysis. Template adoption up 25%. Blocked on experiment data."

7. CRM / TOOL ENTRIES — deal notes, customer records, support tickets
   Example: "CRM: Acme Corp — Stage: Negotiation — Last contact: Sarah (Mar 22) — Note: pushing for 20% discount"

8. VOICE MEMO TRANSCRIPTS — quick voice notes, dictated thoughts
   Example: "Voice memo 3:47pm: Need to remember — David wants the onboarding redesign before August renewal"

Mix these naturally. Not every example needs to be a meeting transcript.
"""

# ── Organization Universe Templates ────────────────────────────────────────

UNIVERSE_PROMPT = """You are generating realistic organizational memory data for training Rabbit, an AI model that powers organizational memory for teams.

CRITICAL RULES:
1. You are creating data for ONE fictional organization. Keep names, projects, and context CONSISTENT across all examples.
2. People recur across meetings. Decisions evolve. Meetings reference previous meetings.
3. Include realistic messiness: vague references ("that thing we discussed"), contradictions, scope changes, follow-ups.
4. Vary formality: some meetings are structured, others are casual standups, Slack messages, or quick emails.
5. USE DIVERSE MEMORY SOURCES — not just meeting transcripts!

{memory_sources}

ORGANIZATION PROFILE:
{org_profile}

CAST OF CHARACTERS:
{cast}

ACTIVE PROJECTS/THREADS:
{projects}

TIMELINE: {timeline}

Now generate {count} training examples for the task: {task}

{task_instructions}

Output ONLY valid JSONL — one JSON object per line, each with "input" and "output" keys.
Do NOT wrap in code blocks. Do NOT add commentary. ONLY JSONL lines."""

# ── Organization profiles for diversity ─────────────────────────────────────

ORG_PROFILES = [
    {
        "name": "NovaByte (Series A SaaS startup, 25 people)",
        "industry": "B2B SaaS — project management tool",
        "cast": [
            "Priya (Founder/CEO)", "Rohit (CTO)", "Ananya (Head of Product)",
            "Karan (Backend Lead)", "Sneha (Frontend Engineer)", "Amit (Sales Lead)",
            "Neha (Designer)", "Vikram (DevOps)", "Meera (Customer Success)",
            "Farhan (Data Scientist)"
        ],
        "projects": [
            "Enterprise tier launch (pricing, features, pilot customers)",
            "Slack integration (reliability issues, webhook drops)",
            "Dashboard redesign (user complaints about complexity)",
            "Series B fundraise prep (metrics, deck, investor meetings)"
        ],
        "timeline": "January 2026 - April 2026"
    },
    {
        "name": "Argonal (Enterprise IT services, 200 people)",
        "industry": "Managed services — ERP/CRM for large clients",
        "cast": [
            "Brian (Client Manager)", "Anjan (Tech Lead)", "Misha (Project Manager)",
            "Lisa (QA Lead)", "Suzuki (Client Stakeholder)", "Julio (Integration Specialist)",
            "Bill (Executive Sponsor)", "Kunal (DevOps)", "Deepa (Business Analyst)",
            "Rahul (Support Lead)"
        ],
        "projects": [
            "DDXT web migration (tickets, deployments, interface issues)",
            "Quarterly audit preparation (user profiles, licensing)",
            "Data push coordination with Japan team",
            "Managed services reporting (consumption, ticket metrics)"
        ],
        "timeline": "February 2026 - May 2026"
    },
    {
        "name": "HealthSync (Healthcare AI startup, 15 people)",
        "industry": "AI-powered clinical documentation",
        "cast": [
            "Dr. Aisha (Co-founder/CMO)", "Raj (Co-founder/CTO)", "Tanya (ML Engineer)",
            "Nikhil (Backend Engineer)", "Kavita (Product Manager)", "Suresh (Compliance Lead)",
            "Pooja (UX Researcher)", "Arjun (iOS Developer)", "Rekha (Sales)",
            "Manoj (Customer Support)"
        ],
        "projects": [
            "HIPAA compliance overhaul (audit, encryption, access logs)",
            "Voice-to-note accuracy improvements (model fine-tuning)",
            "Hospital pilot with St. Mary's (50 doctors, 3 departments)",
            "Mobile app v2 (offline mode, sync issues)"
        ],
        "timeline": "March 2026 - June 2026"
    },
    {
        "name": "UrbanPulse (PropTech scale-up, 80 people)",
        "industry": "Real estate analytics and tenant management",
        "cast": [
            "David (CEO)", "Simran (VP Engineering)", "Aarav (Product Lead)",
            "Jyoti (Data Engineering Lead)", "Kabir (Frontend Lead)", "Nisha (Head of Sales)",
            "Ravi (ML Engineer)", "Parul (Customer Success)", "Manish (DevOps)",
            "Divya (Legal/Compliance)"
        ],
        "projects": [
            "Predictive pricing model (accuracy issues, client trust)",
            "Tenant portal redesign (feedback from property managers)",
            "API platform for third-party integrations",
            "SOC 2 Type II certification (deadline pressure)"
        ],
        "timeline": "January 2026 - April 2026"
    },
    {
        "name": "LearnFlow (EdTech, 40 people)",
        "industry": "AI tutoring and curriculum platform",
        "cast": [
            "Megha (Founder)", "Siddharth (CTO)", "Ritu (Head of Content)",
            "Aakash (ML Lead)", "Prerna (Product Manager)", "Gaurav (Backend)",
            "Ishita (Mobile Lead)", "Rohan (Growth)", "Swati (Partnership Lead)",
            "Vivek (QA)"
        ],
        "projects": [
            "Adaptive learning engine (personalization, A/B testing)",
            "School district pilot (500 students, 20 teachers)",
            "Content creation pipeline (AI-assisted, quality review)",
            "Parent dashboard (engagement tracking, privacy concerns)"
        ],
        "timeline": "February 2026 - May 2026"
    },
    {
        "name": "FinEdge (Fintech, 60 people)",
        "industry": "AI-powered expense management and forecasting",
        "cast": [
            "Akash (CEO)", "Shreya (CTO)", "Varun (Product Lead)",
            "Nandini (Compliance Officer)", "Harsh (Backend Lead)", "Tanvi (Frontend)",
            "Sanjay (Sales Director)", "Bhavna (Customer Success)", "Rahul (Data Engineer)",
            "Deepak (Security Lead)"
        ],
        "projects": [
            "Bank integration reliability (API failures, reconciliation)",
            "SOX compliance audit (Q2 deadline)",
            "Forecasting model v3 (accuracy improvement, enterprise clients)",
            "Mobile expense capture (OCR, receipt scanning)"
        ],
        "timeline": "January 2026 - April 2026"
    },
    {
        "name": "GreenGrid (CleanTech, 30 people)",
        "industry": "Energy management and carbon tracking for buildings",
        "cast": [
            "Lena (Founder/CEO)", "Arjun (VP Engineering)", "Zara (Sustainability Lead)",
            "Dev (IoT Engineer)", "Priyanka (Product Manager)", "Sameer (Data Scientist)",
            "Noor (Enterprise Sales)", "Ria (UX Designer)", "Kunal (Backend)",
            "Fatima (Operations)"
        ],
        "projects": [
            "Real-time energy dashboard (sensor integration, latency)",
            "Carbon credit reporting (regulatory changes, EU compliance)",
            "Building automation pilot with Meridian Properties (3 buildings)",
            "API for HVAC system integrations"
        ],
        "timeline": "February 2026 - May 2026"
    },
    {
        "name": "CraftOS (Developer tools, 20 people)",
        "industry": "AI code review and development workflow automation",
        "cast": [
            "Ankit (Founder/CEO)", "Maya (CTO)", "Sahil (ML Lead)",
            "Diya (Product Manager)", "Nitin (Backend Engineer)", "Pooja (Frontend)",
            "Tarun (DevRel)", "Aditi (QA Lead)", "Rajan (Sales)",
            "Shreyas (Infrastructure)"
        ],
        "projects": [
            "AI review accuracy (false positive reduction)",
            "VS Code extension v2 (performance, new features)",
            "Enterprise SSO integration (OAuth, SAML)",
            "Usage-based pricing migration (from flat-rate)"
        ],
        "timeline": "March 2026 - June 2026"
    },
    {
        "name": "TravelMind (Travel tech, 50 people)",
        "industry": "AI-powered corporate travel management",
        "cast": [
            "Arun (CEO)", "Pallavi (CTO)", "Mandar (Product Head)",
            "Swapnil (Backend Lead)", "Ritika (Frontend Lead)", "Jayesh (Sales VP)",
            "Ankita (ML Engineer)", "Viraj (Operations)", "Deepa (Finance)",
            "Sandeep (Customer Success)"
        ],
        "projects": [
            "Flight recommendation engine (cost optimization, policy compliance)",
            "Expense reconciliation automation (bank feeds, receipt matching)",
            "Marriott/Hilton direct booking integration",
            "Travel policy enforcement engine (approvals, exceptions)"
        ],
        "timeline": "January 2026 - April 2026"
    },
    {
        "name": "MediaForge (Content/Media, 35 people)",
        "industry": "AI-powered content creation and distribution platform",
        "cast": [
            "Rhea (Founder)", "Karthik (CTO)", "Anjali (Head of Content AI)",
            "Vikrant (Backend Lead)", "Sonali (Product Manager)", "Imran (Growth Lead)",
            "Deepika (Designer)", "Nikhil (ML Engineer)", "Ashwin (Sales)",
            "Meera (Customer Success)"
        ],
        "projects": [
            "Content generation quality (hallucination reduction, brand voice)",
            "Multi-channel publishing (scheduling, analytics aggregation)",
            "Enterprise content approval workflow",
            "SEO optimization engine (keyword research, content scoring)"
        ],
        "timeline": "February 2026 - May 2026"
    },
]

# ── Task-specific instructions ──────────────────────────────────────────────

TASK_INSTRUCTIONS = {
    "intent": """Generate query intent classification examples.
Each example: a user asks a question about their organizational memories.
- "input": the user's natural language question (vary: formal, casual, vague, specific, with typos)
- "output": exactly ONE word from: factual | entity | temporal | synthesis | actions | history | aggregation

Make queries that reference THIS organization's people, projects, and meetings specifically.
Include vague queries like "what about that pricing thing" and precise ones like "Who attended the March 15 standup?"
Include queries that reference previous meetings implicitly: "that discussion from last week", "the thing Brian mentioned".
Include queries about emails, Slack messages, calendar events — not just meetings.""",

    "extract": """Generate entity/fact extraction examples.
Each example: raw text from a meeting, email, Slack message, standup, calendar event, CRM note, or voice memo.
- "input": the raw text (VARY THE SOURCE TYPE — meetings, Gmail, Slack, standups, notes, calendar, CRM)
- "output": JSON object with keys: people, organizations, decisions, action_items, dates, topics
  - action_items format: [{{"owner": "Name", "task": "description", "due": "date/timeframe"}}]

Make inputs realistic and messy — include abbreviations, incomplete sentences, casual tone.
Reference the SAME people and projects across multiple examples.
Include email headers ("From: ... Subject: ..."), Slack-style messages ("#channel — Name: ..."),
calendar entries, CRM notes, and voice memo transcriptions.""",

    "triage": """Generate memory classification and summary examples.
Each example: raw captured content that needs to be classified and summarized.
- "input": raw text from ANY source (meeting, email, Slack, standup, calendar, note, CRM, voice memo)
- "output": JSON object with keys: type, summary, tags
  - type: one of: meeting | note | email | decision | action_item | update | conversation | standup | calendar
  - summary: 1-2 sentence essence
  - tags: 3-6 lowercase keywords

Make inputs vary in length (1 sentence to several paragraphs).
Include content from diverse sources — Gmail threads, Slack channels, async standups, calendar descriptions.
Some inputs should be follow-ups: "Following up on yesterday's discussion about...".""",

    "expand": """Generate query expansion examples.
Each example: a vague user query expanded into a precise search query.
- "input": short/vague query (how people ACTUALLY type) — reference this org's people/projects
- "output": expanded query that captures likely intent, mentions what to search for

THIS IS THE MOST CRITICAL TASK. Bad expansion = bad search results.
Include:
- Name-only queries: "priya", "what about rohit"
- Project references: "the slack thing", "enterprise stuff"
- Temporal vagueness: "last week", "recently", "that meeting"
- Implicit references: "what did we decide", "any updates", "the pricing discussion"
- Typos and fragments: "standup tmrw?", "amit client", "bug status"
- Source-specific: "that email from sarah", "slack thread about deploy", "calendar for tomorrow"
- Cross-source: "everything about acme" (should search meetings AND emails AND Slack)""",

    "answer": """Generate conversational Q&A examples over retrieved memories.
Each example: a question + retrieved memory context → conversational answer with citations.
- "input": formatted as "Question: [question]\\nMemories: [1] ... [2] ... [3] ..."
- "output": conversational answer with [1][2][3] citations, NO markdown formatting

The memories should come from DIVERSE SOURCES — mix meeting transcripts, emails, Slack messages,
standups, calendar events, and notes as memory context.
Include cases where:
- Memories from different sources answer the question (email + meeting + Slack)
- Memories show evolution/contradiction (decision changed between meetings)
- Answer needs to synthesize across sources ("The email confirms what was discussed in the meeting")
- Implicit links need to be made across time and source type""",
}

# ── Seed loading ────────────────────────────────────────────────────────────


def load_seed_context() -> str:
    """Load seed files as context for the generator."""
    context_parts = []
    for seed_file in SEED_DIR.glob("*.md"):
        content = seed_file.read_text()
        # Take first ~1500 chars of each as examples
        context_parts.append(f"--- {seed_file.name} (excerpt) ---\n{content[:1500]}\n")
    return "\n".join(context_parts)


# ── Generation ──────────────────────────────────────────────────────────────


def generate_batch(
    client: OpenAI,
    org: dict,
    task: str,
    count: int,
    seed_context: str,
) -> list[dict]:
    """Generate a batch of examples for one org universe and task."""

    prompt = UNIVERSE_PROMPT.format(
        memory_sources=MEMORY_SOURCES,
        org_profile=org["name"],
        cast="\n".join(f"- {c}" for c in org["cast"]),
        projects="\n".join(f"- {p}" for p in org["projects"]),
        timeline=org["timeline"],
        count=count,
        task=task.upper(),
        task_instructions=TASK_INSTRUCTIONS[task],
    )

    system = (
        "You are a training data generator for Rabbit, an AI model for organizational memory. "
        "Generate realistic, connected examples that reflect how real organizations work. "
        "Use diverse memory sources: meetings, Gmail, Slack, standups, calendar, notes, CRM entries, voice memos. "
        "Here are examples of real organizational data for reference:\n\n"
        f"{seed_context[:2500]}\n\n"
        "Match this level of realism and detail. Output ONLY valid JSONL."
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )

    # Parse JSONL
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


def generate_all(total_count: int, tasks: list[str], num_universes: int):
    """Generate synthetic data across multiple organization universes."""

    client = OpenAI()
    seed_context = load_seed_context()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Select universes
    universes = random.sample(ORG_PROFILES, min(num_universes, len(ORG_PROFILES)))

    # Distribute count across tasks and universes
    per_task = total_count // len(tasks)
    per_universe_per_task = max(per_task // len(universes), 10)
    batch_size = min(30, per_universe_per_task)  # gpt-4o-mini handles ~30 per call

    print(f"\n{'='*60}")
    print(f"  RABBIT — Universe-Based Synthetic Data Generator")
    print(f"  Model: {MODEL}")
    print(f"  Total target: {total_count} examples")
    print(f"  Tasks: {', '.join(tasks)}")
    print(f"  Universes: {len(universes)}")
    print(f"  Per task: ~{per_task} | Per universe per task: ~{per_universe_per_task}")
    print(f"{'='*60}")

    for task in tasks:
        output_file = OUTPUT_DIR / f"{task}_synthetic.jsonl"

        # Load existing if resuming
        existing_count = 0
        if output_file.exists():
            with open(output_file) as f:
                existing_count = sum(1 for line in f if line.strip())
            print(f"\n  [{task.upper()}] Resuming: {existing_count} already exist")

        target = per_task
        generated = existing_count

        print(f"\n  [{task.upper()}] Generating {target - generated} more examples...")

        for universe in universes:
            if generated >= target:
                break

            universe_target = min(per_universe_per_task, target - generated)
            batches_needed = (universe_target + batch_size - 1) // batch_size

            print(f"    Universe: {universe['name']}")

            for batch_num in range(batches_needed):
                if generated >= target:
                    break

                this_batch = min(batch_size, target - generated)

                try:
                    examples = generate_batch(
                        client, universe, task, this_batch, seed_context
                    )

                    with open(output_file, "a") as f:
                        for ex in examples:
                            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

                    generated += len(examples)
                    print(f"      Batch {batch_num + 1}: +{len(examples)} "
                          f"(total: {generated}/{target})")

                    time.sleep(0.3)  # Light rate limiting

                except RateLimitError:
                    print("      Rate limited. Waiting 30s...")
                    time.sleep(30)
                except Exception as e:
                    print(f"      Error: {e}")
                    time.sleep(3)

        print(f"  [{task.upper()}] Done: {generated} examples in {output_file}")

    print(f"\n{'='*60}")
    print(f"  RABBIT — Generation complete!")
    print(f"  Next: python scripts/quality_filter.py --task all")
    print(f"{'='*60}")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Generate universe-based synthetic training data"
    )
    parser.add_argument(
        "--count", type=int, default=5000,
        help="Total number of examples to generate (distributed across tasks)",
    )
    parser.add_argument(
        "--task", choices=TASKS + ["all"], default="all",
        help="Which task to generate for (default: all)",
    )
    parser.add_argument(
        "--universes", type=int, default=5,
        help="Number of organization universes to use (default: 5, max 10)",
    )
    parser.add_argument(
        "--model", default=MODEL,
        help=f"OpenAI model to use (default: {MODEL})",
    )

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        print("  export OPENAI_API_KEY=sk-proj-...")
        return

    global MODEL
    MODEL = args.model

    tasks = TASKS if args.task == "all" else [args.task]
    generate_all(args.count, tasks, args.universes)


if __name__ == "__main__":
    main()
