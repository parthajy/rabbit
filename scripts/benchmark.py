"""
Rabbit v1.2 Benchmark — Rabbit vs Groq vs OpenAI
Sends identical inputs to all 3 providers, shows results side by side.

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --signal intent    # Test one signal only
    python scripts/benchmark.py --quick            # 10 tests instead of 50
"""

import argparse
import json
import os
import time

from dotenv import load_dotenv
load_dotenv()
# Also load Reattend's env for Groq key
load_dotenv("/Users/partha/Desktop/Reattend/reattend.com/.env.local")
load_dotenv("/Users/partha/Desktop/Reattend/reattend.com/.env")

import requests
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────

RABBIT_URL = "http://34.93.210.241:8000/v1/chat/completions"
RABBIT_KEY = "rabbit_reattend_2026_secret_key"

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# System prompts matching Reattend's current usage
SYSTEM_PROMPTS = {
    "intent": "Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract": "Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand": "Expand the user's vague query into a precise, comprehensive search query.",
    "answer": "Answer the user's question using the provided memory context. Be conversational, cite sources as [1][2][3]. Include follow-up questions.",
    "summarize": "Generate a rich 2-4 sentence standalone summary. Capture the essence, key decisions, and action items.",
    "sentiment": "Classify the tone. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance": 'Score the importance for organizational memory. Return JSON: {"score": 1-5, "reason": "..."}.',
    "link": 'Given a source record and candidates, determine which are related. Return JSON with links array.',
    "ambient": 'Decide whether to alert the user about contradictions or forgotten commitments. Return JSON.',
}

# ── Test Cases ──────────────────────────────────────────────────────────────

TEST_CASES = [
    # INTENT (5 tests)
    {"signal": "intent", "input": "What did we discuss with Brian last week?", "expected": "history"},
    {"signal": "intent", "input": "Who is responsible for the API integration?", "expected": "entity"},
    {"signal": "intent", "input": "Summarize all decisions from March", "expected": "synthesis"},
    {"signal": "intent", "input": "What are the open action items?", "expected": "actions"},
    {"signal": "intent", "input": "When is the next board meeting?", "expected": "temporal"},

    # EXTRACT (5 tests)
    {"signal": "extract", "input": "Met with Sarah from Acme on Tuesday. She agreed to send the contract by Friday. Budget confirmed at $45,000."},
    {"signal": "extract", "input": "Slack from Ravi: The deployment is blocked because Priya hasn't merged the auth PR. Need it by Thursday or we miss the sprint."},
    {"signal": "extract", "input": "Email from Deepa (Finance): Q2 revenue is $2.1M ARR. Board presentation scheduled for April 15. Need deck from Vikram by April 10."},
    {"signal": "extract", "input": "Standup notes: Jake fixed the login bug. Maria started the dashboard redesign. Arun is blocked on the API docs from the partner team."},
    {"signal": "extract", "input": "Meeting with Sequoia: Tom expressed interest in leading our Series A. Wants to see $3M ARR before committing. Follow-up call scheduled May 1."},

    # TRIAGE (5 tests)
    {"signal": "triage", "input": "Quick sync with dev team. Jake will fix the auth bug by EOD. Maria is starting the dashboard redesign next sprint."},
    {"signal": "triage", "input": "Hey team, just a heads up - the office will be closed on Friday for Diwali. Happy holidays everyone!"},
    {"signal": "triage", "input": "DECISION: After reviewing three vendors, we're going with Stripe for payments. Razorpay was close but Stripe's API documentation is better."},
    {"signal": "triage", "input": "From: noreply@calendar.google.com. Subject: Reminder: Team standup in 15 minutes."},
    {"signal": "triage", "input": "Investor update Q1 2026: Revenue grew 40% QoQ to $1.8M ARR. Churn decreased to 3.2%. Hired 5 new engineers. Runway: 14 months."},

    # EXPAND (5 tests)
    {"signal": "expand", "input": "what about brian"},
    {"signal": "expand", "input": "pricing stuff"},
    {"signal": "expand", "input": "that meeting with acme"},
    {"signal": "expand", "input": "deployment issue"},
    {"signal": "expand", "input": "sarah contract"},

    # SENTIMENT (5 tests)
    {"signal": "sentiment", "input": "This is frustrating. We discussed this three times and nothing has changed.", "expected": "negative"},
    {"signal": "sentiment", "input": "Great news! The pilot went really well and the client wants to expand.", "expected": "positive"},
    {"signal": "sentiment", "input": "The weekly metrics report is attached. Revenue: $180K. Churn: 3.1%.", "expected": "neutral"},
    {"signal": "sentiment", "input": "We need to ship this by Friday or we lose the client. No excuses.", "expected": "urgent"},
    {"signal": "sentiment", "input": "I disagree with the approach. The timeline is unrealistic and the team is already stretched thin.", "expected": "tense"},

    # IMPORTANCE (5 tests)
    {"signal": "importance", "input": "Team standup: CSS fix deployed. Lunch order changed to Thai. Jenkins build is green."},
    {"signal": "importance", "input": "Emergency: production database is down. All users affected. Revenue impact estimated at $50k per hour."},
    {"signal": "importance", "input": "Board decided to pivot from B2C to B2B. Complete strategy overhaul starting next quarter."},
    {"signal": "importance", "input": "Reminder: Submit your timesheets by end of day Friday."},
    {"signal": "importance", "input": "Client Acme renewed their contract for 2 years at $200K ARR. Biggest deal this quarter."},

    # SUMMARIZE (5 tests)
    {"signal": "summarize", "input": "Board meeting recap: Revenue hit $2.1M ARR. Decided to raise Series A in Q3. Tom from Sequoia expressed interest. Need to prep deck by end of month. Marketing budget increased by 30%. New VP of Engineering starts May 1. Product roadmap for H2 approved."},
    {"signal": "summarize", "input": "Sprint retro: What went well — shipped the payment integration 2 days early, client feedback positive. What didn't — QA found 12 bugs post-merge, deployment pipeline broke twice. Action items — add pre-merge test suite, rotate on-call schedule."},
    {"signal": "summarize", "input": "Email thread between Sales and Product: Client wants a custom dashboard for their enterprise plan. Product says it's 3 weeks of work. Sales says the deal is worth $500K ARR. CEO approved fast-tracking it. Design review scheduled for Monday."},
    {"signal": "summarize", "input": "Slack thread in #general: Office AC is broken again. Facilities team says repair scheduled for tomorrow. Multiple complaints about temperature. Remote work approved for anyone affected."},
    {"signal": "summarize", "input": "Interview debrief for candidate Ankit: Strong system design skills, 8 years experience. Concerns about cultural fit — seemed dismissive of testing. Panel split 3-2 in favor. HR to extend offer with 6-month review clause."},

    # ANSWER (5 tests)
    {"signal": "answer", "input": "Question: What happened with the pricing decision?\nMemories: [1] Meeting Mar 15 - team decided on freemium with generous limits. Vikram pushed for it strongly. [2] Email Mar 20 - Finance (Deepa) flagged infrastructure costs as unsustainable at current growth rate. [3] Meeting Mar 22 - heated discussion. Vikram defended freemium, Deepa presented cost projections showing 40% over budget. [4] Slack Mar 25 - CEO asked team to explore usage-based alternatives. [5] Meeting Mar 28 - team reversed decision, moving to usage-based pricing. Vikram reluctantly agreed after seeing unit economics."},
    {"signal": "answer", "input": "Question: What should we focus on next quarter?\nMemories: [1] Board meeting - revenue hit 2.1M ARR but growth slowed from 50% to 30% QoQ. [2] Client feedback survey - 78% want better mobile experience. [3] Team retro - engineering velocity dropped 20% due to tech debt. [4] Investor call - Series A investors want to see $3M ARR and 15% MoM growth. [5] Competitor analysis - Rival launched enterprise tier, stealing 3 of our prospects."},
    {"signal": "answer", "input": "Question: Tell me about the Acme deal.\nMemories: [1] Meeting Mar 15 - initial discussion with Tom from Acme about renewal at $45K. [2] Email Mar 20 - Tom confirmed budget approved internally. [3] Meeting Mar 25 - Legal flagged a liability clause in the contract. [4] Slack Mar 28 - Tom requested revised terms addressing the clause. [5] Meeting Apr 1 - Agreed on modified terms, signing scheduled for next week."},
    {"signal": "answer", "input": "Question: How is the engineering team doing?\nMemories: [1] Sprint retro - velocity dropped 20% this sprint, blamed on context switching. [2] 1-on-1 with Jake - he's frustrated with unclear priorities, considering other offers. [3] Standup notes - 3 out of 5 PRs blocked by code review backlog. [4] Team survey - satisfaction score dropped from 8.2 to 6.9. [5] Manager meeting - Priya proposed dedicated focus time blocks, no meetings before noon."},
    {"signal": "answer", "input": "Question: What do we know about competitor activity?\nMemories: [1] Sales call notes - Prospect mentioned they're also evaluating Glean and Notion AI. [2] Industry report - Glean raised $200M, expanding into mid-market. [3] Customer feedback - Two churned customers said they switched to competitor with better Slack integration. [4] Team discussion - Our Slack integration is basic compared to competitors. [5] Product roadmap - Slack deep integration planned for Q3 but not started."},

    # LINK (3 tests)
    {"signal": "link", "input": "SOURCE RECORD:\nTitle: Pricing decision reversed\nSummary: Team reversed freemium decision, moving to usage-based pricing.\n\nCANDIDATES:\n1. [id-1] Freemium launch plan: Team discussed generous free tier limits and growth projections.\n2. [id-2] Q2 hiring plan: Engineering needs 3 more backend devs.\n3. [id-3] Cost analysis from Finance: Monthly costs 40% over budget with freemium.\n4. [id-4] Customer feedback survey: Enterprise clients prefer predictable pricing.\n5. [id-5] Sprint planning: Next sprint focused on payment integration."},
    {"signal": "link", "input": "SOURCE RECORD:\nTitle: Jake considering leaving\nSummary: Jake mentioned in 1-on-1 that he's frustrated with unclear priorities and considering other offers.\n\nCANDIDATES:\n1. [id-1] Sprint retro: Velocity dropped 20% due to context switching.\n2. [id-2] New office lease: Signed 2-year lease for larger office.\n3. [id-3] Team survey: Satisfaction score dropped from 8.2 to 6.9.\n4. [id-4] Jake's code review: Excellent work on the auth refactor.\n5. [id-5] Holiday calendar: Office closed for Diwali.\n6. [id-6] Priya's proposal: Dedicated focus time, no meetings before noon."},
    {"signal": "link", "input": "SOURCE RECORD:\nTitle: Acme contract signed\nSummary: Acme renewed for 2 years at $200K ARR after resolving liability clause.\n\nCANDIDATES:\n1. [id-1] Acme initial meeting: Discussed renewal at $45K.\n2. [id-2] Monthly revenue report: March revenue was $180K.\n3. [id-3] Legal review: Flagged liability clause in Acme contract.\n4. [id-4] Tom's email: Budget approved at Acme's end.\n5. [id-5] Sales pipeline: 5 deals in negotiation stage.\n6. [id-6] Acme revised terms: Modified contract addressing liability concerns."},

    # AMBIENT (2 tests)
    {"signal": "ambient", "input": "SCREEN TEXT (from Gmail):\nHi Tom, confirming our meeting for October 15th to discuss the renewal at $45,000.\n\nRELATED MEMORIES:\n1. [meeting] Client call with Tom: Discussed renewal timeline, agreed on September 30th deadline.\n2. [email] Tom's email: Budget approved at $42,000 not $45,000.\n3. [note] Account notes: Tom prefers quarterly billing."},
    {"signal": "ambient", "input": "SCREEN TEXT (from Slack):\nJust pushed the payment feature to production. All tests passing.\n\nRELATED MEMORIES:\n1. [meeting] Sprint planning: Payment feature scheduled for next sprint, not this one.\n2. [standup] Jake mentioned payment feature needs security review before deploy.\n3. [note] General notes: Friday deployments discouraged per team policy."},
]


# ── Providers ───────────────────────────────────────────────────────────────


def call_rabbit(signal, user_input):
    """Call Rabbit API."""
    prefix_map = {
        "intent": "[INTENT]", "extract": "[EXTRACT]", "triage": "[TRIAGE]",
        "expand": "[EXPAND]", "answer": "[ANSWER]", "summarize": "[SUMMARIZE]",
        "sentiment": "[SENTIMENT]", "importance": "[IMPORTANCE]",
        "link": "[LINK]", "ambient": "[AMBIENT]",
    }
    prefix = prefix_map.get(signal, "[ANSWER]")

    try:
        start = time.time()
        resp = requests.post(
            RABBIT_URL,
            headers={"Authorization": f"Bearer {RABBIT_KEY}", "Content-Type": "application/json"},
            json={"messages": [{"role": "user", "content": f"{prefix} {user_input}"}]},
            timeout=120,
        )
        latency = int((time.time() - start) * 1000)
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content, latency
    except Exception as e:
        return f"ERROR: {e}", 0


def call_groq(signal, user_input):
    """Call Groq API."""
    try:
        client = OpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1")
        start = time.time()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS.get(signal, "")},
                {"role": "user", "content": user_input},
            ],
            max_tokens=512,
            temperature=0.1,
        )
        latency = int((time.time() - start) * 1000)
        return resp.choices[0].message.content, latency
    except Exception as e:
        return f"ERROR: {e}", 0


def call_openai(signal, user_input):
    """Call OpenAI API."""
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        start = time.time()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS.get(signal, "")},
                {"role": "user", "content": user_input},
            ],
            max_tokens=512,
            temperature=0.1,
        )
        latency = int((time.time() - start) * 1000)
        return resp.choices[0].message.content, latency
    except Exception as e:
        return f"ERROR: {e}", 0


# ── Run Benchmark ───────────────────────────────────────────────────────────


def run_benchmark(signal_filter=None, quick=False):
    tests = TEST_CASES
    if signal_filter:
        tests = [t for t in tests if t["signal"] == signal_filter]
    if quick:
        # Take first 2 per signal
        seen = {}
        filtered = []
        for t in tests:
            count = seen.get(t["signal"], 0)
            if count < 2:
                filtered.append(t)
                seen[t["signal"]] = count + 1
        tests = filtered

    print(f"\n{'='*70}")
    print(f"  RABBIT BENCHMARK — {len(tests)} tests")
    print(f"  Rabbit v1.2  vs  Groq (llama-3.3-70b)  vs  OpenAI (gpt-4o-mini)")
    print(f"{'='*70}")

    results = []
    scores = {"rabbit": 0, "groq": 0, "openai": 0, "tie": 0}

    for i, test in enumerate(tests):
        signal = test["signal"]
        inp = test["input"]
        expected = test.get("expected", None)

        print(f"\n{'─'*70}")
        print(f"  Test {i+1}/{len(tests)} | Signal: {signal.upper()}")
        print(f"  Input: {inp[:100]}{'...' if len(inp) > 100 else ''}")
        if expected:
            print(f"  Expected: {expected}")
        print(f"{'─'*70}")

        # Call all 3
        r_out, r_ms = call_rabbit(signal, inp)
        g_out, g_ms = call_groq(signal, inp)
        o_out, o_ms = call_openai(signal, inp)

        print(f"\n  RABBIT ({r_ms}ms):")
        print(f"    {r_out[:300]}{'...' if len(r_out) > 300 else ''}")
        print(f"\n  GROQ ({g_ms}ms):")
        print(f"    {g_out[:300]}{'...' if len(g_out) > 300 else ''}")
        print(f"\n  OPENAI ({o_ms}ms):")
        print(f"    {o_out[:300]}{'...' if len(o_out) > 300 else ''}")

        # Auto-score for simple signals
        if expected and signal in ("intent", "sentiment"):
            r_correct = expected.lower() in r_out.lower()
            g_correct = expected.lower() in g_out.lower()
            o_correct = expected.lower() in o_out.lower()
            print(f"\n  AUTO-SCORE: Rabbit={'✓' if r_correct else '✗'}  Groq={'✓' if g_correct else '✗'}  OpenAI={'✓' if o_correct else '✗'}")
            if r_correct and not g_correct and not o_correct:
                scores["rabbit"] += 1
            elif g_correct and not r_correct:
                scores["groq"] += 1
            elif o_correct and not r_correct:
                scores["openai"] += 1
            else:
                scores["tie"] += 1
            results.append({"signal": signal, "auto": True, "rabbit": r_correct, "groq": g_correct, "openai": o_correct})
        else:
            # Manual scoring needed
            print(f"\n  SCORE (1=Rabbit best, 2=Groq best, 3=OpenAI best, 0=Tie): ", end="")
            try:
                score = input().strip()
                if score == "1":
                    scores["rabbit"] += 1
                elif score == "2":
                    scores["groq"] += 1
                elif score == "3":
                    scores["openai"] += 1
                else:
                    scores["tie"] += 1
                results.append({"signal": signal, "auto": False, "score": score})
            except (EOFError, KeyboardInterrupt):
                scores["tie"] += 1
                results.append({"signal": signal, "auto": False, "score": "skip"})

    # Summary
    total = len(tests)
    print(f"\n{'='*70}")
    print(f"  BENCHMARK RESULTS")
    print(f"{'='*70}")
    print(f"  Rabbit wins: {scores['rabbit']}/{total} ({scores['rabbit']/total*100:.0f}%)")
    print(f"  Groq wins:   {scores['groq']}/{total} ({scores['groq']/total*100:.0f}%)")
    print(f"  OpenAI wins: {scores['openai']}/{total} ({scores['openai']/total*100:.0f}%)")
    print(f"  Ties:        {scores['tie']}/{total} ({scores['tie']/total*100:.0f}%)")
    print(f"{'='*70}")

    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump({"scores": scores, "total": total, "results": results}, f, indent=2)
    print(f"\n  Results saved to benchmark_results.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal", help="Test one signal only")
    parser.add_argument("--quick", action="store_true", help="Run quick (2 per signal)")
    args = parser.parse_args()

    if not GROQ_KEY:
        print("Warning: GROQ_API_KEY not set. Groq tests will fail.")
    if not OPENAI_KEY:
        print("Warning: OPENAI_API_KEY not set. OpenAI tests will fail.")

    run_benchmark(signal_filter=args.signal, quick=args.quick)
