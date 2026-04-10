"""
Basic Rabbit usage — 10 lines to build a memory system.
"""

from rabbit import Rabbit

rab = Rabbit("rab_test_YOUR_KEY_HERE")

# Remember things from different sources
rab.remember("Sarah decided to delay the launch to March 15. Budget is $50K.", source="meeting")
rab.remember("Q1 revenue hit $2.3M, 15% above target.", source="report")
rab.remember("Tom flagged security concerns about the auth module.", source="slack")

# Ask anything
answer = rab.ask("What's the launch timeline and are there any blockers?")
print(answer.text)
print(f"\nSources: {answer.sources}")
print(f"Follow-ups: {answer.followups}")

# Check for contradictions
alert = rab.check("Planning to launch on March 1st")
if alert.show:
    print(f"\nALERT: {alert.context}")
