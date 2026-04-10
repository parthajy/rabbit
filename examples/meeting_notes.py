"""
Upload meeting recordings/notes and get instant memory.

Decisions, action items, and context — all extracted and linked.
"""

from rabbit import Rabbit

rab = Rabbit("rab_test_YOUR_KEY_HERE")

# Option 1: Upload an audio recording (requires faster-whisper)
# memories = rab.remember_file("standup_2026-04-10.mp3", source="meeting")
# print(f"Transcribed and stored {len(memories)} chunks")

# Option 2: Paste meeting notes as text
meeting_notes = """
Weekly Standup — April 10, 2026

Attendees: Sarah, Tom, Priya, Raj

Updates:
- Sarah: Q2 launch pushed to April 20. Waiting on legal review of the partner agreement.
  Risk: if legal takes more than a week, we miss the window.
- Tom: Auth module security audit complete. Found 2 medium-severity issues.
  Action: patches ready by Monday.
- Priya: Customer onboarding flow redesign is 80% done. Needs Tom's API changes.
  Blocker: waiting on Tom's auth patches.
- Raj: Data pipeline migration to new cluster complete. 40% faster queries.

Decisions:
- Approved $15K additional budget for penetration testing.
- Agreed to do weekly security reviews until launch.

Next meeting: April 17, 2026
"""

memory = rab.remember(meeting_notes, source="meeting", metadata={"title": "Weekly Standup"})
print(f"Stored as: {memory.id}")
print(f"Type: {memory.triage_type}")
print(f"People: {memory.extraction.get('people', [])}")
print(f"Decisions: {memory.extraction.get('decisions', [])}")
print(f"Action items: {memory.extraction.get('action_items', [])}")

# Ask about it later
answer = rab.ask("What are the blockers for the Q2 launch?")
print(f"\n{answer.text}")
