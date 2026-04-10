# Rabbit

**Memory infrastructure for the world.**

Rabbit is a fine-tuned AI that remembers everything for you. Feed it meetings, emails, notes, documents, recordings — it extracts decisions, detects contradictions, links context, and answers questions across your entire history.

Two API calls. That's it.

```python
from rabbit import Rabbit

rab = Rabbit("rab_test_YOUR_KEY")

rab.remember("Sarah delayed the launch to March 15. Budget is $50K.", source="meeting")
rab.remember("Q1 revenue hit $2.3M, above target.", source="report")
rab.remember("Tom flagged auth security concerns.", source="slack")

answer = rab.ask("What's the launch status and are there blockers?")
print(answer.text)
# "The launch has been delayed to March 15 by Sarah [1]. Meanwhile, Tom has
#  raised security concerns about the auth module [3] which could be a blocker..."
```

---

## Install

```bash
pip install rabbit-memory
```

## Get an API Key

```bash
# Free — 1K calls/month, instant, no credit card
curl -X POST https://rabbit.reattend.com/v1/keys/generate?tier=test
```

Keys look like:
- `rab_test_*` — free tier, for testing
- `rab_live_*` — production tier, persistent storage

---

## What Can It Do?

### Remember anything

```python
# Text
rab.remember("Meeting notes: we decided to postpone launch...", source="meeting")

# Files — audio, PDF, DOCX, images, code, email, calendar
rab.remember_file("quarterly_review.pdf")
rab.remember_file("standup_recording.mp3")    # auto-transcribed
rab.remember_file("whiteboard.jpg")           # OCR extracted

# Rabbit automatically:
# - Classifies content type (meeting, decision, task, update...)
# - Extracts people, organizations, decisions, action items, dates
# - Generates a rich summary
# - Detects sentiment and importance (1-5)
# - Creates vector embeddings for search
# - Links to related memories in your knowledge graph
```

### Ask anything

```python
answer = rab.ask("What did we decide about the Q2 budget?")

print(answer.text)        # Conversational answer with [1][2] citations
print(answer.sources)     # Which memories were used
print(answer.followups)   # Suggested follow-up questions
```

### Detect contradictions

```python
alert = rab.check("Let's launch on March 1st")
# alert.show = True
# alert.reason = "contradiction"
# alert.context = "Sarah decided to delay to March 15 in the Q2 planning meeting"
```

### Self-healing knowledge base

```python
# Auto-compile wiki pages from memories
wiki = rab.compile("Sarah")       # Everything known about Sarah
wiki = rab.compile("Q2 Launch")   # All context about the launch

# Audit memory health
report = rab.lint()
# report.contradictions = [...]   Conflicting information
# report.stale_items = [...]      Old action items, outdated decisions
# report.health_score = 0.87      Overall health (0-1)
```

---

## Three Ways to Run

```python
# 1. Hosted API (easiest)
rab = Rabbit("rab_test_abc123")

# 2. Self-hosted API (your server)
rab = Rabbit("rab_live_xyz", base_url="https://rabbit.yourcompany.com")

# 3. Fully local (no internet, model runs on your machine)
rab = Rabbit.local(model_path="reattend/rabbit-v1.4-merged")
```

All three expose the exact same interface. Build with `rab_test`, ship with `rab_live`, go on-prem with `Rabbit.local()` — zero code changes.

---

## CLI

```bash
pip install rabbit-memory
rabbit config set key rab_test_YOUR_KEY

# Remember
rabbit remember "Sarah decided to delay the launch to March 15."
rabbit remember --file recording.mp3
rabbit remember --file report.pdf

# Ask
rabbit ask "When is the launch?"

# Check for contradictions
rabbit check "Let's launch on March 1st"

# Sync an Obsidian vault
rabbit sync --obsidian ~/Documents/MyVault

# Sync any folder
rabbit sync --dir ~/meeting-notes/

# Health
rabbit lint
rabbit stats
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/remember` | POST | Ingest text into memory |
| `/v1/remember/file` | POST | Ingest a file (audio, PDF, image, etc.) |
| `/v1/ask` | POST | Ask a question over memories |
| `/v1/check` | POST | Detect contradictions |
| `/v1/memories` | GET | List stored memories |
| `/v1/memories/:id` | GET | Get a specific memory |
| `/v1/memories/:id` | DELETE | Forget a memory |
| `/v1/graph/:id` | GET | Get memory connections |
| `/v1/compile/:entity` | POST | Compile wiki page |
| `/v1/lint` | POST | Run health audit |
| `/v1/stats` | GET | Usage statistics |
| `/v1/keys/generate` | POST | Generate API key |

---

## What Rabbit Does Under the Hood

When you call `rab.remember()`, Rabbit runs 7 AI signals on your content:

| Signal | What It Does | Output |
|--------|-------------|--------|
| TRIAGE | Classifies content type | meeting, decision, task, idea... |
| EXTRACT | Pulls structured facts | people, decisions, action items, dates |
| SUMMARIZE | Rich standalone summary | 2-4 sentences |
| SENTIMENT | Tone detection | positive, negative, tense, urgent |
| IMPORTANCE | Scores 1-5 with reason | "High — contains budget decision" |
| EMBED | Vector embedding | 768-dim vector for search |
| LINK | Finds related memories | same_topic, contradicts, depends_on... |

When you call `rab.ask()`, Rabbit runs a retrieval pipeline:

1. **Intent** — Classifies your question type
2. **Expand** — Turns vague queries into precise search
3. **Hybrid Search** — Vector similarity + keyword matching
4. **Graph Walk** — Follows links to find connected context
5. **Rerank** — Picks the most relevant memories
6. **Answer** — Generates conversational response with citations

---

## Supported File Types

| Type | Extensions | How |
|------|-----------|-----|
| Audio | .mp3, .wav, .m4a, .ogg, .flac | Whisper transcription |
| PDF | .pdf | Docling / PyPDF2 |
| Office | .docx, .pptx, .xlsx | Docling |
| Images | .png, .jpg, .webp | OCR (pytesseract) |
| Markdown | .md | Native (Obsidian-compatible) |
| HTML | .html | trafilatura |
| Email | .eml | Built-in parser |
| Calendar | .ics | icalendar |
| Code | .py, .js, .ts, .go, .rs... | With language context |

Install processors as needed:
```bash
pip install rabbit-memory[audio]      # Whisper
pip install rabbit-memory[pdf]        # Docling
pip install rabbit-memory[all]        # Everything
```

---

## Self-Hosting

```bash
# Docker (coming soon)
docker compose up -d

# Or manually
pip install rabbit-memory[server]
RABBIT_MODEL=reattend/rabbit-v1.4-merged uvicorn rabbit.api.server:app --host 0.0.0.0 --port 8000
```

---

## Use Cases

- **Personal knowledge base** — Remember everything, find anything
- **Team memory** — Shared context across your organization
- **Meeting intelligence** — Upload recordings, get decisions and action items
- **Obsidian supercharger** — Query across your entire vault
- **Git memory** — Remember commits, PRs, issues across repos
- **Self-healing wiki** — Knowledge base that updates itself
- **CRM enrichment** — Remember every customer interaction
- **Enterprise on-prem** — Knowledge graph behind your firewall

---

## Built With

- **Phi-3.5 Mini (3.8B)** — Fine-tuned with 82K+ memory-specific examples
- **FastEmbed** — nomic-embed-text-v1.5 for embeddings
- **Qdrant** — Vector search with per-tenant isolation
- **SQLite FTS5** — BM25 keyword search
- **faster-whisper** — Audio transcription
- **Docling** — Document parsing (PDF, DOCX, PPTX)

---

## Reattend

Rabbit powers [Reattend](https://reattend.com) — the memory SaaS for individuals and teams. Connect Gmail, Slack, Calendar, and more. Get a dashboard, daily digests, and a self-healing knowledge base.

Rabbit is the infrastructure. Reattend is the product. You can build your own product on Rabbit.

---

## License

MIT

---

Built by [Reattend](https://reattend.com). Memory for the world.
