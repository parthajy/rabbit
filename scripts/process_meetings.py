"""
Rabbit — AMI + ICSI Meeting Corpus Processor
Downloads and processes academic meeting corpora into training examples.

AMI: ~170 scenario-based team meetings with summaries
ICSI: ~75 academic research meetings with summaries

Usage:
    python scripts/process_meetings.py --download
    python scripts/process_meetings.py --process --count 5000
"""

import argparse
import json
import os
import random
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI, RateLimitError

# ── Config ──────────────────────────────────────────────────────────────────

DATA_DIR = Path("data/external/meetings")
OUTPUT_DIR = Path("data/synthetic")
MODEL = "gpt-4o-mini"

TASKS = ["extract", "triage", "summarize", "sentiment", "importance",
         "intent", "expand", "answer"]

# ── Download ────────────────────────────────────────────────────────────────


def download_corpora():
    """Download AMI and ICSI meeting datasets."""
    import urllib.request

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    datasets = [
        {
            "name": "AMI abstractive summaries",
            "url": "https://raw.githubusercontent.com/gcunhase/AMICorpusXML/master/ami_abstractive.json",
            "path": DATA_DIR / "ami_summaries.json",
        },
        {
            "name": "ICSI abstractive summaries",
            "url": "https://raw.githubusercontent.com/gcunhase/AMICorpusXML/master/icsi_abstractive.json",
            "path": DATA_DIR / "icsi_summaries.json",
        },
    ]

    for ds in datasets:
        if ds["path"].exists():
            print(f"  Already downloaded: {ds['name']}")
        else:
            print(f"  Downloading {ds['name']}...")
            try:
                urllib.request.urlretrieve(ds["url"], ds["path"])
                print(f"  Saved to {ds['path']}")
            except Exception as e:
                print(f"  Failed: {e}")
                print(f"  You may need to manually download meeting transcripts.")

    # Also create a synthetic meetings file from common patterns
    synthetic_path = DATA_DIR / "synthetic_meetings.json"
    if not synthetic_path.exists():
        print(f"  Creating synthetic meeting templates...")
        create_synthetic_meeting_templates(synthetic_path)


def create_synthetic_meeting_templates(output_path: Path):
    """Create diverse meeting transcript templates for processing."""
    templates = [
        {
            "type": "standup",
            "template": "Daily standup. {participants}. Updates: {updates}. Blockers: {blockers}.",
        },
        {
            "type": "product_review",
            "template": "Product review meeting. {participants}. Discussed: {topics}. Decisions: {decisions}. Action items: {actions}.",
        },
        {
            "type": "sprint_planning",
            "template": "Sprint planning. {participants}. Stories discussed: {stories}. Estimated points: {points}. Committed: {committed}.",
        },
        {
            "type": "client_call",
            "template": "Client call with {client}. Attendees: {participants}. Topics: {topics}. Client concerns: {concerns}. Follow-ups: {followups}.",
        },
        {
            "type": "retrospective",
            "template": "Sprint retro. What went well: {good}. What didn't: {bad}. Action items: {actions}.",
        },
        {
            "type": "architecture_review",
            "template": "Architecture discussion. {participants}. Proposal: {proposal}. Concerns: {concerns}. Decision: {decision}.",
        },
        {
            "type": "hiring_debrief",
            "template": "Interview debrief for {candidate}. Interviewers: {participants}. Strengths: {strengths}. Concerns: {concerns}. Verdict: {verdict}.",
        },
        {
            "type": "incident_review",
            "template": "Incident post-mortem. Incident: {incident}. Timeline: {timeline}. Root cause: {root_cause}. Action items: {actions}.",
        },
    ]
    with open(output_path, "w") as f:
        json.dump(templates, f, indent=2)


# ── Loading ─────────────────────────────────────────────────────────────────


def load_meeting_data() -> list[dict]:
    """Load available meeting data."""
    meetings = []

    # Load AMI summaries
    ami_path = DATA_DIR / "ami_summaries.json"
    if ami_path.exists():
        try:
            with open(ami_path) as f:
                ami_data = json.load(f)
            if isinstance(ami_data, list):
                for item in ami_data:
                    meetings.append({
                        "source": "AMI",
                        "text": str(item.get("summary", item.get("text", str(item)))),
                    })
            elif isinstance(ami_data, dict):
                for key, val in ami_data.items():
                    meetings.append({
                        "source": "AMI",
                        "id": key,
                        "text": str(val) if isinstance(val, str) else json.dumps(val),
                    })
            print(f"  Loaded {len(meetings)} AMI meetings")
        except Exception as e:
            print(f"  Error loading AMI: {e}")

    # Load ICSI summaries
    icsi_path = DATA_DIR / "icsi_summaries.json"
    prev_count = len(meetings)
    if icsi_path.exists():
        try:
            with open(icsi_path) as f:
                icsi_data = json.load(f)
            if isinstance(icsi_data, list):
                for item in icsi_data:
                    meetings.append({
                        "source": "ICSI",
                        "text": str(item.get("summary", item.get("text", str(item)))),
                    })
            elif isinstance(icsi_data, dict):
                for key, val in icsi_data.items():
                    meetings.append({
                        "source": "ICSI",
                        "id": key,
                        "text": str(val) if isinstance(val, str) else json.dumps(val),
                    })
            print(f"  Loaded {len(meetings) - prev_count} ICSI meetings")
        except Exception as e:
            print(f"  Error loading ICSI: {e}")

    if not meetings:
        print("  No meeting data found. Using seed data as fallback...")
        seed_dir = Path("seed")
        for f in seed_dir.glob("*.md"):
            content = f.read_text()
            # Split into chunks at numbered meeting headers
            chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 100]
            for chunk in chunks[:50]:
                meetings.append({"source": f.name, "text": chunk[:3000]})
        print(f"  Loaded {len(meetings)} chunks from seed files")

    return meetings


# ── Processing ──────────────────────────────────────────────────────────────

PROCESS_PROMPT = """You are converting real meeting transcripts/summaries into training examples for Rabbit, an AI model for organizational memory.

Generate JSONL where each line has: {{"task": "...", "input": "...", "output": "..."}}

TASKS:
1. "extract" — Input: meeting text. Output: JSON with people, organizations, decisions, action_items, dates, topics
2. "triage" — Input: meeting text. Output: JSON with type (meeting/standup/decision), summary, tags
3. "summarize" — Input: meeting text. Output: 2-4 sentence rich summary
4. "sentiment" — Input: meeting text. Output: one word: positive, negative, neutral, tense, urgent
5. "importance" — Input: meeting text. Output: JSON with score (1-5) and reason
6. "intent" — Input: question about this meeting. Output: one word: factual, entity, temporal, synthesis, actions, history, aggregation
7. "expand" — Input: vague query about this meeting. Output: expanded query
8. "answer" — Input: "Question: ...\\nMemories: [1] ... [2] ...". Output: cited answer, no markdown

Generate {count} examples (mix of all tasks). Output ONLY valid JSONL.

MEETING DATA:
{meetings}"""


def process_batch(client: OpenAI, meetings_batch: list[dict], count: int) -> list[dict]:
    """Convert meeting data into training examples."""
    meetings_text = "\n\n---\n\n".join(
        f"[{m.get('source', 'unknown')}] {m['text'][:2000]}"
        for m in meetings_batch
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        timeout=90,
        messages=[
            {
                "role": "system",
                "content": "You convert meeting transcripts into AI training data. Output ONLY valid JSONL.",
            },
            {
                "role": "user",
                "content": PROCESS_PROMPT.format(meetings=meetings_text, count=count),
            },
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
            if "task" in obj and "input" in obj and "output" in obj:
                if obj["task"] in TASKS:
                    examples.append(obj)
        except json.JSONDecodeError:
            continue

    return examples


def process_meetings(target_count: int):
    """Process meeting data into training examples."""
    client = OpenAI()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    meetings = load_meeting_data()
    if not meetings:
        print("  No meeting data available.")
        return

    random.shuffle(meetings)

    output_files = {task: OUTPUT_DIR / f"{task}_synthetic.jsonl" for task in TASKS}

    print(f"\n{'='*60}")
    print(f"  RABBIT — Meeting Corpus Processor")
    print(f"  Meetings loaded: {len(meetings)}")
    print(f"  Target: {target_count} examples")
    print(f"{'='*60}")

    generated = 0
    batch_size = 3

    for i in range(0, len(meetings), batch_size):
        if generated >= target_count:
            break

        batch = meetings[i:i + batch_size]

        try:
            examples = process_batch(client, batch, 20)

            for ex in examples:
                task = ex["task"]
                training_ex = {"input": ex["input"], "output": ex["output"]}
                with open(output_files[task], "a") as f:
                    f.write(json.dumps(training_ex, ensure_ascii=False) + "\n")

            generated += len(examples)
            batch_num = i // batch_size + 1
            print(f"  Batch {batch_num}: +{len(examples)} (total: {generated}/{target_count})")

            time.sleep(0.3)

        except RateLimitError:
            print("  Rate limited. Waiting 30s...")
            time.sleep(30)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(3)

    print(f"\n  Done! Generated {generated} examples from meeting data.")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Process meeting corpora into training data"
    )
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--process", action="store_true")
    parser.add_argument("--count", type=int, default=5000)

    args = parser.parse_args()

    if args.download:
        download_corpora()

    if args.process:
        if not os.environ.get("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set.")
            return
        process_meetings(args.count)

    if not args.download and not args.process:
        print("Use --download then --process.")


if __name__ == "__main__":
    main()
