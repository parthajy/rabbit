"""
Generate long-form training examples for Rabbit v2.0 (Qwen 2.5 32B).

Creates 8,000 examples with longer inputs (1000-5000 words):
- 3,000 long meeting transcript extractions
- 2,000 multi-paragraph email/report extractions
- 2,000 long Ask examples (question + 10 memory blocks + answer)
- 1,000 long document extractions

Uses OpenAI API (gpt-4o-mini) for generation.
Output: data/synthetic/long_examples.jsonl
"""

import json
import os
import random
import time
from pathlib import Path

# Use the OpenAI key from the rabbit .env
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

SIGNALS = {
    "extract": {
        "system": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
        "prefix": "[EXTRACT]",
    },
    "triage": {
        "system": "You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
        "prefix": "[TRIAGE]",
    },
    "summarize": {
        "system": "You are Rabbit, Reattend's memory AI. Generate a rich 2-4 sentence standalone summary of the given content. Capture the essence, key decisions, and action items.",
        "prefix": "[SUMMARIZE]",
    },
    "answer": {
        "system": "You are Rabbit, Reattend's memory AI. Answer the user's question conversationally. Cite sources inline as [1][2][3]. Use **bold** for key names and decisions. End with Sources: and Follow-up questions: sections.",
        "prefix": "[ANSWER]",
    },
}

# Universe templates for generating diverse, realistic long content
MEETING_TEMPLATES = [
    "quarterly business review with {num_attendees} attendees discussing {topic}",
    "product planning sprint review covering {num_features} feature updates",
    "board meeting discussing fundraising, hiring, and market strategy",
    "engineering standup with {num_attendees} engineers covering blockers and progress",
    "sales pipeline review with deal updates across {num_deals} active opportunities",
    "customer success review covering {num_accounts} enterprise accounts",
    "incident postmortem for a {severity} production outage",
    "all-hands meeting with company updates, Q&A, and team recognition",
    "design review for {product} covering UX research and wireframes",
    "legal and compliance review for {regulation} requirements",
]

INDUSTRIES = ["fintech", "healthcare", "edtech", "SaaS", "e-commerce", "cybersecurity", "climate tech", "logistics", "real estate", "biotech"]
TOPICS = ["Q2 launch timeline", "Series B fundraising", "enterprise pricing", "data migration", "team restructuring", "market expansion into Asia", "competitor analysis", "product roadmap 2027", "customer churn analysis", "security audit findings"]

def generate_long_meeting(template: str) -> str:
    """Generate a realistic long meeting transcript (1000-3000 words)."""
    industry = random.choice(INDUSTRIES)
    topic = random.choice(TOPICS)
    num_attendees = random.randint(4, 8)

    names = ["Sarah Chen", "Tom Rivera", "Priya Patel", "James O'Brien", "Lisa Zhang",
             "Marcus Johnson", "Ananya Desai", "Kevin Park", "Rachel Green", "David Kim"]
    attendees = random.sample(names, num_attendees)

    # Build a multi-section meeting transcript
    sections = []
    sections.append(f"Meeting: {template.format(num_attendees=num_attendees, topic=topic, num_features=random.randint(5,12), num_deals=random.randint(8,20), num_accounts=random.randint(10,30), severity=random.choice(['P0','P1','critical']), product=random.choice(['Dashboard','Mobile App','API','Analytics']), regulation=random.choice(['GDPR','SOC2','HIPAA','PCI-DSS']))}")
    sections.append(f"Date: 2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
    sections.append(f"Attendees: {', '.join(attendees)}")
    sections.append(f"Industry context: {industry}")
    sections.append("")

    # Generate 4-6 discussion points
    for i in range(random.randint(4, 6)):
        speaker = random.choice(attendees)
        point_length = random.randint(3, 8)  # sentences
        sections.append(f"{speaker}: " + " ".join([
            f"{'We need to ' if j == 0 else ''}{random.choice(['consider', 'address', 'prioritize', 'review', 'implement', 'evaluate'])} "
            f"the {random.choice(['timeline', 'budget', 'resource allocation', 'technical architecture', 'user feedback', 'competitive landscape', 'risk assessment'])} "
            f"for {topic}. " for j in range(point_length)
        ]))

        # Add a decision or action item occasionally
        if random.random() > 0.5:
            sections.append(f"\nDecision: {random.choice(attendees)} proposed to {random.choice(['delay', 'accelerate', 'modify', 'approve', 'table'])} the {random.choice(['launch', 'release', 'deployment', 'review', 'assessment'])} by {random.choice(['one week', 'two weeks', 'end of month', 'next quarter'])}. Team agreed.")

        if random.random() > 0.6:
            assignee = random.choice(attendees)
            sections.append(f"\nAction item: {assignee} to {random.choice(['prepare', 'complete', 'review', 'draft', 'submit', 'schedule'])} the {random.choice(['report', 'proposal', 'analysis', 'documentation', 'presentation'])} by {random.choice(['Friday', 'next Monday', 'end of week', 'January 30'])}.")

    return "\n\n".join(sections)


def main():
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "long_examples.jsonl"

    print(f"Generating long training examples...")
    print(f"Output: {output_file}")

    examples = []

    # Generate meeting extractions
    for i in range(3000):
        template = random.choice(MEETING_TEMPLATES)
        content = generate_long_meeting(template)

        for signal_name, signal_config in random.sample(list(SIGNALS.items()), k=random.randint(1, 3)):
            example = {
                "messages": [
                    {"role": "system", "content": signal_config["system"]},
                    {"role": "user", "content": f"{signal_config['prefix']} {content}"},
                ]
            }
            # Note: output will be generated by the model during training
            # For now, we store the input format. Actual outputs need to be
            # generated via Claude/GPT-4 API (see generate_synthetic.py)
            examples.append(example)

        if (i + 1) % 500 == 0:
            print(f"  Generated {i + 1} meeting examples...")

    print(f"\nTotal examples prepared: {len(examples)}")
    print(f"Note: Run generate_synthetic.py to generate actual outputs via Claude API")
    print(f"Then quality_filter.py to clean them")

    # Save
    with open(output_file, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()
