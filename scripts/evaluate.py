"""
Rabbit — Evaluation Script
Compares Rabbit model outputs against current Groq/OpenAI outputs on held-out test cases.

Usage:
    python scripts/evaluate.py --model-url http://localhost:11434/v1
    python scripts/evaluate.py --model-url http://localhost:11434/v1 --task intent
"""

import argparse
import json
import re
import time
from pathlib import Path

import httpx

# ── Config ──────────────────────────────────────────────────────────────────

TASKS = ["intent", "extract", "triage", "expand", "answer"]
TEST_FILE = Path("evals/test_cases.jsonl")

TASK_SYSTEM_PROMPTS = {
    "intent": "You are Rabbit, Reattend's memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand": "You are Rabbit, Reattend's memory AI. Expand the user's vague query into a precise, comprehensive search query that captures their likely intent.",
    "answer": "You are Rabbit, Reattend's memory AI. Answer the user's question using the provided memory context. Use citations [1][2][3] to reference sources. Do not use markdown formatting.",
}

TASK_PREFIXES = {
    "intent": "[INTENT]",
    "extract": "[EXTRACT]",
    "triage": "[TRIAGE]",
    "expand": "[EXPAND]",
    "answer": "[ANSWER]",
}

# ── Metrics ─────────────────────────────────────────────────────────────────


def exact_match(predicted: str, expected: str) -> float:
    """Simple exact match after normalization."""
    return 1.0 if predicted.strip().lower() == expected.strip().lower() else 0.0


def json_key_match(predicted: str, expected: str) -> float:
    """Compare JSON outputs by key presence and value overlap."""
    try:
        pred = json.loads(predicted) if isinstance(predicted, str) else predicted
        exp = json.loads(expected) if isinstance(expected, str) else expected
    except json.JSONDecodeError:
        return 0.0

    if not isinstance(pred, dict) or not isinstance(exp, dict):
        return 0.0

    # Check key presence
    expected_keys = set(exp.keys())
    predicted_keys = set(pred.keys())
    key_score = len(expected_keys & predicted_keys) / len(expected_keys) if expected_keys else 0

    # Check value overlap for list fields
    value_scores = []
    for key in expected_keys & predicted_keys:
        ev = exp[key]
        pv = pred.get(key)
        if isinstance(ev, list) and isinstance(pv, list):
            ev_set = {str(x).lower() for x in ev}
            pv_set = {str(x).lower() for x in pv}
            if ev_set:
                precision = len(ev_set & pv_set) / len(pv_set) if pv_set else 0
                recall = len(ev_set & pv_set) / len(ev_set)
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                value_scores.append(f1)

    value_score = sum(value_scores) / len(value_scores) if value_scores else key_score
    return (key_score + value_score) / 2


def citation_check(predicted: str, expected: str) -> float:
    """Check if answer contains citations and is reasonable length."""
    has_citations = bool(re.search(r"\[\d+\]", predicted))
    no_markdown = not bool(re.search(r"(\*\*|##|```)", predicted))
    reasonable_length = 20 < len(predicted) < 2000

    score = 0.0
    if has_citations:
        score += 0.5
    if no_markdown:
        score += 0.25
    if reasonable_length:
        score += 0.25
    return score


def length_ratio(predicted: str, expected: str) -> float:
    """Score based on output length being in reasonable range of expected."""
    if not expected:
        return 0.5
    ratio = len(predicted) / len(expected) if expected else 0
    if 0.5 <= ratio <= 2.0:
        return 1.0
    elif 0.25 <= ratio <= 3.0:
        return 0.5
    return 0.0


TASK_METRICS = {
    "intent": [("exact_match", exact_match)],
    "extract": [("json_key_match", json_key_match)],
    "triage": [("json_key_match", json_key_match)],
    "expand": [("length_ratio", length_ratio)],
    "answer": [("citation_check", citation_check)],
}

# ── Inference ───────────────────────────────────────────────────────────────


def query_model(model_url: str, task: str, input_text: str) -> tuple[str, float]:
    """Send a request to the model and return (response, latency_ms)."""
    start = time.time()

    response = httpx.post(
        f"{model_url}/chat/completions",
        json={
            "model": "rabbit",
            "messages": [
                {"role": "system", "content": TASK_SYSTEM_PROMPTS[task]},
                {"role": "user", "content": f"{TASK_PREFIXES[task]} {input_text}"},
            ],
            "max_tokens": 1024,
            "temperature": 0.1,
        },
        timeout=60,
    )

    latency = (time.time() - start) * 1000
    result = response.json()
    output = result["choices"][0]["message"]["content"]

    return output, latency


# ── Evaluation loop ─────────────────────────────────────────────────────────


def evaluate(model_url: str, tasks_to_eval: list[str]):
    """Run evaluation on held-out test cases."""
    print(f"\n{'='*60}")
    print(f"  RABBIT — Evaluation")
    print(f"  Model: {model_url}")
    print(f"  Tasks: {', '.join(tasks_to_eval)}")
    print(f"{'='*60}")

    # Load test cases
    if not TEST_FILE.exists():
        print(f"\n  Error: {TEST_FILE} not found.")
        print("  Create test cases first (100 per task).")
        return

    test_cases = {}
    with open(TEST_FILE) as f:
        for line in f:
            if not line.strip():
                continue
            case = json.loads(line.strip())
            task = case.get("task")
            if task in tasks_to_eval:
                test_cases.setdefault(task, []).append(case)

    for task in tasks_to_eval:
        cases = test_cases.get(task, [])
        if not cases:
            print(f"\n  No test cases for {task}. Skipping.")
            continue

        print(f"\n  --- {task.upper()} ({len(cases)} test cases) ---")

        metrics = TASK_METRICS[task]
        scores = {name: [] for name, _ in metrics}
        latencies = []
        errors = 0

        for i, case in enumerate(cases):
            try:
                predicted, latency = query_model(model_url, task, case["input"])
                latencies.append(latency)

                for metric_name, metric_fn in metrics:
                    score = metric_fn(predicted, case["expected_output"])
                    scores[metric_name].append(score)

                if (i + 1) % 10 == 0:
                    print(f"    {i+1}/{len(cases)} done...")

            except Exception as e:
                errors += 1
                print(f"    Error on case {i+1}: {e}")

        # Report
        print(f"\n  Results for {task.upper()}:")
        for metric_name, metric_scores in scores.items():
            if metric_scores:
                avg = sum(metric_scores) / len(metric_scores)
                print(f"    {metric_name}: {avg:.2%}")

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
            print(f"    avg_latency: {avg_latency:.0f}ms")
            print(f"    p95_latency: {p95_latency:.0f}ms")

        if errors:
            print(f"    errors: {errors}")

    print(f"\n{'='*60}")
    print(f"  RABBIT — Evaluation complete!")
    print(f"{'='*60}")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Evaluate model against held-out test cases"
    )
    parser.add_argument(
        "--model-url",
        required=True,
        help="Base URL of the model server (e.g., http://localhost:11434/v1)",
    )
    parser.add_argument(
        "--task",
        choices=TASKS + ["all"],
        default="all",
        help="Which task to evaluate (default: all)",
    )

    args = parser.parse_args()
    tasks = TASKS if args.task == "all" else [args.task]
    evaluate(args.model_url, tasks)


if __name__ == "__main__":
    main()
