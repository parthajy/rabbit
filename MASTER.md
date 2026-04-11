# Rabbit — Master Document

> Memory infrastructure for the world. Built by Reattend.
> Single source of truth. Updated April 11, 2026.

---

## Current State

### What's Live

| Component | Status | Location |
|---|---|---|
| Rabbit v1.4 (12 signals) | **LIVE** | GCP Mumbai, api.rabbit.reattend.com:8000 |
| Rabbit Platform (API + SDK + CLI) | **LIVE** | 15 endpoints, rab_test/rab_live auth |
| FastEmbed (embeddings) | **LIVE** | Bundled (nomic-embed-text-v1.5) |
| Qdrant (vector search) | **LIVE** | Local file storage, per-tenant |
| SQLite FTS5 (keyword search) | **LIVE** | BM25 + memory graph |
| Model weights | **Safe** | HuggingFace (reattend/rabbit-v1.4-merged) |
| Training data + scripts | **Safe** | GitHub (parthajy/rabbit, private) |

### Infrastructure

| | Details |
|---|---|
| Server | GCP n1-standard-4 + T4 GPU (16GB VRAM), spot |
| IP | 35.200.167.8 (static) |
| DNS | api.rabbit.reattend.com |
| Cost | ~$142/month |
| OS | Ubuntu 22.04, systemd auto-restart |
| Storage | /opt/rabbit-data (Qdrant + SQLite per tenant) |

### API Key

```
rab_test_09F05-B9FxJ__JhQW2DHZP12  (test tier, 100 calls/day)
```

---

## Architecture

```
Layer 3:  REATTEND (SaaS)              reattend.com
          Dashboard, integrations, teams.
          Built ENTIRELY on the Rabbit SDK.

Layer 2:  RABBIT API (Platform)        api.rabbit.reattend.com:8000
          /v1/remember, /v1/ask, /v1/check
          Auth, multi-tenancy, rate limits, SDKs.

Layer 1:  RABBIT CORE (Engine)         The model + processors + storage
          Fine-tuned LLM (12 signals) + Whisper + Qdrant + FastEmbed
          + Memory Graph + Hybrid Search
          This is what ships on-prem.
```

---

## The 12 Signals

| # | Signal | What It Does | When | Latency |
|---|---|---|---|---|
| 1 | INTENT | Classify query type | Query | 240ms |
| 2 | EXTRACT | Pull people, orgs, dates, decisions, action items, topics | Ingest | 300-500ms |
| 3 | TRIAGE | Classify content type + summary + tags | Ingest | 300-500ms |
| 4 | EXPAND | Turn vague queries into precise search | Query | 400ms |
| 5 | ANSWER | Conversational Q&A with citations, sources, follow-ups | Response | 3-25s |
| 6 | SUMMARIZE | Rich 2-4 sentence standalone summary | Ingest | 400ms |
| 7 | SENTIMENT | Tone classification | Ingest | 240ms |
| 8 | IMPORTANCE | Score 1-5 with reason | Ingest | 300ms |
| 9 | MULTITURN | Follow-up conversation | Response | same as ANSWER |
| 10 | DONTKNOW | Graceful "I don't know" | Response | same as ANSWER |
| 11 | LINK | Memory relationship detection (7 types) | Ingest | 500ms |
| 12 | AMBIENT | Contradiction/forgotten commitment detection | Real-time | 400ms |

---

## Training History

| Version | Date | Data | Signals | Status |
|---|---|---|---|---|
| v1.0 | Apr 3 | 55,750 | 8 | Archived on HF |
| v1.1 | Apr 5 | 53,901 | 10 | Archived on HF |
| v1.2 | Apr 6 | 61,178 | 12 | Archived on HF |
| v1.4 | Apr 9 | 82,314 | 12 | **LIVE** |
| v1.5 | Planned | ~100,000 | 12 | 18K targeted fixes (see V1.5_TRAINING.md) |

---

## What We Sell

| # | Product | Customer | Deployment |
|---|---------|----------|------------|
| 1 | **Rabbit API** | Developers | Our servers (api.rabbit.reattend.com) |
| 2 | **Reattend SaaS** | Individuals & teams | Our servers (reattend.com) |
| 3 | **Rabbit On-Prem** | Enterprises | Their servers (Docker) |
| 4 | **Reattend + Rabbit Bundle** | Enterprises | Their servers (Docker) |
| 5 | **Managed Rabbit** | Enterprises | Our servers, their isolated instance |

---

## API Endpoints (15 total)

### Core
| Method | Endpoint | What It Does |
|--------|----------|-------------|
| POST | `/v1/remember` | Ingest text → full pipeline → memory stored |
| POST | `/v1/remember/file` | Ingest file (audio, PDF, image, doc) |
| POST | `/v1/ask` | Ask a question → retrieval + answer |
| POST | `/v1/check` | Detect contradictions |

### Memory Management
| Method | Endpoint | What It Does |
|--------|----------|-------------|
| GET | `/v1/memories` | List stored memories |
| GET | `/v1/memories/:id` | Get a specific memory |
| DELETE | `/v1/memories/:id` | Forget a memory |
| GET | `/v1/graph/:id` | Get memory connections |

### Knowledge Base
| Method | Endpoint | What It Does |
|--------|----------|-------------|
| POST | `/v1/compile/:entity` | Compile wiki page |
| POST | `/v1/lint` | Health audit |
| GET | `/v1/stats` | Usage statistics |
| POST | `/v1/keys/generate` | Generate API key |

### Legacy Compatibility
| Method | Endpoint | What It Does |
|--------|----------|-------------|
| POST | `/v1/chat/completions` | OpenAI-compatible signal routing |
| POST | `/v1/embeddings` | Generate embeddings |
| GET | `/health` | Health check |

---

## Input Processors

| Type | Extensions | Dependency | Status on Server |
|------|-----------|-----------|-----------------|
| Text | raw string | None | **Working** |
| Markdown | .md, .mdx | None | **Working** |
| Email | .eml | stdlib | **Working** |
| Code | .py, .js, .ts, .go, .rs, etc. | None | **Working** |
| Audio | .mp3, .wav, .m4a, .ogg | faster-whisper | **Installed** |
| PDF | .pdf | PyPDF2 or Docling | **Needs install** |
| Office | .docx, .pptx, .xlsx | Docling | **Needs install** |
| Images | .png, .jpg, .webp | pytesseract | **Needs install** |
| HTML | .html | trafilatura (fallback: regex) | **Partial** |
| Calendar | .ics | icalendar | **Needs install** |

---

## Retrieval Pipeline

1. **Vector search** — semantic similarity via FastEmbed + Qdrant
2. **BM25 search** — keyword matching via SQLite FTS5
3. **Graph walk** — follow LINK edges 1-2 hops from results
4. **Importance weighting** — high-importance memories score higher
5. **Recency weighting** — recent memories score higher
6. **Reranking** — Jina Reranker (planned, not yet integrated)

---

## Sprint Plan (Updated April 11, 2026)

### Sprint 2: Complete the Platform (Current)

**Input Processors — install deps + test:**
- [ ] PDF (PyPDF2)
- [ ] Office docs (Docling or python-docx)
- [ ] Images/OCR (tesseract + pytesseract)
- [ ] HTML/Web (trafilatura)
- [ ] Calendar (icalendar)

**Post-processing fixes:**
- [ ] Summary bleed: clip at `[DETAILED` or `[INSTRUCTION`
- [ ] Triage type: strip signal prefix from type and tags

**Advanced retrieval:**
- [ ] Jina Reranker integration (137M, ~500MB)

**Streaming + SDKs:**
- [ ] SSE streaming for /v1/ask
- [ ] JS/TS SDK (npm install @reattend/rabbit)

**Deferred to L4 upgrade:**
- [ ] ColPali (3B, 3GB VRAM — too tight on T4 with other models)

### Sprint 3: Ecosystem

- [ ] Webhooks (memory.created, contradiction.detected events)
- [ ] Connectors (Gmail, Slack, Calendar, Obsidian, Git)
- [ ] COMPILE signal (auto-wiki on ingest) — needs training data
- [ ] LINT signal (deep contradiction audit) — needs training data
- [ ] Publish to PyPI (pip install rabbit-memory)
- [ ] Publish to npm (@reattend/rabbit)
- [ ] Push GitHub repo public (reattend/rabbit)

### Sprint 4: rabbit.reattend.com + Reattend SaaS (parallel)

- [ ] Landing page at rabbit.reattend.com
- [ ] API key signup (email → rab_test key)
- [ ] Docs: API reference, guides, Obsidian guide, code examples
- [ ] Stripe integration for rab_live upgrade
- [ ] Rebuild Reattend as a Rabbit SDK client
- [ ] Reattend dashboard: memory timeline, search, graph viz
- [ ] Gmail, Calendar, Slack connectors in Reattend

### Sprint 5: Teams + Enterprise

- [ ] Team workspaces (shared memory namespace)
- [ ] Meeting upload (audio → Whisper → pipeline)
- [ ] Self-healing wiki (COMPILE on ingest, LINT weekly)
- [ ] Knowledge graph visualization
- [ ] Feedback loop (thumbs up/down → training data)
- [ ] Docker Compose for on-prem

---

## Known v1.4 Quality Issues (see V1.5_TRAINING.md)

| Issue | Workaround | Fix |
|-------|-----------|-----|
| Summary bleed | TODO: post-processing clip | v1.5 retrain |
| Sentiment explanation | Clips to first word (deployed) | v1.5 retrain |
| Triage type = "TRIAGE" | TODO: post-processing strip | v1.5 retrain |
| Org hallucination ("Recode") | None | v1.5 retrain |
| Tags include signal prefix | TODO: post-processing strip | v1.5 retrain |
| Answer date hallucination | None | v1.5 retrain |
| Retrieval bias (importance) | None | v1.5 retrain + retrieval tuning |

---

## Financial Summary

### Costs

| Item | Monthly |
|---|---|
| GCP (T4 Spot, Mumbai) | $142 |
| Reattend hosting (DO) | $20 |
| Monthly retrain (RunPod) | $2 |
| Misc (domains) | $10 |
| **Total** | **~$175** |

### Revenue Targets

| Month | Revenue | Source |
|---|---|---|
| 1 | $0 | Building + launching |
| 2 | $500 | 1-2 API developers |
| 3 | $2,000 | 5 API + first SaaS users |
| 4 | $5,000 | 10 API + SaaS Pro tier |
| 6 | $15,000 | 20 API + 1 enterprise pilot |
| 12 | $50,000 | 50 API + 3 enterprise |

---

## Competitive Landscape

| | Rabbit | Glean | Notion AI | Cohere |
|---|---|---|---|---|
| Owns the model | **YES** | No | No | Yes |
| Auto-captures memories | **YES** | Partial | No | No |
| Memory graph | **YES** | No | No | No |
| On-prem | **YES** | No | No | Yes |
| Offline capable | **YES** | No | No | N/A |
| Memory-specialized (12 signals) | **YES** | No | No | No |
| Self-healing KB | **YES** | No | No | No |
| Data flywheel | **YES** | No | No | Partial |

---

## The Vision

> Every AI system in the world has amnesia. We built Rabbit — a proprietary AI that doesn't just store memories. It extracts decisions, detects contradictions, links context, and reasons over your team's entire history. 12 signals, one model, one server. It runs on-premise. Nothing leaves your firewall. And it gets smarter with every interaction.

---

*Last updated: April 11, 2026*
*Rabbit v1.4 live at api.rabbit.reattend.com:8000*
*Sprint 2: Complete platform (processors, reranker, streaming, JS SDK)*
