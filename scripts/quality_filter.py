"""
Rabbit — Quality Filter
Removes bad/duplicate examples from synthetic data before training.

Usage:
    python scripts/quality_filter.py --task intent
    python scripts/quality_filter.py --task all
"""

import argparse
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

TASKS = ["intent", "extract", "triage", "expand", "answer", "summarize", "sentiment", "importance", "multiturn", "dontknow"]

SYNTHETIC_DIR = Path("data/synthetic")
FILTERED_DIR = Path("data/filtered")

# ── Task-specific validators ────────────────────────────────────────────────

VALID_INTENTS = {"factual", "entity", "temporal", "synthesis", "actions", "history", "aggregation"}
VALID_TRIAGE_TYPES = {"meeting", "note", "email", "decision", "action_item", "update", "conversation", "standup", "calendar"}
VALID_SENTIMENTS = {"positive", "negative", "neutral", "tense", "urgent"}


def validate_intent(example: dict) -> bool:
    """Intent output must be a single valid word."""
    output = example.get("output", "").strip().lower()
    return output in VALID_INTENTS


def validate_extract(example: dict) -> bool:
    """Extract output must be valid JSON with required keys."""
    output = example.get("output", "")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except json.JSONDecodeError:
            return False

    required_keys = {"people", "organizations", "decisions", "action_items", "dates", "topics"}
    if not isinstance(output, dict):
        return False
    return required_keys.issubset(output.keys())


def validate_triage(example: dict) -> bool:
    """Triage output must have type, summary, tags."""
    output = example.get("output", "")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except json.JSONDecodeError:
            return False

    if not isinstance(output, dict):
        return False
    if "type" not in output or "summary" not in output or "tags" not in output:
        return False
    return output.get("type", "").lower() in VALID_TRIAGE_TYPES


def validate_expand(example: dict) -> bool:
    """Expanded query should be longer than input and non-empty."""
    inp = example.get("input", "")
    out = example.get("output", "")
    return len(out) > len(inp) and len(out) > 20


def validate_answer(example: dict) -> bool:
    """Answer should contain citations, Sources section, and no markdown."""
    output = example.get("output", "")
    has_citation = bool(re.search(r"\[\d+\]", output))
    has_markdown = bool(re.search(r"(\*\*|##|```)", output))
    return has_citation and not has_markdown and len(output) > 50


def validate_summarize(example: dict) -> bool:
    """Summary should be 2-4 sentences, reasonable length."""
    output = example.get("output", "")
    if isinstance(output, dict):
        output = str(output)
    return 30 < len(output) < 2000 and len(output) > len(example.get("input", "")) * 0.1


def validate_sentiment(example: dict) -> bool:
    """Sentiment output must be a single valid word."""
    output = example.get("output", "").strip().lower()
    return output in VALID_SENTIMENTS


def validate_importance(example: dict) -> bool:
    """Importance must have score (1-5) and reason."""
    output = example.get("output", "")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except json.JSONDecodeError:
            return False

    if not isinstance(output, dict):
        return False
    score = output.get("score")
    if not isinstance(score, (int, float)) or score < 1 or score > 5:
        return False
    return "reason" in output and len(str(output["reason"])) > 5


def validate_multiturn(example: dict) -> bool:
    """Multi-turn must have Turn 1/Turn 2 in input and Sources in output."""
    inp = example.get("input", "")
    output = example.get("output", "")
    has_turns = "Turn 1" in inp or "Turn 2" in inp
    return has_turns and len(output) > 50


def validate_dontknow(example: dict) -> bool:
    """Don't-know must acknowledge gaps honestly."""
    output = example.get("output", "")
    # Should NOT be a confident full answer — should have hedging language
    has_honesty = any(phrase in output.lower() for phrase in [
        "don't have", "no record", "not find", "couldn't find",
        "missing", "not available", "no mention", "not clear",
        "might want to", "you could", "suggest", "follow up",
        "not enough", "partially", "limited",
    ])
    return has_honesty and len(output) > 30


VALIDATORS = {
    "intent": validate_intent,
    "extract": validate_extract,
    "triage": validate_triage,
    "expand": validate_expand,
    "answer": validate_answer,
    "summarize": validate_summarize,
    "sentiment": validate_sentiment,
    "importance": validate_importance,
    "multiturn": validate_multiturn,
    "dontknow": validate_dontknow,
}

# ── Deduplication ───────────────────────────────────────────────────────────


def deduplicate(examples: list[dict], threshold: float = 0.9) -> list[dict]:
    """Remove examples with >threshold string similarity."""
    unique = []
    seen_inputs = []

    for ex in examples:
        inp = ex.get("input", "")
        is_dup = False

        # Only check against last 100 for performance
        for prev in seen_inputs[-100:]:
            if SequenceMatcher(None, inp, prev).ratio() > threshold:
                is_dup = True
                break

        if not is_dup:
            unique.append(ex)
            seen_inputs.append(inp)

    return unique


# ── Outlier removal ─────────────────────────────────────────────────────────


def remove_outliers(examples: list[dict], key: str = "output") -> list[dict]:
    """Remove examples where output length is a statistical outlier."""
    if len(examples) < 10:
        return examples

    lengths = [len(str(ex.get(key, ""))) for ex in examples]
    lengths.sort()

    # Remove top/bottom 5% by length
    p5 = lengths[len(lengths) // 20]
    p95 = lengths[-len(lengths) // 20]

    return [
        ex for ex in examples
        if p5 <= len(str(ex.get(key, ""))) <= p95
    ]


# ── Main filter pipeline ───────────────────────────────────────────────────


def filter_task(task: str):
    """Run the full filter pipeline for a task."""
    print(f"\n{'='*60}")
    print(f"  RABBIT — Filtering: {task.upper()}")
    print(f"{'='*60}")

    input_file = SYNTHETIC_DIR / f"{task}_synthetic.jsonl"
    if not input_file.exists():
        print(f"  No synthetic data found at {input_file}. Skipping.")
        return

    # Load all examples (seeds + synthetic)
    examples = []

    # Load seeds first
    seed_file = Path("data/seeds") / f"{task}_seeds.jsonl"
    if seed_file.exists():
        with open(seed_file) as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line.strip()))
        print(f"  Loaded {len(examples)} seed examples")

    # Load synthetic
    synthetic_count = 0
    with open(input_file) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line.strip()))
                synthetic_count += 1
    print(f"  Loaded {synthetic_count} synthetic examples")
    print(f"  Total before filtering: {len(examples)}")

    # Step 1: Format validation
    validator = VALIDATORS[task]
    valid = [ex for ex in examples if validator(ex)]
    print(f"  After format validation: {len(valid)} ({len(examples) - len(valid)} removed)")

    # Step 2: Deduplication
    deduped = deduplicate(valid)
    print(f"  After deduplication: {len(deduped)} ({len(valid) - len(deduped)} removed)")

    # Step 3: Outlier removal
    filtered = remove_outliers(deduped)
    print(f"  After outlier removal: {len(filtered)} ({len(deduped) - len(filtered)} removed)")

    # Write output
    FILTERED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = FILTERED_DIR / f"{task}_filtered.jsonl"
    with open(output_file, "w") as f:
        for ex in filtered:
            f.write(json.dumps(ex) + "\n")

    keep_rate = len(filtered) / len(examples) * 100 if examples else 0
    print(f"\n  Result: {len(filtered)} clean examples ({keep_rate:.0f}% kept)")
    print(f"  Written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Filter synthetic training data for quality"
    )
    parser.add_argument(
        "--task",
        choices=TASKS + ["all"],
        required=True,
        help="Which task to filter (or 'all')",
    )

    args = parser.parse_args()
    tasks = TASKS if args.task == "all" else [args.task]

    for task in tasks:
        filter_task(task)

    print("\n" + "=" * 60)
    print("  RABBIT — Quality filtering complete!")
    print("  Next step: python scripts/finetune.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
