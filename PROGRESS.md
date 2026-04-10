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

### Not Yet Tested (needs GPU server)
- [ ] LLM inference (model.generate)
- [ ] Full remember() pipeline end-to-end
- [ ] Full ask() pipeline end-to-end
- [ ] FastAPI server running
- [ ] File upload (audio, PDF, image)
- [ ] Qdrant vector search
- [ ] Hybrid retrieval (vector + BM25 + graph)

---

## Infrastructure Plan

### Old Server (to be killed)
- Google Cloud T4 (16GB VRAM), Mumbai
- IP: 34.47.236.12:8000
- Running old `server/app.py` (v1.4, bare signals, no platform)

### New Server (to be created)
- **GPU:** L4 (24GB VRAM) — room for Whisper + Reranker alongside Rabbit
- **RAM:** 32GB
- **Region:** Mumbai (ap-south1) for low latency to India
- **Cost:** ~$200-250/month on spot
- **Runs:** `rabbit/api/server.py` — the full platform with auth, multi-tenancy, all endpoints
- **Domain:** rabbit.reattend.com → new server IP

### Why L4 over T4
| | T4 (old) | L4 (new) |
|--|---------|---------|
| VRAM | 16GB | 24GB |
| Rabbit model | ~5GB | ~5GB |
| Whisper (base) | — | ~1.5GB |
| Jina Reranker | — | ~500MB |
| FastEmbed | ~500MB | ~500MB |
| Headroom | 10GB (tight) | 16GB (comfortable) |
| Concurrent requests | crashes | handles it |

---

## What Deploys Where

```
HuggingFace (already there)
└── reattend/rabbit-v1.4-merged    ← model weights, pulled at server startup

New GCP L4 Server
└── rabbit/api/server.py           ← the full platform
    ├── Auth (rab_test_*/rab_live_*)
    ├── /v1/remember, /v1/ask, /v1/check (+ 9 more endpoints)
    ├── Qdrant (local file storage, per-tenant)
    ├── SQLite (FTS5 + memory graph, per-tenant)
    └── FastEmbed (embeddings, local)

GitHub (public repo)
└── reattend/rabbit
    ├── rabbit/          ← Python package (pip install rabbit-memory)
    ├── examples/
    ├── README.md
    └── pyproject.toml

PyPI (later)
└── rabbit-memory       ← pip install rabbit-memory
```

---

## Deployment Steps (Next Session)

1. [ ] Create new GCP L4 instance (Mumbai, 32GB RAM, spot)
2. [ ] Install: Python 3.11, CUDA, pip dependencies
3. [ ] Clone repo, install: `pip install -e ".[server]"`
4. [ ] Set env vars: `HF_TOKEN`, `RABBIT_MODEL`, `RABBIT_STORAGE`
5. [ ] Start server: `uvicorn rabbit.api.server:app --host 0.0.0.0 --port 8000`
6. [ ] Generate first API key: `POST /v1/keys/generate?tier=test`
7. [ ] Test remember + ask end-to-end
8. [ ] Point rabbit.reattend.com DNS to new IP
9. [ ] Kill old T4 instance
10. [ ] Push to GitHub as public repo

---

## Sprint Progress

### Sprint 1 — Rabbit Core Engine (Week 1-2) ✅ COMPLETE
- [x] Restructure repo: `rabbit/core/`, `rabbit/processors/`, `rabbit/storage/`
- [x] Input processors: text, audio (faster-whisper), PDF (Docling), DOCX, images, markdown, HTML, email, calendar, code
- [x] SQLite storage with FTS5 full-text search
- [x] Memory graph (SQLite edges table)
- [x] Hybrid retrieval: vector + BM25 + graph walk + importance/recency boost
- [x] Unified ingestion pipeline: input → triage → extract → summarize → sentiment → importance → embed → store → link
- [x] Unified query pipeline: question → intent → expand → retrieve → rerank → graph walk → answer
- [x] `RabbitCore` class: `ingest()`, `ingest_file()`, `ask()`, `check()`, `compile()`, `lint()`
- [x] API gateway with rab_test_*/rab_live_* auth
- [x] Python SDK: `from rabbit import Rabbit`
- [x] CLI tool: `rabbit remember`, `rabbit ask`, etc.
- [x] Package config: pyproject.toml
- [x] README + examples
- [ ] 50 end-to-end test cases (need GPU)
- [ ] Qdrant integration test (need qdrant-client)
- [ ] Deploy to server

### Sprint 2 — Rabbit API + SDK (Week 3-4) 🔜
- [x] FastAPI gateway (built, needs deployment)
- [x] Auth system (built, tested)
- [x] Python SDK (built, tested)
- [ ] JS/TS SDK
- [ ] SSE streaming for answers
- [ ] Deploy to rabbit.reattend.com

### Sprint 3 — GitHub Launch (Week 5-6) 🔜
### Sprint 4 — Reattend SaaS v2 (Week 7-8) 🔜
### Sprint 5 — Teams + Polish (Week 9-10) 🔜
### Sprint 6 — Enterprise (Week 11-14) 🔜

---

## File Count

```
Platform code:    10 Python files (rabbit/)
Examples:          3 Python files (examples/)
Docs:              3 Markdown files (README, ROADMAP, PROGRESS)
Config:            1 TOML file (pyproject.toml)
Training scripts: 17 Python files (scripts/) — existing, unchanged
Training data:    82,314 examples (data/) — existing, unchanged
Model weights:     On HuggingFace — existing, unchanged
```
