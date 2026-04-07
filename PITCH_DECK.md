# Rabbit — Pitch Deck (Google Accelerator)

12 slides. 15 minutes. Tell the story.

---

## Slide 1: The Problem

**"Every Organization Has Amnesia"**

- 10,000 decisions made every month across email, Slack, meetings, docs
- 90% are forgotten within 30 days
- When people leave, institutional knowledge leaves with them
- When auditors ask "who approved this?", it takes days — or the answer is "we don't know"

*"The average employee spends 20% of their time searching for information that already exists inside their organization."*
— McKinsey

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

Rabbit is a proprietary AI model that:
- **Captures** every decision from email, Slack, meetings, docs — automatically
- **Extracts** people, decisions, action items, dates, topics
- **Links** related memories into a knowledge graph
- **Detects** contradictions and forgotten commitments in real-time
- **Answers** any question about your organization with cited sources
- **Maintains** a living wiki that heals itself daily

**15 signals. One model. One server. Zero data leakage.**

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

| | Rabbit | Everyone Else |
|---|---|---|
| AI Model | **Proprietary, fine-tuned for memory** | Rents GPT-4 / Claude / Llama via API |
| Cost at 20K users | **$600/month** (own server) | $6,000+/month (API fees) |
| On-premise | **Yes** (Docker, one command) | No (data goes to OpenAI) |
| Offline | **Yes** (runs locally) | No |
| Gets smarter | **Yes** (monthly retrain from real data) | No (generic model, static) |

**Rabbit is a 3.8B parameter model trained on 80,000+ organizational memory examples across 15 signals.** Built in-house. Fine-tuned specifically for extraction, linking, reasoning, and conversational recall.

No other company has a model trained specifically for organizational memory.

---

## Slide 8: The Flywheel

**"Every User Makes Rabbit Smarter"**

```
Users create memories → Rabbit processes them
     ↓
Users ask questions → Rabbit answers
     ↓
Users rate answers (👍/👎) → Training data
     ↓
Monthly retrain → Better model
     ↓
Better answers → More trust → More usage
     ↓
More data → Even better model
     ↓
Competitors can't catch up — they don't have the data
```

**This is our moat.** The model architecture is replicable. The training data from real organizational usage is not.

---

## Slide 9: Market & Business Model

**"$47B Market. Three Revenue Streams."**

**TAM:** Enterprise knowledge management — $47B by 2028 (Grand View Research)

| Revenue Stream | Price | Target |
|---|---|---|
| **Rabbit API** | Free tier → $29-99/month | Developers building AI products |
| **Reattend (SaaS)** | Free → $8/user/month | Teams who want the full product |
| **Rabbit On-Prem** | $50-200K/year | Banks, law firms, pharma, government |

**Unit economics:**
- Gross margin (API): 98%
- Gross margin (On-prem): 88%
- Break-even: 1 customer at $500/month
- Current infra cost: $160/month

---

## Slide 10: Traction & Ask

**"Built in 72 Hours. Deployed. Live."**

**What we've done:**
- Built and trained Rabbit (proprietary model, 15 signals, 80K examples)
- Deployed on Google Cloud (Mumbai, live API serving requests)
- Reattend has real users generating real organizational memories
- MCP server integration — works inside Cursor, Claude
- Full on-prem Docker deployment ready

**What we need from Google Accelerator:**
- $2,000 Google Cloud credits → 10+ months of Rabbit hosting
- Access to GCP enterprise customers for pilot programs
- Mentorship on enterprise go-to-market
- Google for Startups brand credibility for fundraising

**Next 90 days:**
- 3 enterprise pilots (banking, legal, consulting)
- Publish MemoryBench (first organizational memory benchmark)
- Rabbit v2 trained on real production data
- First paying enterprise customer

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
