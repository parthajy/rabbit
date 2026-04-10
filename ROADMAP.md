# Rabbit Roadmap

> Rabbit is the memory infrastructure for the world. Reattend is the product built on it.

**Last updated:** April 10, 2026

---

## The Architecture

```
Layer 3:  REATTEND (SaaS)              reattend.com
          Dashboard, integrations, teams.
          Built ENTIRELY on the Rabbit SDK.

Layer 2:  RABBIT API (Platform)        rabbit.reattend.com → rabbit.so
          /v1/remember, /v1/ask, /v1/check
          Auth, multi-tenancy, rate limits, SDKs.

Layer 1:  RABBIT CORE (Engine)         The model + processors + storage
          Fine-tuned LLM (12 signals) + Whisper + Docling + ColPali
          + Qdrant + Memory Graph + FastEmbed + Reranker
          This is what ships on-prem.
```

Reattend never calls the model directly. It calls the Rabbit SDK. The Rabbit SDK calls Rabbit Core. This makes every deployment mode possible with zero code changes.

---

## What We Sell

| # | Product | Customer | Deployment |
|---|---------|----------|------------|
| 1 | **Rabbit API** | Developers | Our servers (rabbit.reattend.com) |
| 2 | **Reattend SaaS** | Individuals & teams | Our servers (reattend.com) |
| 3 | **Rabbit On-Prem** | Enterprises | Their servers (Docker) |
| 4 | **Reattend + Rabbit Bundle** | Enterprises | Their servers (Docker) |
| 5 | **Managed Rabbit** | Enterprises | Our servers, their isolated instance |

---

## API Key Scheme

```
rab_test_<24chars>   →  Free. 1K calls/month. Data wiped after 7 days.
rab_live_<24chars>   →  Paid. Persistent. SLA. Production-ready.
```

---

## The Developer Experience

```python
from rabbit import Rabbit

rab = Rabbit("rab_test_abc123")

# Remember anything — text, file, audio, PDF, image
rab.remember("Sarah delayed the launch to March 15. Budget is $50K.", source="meeting")
rab.remember_file("quarterly_review.pdf")
rab.remember_file("standup_recording.mp3")

# Ask anything
answer = rab.ask("When is the launch and what's the budget?")
print(answer.text)       # Conversational answer with citations
print(answer.sources)    # Which memories were used
print(answer.followups)  # Suggested follow-up questions

# Detect contradictions in real-time
alert = rab.check("Let's launch on March 1st")
# → Contradiction: Sarah decided to delay to March 15

# Self-healing knowledge base
wiki = rab.compile("Project Phoenix")   # Auto-generated wiki page
health = rab.lint()                      # Contradictions, gaps, stale info
```

Three modes, same interface:
```python
rab = Rabbit("rab_test_xxx")                                    # Hosted API
rab = Rabbit("rab_live_xxx", base_url="https://your-server")    # Self-hosted API
rab = Rabbit.local(model_path="reattend/rabbit-v1.4")           # Fully local
```

---

## Rabbit Core Components

### The Model (what we built)

Fine-tuned Phi-3.5 Mini (3.8B) with 82K+ training examples across 12 signals:

| Signal | Purpose | Latency |
|--------|---------|---------|
| INTENT | Classify query type | 240ms |
| EXTRACT | Pull people, decisions, dates, actions (JSON) | 300-500ms |
| TRIAGE | Classify content type + summary + tags | 300-500ms |
| EXPAND | Turn vague query into precise search | 400ms |
| ANSWER | Conversational Q&A with citations | 3-5s (vLLM) |
| SUMMARIZE | Rich 2-4 sentence summary | 400ms |
| SENTIMENT | Tone classification | 240ms |
| IMPORTANCE | Score 1-5 with reason | 300ms |
| MULTITURN | Follow-up conversation handling | same as ANSWER |
| DONTKNOW | Graceful "I don't know" responses | same as ANSWER |
| LINK | Memory relationship detection (7 types) | 500ms |
| AMBIENT | Real-time contradiction detection | 400ms |

Planned signals: COMPILE (auto-wiki), LINT (audit), COMPILE_ANSWER (answer→memory)

### Input Processors (what we're adding)

| Input | Tool | Size | License |
|-------|------|------|---------|
| Text | Built-in | 0 | — |
| Audio | faster-whisper (CTranslate2) | ~1.5GB | MIT |
| PDF/DOCX/PPTX/XLSX | Docling (IBM) | ~200MB | MIT |
| Images | ColPali (3B) | ~3GB | Apache 2.0 |
| HTML/Web pages | trafilatura | tiny | GPL-3 |
| Markdown | Built-in parser | 0 | — |
| Code | tree-sitter | tiny | MIT |
| Email (.eml/.mbox) | mailparser | tiny | MIT |
| Calendar (.ics) | icalendar | tiny | BSD |

### Storage Layer

| Component | Tool | Purpose |
|-----------|------|---------|
| Vectors | Qdrant | Semantic search, per-tenant namespaces |
| Embeddings | FastEmbed (nomic-embed-text-v1.5) | Convert text → vectors |
| Memory Graph | SQLite + edges table | Relationships between memories |
| Metadata | SQLite | Extractions, importance, sentiment, source |
| Reranking | Jina Reranker (137M) | Pick best results from candidates |

### Retrieval Pipeline (what makes answers great)

1. Vector search (semantic similarity)
2. BM25 search (keyword matching — exact names, numbers)
3. Graph walk (follow LINK edges 1-2 hops)
4. Temporal weighting (recent memories score higher)
5. Importance weighting (high-importance memories score higher)
6. Reranking (Jina reranker picks final top-K)

### Self-Healing Knowledge Base

- **COMPILE** — When new memory arrives, auto-update entity/topic wiki pages
- **LINT** — Periodic audit: find contradictions, stale info, knowledge gaps
- **DECAY** — Reduce importance of superseded decisions, completed action items

---

## API Endpoints

```
POST   /v1/remember          Ingest text → full pipeline → memory stored
POST   /v1/remember/file     Ingest file (audio, PDF, image, doc) → same
POST   /v1/ask               Ask a question → retrieval + answer
POST   /v1/check             Ambient check → contradiction detection
GET    /v1/memories           List/search stored memories
GET    /v1/memories/:id      Get a specific memory with extractions
DELETE /v1/memories/:id      Forget a memory
GET    /v1/graph/:id         Get a memory's connections
POST   /v1/compile/:entity   Get/refresh compiled wiki page
POST   /v1/lint              Run health audit
GET    /v1/stats             Usage stats, memory count, health score
```

---

## Connectors (for Reattend SaaS)

| Connector | Data Source | Method |
|-----------|-----------|--------|
| Gmail | Emails | OAuth2, periodic sync |
| Google Calendar | Events + descriptions | OAuth2, periodic sync |
| Slack | Messages, threads | Slack App, Events API |
| Obsidian | Markdown notes | Folder sync, file watcher |
| Git/GitHub | Commits, PRs, issues | GitHub API or local repo |
| Notion | Pages, databases | Notion API |
| Google Drive | Docs, Sheets, Slides | Drive API + Docling |
| Local filesystem | Any files in a folder | watchdog file watcher |
| Webhook | Anything else | POST to /v1/remember |

---

## Reattend SaaS Tiers

| Tier | Price | Memories | Connectors | Users |
|------|-------|----------|------------|-------|
| Free | $0 | 1,000 | 3 | 1 |
| Pro | $12/mo | Unlimited | All | 1 |
| Team | $8/user/mo | Unlimited | All + shared | 10 |
| Business | $20/user/mo | Unlimited | All + SSO + audit | 100 |
| Enterprise | Custom | Unlimited | On-prem | Unlimited |

---

## Enterprise Features (On-Prem)

- SSO/SAML integration
- Role-based access control (RBAC)
- Full audit log (every query, every ingestion)
- Data retention policies (auto-delete after N days)
- Custom model training on company data
- Air-gapped mode (zero internet)
- High availability (multi-node)
- Automated backup/restore

---

## Build Sequence

### Sprint 1 — Rabbit Core Engine (Week 1-2)

- [ ] Restructure repo: `rabbit/core/`, `rabbit/processors/`, `rabbit/storage/`
- [ ] Input processors: text (done), audio (faster-whisper), PDF/DOCX (Docling)
- [ ] Qdrant integration for vector storage
- [ ] Memory graph (SQLite + edges table)
- [ ] Hybrid retrieval: vector + BM25 + graph walk + reranker
- [ ] Unified ingestion pipeline: input → triage → extract → summarize → sentiment → importance → embed → store → link
- [ ] Unified query pipeline: question → intent → expand → retrieve → rerank → graph walk → answer
- [ ] `RabbitCore` class: `ingest()`, `ingest_file()`, `ask()`, `check()`
- [ ] 50 end-to-end test cases

### Sprint 2 — Rabbit API + SDK (Week 3-4)

- [ ] FastAPI gateway: `/v1/remember`, `/v1/ask`, `/v1/check`, `/v1/memories`
- [ ] Auth: `rab_test_*` / `rab_live_*` key generation + validation
- [ ] Multi-tenant isolation (per-key namespaces)
- [ ] Rate limiting
- [ ] Python SDK: `pip install rabbit-memory`
- [ ] JS/TS SDK: `npm install @reattend/rabbit`
- [ ] CLI: `rabbit remember`, `rabbit ask`, `rabbit sync`
- [ ] SSE streaming for answers
- [ ] File upload endpoint
- [ ] Deploy to rabbit.reattend.com

### Sprint 3 — GitHub Launch + Connectors (Week 5-6)

- [ ] Public GitHub repo with README + quickstart + examples
- [ ] API reference docs
- [ ] Examples: basic, Slack bot, meeting notes, Obsidian sync, personal wiki
- [ ] Obsidian connector
- [ ] Git connector
- [ ] Local filesystem watcher
- [ ] Publish to PyPI and npm
- [ ] Launch: Hacker News, Reddit, Twitter/X

### Sprint 4 — Reattend SaaS v2 (Week 7-8)

- [ ] Fresh Next.js app at reattend.com
- [ ] Built entirely on Rabbit SDK
- [ ] Dashboard: memory timeline, search, knowledge graph visualization
- [ ] Gmail connector (OAuth2)
- [ ] Google Calendar connector
- [ ] Slack connector
- [ ] Daily digest email
- [ ] Free tier live

### Sprint 5 — Teams + Polish (Week 9-10)

- [ ] Team workspaces (shared memory namespace)
- [ ] Meeting upload (audio → Whisper → Rabbit)
- [ ] Self-healing wiki (COMPILE on ingest, LINT weekly)
- [ ] Knowledge graph visualization
- [ ] Feedback loop (thumbs up/down → training data)
- [ ] Webhook system
- [ ] Pro tier launch ($12/mo)

### Sprint 6 — Enterprise + On-Prem (Week 11-14)

- [ ] Docker Compose distribution
- [ ] GPU and CPU-only Dockerfiles
- [ ] Enterprise features: SSO, RBAC, audit logs
- [ ] On-prem setup guide
- [ ] First enterprise pilot
- [ ] ColPali integration (image understanding)
- [ ] Managed deployment option
- [ ] Enterprise pricing page

---

## Revenue Targets

| Month | Revenue | Source |
|-------|---------|-------|
| 1 | $0 | Building + benchmarking |
| 2 | $500 | 1-2 API developers |
| 3 | $2,000 | 5 API + first SaaS users |
| 4 | $5,000 | 10 API + SaaS Pro tier |
| 6 | $15,000 | 20 API + 1 enterprise pilot |
| 12 | $50,000 | 50 API + 3 enterprise + SaaS |

Infrastructure cost: ~$160/month. Break-even: 1 customer at $500/month.

---

## The Moat

1. **Specialized LLM** — 12 memory signals, not a general chatbot
2. **82K+ curated training examples** — years of data generation work
3. **Data flywheel** — every user makes the model better monthly
4. **Hybrid retrieval** — vector + BM25 + graph + temporal + importance + reranking
5. **Self-healing KB** — compile, lint, decay. Memory that maintains itself
6. **Multi-modal ingestion** — text, audio, PDF, images, code, email, calendar
7. **Five deployment modes** — API, SaaS, on-prem, bundled, managed
8. **SDKs + CLI** — Python, JS, command line
9. **Native connectors** — Gmail, Slack, Calendar, Obsidian, Git, Notion
10. **Network effects** — developers building on the platform can't easily leave

---

## The Vision

Recall.ai became the infrastructure for meeting transcripts. Every meeting bot (Fireflies, Otter, etc.) runs on it.

**Rabbit becomes the infrastructure for memory.** Every app that needs to remember — personal assistants, team tools, CRMs, knowledge bases, enterprise search — runs on Rabbit.

One model. One API. Memory for the world.
