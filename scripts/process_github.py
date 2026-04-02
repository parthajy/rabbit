"""
Rabbit — GitHub Issues/PRs Processor
Fetches public GitHub issues and PR discussions, converts to training examples.

Real team discussions with decisions, assignments, follow-ups, and technical context.

Usage:
    python scripts/process_github.py --count 15000
    python scripts/process_github.py --count 5000 --repos "vercel/next.js,microsoft/vscode"
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import httpx
from openai import OpenAI, RateLimitError

# ── Config ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("data/synthetic")
MODEL = "gpt-4o-mini"

TASKS = ["extract", "triage", "summarize", "sentiment", "importance",
         "intent", "expand", "answer"]

# Popular repos with rich discussions
DEFAULT_REPOS = [
    "vercel/next.js",
    "microsoft/vscode",
    "facebook/react",
    "tailwindlabs/tailwindcss",
    "supabase/supabase",
    "langchain-ai/langchain",
    "openai/openai-python",
    "remix-run/remix",
    "prisma/prisma",
    "trpc/trpc",
    "calcom/cal.com",
    "novuhq/novu",
    "n8n-io/n8n",
    "docker/compose",
    "grafana/grafana",
]

# ── GitHub API ──────────────────────────────────────────────────────────────


def fetch_issues(repo: str, per_page: int = 30, pages: int = 5) -> list[dict]:
    """Fetch issues with comments from a GitHub repo."""
    headers = {}
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    issues = []
    client = httpx.Client(timeout=30)

    for page in range(1, pages + 1):
        try:
            # Fetch issues (include PRs since they have discussions too)
            resp = client.get(
                f"https://api.github.com/repos/{repo}/issues",
                params={
                    "state": "closed",  # closed issues have full discussions
                    "sort": "comments",  # most discussed first
                    "direction": "desc",
                    "per_page": per_page,
                    "page": page,
                },
                headers=headers,
            )

            if resp.status_code == 403:
                print(f"      Rate limited on {repo}. Waiting 60s...")
                time.sleep(60)
                continue
            if resp.status_code != 200:
                print(f"      Error {resp.status_code} on {repo}")
                break

            page_issues = resp.json()
            if not page_issues:
                break

            for issue in page_issues:
                # Skip issues with no comments (no discussion)
                if issue.get("comments", 0) < 2:
                    continue

                # Fetch comments
                comments = []
                try:
                    cresp = client.get(
                        issue["comments_url"],
                        params={"per_page": 10},
                        headers=headers,
                    )
                    if cresp.status_code == 200:
                        comments = cresp.json()
                except Exception:
                    pass

                issues.append({
                    "repo": repo,
                    "title": issue.get("title", ""),
                    "body": (issue.get("body") or "")[:2000],
                    "user": issue.get("user", {}).get("login", ""),
                    "labels": [l["name"] for l in issue.get("labels", [])],
                    "state": issue.get("state", ""),
                    "created_at": issue.get("created_at", ""),
                    "closed_at": issue.get("closed_at", ""),
                    "comments": [
                        {
                            "user": c.get("user", {}).get("login", ""),
                            "body": (c.get("body") or "")[:1000],
                            "created_at": c.get("created_at", ""),
                        }
                        for c in comments[:8]
                    ],
                })

            time.sleep(1)  # Be nice to GitHub API

        except Exception as e:
            print(f"      Error fetching {repo} page {page}: {e}")
            break

    client.close()
    return issues


# ── Processing ──────────────────────────────────────────────────────────────

PROCESS_PROMPT = """You are converting real GitHub issue discussions into training examples for Rabbit, an AI model for organizational memory.

These are real team discussions about bugs, features, and decisions. Convert them into training data.

Generate JSONL where each line has: {{"task": "...", "input": "...", "output": "..."}}

TASKS:
1. "extract" — Input: issue/discussion text. Output: JSON with people, organizations, decisions, action_items, dates, topics
2. "triage" — Input: issue/discussion text. Output: JSON with type (conversation/decision/action_item/update), summary, tags
3. "summarize" — Input: issue/discussion text. Output: 2-4 sentence rich summary
4. "sentiment" — Input: issue/discussion text. Output: one word: positive, negative, neutral, tense, urgent
5. "importance" — Input: issue/discussion text. Output: JSON with score (1-5) and reason
6. "intent" — Input: a question about this discussion. Output: one word: factual, entity, temporal, synthesis, actions, history, aggregation
7. "expand" — Input: vague query about this issue. Output: expanded search query
8. "answer" — Input: "Question: ...\\nMemories: [1] ... [2] ...". Output: cited answer, no markdown

Treat these as organizational memories — like meeting notes or team discussions.
Generate {count} examples (mix of all tasks). Output ONLY valid JSONL.

DISCUSSIONS:
{discussions}"""


def format_issue(issue: dict) -> str:
    """Format a GitHub issue into readable text."""
    parts = [
        f"[{issue['repo']}] {issue['title']}",
        f"Opened by @{issue['user']} on {issue['created_at'][:10]}",
    ]
    if issue["labels"]:
        parts.append(f"Labels: {', '.join(issue['labels'])}")
    if issue["body"]:
        parts.append(f"\n{issue['body'][:800]}")

    for c in issue["comments"][:5]:
        parts.append(f"\n@{c['user']} ({c['created_at'][:10]}): {c['body'][:400]}")

    return "\n".join(parts)


def process_batch(client: OpenAI, issues_batch: list[dict], count: int) -> list[dict]:
    """Convert a batch of issues into training examples."""
    discussions_text = "\n\n---\n\n".join(
        format_issue(issue) for issue in issues_batch
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        timeout=90,
        messages=[
            {
                "role": "system",
                "content": "You convert team discussions into AI training data. Output ONLY valid JSONL.",
            },
            {
                "role": "user",
                "content": PROCESS_PROMPT.format(discussions=discussions_text, count=count),
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


def process_github(target_count: int, repos: list[str]):
    """Fetch and process GitHub issues into training data."""
    client = OpenAI()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  RABBIT — GitHub Issues Processor")
    print(f"  Repos: {len(repos)}")
    print(f"  Target: {target_count} examples")
    print(f"{'='*60}")

    # Fetch issues from all repos
    all_issues = []
    issues_per_repo = max(50, target_count // (len(repos) * 15))

    for repo in repos:
        print(f"\n  Fetching from {repo}...")
        issues = fetch_issues(repo, per_page=30, pages=(issues_per_repo // 30) + 1)
        print(f"    Got {len(issues)} issues with discussions")
        all_issues.extend(issues)

    random.shuffle(all_issues)
    print(f"\n  Total issues fetched: {len(all_issues)}")

    # Process into training examples
    output_files = {task: OUTPUT_DIR / f"{task}_synthetic.jsonl" for task in TASKS}
    generated = 0
    batch_size = 3  # issues per API call

    for i in range(0, len(all_issues), batch_size):
        if generated >= target_count:
            break

        batch = all_issues[i:i + batch_size]

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

    print(f"\n  Done! Generated {generated} examples from GitHub issues.")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Process GitHub issues into training data"
    )
    parser.add_argument("--count", type=int, default=15000)
    parser.add_argument("--repos", type=str, default=None,
                        help="Comma-separated repo list (default: built-in popular repos)")

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    repos = args.repos.split(",") if args.repos else DEFAULT_REPOS
    process_github(args.count, repos)


if __name__ == "__main__":
    main()
