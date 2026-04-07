# Rabbit — Pitch Deck (Google Accelerator)

12 slides. 15 minutes. Tell the story.

---

## Slide 1: The Problem

**"Every Organization Has Amnesia"**

- A 50-person company generates **~15,000 messages, emails, and meeting minutes per month**
- **90% of decisions** are never documented — they live in Slack threads and email chains
- When someone leaves, **3 years of institutional knowledge walks out the door**
- Knowledge workers spend **1.8 hours/day (9.3 hours/week)** searching for information — **$12,000/employee/year wasted** (IDC Research)
- Compliance teams take **3-5 business days** to answer "who approved this and when?"

**In numbers:**
- 50-person org: $600,000/year lost to knowledge search
- 500-person enterprise: $6M/year lost
- Global: **$47B knowledge management market** by 2028 (Grand View Research)

*The problem isn't storage. It's that organizations remember nothing.*

---

## Slide 2: Why Current Solutions Fail

**"Search ≠ Memory"**

| Tool | What It Does | What It Doesn't Do |
|---|---|---|
| Glean | Searches your documents | Doesn't remember decisions or detect contradictions |
| Notion AI | Answers questions about your pages | Only works within Notion. Manual input. |
| ChatGPT | General AI assistant | Forgets everything between sessions |
| Confluence | Stores wiki pages | Someone has to write them. Nobody does. |

**The gap:** No one builds organizational MEMORY — a system that captures, links, validates, and reasons over everything your team discusses.

---

## Slide 3: Introducing Rabbit

**"The Memory AI for Organizations"**

### What Rabbit Is (Technical Definition)

Rabbit is a **3.8 billion parameter large language model** (LLM), fine-tuned from Microsoft's Phi-3.5 Mini using **LoRA (Low-Rank Adaptation)** on **80,000+ proprietary training examples** across **15 specialized memory signals**.

Unlike general-purpose models (GPT-4, Claude, Llama) that do everything okay, Rabbit does ONE thing exceptionally: **organizational memory** — capture, extract, link, reason, and recall.

### What Rabbit Does

| Signal | What It Does | Speed |
|---|---|---|
| **EXTRACT** | Pulls people, orgs, decisions, action items, dates from raw text | 300ms |
| **TRIAGE** | Classifies content type + generates summary + tags | 300ms |
| **SUMMARIZE** | Rich standalone summary of any content | 400ms |
| **SENTIMENT** | Detects tone (positive/negative/tense/urgent) | 270ms |
| **IMPORTANCE** | Scores 1-5 with reason | 300ms |
| **LINK** | Connects related memories (7 relationship types) | 500ms |
| **AMBIENT** | Real-time contradiction + forgotten commitment detection | 400ms |
| **INTENT** | Classifies user query type | 270ms |
| **EXPAND** | Turns vague queries into precise search | 400ms |
| **ANSWER** | Conversational response with citations, sources, follow-ups | 3-5s |
| **COMPILE** | Updates org wiki pages when new info arrives | 500ms |
| **LINT** | Daily audit: contradictions, stale info, knowledge gaps | batch |

**15 signals. One model. One GPU server. One API call. Zero data leakage.**

---

## Slide 4: How Rabbit Works

**"From Raw Signal to Organizational Intelligence"**

```
Email / Slack / Meeting / Doc arrives
         ↓
┌─────────────────────────────────────┐
│         RABBIT (one API call)       │
│                                     │
│  Extract → people, decisions, dates │
│  Classify → type, importance, tone  │
│  Summarize → rich standalone summary│
│  Link → connect to related memories │
│  Compile → update the org wiki      │
│  Lint → detect contradictions daily │
└─────────────────────────────────────┘
         ↓
User asks: "What happened with pricing?"
         ↓
Rabbit: Conversational answer with citations,
        sources, and follow-up questions.
        Instant. From the compiled wiki.
```

---

## Slide 5: The Demo Moment

**"Watch Rabbit Think"**

[LIVE DEMO — paste a meeting transcript]

**Input:** A 500-word meeting transcript about a pricing discussion

**Rabbit outputs in 2 seconds:**
- 4 people extracted
- 2 decisions identified
- 3 action items with owners and dates
- Sentiment: "tense"
- Importance: 4/5 ("team-level strategic decision")
- Linked to 3 related memories from last month
- Wiki page for "Pricing Strategy" auto-updated

**Then ask:** "What happened with pricing?"

**Rabbit answers:** A 300-word narrative telling the story of how pricing evolved, with [1][2][3] citations, sources section, and 3 follow-up questions.

---

## Slide 6: The Organization Wiki

**"Knowledge That Builds and Heals Itself"**

Traditional wiki: Someone writes a page. Nobody updates it. It rots.

Rabbit wiki: Auto-built from every memory. Updated every time new information arrives. Validated every night.

```
Organization Wiki (auto-maintained)
├── People/     → every person, their role, what they said, what they owe
├── Projects/   → every initiative, status, decisions, blockers
├── Clients/    → every interaction, deal status, open items
├── Decisions/  → every decision, who approved, linked discussions
└── Lint Report → contradictions caught, stale info flagged, gaps identified
```

**After 30 days with 50 users: 4,000 memories, 89 decisions tracked, 45 entity pages, 7 contradictions caught — all automatically.**

---

## Slide 7: Why We Own the Model

**"We Don't Rent AI. We Built It."**

### Technical Architecture

```
Base Model:     Microsoft Phi-3.5 Mini (3.8B params, MIT license)
Fine-tuning:    LoRA (r=16, α=16) — trains 0.78% of weights
Training Data:  80,000+ proprietary examples (never published)
Training Cost:  ~$100 total (RunPod A100, 3 training runs)
Inference:      4-bit quantized, runs on single NVIDIA T4 GPU (16GB VRAM)
Serving:        FastAPI, 270ms-5s latency depending on signal
Embeddings:     nomic-embed-text-v1.5 (768-dim vectors, bundled)
```

### Rabbit vs Renting AI

| Metric | Rabbit (ours) | GPT-4o-mini (OpenAI) | Llama 3.3 70B (Groq) |
|---|---|---|---|
| Model ownership | **Ours — weights, data, architecture** | Rented per token | Open weights, no customization |
| Memory task accuracy | **95%+ intent, 85%+ extraction** | 80% intent | 0% (no fine-tuning) |
| Cost at 100K calls/month | **$127/month (fixed)** | ~$150/month (variable) | ~$80/month (variable) |
| Cost at 1M calls/month | **$127/month (fixed)** | ~$1,500/month | ~$800/month |
| On-premise deployment | **Yes — Docker, one command** | No — data goes to OpenAI | No |
| Data privacy | **100% — nothing leaves your server** | Data sent to OpenAI servers | Data sent to Groq servers |
| Gets smarter with use | **Yes — monthly retrain flywheel** | No — generic, static | No |
| Offline capable | **Yes** | No | No |

**At scale, Rabbit is 10-50x cheaper and the only option for on-premise deployment.**

---

## Slide 8: The Flywheel & Moat

**"Every User Makes Rabbit Smarter. Competitors Can't Catch Up."**

```
Users create memories → Rabbit processes (15 signals)
     ↓
Users ask questions → Rabbit answers with citations
     ↓
Users rate answers (👍/👎) → Labeled training data (FREE)
     ↓
Monthly retrain on RunPod ($2/run) → Better model
     ↓
Better answers → More trust → More usage
     ↓
More data → Even better model → Cycle repeats
```

### The 3-Layer Moat

| Layer | What | Replicable? |
|---|---|---|
| **1. Model weights** | Fine-tuned on 80K+ org memory examples | Takes 6+ months to collect equivalent data |
| **2. Training data** | Grows with every user interaction | Impossible without users (chicken-and-egg) |
| **3. Compile-Link-Lint architecture** | Self-maintaining org wiki | 12+ months of engineering to replicate |

**A competitor starting today is 12 months behind.** By then, our flywheel has generated 500K+ real training examples they don't have.

### Defensibility Math

```
Month 1:   80,000 training examples (synthetic)
Month 6:   130,000 examples (synthetic + real user data)
Month 12:  500,000 examples (production flywheel running)
Month 24:  2,000,000 examples (multiple enterprise clients)

Each 2x in data = measurable quality improvement.
No competitor can buy this data. It only exists inside Rabbit.
```

---

## Slide 9: Market & Business Model

**"$47B Market. Three Revenue Streams."**

**TAM:** Enterprise knowledge management — **$47B by 2028** (Grand View Research)
**SAM:** AI-powered enterprise memory/search — **$8.5B by 2028** (Gartner)
**SOM (Year 3 target):** 50 enterprise + 500 API customers — **$5M ARR**

### Revenue Streams

| Stream | Price | Target Customer | Gross Margin |
|---|---|---|---|
| **Rabbit API** | Free → $29 → $99/month | Developers, SaaS companies | **98%** |
| **Reattend SaaS** | Free → $8/user/month | Teams (5-500 people) | **90%** |
| **Rabbit On-Prem** | $50-200K/year | Banks, law firms, pharma, govt | **88%** |

### Unit Economics

```
Infrastructure cost:         $160/month (Google Cloud T4 Spot)
Break-even:                  1 API customer at $500/month
Marginal cost per customer:  ~$0 (API), ~$500/month (enterprise support)

Revenue per enterprise deal:  $150,000/year
Support cost per enterprise:  ~$18,000/year
Enterprise gross margin:      88%

Revenue projection:
  Month 6:   $15,000 MRR (20 API + 1 enterprise pilot)
  Month 12:  $50,000 MRR (50 API + 3 enterprise)
  Month 24:  $200,000 MRR (200 API + 10 enterprise)
```

### Comparable Valuations

| Company | What They Do | Valuation | Revenue Multiple |
|---|---|---|---|
| Glean | Enterprise AI search | $4.6B | ~100x ARR |
| Cohere | Enterprise AI models | $5.5B | ~50x ARR |
| Mem | AI note-taking | $110M | Early stage |
| **Rabbit (target)** | **Memory AI** | **$10-20M (seed)** | — |

---

## Slide 10: Traction & Ask

**"Built in 72 Hours for $100. Deployed. Live."**

### What We've Built (Numbers)

| Metric | Value |
|---|---|
| Model versions trained | 4 (v1.0, v1.1, v1.2, v1.3 in progress) |
| Training examples | 80,000+ proprietary |
| Specialized signals | 15 |
| Total training cost | ~$100 (compute + API) |
| API endpoint | Live on Google Cloud Mumbai |
| Average simple signal latency | 270ms |
| Reattend users | Active, generating real memories |
| Integrations | Gmail, Slack, Calendar, MCP (Cursor/Claude) |
| Code | 4,500+ lines across training pipeline, API server, benchmarks |
| Time from zero to deployed LLM | 72 hours |

### What We Need from Google

| Ask | Why |
|---|---|
| **Google Cloud credits ($50-100K)** | Scale Rabbit to multi-GPU, serve 1000+ enterprise users |
| **Access to GCP enterprise customers** | Banks, pharma, consulting firms already on GCP — warm intros for pilots |
| **Enterprise GTM mentorship** | First enterprise sales playbook |
| **Google for Startups brand** | Credibility for fundraising and enterprise trust |

### Next 90 Days

| Milestone | Target |
|---|---|
| Enterprise pilots | 3 (banking, legal, consulting) |
| API customers | 10 |
| MemoryBench published | First organizational memory benchmark |
| Rabbit v2 | Trained on real production data |
| First paying enterprise | $50-150K contract signed |
| Seed round | $500K-1M (if needed) |

---

## Slide 11: Reattend — The Product

**"Rabbit's First Customer"**

Reattend is a team memory tool powered by Rabbit.

- **Free forever** for teams up to 5 users
- Connect Gmail, Slack, Calendar — memories captured automatically
- Ask anything → cited conversational answers
- Browser extension + desktop app for passive capture
- MCP server → works inside Cursor, Claude, any AI tool

**Reattend proves Rabbit works.** Real users, real memories, real answers. Every Reattend user generates training data that makes Rabbit better.

**Reattend is the demo. Rabbit is the platform.**

---

## Slide 12: Rabbit + Reattend — The Vision

**"The Memory Layer for the AI Era"**

```
Year 1: Prove
  Rabbit works. Reattend has users. First enterprise pilot.

Year 2: Scale  
  50 API customers. 3 enterprise on-prem.
  Rabbit v3 trained on 500K+ real examples.
  "Powered by Rabbit" in 100+ products.

Year 3: Platform
  Rabbit is the standard memory API.
  Every AI assistant, every copilot, every enterprise tool 
  needs persistent memory. They all call Rabbit.

Endgame: "Powered by Rabbit" becomes the "Powered by Stripe" 
         of organizational intelligence.
```

**We're not building a better search engine. We're building the memory layer that every AI system will need.**

---

## Speaker Notes / Talking Points

### If they ask "Why not just use RAG?"
"RAG retrieves documents. Rabbit builds and maintains a living knowledge base. RAG answers questions. Rabbit detects contradictions, tracks decisions, and generates follow-up questions. RAG is a technique. Rabbit is an intelligence layer."

### If they ask "Why not a bigger model?"
"A 3.8B model trained specifically for memory tasks outperforms a 70B general model on our benchmarks. It's faster, cheaper, and runs on a single GPU. We'll scale the model when the data warrants it — right now, more training data matters more than more parameters."

### If they ask "What's your moat?"
"Three things: 1) Proprietary training data that grows with every user. 2) A model fine-tuned for memory that nobody else has trained. 3) The compile-link-lint architecture that turns raw memories into a self-maintaining wiki. You can copy any one of these. Copying all three takes 12+ months, by which time our flywheel is 12 months ahead."

### If they ask "Why should Google care?"
"Every enterprise running on Google Cloud needs organizational memory. Rabbit runs on GCP. Every enterprise deal we close is a long-term GCP customer paying for GPU compute. We're not just a startup — we're a distribution channel for Google Cloud GPU instances."

---

*Deck designed for 15 minutes. Slide 5 (demo) takes 3 minutes. Rest are 1-minute each.*
