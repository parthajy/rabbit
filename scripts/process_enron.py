"""
Rabbit — Enron Email Dataset Processor
Downloads and processes the Enron email corpus into training examples for all 8 signals.

The Enron corpus contains 500,000+ real corporate emails (legally public).
We process them into structured training data for extract, triage, summarize,
sentiment, importance, intent, expand, and answer tasks.

Usage:
    python scripts/process_enron.py --download          # Download corpus first
    python scripts/process_enron.py --process --count 30000   # Process into training data
"""

import argparse
import email
import json
import os
import random
import re
import tarfile
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI, RateLimitError

# ── Config ──────────────────────────────────────────────────────────────────

DATA_DIR = Path("data/external/enron")
OUTPUT_DIR = Path("data/synthetic")
MODEL = "gpt-4o-mini"

TASKS = ["extract", "triage", "summarize", "sentiment", "importance",
         "intent", "expand", "answer"]

# ── Download ────────────────────────────────────────────────────────────────


def download_enron():
    """Download the Enron email dataset."""
    import urllib.request

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"
    tar_path = DATA_DIR / "enron_mail.tar.gz"

    if tar_path.exists():
        print(f"  Already downloaded: {tar_path}")
    else:
        print(f"  Downloading Enron corpus (~423MB)...")
        print(f"  URL: {url}")
        urllib.request.urlretrieve(url, tar_path)
        print(f"  Downloaded to {tar_path}")

    # Extract
    extract_dir = DATA_DIR / "maildir"
    if extract_dir.exists():
        print(f"  Already extracted: {extract_dir}")
    else:
        print(f"  Extracting...")
        with tarfile.open(tar_path) as tar:
            tar.extractall(DATA_DIR)
        print(f"  Extracted to {DATA_DIR}")


# ── Email parsing ───────────────────────────────────────────────────────────


def parse_email_file(filepath: Path) -> dict | None:
    """Parse a single Enron email file into structured data."""
    try:
        with open(filepath, "r", errors="replace") as f:
            msg = email.message_from_file(f)

        body = msg.get_payload()
        if not isinstance(body, str):
            return None

        # Clean up body
        body = body.strip()
        if not body or len(body) < 50 or len(body) > 5000:
            return None

        # Skip automated/spam-like emails
        subject = msg.get("Subject", "")
        if any(skip in subject.lower() for skip in [
            "unsubscribe", "out of office", "auto-reply", "spam",
            "newsletter", "fyi - ", "test", "reminder:",
        ]):
            return None

        return {
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "cc": msg.get("Cc", ""),
            "subject": subject,
            "date": msg.get("Date", ""),
            "body": body,
        }
    except Exception:
        return None


def load_enron_emails(max_count: int = 50000) -> list[dict]:
    """Load and filter Enron emails."""
    maildir = DATA_DIR / "maildir"
    if not maildir.exists():
        # Try alternate path (some extractions nest differently)
        maildir = DATA_DIR / "enron_mail_20150507" / "maildir"
    if not maildir.exists():
        print(f"  Error: maildir not found at {maildir}")
        print(f"  Run with --download first.")
        return []

    print(f"  Scanning {maildir}...")
    email_files = list(maildir.rglob("*"))
    email_files = [f for f in email_files if f.is_file()]
    random.shuffle(email_files)

    print(f"  Found {len(email_files)} files. Parsing...")

    emails = []
    for f in email_files[:max_count * 3]:  # parse more than needed, filter later
        parsed = parse_email_file(f)
        if parsed:
            emails.append(parsed)
        if len(emails) >= max_count:
            break

    print(f"  Parsed {len(emails)} valid emails")
    return emails


# ── Processing into training examples ───────────────────────────────────────

PROCESS_PROMPT = """You are converting real corporate emails into training examples for Rabbit, an AI model for organizational memory.

Given these emails, generate training examples for ALL of the following tasks. Output JSONL where each line has: {{"task": "...", "input": "...", "output": "..."}}

TASKS:
1. "extract" — Input: email text. Output: JSON with people, organizations, decisions, action_items, dates, topics
2. "triage" — Input: email text. Output: JSON with type (email/decision/action_item/update), summary, tags
3. "summarize" — Input: email text. Output: 2-4 sentence rich summary
4. "sentiment" — Input: email text. Output: one word: positive, negative, neutral, tense, urgent
5. "importance" — Input: email text. Output: JSON with score (1-5) and reason (one line)
6. "intent" — Input: a question someone might ask about this email. Output: one word: factual, entity, temporal, synthesis, actions, history, aggregation
7. "expand" — Input: a vague query about this email's content. Output: expanded precise query
8. "answer" — Input: "Question: [question]\\nMemories: [1] [email content] [2] [related content]". Output: conversational answer with [1][2] citations, no markdown

Generate {count} total examples (mix of all tasks). Make it realistic.
Output ONLY valid JSONL lines.

EMAILS:
{emails}"""


def format_email_for_prompt(em: dict) -> str:
    """Format an email dict into a readable string."""
    parts = []
    if em["from"]:
        parts.append(f"From: {em['from']}")
    if em["to"]:
        parts.append(f"To: {em['to']}")
    if em["cc"]:
        parts.append(f"Cc: {em['cc']}")
    if em["subject"]:
        parts.append(f"Subject: {em['subject']}")
    if em["date"]:
        parts.append(f"Date: {em['date']}")
    parts.append(f"\n{em['body'][:1500]}")
    return "\n".join(parts)


def process_batch(
    client: OpenAI,
    emails_batch: list[dict],
    count: int,
) -> list[dict]:
    """Process a batch of emails into training examples via GPT."""

    emails_text = "\n\n---\n\n".join(
        format_email_for_prompt(em) for em in emails_batch
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        timeout=90,
        messages=[
            {
                "role": "system",
                "content": "You convert corporate emails into AI training data. Output ONLY valid JSONL.",
            },
            {
                "role": "user",
                "content": PROCESS_PROMPT.format(emails=emails_text, count=count),
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


def process_enron(target_count: int):
    """Process Enron emails into training examples."""
    client = OpenAI()

    emails = load_enron_emails(max_count=target_count)
    if not emails:
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Open output files (append mode for resume support)
    output_files = {}
    existing_counts = {}
    for task in TASKS:
        outfile = OUTPUT_DIR / f"{task}_synthetic.jsonl"
        existing_counts[task] = 0
        if outfile.exists():
            with open(outfile) as f:
                existing_counts[task] = sum(1 for line in f if line.strip())
        output_files[task] = outfile

    total_existing = sum(existing_counts.values())
    print(f"\n{'='*60}")
    print(f"  RABBIT — Enron Email Processor")
    print(f"  Emails loaded: {len(emails)}")
    print(f"  Target: {target_count} new examples")
    print(f"  Existing synthetic: {total_existing}")
    print(f"{'='*60}")

    batch_size = 5  # emails per API call
    examples_per_batch = 20  # target examples per call
    generated = 0

    for i in range(0, len(emails), batch_size):
        if generated >= target_count:
            break

        batch = emails[i:i + batch_size]

        try:
            examples = process_batch(client, batch, examples_per_batch)

            # Write to task-specific files
            for ex in examples:
                task = ex["task"]
                outfile = output_files[task]
                training_ex = {"input": ex["input"], "output": ex["output"]}
                with open(outfile, "a") as f:
                    f.write(json.dumps(training_ex, ensure_ascii=False) + "\n")

            generated += len(examples)
            batch_num = i // batch_size + 1
            print(f"  Batch {batch_num}: +{len(examples)} "
                  f"(total: {generated}/{target_count})")

            time.sleep(0.3)

        except RateLimitError:
            print("  Rate limited. Waiting 30s...")
            time.sleep(30)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(3)

    print(f"\n  Done! Generated {generated} examples from Enron emails.")
    for task in TASKS:
        outfile = output_files[task]
        if outfile.exists():
            with open(outfile) as f:
                count = sum(1 for line in f if line.strip())
            print(f"    {task}: {count} total")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Process Enron emails into training data"
    )
    parser.add_argument("--download", action="store_true", help="Download the Enron corpus")
    parser.add_argument("--process", action="store_true", help="Process emails into training data")
    parser.add_argument("--count", type=int, default=30000, help="Target example count (default: 30000)")

    args = parser.parse_args()

    if args.download:
        download_enron()

    if args.process:
        if not os.environ.get("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set.")
            return
        process_enron(args.count)

    if not args.download and not args.process:
        print("Use --download to fetch the corpus, --process to generate training data.")
        print("Example: python scripts/process_enron.py --download --process --count 30000")


if __name__ == "__main__":
    main()
