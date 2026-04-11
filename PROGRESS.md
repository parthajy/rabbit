# Rabbit Build Progress

> Tracking what's built, what's live, what's next.

**Last updated:** April 10, 2026

---

## Current Status: Sprint 1 Complete

The Rabbit platform layer is built. The model weights (v1.4) are already on HuggingFace. Everything below wraps those weights into a product.

---

## What Exists

### Model (on HuggingFace — no changes needed)
- [x] Rabbit v1.4 merged model: `reattend/rabbit-v1.4-merged` (4-bit quantized, ~2.2GB)
- [x] 82,314 training examples across 12 signals
- [x] Trained on RunPod A100, 10 hours, 3 epochs
- [x] Base: Phi-3.5 Mini Instruct (3.8B) + LoRA (r=16, alpha=16)

### Platform (built April 10, 2026)

| Module | File | Status | What It Does |
|--------|------|--------|-------------|
| **Core Types** | `rabbit/core/types.py` | Tested | Memory, Answer, Alert, Extraction, HealthReport |
| **Signals** | `rabbit/core/signals.py` | Tested | 12 signal definitions (prompts, prefixes, settings) |
| **LLM** | `rabbit/core/llm.py` | Tested (no GPU) | Model loading, inference, output cleaning |
| **Engine** | `rabbit/core/engine.py` | Tested (no GPU) | RabbitCore: remember(), ask(), check(), compile(), lint() |
| **Processors** | `rabbit/processors/router.py` | Tested | 10 input types: text, audio, PDF, DOCX, images, markdown, HTML, email, calendar, code |
| **Storage** | `rabbit/storage/memory_store.py` | Tested | Qdrant vectors + SQLite FTS5 + memory graph |
| **Auth** | `rabbit/api/auth.py` | Tested | rab_test_*/rab_live_* key gen, validation, rate limits |
| **API Server** | `rabbit/api/server.py` | Built (needs FastAPI) | 12 endpoints: /v1/remember, /v1/ask, /v1/check, etc. |
| **SDK** | `rabbit/sdk/client.py` | Tested | Rabbit (API client) + RabbitLocal (direct model) |
| **CLI** | `rabbit/cli.py` | Tested | 9 commands: remember, ask, check, memories, stats, lint, compile, config, sync |
| **Packaging** | `pyproject.toml` | Built | pip install rabbit-memory (with extras) |
| **README** | `README.md` | Written | Public-facing launch page |
| **Roadmap** | `ROADMAP.md` | Written | Full 6-sprint plan |
| **Examples** | `examples/` | Written | basic.py, meeting_notes.py, obsidian_sync.py |

### Tests Passed (April 10, 2026)

```
[PASS] Core types — Memory, Answer, Alert, Extraction
[PASS] Signals — 12 signals configured
[PASS] LLM — parse, clean, lazy init
[PASS] Processors — text, markdown, chunking, email, code
[PASS] Storage — SQLite + FTS5 + graph + BM25
[PASS] Auth — key gen, validate, reject invalid, rate limits
[PASS] SDK — Rabbit client, RabbitLocal, data classes
[PASS] CLI — 9 commands
```

### GPU Server Tests (April 11, 2026) — PASSED

```
[PASS] LLM inference — model.generate works on T4
[PASS] /v1/remember — full ingestion pipeline (triage, extract, summarize, sentiment, importance, embed, store, link)
[PASS] /v1/ask — full query pipeline (intent, expand, retrieve, graph walk, answer)
[PASS] Qdrant vector search — stores and retrieves embeddings
[PASS] Memory linking — LINK signal connects related memories automatically
[PASS] BM25 search — SQLite FTS5 keyword matching
[PASS] Hybrid retrieval — vector + BM25 combined
[PASS] API auth — rab_test_* key generation and validation
[PASS] FastAPI server — all endpoints responding
```

### Known Model Issues (to fix in v1.5 training — see V1.5_TRAINING.md)
- Summary bleed: model adds `[DETAILED EXPLANATION]` / `[INSTRUCTION]` after good summary
- Triage type returns "TRIAGE" instead of actual type (meeting, report, etc.)
- Organization hallucination: invents org names not in source text ("Recode")
- Answer date hallucination: invents dates for citations
- Tags include signal prefix ("TRIAGE" as a tag)

---

## Infrastructure — DEPLOYED

### Live Server (April 11, 2026)
- **Instance:** rabbit-platform
- **GPU:** NVIDIA T4 (16GB VRAM)
- **Machine:** n1-standard-4 (4 vCPU, 15GB RAM)
- **Region:** asia-south1-a (Mumbai)
- **IP:** 35.200.167.8:8000
- **Cost:** ~$142/month (spot)
- **OS:** Ubuntu 22.04 LTS, 50GB SSD
- **Service:** systemd (`rabbit.service`), auto-restart
- **Runs:** `rabbit/api/server.py` — full platform with auth, multi-tenancy

### First API Key
- `rab_test_09F05-B9FxJ__JhQW2DHZP12` (test tier, 100 calls/day)

### Old Server (to be killed)
- IP: 34.47.236.12:8000
- Running old `server/app.py` (v1.4, bare signals, no platform)
- **Kill after DNS switch**

---

## Deployment — COMPLETE (April 11, 2026)

```
HuggingFace
└── reattend/rabbit-v1.4-merged    ← model weights

GCP T4 Server (35.200.167.8, static IP)
└── rabbit/api/server.py           ← full platform
    ├── Auth (rab_test_*/rab_live_*)
    ├── 15 endpoints
    ├── Qdrant (vectors, per-tenant)
    ├── SQLite (FTS5 + graph, per-tenant)
    └── FastEmbed (embeddings)

DNS: api.rabbit.reattend.com → 35.200.167.8
```

### Deployment Steps — ALL DONE
- [x] Create GCP T4 instance (Mumbai, 15GB RAM, spot) — $142/month
- [x] Install NVIDIA drivers + CUDA
- [x] Clone repo, install `pip install -e ".[server]"`
- [x] Start server, generate first API key
- [x] Test remember + ask end-to-end from laptop
- [x] Reserve static IP (35.200.167.8)
- [x] Set DNS: api.rabbit.reattend.com
- [x] Set up systemd auto-restart
- [x] Kill old server (34.47.236.12)
- [x] Verify SDK works with default URL (zero config)

---

## Sprint Progress

### Sprint 1 — Rabbit Core Engine ✅ COMPLETE (April 10)
- [x] Repo restructured: `rabbit/core/`, `rabbit/processors/`, `rabbit/storage/`
- [x] 10 input processors built (text, audio, PDF, DOCX, images, markdown, HTML, email, calendar, code)
- [x] SQLite FTS5 + memory graph
- [x] Qdrant vector search
- [x] Hybrid retrieval (vector + BM25 + graph walk + importance + recency)
- [x] Ingestion pipeline (triage → extract → summarize → sentiment → importance → embed → store → link)
- [x] Query pipeline (intent → expand → retrieve → graph walk → answer)
- [x] RabbitCore class with all methods
- [x] API gateway (15 endpoints)
- [x] Auth (rab_test_*/rab_live_*)
- [x] Python SDK
- [x] CLI (9 commands)
- [x] Deployed to GCP, tested end-to-end

### Sprint 2 — Complete the Platform 🔄 IN PROGRESS

**Input processor deps (install on server + test):**
- [ ] PDF (PyPDF2)
- [ ] Office docs (python-docx or Docling)
- [ ] Images/OCR (tesseract + pytesseract)
- [ ] HTML/Web (trafilatura)
- [ ] Calendar (icalendar)

**Post-processing fixes:**
- [ ] Summary bleed: clip at `[DETAILED` or `[INSTRUCTION`
- [ ] Triage type: strip signal prefix from type and tags

**Advanced retrieval:**
- [ ] Jina Reranker integration (137M, ~500MB VRAM)

**Streaming + SDKs:**
- [ ] SSE streaming for /v1/ask
- [ ] JS/TS SDK (npm install @reattend/rabbit)

**Deferred:**
- [ ] ColPali (3B, 3GB VRAM) — deferred to L4 upgrade, OCR covers 80% of image cases

### Sprint 3 — Ecosystem

- [ ] Webhooks (memory.created, contradiction.detected)
- [ ] Connectors (Gmail, Slack, Calendar, Obsidian, Git)
- [ ] COMPILE signal (auto-wiki on ingest) — needs v1.5 training data
- [ ] LINT signal (deep audit) — needs v1.5 training data
- [ ] Publish to PyPI (pip install rabbit-memory)
- [ ] Publish to npm (@reattend/rabbit)
- [ ] Push GitHub repo public (reattend/rabbit)

### Sprint 4 — rabbit.reattend.com + Reattend SaaS (parallel with Sprint 3)

- [ ] Landing page at rabbit.reattend.com
- [ ] API key signup (email → rab_test key, no credit card)
- [ ] Docs site: API reference, guides, Obsidian guide
- [ ] Stripe for rab_live upgrade
- [ ] Rebuild Reattend as a Rabbit SDK client
- [ ] Reattend dashboard: memory timeline, search, knowledge graph
- [ ] Connectors in Reattend (Gmail, Calendar, Slack)

### Sprint 5 — Teams + Enterprise

- [ ] Team workspaces (shared memory namespace)
- [ ] Meeting upload (audio → Whisper → pipeline)
- [ ] Self-healing wiki (COMPILE on ingest, LINT weekly)
- [ ] Knowledge graph visualization
- [ ] Docker Compose for on-prem
- [ ] First enterprise pilot

---

## File Count

```
Platform code:    10 Python files (rabbit/)
Examples:          3 Python files (examples/)
Docs:              6 Markdown files (README, ROADMAP, PROGRESS, MASTER, V1.5_TRAINING, PITCH_DECK)
Config:            1 TOML file (pyproject.toml)
Training scripts: 17 Python files (scripts/) — existing
Training data:    82,314 examples (data/) — existing
Model weights:     On HuggingFace — existing
```
