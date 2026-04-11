"""
Generate 10K realistic full-length organizational content for Rabbit v2.0.

- 3K full meeting transcripts (2000-5000 words, multiple speakers)
- 3K email threads (3-8 emails in a thread)
- 2K Slack conversations (10-30 messages)
- 2K documents/reports (1000-3000 words)

Each example includes the raw content + full extraction.
Run on RunPod CPU pod: bash scripts/runpod_generate.sh 3

Output: data/synthetic/v2_realistic_*.jsonl
"""

from __future__ import annotations
import json
import os
import sys
import random
import time
import argparse
from typing import Optional
from pathlib import Path

API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

UNIVERSES = [
    {"company": "Meridian Health", "industry": "healthcare", "people": ["Dr. Ananya Rao", "James Chen", "Maria Santos", "David Park", "Lisa Okonkwo", "Dr. Raj Kapoor", "Sarah Mitchell", "Tom Nguyen"], "projects": ["Patient Portal 2.0", "HIPAA Audit", "Telemedicine Expansion"]},
    {"company": "Axion Finance", "industry": "fintech", "people": ["Priya Sharma", "Marcus Johnson", "Elena Volkov", "Kevin O'Brien", "Zara Ahmed", "Chris Wu", "Rachel Green", "Nathan Cole"], "projects": ["Basel III Implementation", "Mobile Banking v3", "KYC Automation"]},
    {"company": "NovaTech Solutions", "industry": "enterprise SaaS", "people": ["Karan Mehta", "Sophie Anderson", "Diego Ramirez", "Fatima Al-Hassan", "Ben Thompson", "Yuki Tanaka", "Alex Rivera", "Nina Petrova"], "projects": ["Platform v4 Migration", "Enterprise SSO", "Analytics Dashboard"]},
    {"company": "GreenPath Energy", "industry": "clean energy", "people": ["Arjun Reddy", "Clara Johansson", "Michael Obi", "Sana Khan", "Patrick Dubois", "Mei Lin", "Jack Morrison", "Amara Diallo"], "projects": ["Solar Grid Optimization", "Carbon Credit Platform", "Battery Storage Pilot"]},
    {"company": "LexShield Legal", "industry": "legal tech", "people": ["Amanda Chen", "Robert Fitzgerald", "Deepa Nair", "Carlos Mendez", "Emily Watson", "Omar Hassan", "Victoria Lee", "Thomas Blake"], "projects": ["Contract AI Review", "Case Management v2", "Compliance Tracker"]},
]


def call_api(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    import urllib.request
    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.85,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(API_URL, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  API error: {e}")
        return ""


def generate_meeting_transcript(universe: dict) -> Optional[dict]:
    """Full multi-speaker meeting transcript, 2000-4000 words."""
    num_speakers = random.randint(4, 7)
    speakers = random.sample(universe["people"], num_speakers)
    project = random.choice(universe["projects"])
    month = random.randint(1, 12)
    day = random.randint(1, 28)

    prompt = f"""Write a FULL realistic meeting transcript for {universe['company']} ({universe['industry']}).

Meeting: {random.choice(['Weekly standup', 'Sprint review', 'Quarterly planning', 'Product review', 'Board update', 'Post-mortem', 'Strategy session', 'Client review', 'Budget review', 'Hiring committee'])}
Date: 2026-{month:02d}-{day:02d}
Speakers: {', '.join(speakers)}
Topic: {project}

REQUIREMENTS:
- 2000-3500 words minimum
- Each speaker talks 3-5 times
- Include specific numbers (revenue, budget, metrics, dates)
- Include at least 4 decisions made
- Include at least 5 action items assigned to specific people with deadlines
- Include disagreements or pushback
- Include references to previous meetings or decisions
- Format as speaker labels followed by their dialogue
- Make it feel like a real meeting, not a script

Write the FULL transcript. Do not summarize or abbreviate."""

    content = call_api("You write extremely realistic, detailed corporate meeting transcripts.", prompt, max_tokens=4096)
    if not content or len(content) < 1500:
        return None

    # Generate extraction
    extract_prompt = f"""Extract ALL structured information from this meeting transcript. Return ONLY valid JSON.

{content[:6000]}

Return JSON:
{{"people": ["full names"], "organizations": ["companies/teams"], "decisions": ["exact decisions quoted"], "action_items": [{{"owner": "name", "task": "specific task", "due": "deadline"}}], "dates": ["all dates"], "topics": ["key topics"]}}

Be exhaustive. Extract EVERY person, decision, action item, and date."""

    output = call_api("Return only valid JSON. Be exhaustive in extraction.", extract_prompt, max_tokens=2000)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    except:
        return None

    return {
        "input": f"[EXTRACT] {content}",
        "output": json.dumps(parsed),
    }


def generate_email_thread(universe: dict) -> Optional[dict]:
    """Full email thread with 3-6 emails."""
    num_emails = random.randint(3, 6)
    participants = random.sample(universe["people"], random.randint(2, 4))
    project = random.choice(universe["projects"])

    prompt = f"""Write a FULL email thread with {num_emails} emails for {universe['company']}.

Participants: {', '.join(participants)}
Subject: {random.choice(['Re: ', 'Fwd: ', ''])}Update on {project}
Context: {universe['industry']}

REQUIREMENTS:
- {num_emails} separate emails in chronological order
- Include From, To, Date, Subject headers for each
- Each email is 100-300 words
- Thread should evolve (question -> response -> follow-up -> decision)
- Include specific numbers, dates, and action items
- At least one email should express disagreement or concern

Write the FULL thread."""

    content = call_api("You write realistic corporate email threads.", prompt, max_tokens=3000)
    if not content or len(content) < 500:
        return None

    extract_prompt = f"""Extract ALL structured information from this email thread. Return ONLY valid JSON.

{content[:5000]}

Return JSON:
{{"people": ["names"], "organizations": ["orgs"], "decisions": ["decisions"], "action_items": [{{"owner": "name", "task": "task", "due": "deadline"}}], "dates": ["dates"], "topics": ["topics"]}}"""

    output = call_api("Return only valid JSON.", extract_prompt, max_tokens=1500)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    except:
        return None

    return {
        "input": f"[EXTRACT] {content}",
        "output": json.dumps(parsed),
    }


def generate_slack_conversation(universe: dict) -> Optional[dict]:
    """Slack channel conversation, 15-25 messages."""
    num_messages = random.randint(15, 25)
    participants = random.sample(universe["people"], random.randint(3, 5))
    project = random.choice(universe["projects"])
    channel = random.choice(["#general", "#engineering", "#product", "#sales", f"#{project.lower().replace(' ', '-')}"])

    prompt = f"""Write a realistic Slack conversation in {channel} at {universe['company']}.

Participants: {', '.join(participants)}
Topic: {project}
Messages: {num_messages}

REQUIREMENTS:
- Casual tone, like real Slack
- Include timestamps
- Include reactions/emoji occasionally
- Mix of short messages and longer ones
- Include at least 2 decisions reached
- Include at least 3 action items
- Include links, @mentions, and thread references
- Some messages should be quick responses ("agreed", "makes sense", "+1")

Format: [timestamp] **Speaker**: message"""

    content = call_api("You write realistic Slack conversations.", prompt, max_tokens=3000)
    if not content or len(content) < 400:
        return None

    extract_prompt = f"""Extract ALL structured information from this Slack conversation. Return ONLY valid JSON.

{content[:5000]}

Return JSON:
{{"people": ["names"], "organizations": ["orgs/teams"], "decisions": ["decisions made"], "action_items": [{{"owner": "name", "task": "task", "due": "when"}}], "dates": ["dates"], "topics": ["topics"]}}"""

    output = call_api("Return only valid JSON.", extract_prompt, max_tokens=1500)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    except:
        return None

    return {
        "input": f"[EXTRACT] {content}",
        "output": json.dumps(parsed),
    }


def generate_document(universe: dict) -> Optional[dict]:
    """Full document/report, 1000-2500 words."""
    doc_type = random.choice(["quarterly report", "project proposal", "incident postmortem", "strategy document", "performance review summary", "budget proposal", "technical architecture doc"])
    project = random.choice(universe["projects"])

    prompt = f"""Write a FULL {doc_type} for {universe['company']} ({universe['industry']}).

About: {project}
Author: {random.choice(universe['people'])}

REQUIREMENTS:
- 1000-2500 words
- Professional tone
- Include specific metrics and numbers
- Include dates and deadlines
- Reference multiple team members by name
- Include recommendations or next steps
- Include section headers

Write the FULL document."""

    content = call_api("You write realistic corporate documents.", prompt, max_tokens=3500)
    if not content or len(content) < 800:
        return None

    extract_prompt = f"""Extract ALL structured information from this document. Return ONLY valid JSON.

{content[:5000]}

Return JSON:
{{"people": ["names"], "organizations": ["orgs"], "decisions": ["decisions/recommendations"], "action_items": [{{"owner": "name", "task": "task", "due": "deadline"}}], "dates": ["dates"], "topics": ["topics"]}}"""

    output = call_api("Return only valid JSON.", extract_prompt, max_tokens=1500)
    if not output:
        return None

    try:
        parsed = json.loads(output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    except:
        return None

    return {
        "input": f"[EXTRACT] {content}",
        "output": json.dumps(parsed),
    }


GENERATORS = {
    "meeting": (generate_meeting_transcript, 3000),
    "email": (generate_email_thread, 3000),
    "slack": (generate_slack_conversation, 2000),
    "document": (generate_document, 2000),
}


def main():
    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY")
        sys.exit(1)

    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    for task_name, (generator, target) in GENERATORS.items():
        output_file = output_dir / f"v2_realistic_{task_name}.jsonl"
        existing = sum(1 for _ in open(output_file)) if output_file.exists() else 0
        remaining = target - existing

        if remaining <= 0:
            print(f"{task_name}: Already done ({existing})")
            continue

        print(f"\n{task_name}: generating {remaining} (have {existing})")
        success = 0
        failures = 0

        with open(output_file, "a") as f:
            for i in range(remaining):
                universe = random.choice(UNIVERSES)
                example = generator(universe)

                if example:
                    f.write(json.dumps(example) + "\n")
                    success += 1
                else:
                    failures += 1

                if (i + 1) % 25 == 0:
                    print(f"  {task_name}: {success}/{i+1} ({failures} failed)")
                    f.flush()

                time.sleep(0.5)  # Rate limit

        print(f"  {task_name}: DONE - {success} generated")

    print("\nAll realistic content generated!")
    print("Files:")
    for f in output_dir.glob("v2_realistic_*.jsonl"):
        count = sum(1 for _ in open(f))
        print(f"  {f.name}: {count} examples")


if __name__ == "__main__":
    main()
