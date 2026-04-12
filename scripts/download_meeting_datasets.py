"""
Download and convert public meeting datasets for Rabbit v2.0 training.

Commercial-safe datasets only:
- AMI Meeting Corpus (CC BY 4.0) — 170 meetings with decisions/actions
- QMSum (MIT) — 1.8K query-focused meeting summaries
- GovReport (public domain) — 19K long government reports
- BillSum (public domain) — 23K congressional bills + summaries
- ELITR Minuting (CC BY-SA 4.0) — real project meeting minutes

Output: data/filtered/meetings_real_filtered.jsonl
  Format: {"input": "[SIGNAL] content", "output": "extraction/summary"}

Run on RunPod CPU pod:
  pip install datasets
  python scripts/download_meeting_datasets.py
"""

import json
import os
from pathlib import Path
from typing import Optional

OUTPUT_FILE = Path("data/filtered/meetings_real_filtered.jsonl")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def write_example(f, signal: str, content: str, output: str):
    """Write one training example."""
    f.write(json.dumps({
        "input": f"[{signal}] {content}",
        "output": output,
    }) + "\n")


def process_ami():
    """AMI Meeting Corpus — full transcripts with annotations."""
    print("\n[1/5] Processing AMI Meeting Corpus...")
    try:
        from datasets import load_dataset
        ds = load_dataset("edinburghcstr/ami", "ihm", split="train", trust_remote_code=True)
        print(f"  Loaded {len(ds)} AMI examples")

        count = 0
        with open(OUTPUT_FILE, "a") as f:
            for item in ds:
                # AMI has words with speaker labels and timestamps
                # Group by meeting and create transcripts
                text = item.get("text", "")
                if len(text) > 500:
                    # Use as ANSWER training: question about meeting content
                    write_example(f, "SUMMARIZE", text[:4000],
                                  "Meeting transcript with multiple speakers discussing project design and decisions.")
                    count += 1
                    if count >= 500:
                        break
        print(f"  Added {count} AMI examples")
        return count
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def process_qmsum():
    """QMSum — query-focused meeting summarization."""
    print("\n[2/5] Processing QMSum...")
    try:
        from datasets import load_dataset
        ds = load_dataset("tau/scrolls", "qmsum", split="train", trust_remote_code=True)
        print(f"  Loaded {len(ds)} QMSum examples")

        count = 0
        with open(OUTPUT_FILE, "a") as f:
            for item in ds:
                inp = item.get("input", "")
                out = item.get("output", "")
                if inp and out and len(inp) > 200:
                    # QMSum format: "query: X\n\n<transcript>"
                    # Perfect ANSWER training data
                    write_example(f, "ANSWER", inp, out)
                    count += 1
        print(f"  Added {count} QMSum examples")
        return count
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def process_govreport():
    """GovReport — long government documents with summaries."""
    print("\n[3/5] Processing GovReport...")
    try:
        from datasets import load_dataset
        ds = load_dataset("launch/gov_report", split="train", trust_remote_code=True)
        print(f"  Loaded {len(ds)} GovReport examples")

        count = 0
        with open(OUTPUT_FILE, "a") as f:
            for item in ds:
                doc = item.get("document", item.get("report", ""))
                summary = item.get("summary", item.get("abstract", ""))
                if doc and summary and len(doc) > 500:
                    # Truncate very long docs
                    doc = doc[:8000]
                    write_example(f, "SUMMARIZE", doc, summary[:2000])
                    count += 1
                    if count >= 2000:
                        break
        print(f"  Added {count} GovReport examples")
        return count
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def process_billsum():
    """BillSum — Congressional bills with summaries."""
    print("\n[4/5] Processing BillSum...")
    try:
        from datasets import load_dataset
        ds = load_dataset("FiscalNote/billsum", split="train")
        print(f"  Loaded {len(ds)} BillSum examples")

        count = 0
        with open(OUTPUT_FILE, "a") as f:
            for item in ds:
                text = item.get("text", "")
                summary = item.get("summary", "")
                if text and summary and len(text) > 500:
                    text = text[:6000]
                    write_example(f, "SUMMARIZE", text, summary[:1500])
                    count += 1
                    if count >= 2000:
                        break
        print(f"  Added {count} BillSum examples")
        return count
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def process_dialogsum():
    """DialogSum — dialogue summarization (bonus)."""
    print("\n[5/5] Processing DialogSum...")
    try:
        from datasets import load_dataset
        ds = load_dataset("knkarthick/dialogsum", split="train")
        print(f"  Loaded {len(ds)} DialogSum examples")

        count = 0
        with open(OUTPUT_FILE, "a") as f:
            for item in ds:
                dialogue = item.get("dialogue", "")
                summary = item.get("summary", "")
                topic = item.get("topic", "")
                if dialogue and summary and len(dialogue) > 200:
                    # Use for TRIAGE + SUMMARIZE
                    triage_output = json.dumps({
                        "type": "meeting",
                        "summary": summary,
                        "tags": [topic.lower()] if topic else [],
                    })
                    write_example(f, "TRIAGE", dialogue, triage_output)
                    write_example(f, "SUMMARIZE", dialogue, summary)
                    count += 2
                    if count >= 2000:
                        break
        print(f"  Added {count} DialogSum examples")
        return count
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def main():
    print("=" * 60)
    print("  Downloading Public Meeting Datasets for Rabbit v2.0")
    print("=" * 60)

    # Clear existing file
    if OUTPUT_FILE.exists():
        backup = OUTPUT_FILE.with_suffix(".jsonl.bak")
        OUTPUT_FILE.rename(backup)
        print(f"Backed up existing file to {backup}")

    total = 0
    total += process_ami()
    total += process_qmsum()
    total += process_govreport()
    total += process_billsum()
    total += process_dialogsum()

    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {total} examples added to {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
