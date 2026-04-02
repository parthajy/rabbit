"""
Rabbit — Seed Converter
Converts raw seed files (transcript.md, thread.md, copilot.md, standups.md)
into structured JSONL training examples across all 5 tasks using Claude.

This uses Claude to intelligently extract training examples from your real
organizational data, producing high-quality seed examples that reflect
actual usage patterns.

Usage:
    python scripts/convert_seeds.py
    python scripts/convert_seeds.py --seed-dir seed --output-dir data/seeds
"""

import argparse
import json
import os
import time
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-20250514"
SEED_DIR = Path("seed")
OUTPUT_DIR = Path("data/seeds")

TASKS = ["intent", "extract", "triage", "expand", "answer"]

# ── Conversion prompts ──────────────────────────────────────────────────────

CONVERSION_PROMPTS = {
    "intent": """From the following raw organizational data, generate intent classification training examples.

For each example:
- "input": a realistic question someone would ask about the information in this data
- "output": exactly ONE word: factual | entity | temporal | synthesis | actions | history | aggregation

Generate diverse queries: formal, casual, vague ("what about that pricing thing"), specific, with implicit references.
Aim for {count} examples. Output ONLY valid JSONL.

Raw data:
{content}""",

    "extract": """From the following raw organizational data, generate entity extraction training examples.

For each example:
- "input": a passage of raw text (meeting snippet, note, message) taken from or inspired by this data
- "output": JSON object with: people, organizations, decisions, action_items, dates, topics
  - action_items: [{{"owner": "Name", "task": "desc", "due": "date"}}]

Keep the input text realistic and messy. Aim for {count} examples. Output ONLY valid JSONL.

Raw data:
{content}""",

    "triage": """From the following raw organizational data, generate memory classification examples.

For each example:
- "input": raw captured content (meeting transcript, note, message, standup)
- "output": JSON object with: type, summary, tags
  - type: meeting | note | email | decision | action_item | update | conversation
  - summary: 1-2 sentences
  - tags: 3-6 lowercase keywords

Aim for {count} examples. Output ONLY valid JSONL.

Raw data:
{content}""",

    "expand": """From the following raw organizational data, generate query expansion examples.

For each example:
- "input": a short/vague query someone might type about this data (how people ACTUALLY search)
- "output": an expanded, precise query that captures the user's likely intent

Include name-only queries ("brian"), project refs ("the slack thing"), temporal vagueness ("last week"),
implicit refs ("what did we decide"), typos ("standup tmrw?").

Aim for {count} examples. Output ONLY valid JSONL.

Raw data:
{content}""",

    "answer": """From the following raw organizational data, generate Q&A training examples.

For each example:
- "input": "Question: [question]\\nMemories: [1] ... [2] ... [3] ..."
  Use actual content from the data as memory context.
- "output": conversational answer with [1][2][3] citations, NO markdown

Include cases where memories show decision evolution, partial answers, and cross-meeting synthesis.

Aim for {count} examples. Output ONLY valid JSONL.

Raw data:
{content}""",
}


def chunk_content(content: str, max_chars: int = 6000) -> list[str]:
    """Split content into chunks that fit in API calls."""
    lines = content.split("\n")
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        if current_len + len(line) > max_chars and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("\n".join(current))

    return chunks


def convert_chunk(
    client: anthropic.Anthropic,
    content: str,
    task: str,
    count: int,
) -> list[dict]:
    """Convert a chunk of raw content into training examples."""

    prompt = CONVERSION_PROMPTS[task].format(content=content, count=count)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system="You are converting real organizational data into training examples for Rabbit, an AI memory model. Output ONLY valid JSONL lines.",
        messages=[{"role": "user", "content": prompt}],
    )

    examples = []
    for line in response.content[0].text.strip().split("\n"):
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


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Convert raw seed files into JSONL training data"
    )
    parser.add_argument("--seed-dir", type=Path, default=SEED_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--examples-per-chunk", type=int, default=15,
        help="Target examples per chunk per task (default: 15)",
    )

    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set.")
        return

    client = anthropic.Anthropic()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load all seed files
    seed_files = list(args.seed_dir.glob("*.md"))
    print(f"\n{'='*60}")
    print(f"  RABBIT — Seed Converter")
    print(f"  Seed files: {[f.name for f in seed_files]}")
    print(f"  Tasks: {TASKS}")
    print(f"{'='*60}")

    for task in TASKS:
        output_file = args.output_dir / f"{task}_seeds.jsonl"
        all_examples = []

        # Load existing examples
        if output_file.exists():
            with open(output_file) as f:
                for line in f:
                    if line.strip():
                        all_examples.append(json.loads(line.strip()))
            print(f"\n  [{task.upper()}] {len(all_examples)} existing examples")

        for seed_file in seed_files:
            content = seed_file.read_text()
            chunks = chunk_content(content)

            print(f"\n  [{task.upper()}] Processing {seed_file.name} "
                  f"({len(chunks)} chunks)...")

            for i, chunk in enumerate(chunks):
                try:
                    examples = convert_chunk(
                        client, chunk, task, args.examples_per_chunk
                    )
                    all_examples.extend(examples)
                    print(f"    Chunk {i+1}/{len(chunks)}: +{len(examples)} examples")
                    time.sleep(0.5)

                except anthropic.RateLimitError:
                    print("    Rate limited. Waiting 30s...")
                    time.sleep(30)
                except Exception as e:
                    print(f"    Error: {e}")
                    time.sleep(3)

        # Write all examples
        with open(output_file, "w") as f:
            for ex in all_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        print(f"  [{task.upper()}] Total: {len(all_examples)} → {output_file}")

    print(f"\n{'='*60}")
    print(f"  RABBIT — Seed conversion complete!")
    print(f"  Next: python scripts/generate_synthetic.py --count 5000")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
