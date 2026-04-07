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
# v1.3 targets: fix quality gaps + add wiki signals
TASK_TARGETS = {
    "faithful_extract": 3000,
    "formatted_answer": 3000,
    "followup_answer": 2000,
    "clean_json": 2000,
    "compile": 3000,
    "lint": 2000,
    "compile_answer": 1000,
    # Existing tasks — only generate if below target
    "link": 5000,
    "ambient": 3000,
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

    "link": """Generate memory linking examples.
- "input": "SOURCE RECORD:\\nTitle: [title]\\nSummary: [summary]\\n\\nCANDIDATES:\\n1. [id-1] Title: Summary\\n2. [id-2] Title: Summary\\n..." (8-12 candidates)
- "output": JSON {"links": [{"target_id":"id-1","kind":"same_topic","weight":0.85,"explanation":"Both discuss Q2 plans"}]}
Kinds: same_topic, depends_on, contradicts, continuation_of, same_people, causes, temporal.
Max 8 links. Include examples with 0 links (no relation), 1-2 links, and 5-8 links.
Generate candidates from the SAME org — meetings, emails, Slack about SAME projects/people.""",

    "ambient": """Generate ambient recall examples. User is working (screen text) and Rabbit has related memories.
- "input": "SCREEN TEXT (from [app]):\\n[what user is typing/reading]\\n\\nRELATED MEMORIES:\\n1. [type] Title: Summary\\n2. ..."
- "output": JSON. Either {"show": false} (no alert) or {"show": true, "reason": "contradiction|forgotten_commitment|critical_context", "memory_indices": [1,2], "context": "precise explanation"}
Generate ~60% show:false, ~40% show:true. Most screen text is NOT alert-worthy.""",

    "faithful_extract": """Generate entity extraction examples where EXACT reproduction of names, numbers, and dates is critical.
- "input": text containing specific names, dollar amounts, dates, email addresses, phone numbers, company names
- "output": JSON with keys: people, organizations, decisions, action_items, dates, topics
CRITICAL RULES:
- Every name in the output MUST appear EXACTLY as spelled in the input. Never paraphrase or abbreviate names.
- Every number must be EXACTLY as stated. $45,000 stays $45,000, not $45K.
- Every date must be EXACTLY as stated. "April 15" stays "April 15", not "mid-April".
- If the input says "Sarah", output MUST say "Sarah", never "Sara" or any variant.
- Include tricky names: Priyanka, Sreejith, Venkataraman, Muhammad, Krzyzewski — they must be reproduced exactly.
- Include mixed formats: "$2.1M ARR", "Q2 2026", "3:30 PM IST", "v2.0.1"
Output ONLY valid JSON. No markdown. No explanation.""",

    "formatted_answer": """Generate conversational Q&A examples with PROPER FORMATTING.
- "input": "Question: [question]\\nMemories: [1] source, date — content [2]...[3]...[4]...[5]..."
- "output": A rich answer that MUST use this EXACT structure:

[2-4 paragraphs of narrative. Use **bold** for person names first time mentioned. Use **bold** for key decisions. Cite inline as [1][2] etc.]

Sources:
[1] Source Type, Date — Brief description
[2] Source Type, Date — Brief description
[3] Source Type, Date — Brief description

Follow-up questions:
→ First relevant question
→ Second relevant question
→ Third deeper question

RULES:
- **Bold** every person name on first mention
- **Bold** every key decision
- Always include Sources: section with ALL cited memories
- Always include Follow-up questions: section with exactly 3 questions prefixed with →
- Minimum 300 words in the narrative section
- Use reasoning: "What's interesting is...", "The pattern suggests...", "This indicates..."
- Sound like a smart colleague telling a story, not a search engine""",

    "followup_answer": """Generate answer examples specifically focused on correct Follow-up questions format.
- "input": "Question: [question]\\nMemories: [1]...[2]...[3]..."
- "output": answer that ALWAYS ends with:

Follow-up questions:
→ [Specific, useful question related to the topic]
→ [Question that goes deeper into a detail mentioned]
→ [Strategic question that requires reasoning]

The follow-up questions must be:
- Specific to the content (not generic like "What else?")
- Genuinely useful (would help the user think deeper)
- Varied (one factual, one analytical, one strategic)""",

    "clean_json": """Generate examples for JSON-output signals where the output is PURE JSON with NO trailing text.
Mix of extract, triage, importance, link, and ambient examples.
- "input": varies by signal type
- "output": ONLY valid JSON. Nothing before or after the JSON object. No explanation. No markdown.

BAD output: {"score": 3, "reason": "routine update"} This is because the meeting was routine.
GOOD output: {"score": 3, "reason": "routine update"}

BAD output: ```json\\n{"links": [...]}\\n```
GOOD output: {"links": [...]}

Generate a mix of:
- extract outputs (people, orgs, decisions JSON)
- triage outputs (type, summary, tags JSON)
- importance outputs (score, reason JSON)
- link outputs (links array JSON)
- ambient outputs (show, reason, context JSON)""",

    "compile": """Generate COMPILE examples — updating an existing wiki/entity page with new information.
- "input": "EXISTING PAGE:\\n[current entity/topic page content]\\n\\nNEW MEMORY:\\n[new information to integrate]"
- "output": The UPDATED page content that merges the new information into the existing page.

Rules:
- Preserve all existing information that's still valid
- Add new information in the right context
- If new info CONTRADICTS existing info, note both: "Previously $42K (Mar 20), now updated to $45K (Apr 7)"
- Update "Last updated" date
- Keep the page concise but complete
- Format: Summary paragraph, Key People, Open Items, Recent Activity, Related Topics

Example input:
EXISTING PAGE:
Entity: Acme Corp
Type: Organization
Last updated: March 25, 2026
Summary: Enterprise client discussing renewal. Primary contact Tom.
Key People: Tom (primary)
Open Items: Contract terms under review
Recent Activity:
- Mar 15: Initial renewal discussion
- Mar 20: Tom confirmed budget approved

NEW MEMORY: Meeting Apr 1 — Legal flagged a liability clause. Tom requested revised terms.

Example output:
Entity: Acme Corp
Type: Organization
Last updated: April 1, 2026
Summary: Enterprise client in active renewal. Primary contact Tom. Contract terms being revised after legal review flagged a liability clause.
Key People: Tom (primary contact), Legal team (flagged clause)
Open Items: Revised contract terms pending, liability clause needs resolution
Recent Activity:
- Apr 1: Legal flagged liability clause, Tom requested revised terms
- Mar 20: Tom confirmed budget approved
- Mar 15: Initial renewal discussion
Related: [Pricing Strategy], [Enterprise Clients], [Legal Reviews]""",

    "lint": """Generate LINT examples — detecting issues in a knowledge base.
- "input": "ENTITY PAGE:\\n[wiki page content]\\n\\nRECENT MEMORIES:\\n[1] ...[2] ...[3] ..."
- "output": JSON with detected issues:
{
  "contradictions": [{"issue": "description", "page_says": "X", "memory_says": "Y", "memory_index": 1}],
  "stale_items": [{"issue": "description", "date_mentioned": "YYYY-MM-DD", "status": "past_due|no_update"}],
  "missing_links": [{"entity": "name", "mentioned_in": [1, 3], "has_page": false}],
  "suggested_actions": ["Update page with...", "Create page for...", "Resolve contradiction about..."]
}

Generate a mix:
- ~30% examples with contradictions (dates wrong, numbers changed, decisions reversed)
- ~30% examples with stale info (deadlines passed, no follow-up recorded)
- ~20% examples with missing links (people mentioned but no entity page)
- ~20% examples with NO issues (clean knowledge base — output: all empty arrays)""",

    "compile_answer": """Generate examples of converting a synthesized answer into a wiki entry.
- "input": "QUESTION: [original question]\\nANSWER: [Rabbit's synthesized answer with citations]\\nSOURCE_IDS: [id-1, id-2, id-3]"
- "output": JSON wiki entry:
{
  "title": "Short descriptive title (max 80 chars)",
  "content": "The synthesized knowledge, rewritten as a wiki entry (not Q&A format)",
  "category": "decisions|projects|people|strategy|operations",
  "source_ids": ["id-1", "id-2", "id-3"],
  "auto_update": true,
  "keywords": ["keyword1", "keyword2"]
}

The content should be rewritten from Q&A format to wiki format:
- Remove "Based on your question..." type phrasing
- Write as objective knowledge: "The pricing strategy evolved from freemium to usage-based..."
- Keep all factual information and citations
- Make it scannable and reusable""",
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
