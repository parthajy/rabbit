"""
Rabbit — Master Dataset Builder
Orchestrates all data sources to build the 100K training dataset.

Runs each processor in sequence, tracks progress, and gives a final report.

Usage:
    python scripts/build_dataset.py                    # Run everything
    python scripts/build_dataset.py --skip-download    # Skip downloading (if already done)
    python scripts/build_dataset.py --source github    # Run only one source
    python scripts/build_dataset.py --status           # Just show current counts
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SYNTHETIC_DIR = Path("data/synthetic")
FILTERED_DIR = Path("data/filtered")

TASKS = ["intent", "extract", "triage", "expand", "answer",
         "summarize", "sentiment", "importance"]


def count_examples(directory: Path) -> dict:
    """Count examples per task in a directory."""
    counts = {}
    for task in TASKS:
        for pattern in [f"{task}_synthetic.jsonl", f"{task}_filtered.jsonl", f"{task}_seeds.jsonl"]:
            filepath = directory / pattern
            if filepath.exists():
                with open(filepath) as f:
                    count = sum(1 for line in f if line.strip())
                key = f"{task}"
                counts[key] = counts.get(key, 0) + count
    return counts


def show_status():
    """Show current dataset status."""
    print(f"\n{'='*70}")
    print(f"  RABBIT — Dataset Status")
    print(f"{'='*70}")

    # Count synthetic
    print(f"\n  Synthetic (data/synthetic/):")
    total_synthetic = 0
    for task in TASKS:
        filepath = SYNTHETIC_DIR / f"{task}_synthetic.jsonl"
        if filepath.exists():
            with open(filepath) as f:
                count = sum(1 for line in f if line.strip())
            print(f"    {task:15s} {count:>8,}")
            total_synthetic += count
        else:
            print(f"    {task:15s}        0")
    print(f"    {'TOTAL':15s} {total_synthetic:>8,}")

    # Count filtered
    print(f"\n  Filtered (data/filtered/):")
    total_filtered = 0
    for task in TASKS:
        filepath = FILTERED_DIR / f"{task}_filtered.jsonl"
        if filepath.exists():
            with open(filepath) as f:
                count = sum(1 for line in f if line.strip())
            print(f"    {task:15s} {count:>8,}")
            total_filtered += count
        else:
            print(f"    {task:15s}        0")
    print(f"    {'TOTAL':15s} {total_filtered:>8,}")

    # Count seeds
    seed_dir = Path("data/seeds")
    print(f"\n  Seeds (data/seeds/):")
    total_seeds = 0
    for task in TASKS:
        filepath = seed_dir / f"{task}_seeds.jsonl"
        if filepath.exists():
            with open(filepath) as f:
                count = sum(1 for line in f if line.strip())
            print(f"    {task:15s} {count:>8,}")
            total_seeds += count
    print(f"    {'TOTAL':15s} {total_seeds:>8,}")

    grand_total = total_synthetic + total_seeds
    print(f"\n  {'GRAND TOTAL':17s} {grand_total:>8,}")
    print(f"  {'TARGET':17s} {'100,000':>8s}")
    print(f"  {'PROGRESS':17s} {grand_total/1000:.1f}%")
    print(f"{'='*70}\n")


def run_step(description: str, command: list[str]) -> bool:
    """Run a pipeline step and report result."""
    print(f"\n{'─'*60}")
    print(f"  STEP: {description}")
    print(f"{'─'*60}")

    try:
        result = subprocess.run(
            command,
            check=False,
            timeout=7200,  # 2 hour max per step
        )
        if result.returncode == 0:
            print(f"  ✓ {description} completed")
            return True
        else:
            print(f"  ✗ {description} failed (exit code {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ {description} timed out (2 hours)")
        return False
    except Exception as e:
        print(f"  ✗ {description} error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Build the 100K training dataset"
    )
    parser.add_argument("--status", action="store_true", help="Show current counts only")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading datasets")
    parser.add_argument("--source", choices=["github", "meetings", "enron", "synthetic", "filter"],
                        help="Run only one source")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    py = sys.executable  # Use the same Python that's running this script

    print(f"\n{'='*70}")
    print(f"  RABBIT — Building 100K Training Dataset")
    print(f"  Target: 100,000 clean training examples across 8 signals")
    print(f"{'='*70}")

    show_status()

    steps = []

    # ── Step 1: Download external datasets ──
    if not args.skip_download and args.source in (None, "meetings", "enron"):
        steps.append(("Download meeting corpora",
                       [py, "scripts/process_meetings.py", "--download"]))

    # ── Step 2: Process GitHub Issues (free, no download needed) ──
    if args.source in (None, "github"):
        steps.append(("Process GitHub Issues → 15,000 examples",
                       [py, "scripts/process_github.py", "--count", "15000"]))

    # ── Step 3: Process meeting corpora ──
    if args.source in (None, "meetings"):
        steps.append(("Process meeting corpora → 5,000 examples",
                       [py, "scripts/process_meetings.py", "--process", "--count", "5000"]))

    # ── Step 4: Process Enron (if downloaded) ──
    if args.source in (None, "enron"):
        enron_dir = Path("data/external/enron/maildir")
        if enron_dir.exists() or not args.skip_download:
            steps.append(("Process Enron emails → 30,000 examples",
                           [py, "scripts/process_enron.py", "--process", "--count", "30000"]))
        else:
            print("\n  Note: Enron corpus not downloaded. Run with --download or:")
            print("    python scripts/process_enron.py --download")

    # ── Step 5: Scale synthetic generation ──
    if args.source in (None, "synthetic"):
        steps.append(("Generate synthetic (all 8 signals) → 40,000 examples",
                       [py, "scripts/generate_synthetic.py", "--count", "40000", "--universes", "10"]))

    # ── Step 6: Quality filter everything ──
    if args.source in (None, "filter"):
        steps.append(("Quality filter all tasks",
                       [py, "scripts/quality_filter.py", "--task", "all"]))

    # Run all steps
    completed = 0
    failed = 0
    for description, command in steps:
        success = run_step(description, command)
        if success:
            completed += 1
        else:
            failed += 1

    # Final report
    print(f"\n{'='*70}")
    print(f"  RABBIT — Dataset Build Complete")
    print(f"  Steps completed: {completed}/{completed + failed}")
    if failed:
        print(f"  Steps failed: {failed}")
    print(f"{'='*70}")

    show_status()

    print("  Next: python scripts/finetune.py")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
