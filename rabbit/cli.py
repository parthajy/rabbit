"""
Rabbit CLI.

Usage:
    rabbit remember "Sarah delayed the launch to March 15."
    rabbit remember --file recording.mp3
    rabbit ask "When is the launch?"
    rabbit check "Let's launch on March 1st"
    rabbit memories
    rabbit stats
    rabbit lint
    rabbit compile "Sarah"
    rabbit sync --obsidian ~/Documents/MyVault
    rabbit config set key rab_test_abc123
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def get_client():
    """Get a Rabbit client using the configured API key."""
    from rabbit import Rabbit

    key = os.environ.get("RABBIT_API_KEY", "")
    base_url = os.environ.get("RABBIT_API_URL", "")

    # Check config file
    config_path = Path("~/.rabbit/config.json").expanduser()
    if config_path.exists():
        config = json.loads(config_path.read_text())
        key = key or config.get("key", "")
        base_url = base_url or config.get("base_url", "")

    if not key:
        print("No API key configured.")
        print("Set it with: rabbit config set key rab_test_YOUR_KEY")
        print("Or: export RABBIT_API_KEY=rab_test_YOUR_KEY")
        sys.exit(1)

    kwargs = {"api_key": key}
    if base_url:
        kwargs["base_url"] = base_url

    return Rabbit(**kwargs)


def cmd_remember(args):
    rab = get_client()
    if args.file:
        memories = rab.remember_file(args.file, source=args.source)
        print(f"Remembered {len(memories)} chunk(s) from {args.file}")
        for m in memories:
            print(f"  {m.id}: {m.summary[:80]}...")
    elif args.content:
        content = " ".join(args.content)
        memory = rab.remember(content, source=args.source)
        print(f"Remembered: {memory.id}")
        print(f"  Summary: {memory.summary}")
        print(f"  Type: {memory.triage_type} | Sentiment: {memory.sentiment} | Importance: {memory.importance}/5")
        if memory.tags:
            print(f"  Tags: {', '.join(memory.tags)}")
    else:
        print("Provide text or --file to remember.")


def cmd_ask(args):
    rab = get_client()
    question = " ".join(args.question)
    answer = rab.ask(question)
    print(answer.text)
    if answer.followups:
        print("\nFollow-up questions:")
        for q in answer.followups:
            print(f"  -> {q}")


def cmd_check(args):
    rab = get_client()
    context = " ".join(args.context)
    alert = rab.check(context)
    if alert.show:
        print(f"ALERT ({alert.reason}): {alert.context}")
    else:
        print("No contradictions or issues detected.")


def cmd_memories(args):
    rab = get_client()
    memories = rab.memories(limit=args.limit, source=args.source)
    if not memories:
        print("No memories stored yet.")
        return
    for m in memories:
        summary = m.get("summary", m.get("content", "")[:80])
        print(f"  {m['id']}: [{m.get('source', '?')}] {summary}")
    print(f"\nTotal: {len(memories)} memories shown")


def cmd_stats(args):
    rab = get_client()
    stats = rab.stats()
    print(json.dumps(stats, indent=2))


def cmd_lint(args):
    rab = get_client()
    report = rab.lint()
    print(f"Health Score: {report.get('health_score', 0):.0%}")
    print(f"Total Memories: {report.get('total_memories', 0)}")
    if report.get("contradictions"):
        print(f"\nContradictions ({len(report['contradictions'])}):")
        for c in report["contradictions"]:
            print(f"  - {c.get('explanation', 'Unknown')}")
    if report.get("stale_items"):
        print(f"\nStale Items ({len(report['stale_items'])}):")
        for s in report["stale_items"]:
            print(f"  - {s.get('summary', '')} ({s.get('age_days', '?')} days old)")


def cmd_compile(args):
    rab = get_client()
    entity = " ".join(args.entity)
    page = rab.compile(entity)
    print(page)


def cmd_config(args):
    config_path = Path("~/.rabbit/config.json").expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text())

    if args.action == "set":
        config[args.key] = args.value
        config_path.write_text(json.dumps(config, indent=2))
        print(f"Set {args.key} = {args.value}")
    elif args.action == "get":
        print(config.get(args.key, "(not set)"))
    elif args.action == "list":
        for k, v in config.items():
            display = v[:20] + "..." if len(str(v)) > 20 else v
            print(f"  {k} = {display}")


def cmd_sync(args):
    rab = get_client()

    if args.obsidian:
        vault_path = Path(args.obsidian).expanduser()
        if not vault_path.exists():
            print(f"Vault not found: {vault_path}")
            sys.exit(1)

        md_files = list(vault_path.glob("**/*.md"))
        print(f"Found {len(md_files)} markdown files in {vault_path}")

        for i, f in enumerate(md_files):
            text = f.read_text(encoding="utf-8", errors="replace")
            if len(text.strip()) < 10:
                continue
            memory = rab.remember(text, source="obsidian", metadata={"filename": f.name})
            print(f"  [{i+1}/{len(md_files)}] {f.name} -> {memory.id}")

        print(f"\nSynced {len(md_files)} notes.")

    elif args.dir:
        dir_path = Path(args.dir).expanduser()
        if not dir_path.exists():
            print(f"Directory not found: {dir_path}")
            sys.exit(1)

        files = [f for f in dir_path.rglob("*") if f.is_file() and not f.name.startswith(".")]
        print(f"Found {len(files)} files in {dir_path}")

        for i, f in enumerate(files):
            try:
                memories = rab.remember_file(str(f), source="file")
                print(f"  [{i+1}/{len(files)}] {f.name} -> {len(memories)} memories")
            except Exception as e:
                print(f"  [{i+1}/{len(files)}] {f.name} -> SKIP ({e})")

    else:
        print("Specify --obsidian <vault_path> or --dir <directory>")


def main():
    parser = argparse.ArgumentParser(
        prog="rabbit",
        description="Rabbit CLI — Memory infrastructure for the world.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # remember
    p_remember = subparsers.add_parser("remember", help="Remember text or a file")
    p_remember.add_argument("content", nargs="*", help="Text to remember")
    p_remember.add_argument("--file", "-f", help="File to ingest")
    p_remember.add_argument("--source", "-s", default="cli", help="Source label")

    # ask
    p_ask = subparsers.add_parser("ask", help="Ask a question")
    p_ask.add_argument("question", nargs="+", help="Your question")

    # check
    p_check = subparsers.add_parser("check", help="Check for contradictions")
    p_check.add_argument("context", nargs="+", help="Current context to check")

    # memories
    p_memories = subparsers.add_parser("memories", help="List stored memories")
    p_memories.add_argument("--limit", "-n", type=int, default=20)
    p_memories.add_argument("--source", "-s")

    # stats
    subparsers.add_parser("stats", help="Show usage statistics")

    # lint
    subparsers.add_parser("lint", help="Audit memory health")

    # compile
    p_compile = subparsers.add_parser("compile", help="Compile wiki page for an entity")
    p_compile.add_argument("entity", nargs="+", help="Entity name")

    # config
    p_config = subparsers.add_parser("config", help="Configure Rabbit CLI")
    p_config.add_argument("action", choices=["set", "get", "list"])
    p_config.add_argument("key", nargs="?", default="")
    p_config.add_argument("value", nargs="?", default="")

    # sync
    p_sync = subparsers.add_parser("sync", help="Sync a folder or vault")
    p_sync.add_argument("--obsidian", help="Path to Obsidian vault")
    p_sync.add_argument("--dir", help="Path to directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "remember": cmd_remember,
        "ask": cmd_ask,
        "check": cmd_check,
        "memories": cmd_memories,
        "stats": cmd_stats,
        "lint": cmd_lint,
        "compile": cmd_compile,
        "config": cmd_config,
        "sync": cmd_sync,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
