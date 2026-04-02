"""
Rabbit — Synthetic Data Generator
Uses Claude API to expand seed examples into large training datasets.

Usage:
    python scripts/generate_synthetic.py --task intent --count 2000
    python scripts/generate_synthetic.py --task all --count 10000
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

import anthropic

# ── Config ──────────────────────────────────────────────────────────────────

TASKS = ["intent", "extract", "triage", "expand", "answer"]

SEED_DIR = Path("data/seeds")
OUTPUT_DIR = Path("data/synthetic")

# How many seed examples to include in each generation prompt
SEEDS_PER_BATCH = 15

# How many examples to request per API call
EXAMPLES_PER_CALL = 25

MODEL = "claude-sonnet-4-20250514"

# ── Task-specific generation prompts ────────────────────────────────────────

TASK_PROMPTS = {
    "intent": """You are generating training data for Rabbit, an AI model that classifies user query intent for an organizational memory system.

Given these seed examples, generate {count} NEW examples following the exact same format.

Rules:
- Input is a natural language question someone would ask about their work memories
- Output is exactly ONE word from: factual | entity | temporal | synthesis | actions | history | aggregation
- Vary the topics: meetings, projects, people, deadlines, budgets, decisions, emails, Slack messages
- Vary phrasing: formal, casual, typos, short, long, vague, specific
- Vary industries: tech, finance, healthcare, legal, marketing, education, consulting
- Make some queries ambiguous to test edge cases
- Output ONLY valid JSONL, one example per line

Seed examples:
{seeds}

Generate {count} new examples in JSONL format (one JSON object per line):""",

    "extract": """You are generating training data for Rabbit, an AI model that extracts structured information from raw text for an organizational memory system.

Given these seed examples, generate {count} NEW examples following the exact same format.

Rules:
- Input is raw text: meeting notes, email snippets, Slack messages, note fragments
- Output is a JSON object with keys: people, organizations, decisions, action_items, dates, topics
- action_items should have: owner, task, due (if mentioned)
- Vary the complexity: some have 1 entity, some have 10+
- Include messy inputs: abbreviations, typos, incomplete sentences
- Vary industries and contexts
- Output ONLY valid JSONL, one example per line

Seed examples:
{seeds}

Generate {count} new examples in JSONL format (one JSON object per line):""",

    "triage": """You are generating training data for Rabbit, an AI model that classifies and summarizes incoming content for an organizational memory system.

Given these seed examples, generate {count} NEW examples following the exact same format.

Rules:
- Input is raw captured content (meeting transcript, note, email, Slack thread)
- Output is a JSON object with keys: type, summary, tags
- type is one of: meeting, note, email, decision, action_item, update, conversation
- summary is 1-2 sentences capturing the essence
- tags are 3-6 lowercase keywords
- Vary content length: 1 sentence to 3 paragraphs
- Output ONLY valid JSONL, one example per line

Seed examples:
{seeds}

Generate {count} new examples in JSONL format (one JSON object per line):""",

    "expand": """You are generating training data for Rabbit, an AI model that expands vague user queries into precise search queries for an organizational memory system.

Given these seed examples, generate {count} NEW examples following the exact same format.

Rules:
- Input is a short/vague user query (how people actually type)
- Output is an expanded, specific query that captures the user's likely intent
- The expanded query should mention: what to search for, what types of information to include, time ranges if relevant
- Vary vagueness: "brian?" vs "what about the Q2 thing" vs "updates on project alpha"
- This is THE MOST CRITICAL TASK — bad expansion = bad search results
- Output ONLY valid JSONL, one example per line

Seed examples:
{seeds}

Generate {count} new examples in JSONL format (one JSON object per line):""",

    "answer": """You are generating training data for Rabbit, an AI model that generates conversational answers from retrieved memory context.

Given these seed examples, generate {count} NEW examples following the exact same format.

Rules:
- Input has two parts: "Question:" and "Memories:" (numbered [1], [2], [3]...)
- Output is a conversational answer with citations [1][2][3] referencing the memory sources
- NO markdown formatting in the output (no **, no ##, no bullet points)
- Answers should be natural, concise, and directly address the question
- Include cases where memories partially answer the question
- Include cases where memories conflict slightly
- Output ONLY valid JSONL, one example per line

Seed examples:
{seeds}

Generate {count} new examples in JSONL format (one JSON object per line):""",
}

# ── Core logic ──────────────────────────────────────────────────────────────


def load_seeds(task: str) -> list[dict]:
    """Load seed examples for a task."""
    seed_file = SEED_DIR / f"{task}_seeds.jsonl"
    if not seed_file.exists():
        raise FileNotFoundError(
            f"Seed file not found: {seed_file}\n"
            f"Create it first with 100 hand-written examples."
        )

    seeds = []
    with open(seed_file) as f:
        for line in f:
            line = line.strip()
            if line:
                seeds.append(json.loads(line))

    print(f"  Loaded {len(seeds)} seed examples from {seed_file}")
    return seeds


def generate_batch(
    client: anthropic.Anthropic,
    task: str,
    seeds: list[dict],
    count: int,
) -> list[dict]:
    """Generate a batch of synthetic examples using Claude."""

    # Sample random seeds for this batch
    sampled = random.sample(seeds, min(SEEDS_PER_BATCH, len(seeds)))
    seeds_text = "\n".join(json.dumps(s) for s in sampled)

    prompt = TASK_PROMPTS[task].format(seeds=seeds_text, count=count)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse JSONL from response
    examples = []
    for line in response.content[0].text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if "input" in obj and "output" in obj:
                examples.append(obj)
        except json.JSONDecodeError:
            continue  # skip malformed lines

    return examples


def generate_for_task(task: str, target_count: int):
    """Generate synthetic data for a single task."""
    print(f"\n{'='*60}")
    print(f"  RABBIT — Generating synthetic data for: {task.upper()}")
    print(f"  Target: {target_count} examples")
    print(f"{'='*60}")

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    seeds = load_seeds(task)

    output_file = OUTPUT_DIR / f"{task}_synthetic.jsonl"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing examples if resuming
    existing = []
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                if line.strip():
                    existing.append(json.loads(line.strip()))
        print(f"  Resuming: {len(existing)} examples already generated")

    total = len(existing)
    batch_num = 0

    while total < target_count:
        batch_num += 1
        remaining = target_count - total
        batch_size = min(EXAMPLES_PER_CALL, remaining)

        print(f"\n  Batch {batch_num}: requesting {batch_size} examples "
              f"({total}/{target_count} done)...")

        try:
            examples = generate_batch(client, task, seeds, batch_size)

            # Append to file
            with open(output_file, "a") as f:
                for ex in examples:
                    f.write(json.dumps(ex) + "\n")

            total += len(examples)
            print(f"  Got {len(examples)} valid examples. Total: {total}")

            # Rate limiting
            time.sleep(1)

        except anthropic.RateLimitError:
            print("  Rate limited. Waiting 30 seconds...")
            time.sleep(30)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(5)

    print(f"\n  Done! {total} examples written to {output_file}")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Generate synthetic training data via Claude API"
    )
    parser.add_argument(
        "--task",
        choices=TASKS + ["all"],
        required=True,
        help="Which task to generate data for (or 'all')",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10000,
        help="Number of examples to generate per task (default: 10000)",
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        return

    tasks = TASKS if args.task == "all" else [args.task]

    for task in tasks:
        generate_for_task(task, args.count)

    print("\n" + "=" * 60)
    print("  RABBIT — Synthetic data generation complete!")
    print("  Next step: python scripts/quality_filter.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
