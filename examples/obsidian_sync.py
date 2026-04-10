"""
Sync an Obsidian vault into Rabbit memory.

Your notes become searchable, linked, and queryable.
"""

from pathlib import Path
from rabbit import Rabbit

rab = Rabbit("rab_test_YOUR_KEY_HERE")

vault_path = Path("~/Documents/MyVault").expanduser()

# Ingest all markdown files
for md_file in vault_path.glob("**/*.md"):
    text = md_file.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) < 20:
        continue

    memory = rab.remember(
        text,
        source="obsidian",
        metadata={"filename": md_file.name, "path": str(md_file.relative_to(vault_path))},
    )
    print(f"  {md_file.name} -> {memory.summary[:60]}...")

# Now query across all your notes
answer = rab.ask("What are the key themes across my notes?")
print(f"\n{answer.text}")

# Compile a wiki page for a topic
wiki = rab.compile("project ideas")
print(f"\n--- Wiki: Project Ideas ---\n{wiki}")
