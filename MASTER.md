# Rabbit — Master Document

> The proprietary memory AI for organizations. Built by Reattend.

---

## What We Built (3 Days, ~$100)

### The Model

| Version | Training Data | Signals | Status |
|---|---|---|---|
| v1.0 | 55,750 examples | 8 signals | HuggingFace (private) |
| v1.1 | 53,901 examples | 10 signals (+ multiturn, dontknow) | HuggingFace (private) |
| v1.2 | 61,178 examples | 12 signals (+ link, ambient) | **LIVE on Google Cloud** |

### The 12 Signals

| # | Signal | What It Does | When It Runs |
|---|---|---|---|
| 1 | INTENT | Classifies query type (factual/entity/temporal/synthesis/actions/history/aggregation) | Query time |
| 2 | EXTRACT | Pulls people, orgs, dates, decisions, action items, topics from text | Ingestion time |
| 3 | TRIAGE | Classifies content type + generates summary + tags | Ingestion time |
| 4 | EXPAND | Turns vague queries ("what about brian") into precise search queries | Query time |
| 5 | ANSWER | Conversational response with narrative, reasoning, citations, sources, follow-up questions | Response time |
| 6 | SUMMARIZE | Rich 2-4 sentence standalone summary | Ingestion time |
| 7 | SENTIMENT | Tone classification: positive/negative/neutral/tense/urgent | Ingestion time |
| 8 | IMPORTANCE | Scores 1-5 with reason | Ingestion time |
| 9 | MULTITURN | Handles follow-up questions with context from previous turn | Response time |
| 10 | DONTKNOW | Gracefully handles when memories don't fully answer the question | Response time |
| 11 | LINK | Detects relationships between memories (same_topic/contradicts/continuation_of/depends_on/same_people/causes/temporal) | Ingestion time |
| 12 | AMBIENT | Detects contradictions, forgotten commitments, critical context from screen text | Real-time |

### Infrastructure

| Component | Where | Cost |
|---|---|---|
| Rabbit v1.2 model | Google Cloud (Mumbai, T4 GPU) | $127/month (Spot) |
| API endpoint | http://34.93.210.241:8000 | Included above |
| Model weights backup | HuggingFace (private repos) | Free |
| Training data | GitHub (private repo) | Free |
| Training compute | RunPod (on-demand) | ~$2 per training run |
| Data generation | RunPod CPU + OpenAI API | ~$80 per 50K examples |

### Training Data Pipeline

```
Seed data (real Reattend examples)
  → Synthetic generation (GPT-4o-mini, 10 org universes)
  → Quality filtering (task-specific validators + dedup)
  → Fine-tuning (Unsloth + LoRA on Phi-3.5 Mini)
  → Testing (12-signal test bench)
  → Deployment (Google Cloud T4 GPU)
```

### API Endpoints

```
POST /v1/chat/completions  → Any signal (OpenAI-compatible format)
POST /v1/ingest            → Full pipeline: triage + extract + summarize + sentiment + importance + embed
POST /v1/query             → Query pipeline: intent + expand + answer
POST /v1/embeddings        → Vector embeddings (FastEmbed)
POST /v1/link              → Memory relationship detection
POST /v1/ambient           → Contradiction/commitment detection
GET  /health               → Server status
```

### What Rabbit Replaces in Reattend

| Task | Was | Now |
|---|---|---|
| Intent classification | Groq (llama-3.3-70b) | Rabbit [INTENT] |
| Query expansion | Groq | Rabbit [EXPAND] |
| Triage + extraction | Groq | Rabbit [TRIAGE] + [EXTRACT] |
| Ask / Q&A | OpenAI (gpt-4o-mini) | Rabbit [ANSWER] |
| Entity profile summaries | Groq | Rabbit [SUMMARIZE] |
| Memory compression | Groq | Rabbit [SUMMARIZE] |
| Weekly digest | Groq | Rabbit [ANSWER] |
| Meeting brief | Groq | Rabbit [ANSWER] |
| Memory linking | Groq | Rabbit [LINK] |
| Ambient recall | Groq | Rabbit [AMBIENT] |
| Sentiment (NEW) | — | Rabbit [SENTIMENT] |
| Importance (NEW) | — | Rabbit [IMPORTANCE] |
| Embeddings | FastEmbed (local) | FastEmbed (bundled in Rabbit server) |
| Audio transcription | AssemblyAI | Cohere Transcribe (future, on same server) |

---

## The Flywheel

### How It Works

```
Stage 1: CAPTURE
  Users connect Gmail, Slack, Calendar, take notes
  → Memories flow into Reattend
  → Each memory processed by Rabbit (extract, triage, summarize, sentiment, importance)
  → Stored with embedding + linked to related memories

Stage 2: QUERY
  User asks a question
  → Rabbit classifies intent + expands query
  → Vector search retrieves relevant memories
  → Rabbit generates conversational answer with citations

Stage 3: FEEDBACK
  User sees the answer
  → Thumbs up / thumbs down
  → This becomes labeled training data

Stage 4: RETRAIN
  Monthly: collect positive feedback examples
  → Add to training dataset
  → Fine-tune Rabbit on RunPod (~$2, ~1 hour)
  → Deploy new version to Google Cloud (5 min swap)
  → Better answers

Stage 5: COMPOUND
  Better answers → more user trust → more usage
  → More memories ingested → richer knowledge base
  → More questions asked → more feedback → more training data
  → Better Rabbit → cycle repeats

THIS IS THE MOAT.
Competitors can copy the model architecture.
They cannot copy the training data from real users.
The flywheel gets stronger every month.
```

### Flywheel Metrics to Track

| Metric | What It Measures | Target (Month 1) | Target (Month 6) |
|---|---|---|---|
| Memories ingested / day | Data capture volume | 500 | 10,000 |
| Queries / day | User engagement | 50 | 1,000 |
| Thumbs up rate | Answer quality | 70% | 85% |
| Training examples from feedback | Flywheel velocity | 100/month | 5,000/month |
| Retrain frequency | Model freshness | Monthly | Bi-weekly |
| Answer latency (P50) | User experience | 5s | 1s |

### Making the Flywheel Faster

1. **Compile on Ingest** — Pre-build entity/topic pages when memories arrive. 90% of queries become instant reads.

2. **Answers Become Knowledge** — Save great synthesized answers as compiled knowledge. Next person asking similar question gets instant response.

3. **Lint Pass** — Daily background job: find contradictions, stale info, missing links. Self-healing knowledge base.

4. **DPO Training** — When enough thumbs up/down pairs (1000+), train with Direct Preference Optimization. Expected 10-20% quality jump.

---

## Enterprise On-Premise: The Pitch

### The Problem (Every Enterprise Has This)

> "Your organization makes 10,000 decisions a month across Slack, email, meetings, and documents. How many are remembered? How many are contradicted three months later because nobody recalled the original discussion?"

> "When a senior engineer leaves, they take 3 years of institutional knowledge with them. The next person spends 6 months rebuilding context that already existed — in messages nobody can find."

> "Your compliance team needs to prove when a decision was made and who approved it. But the decision lives in a Slack thread from 8 months ago that nobody bookmarked."

### The Solution

> "Rabbit is a memory AI that runs entirely on your infrastructure. It captures every decision, discussion, and commitment across your tools — Slack, email, meetings, documents. It extracts entities, detects contradictions, links related memories, and answers natural language questions with cited sources."

> "Nothing leaves your servers. No external API calls. One Docker container, one GPU. Complete organizational memory."

### The Demo Script (15 Minutes)

```
Minute 1-3: Show the problem
  "Here's a typical scenario. Your team discussed pricing in March.
   Three meetings, two emails, one Slack thread. Can anyone tell me
   what was decided and why? ... [silence] ... That's the problem."

Minute 3-8: Show Rabbit processing
  [Paste a meeting transcript into the API]
  "Rabbit just extracted: 4 people, 2 decisions, 3 action items,
   classified it as a 'meeting' with importance 4/5, sentiment 'tense',
   and linked it to 3 related memories from last month."

Minute 8-12: Show Rabbit answering
  [Ask: "What happened with pricing?"]
  "Rabbit tells the STORY: started with freemium, costs flagged,
   reversed to usage-based. With citations. With follow-up questions.
   In 2 seconds."

Minute 12-14: Show contradiction detection
  [Type an email with wrong date/price]
  "Rabbit just caught that you said $45K but the approved budget was $42K.
   And the meeting date you wrote conflicts with what Tom agreed to."

Minute 14-15: The close
  "This runs on YOUR server. Nothing we showed you left this building.
   That's Rabbit."
```

### Enterprise Pricing

| Package | What's Included | Price |
|---|---|---|
| **Rabbit Cloud** | API access, hosted by us | $500-2,000/month |
| **Rabbit On-Prem (Team)** | Docker image, 1 GPU, up to 100 users | $50,000/year |
| **Rabbit On-Prem (Enterprise)** | Docker image, multi-GPU, SSO, SLA, dedicated support | $100-200,000/year |
| **Rabbit Edge** (future) | Quantized model for laptops, offline | $10/user/month |

### Target Enterprise Verticals

| Vertical | Why They Need Rabbit | Decision Maker | Deal Size |
|---|---|---|---|
| **Banking / Financial Services** | Regulatory compliance, decision audit trails, no data can leave | CTO / CISO | $100-200K |
| **Law Firms** | Case history recall, precedent search, client matter memory | Managing Partner / CTO | $50-100K |
| **Consulting** | Project knowledge retention, institutional memory across engagements | Knowledge Management Lead | $50-100K |
| **Pharma / Healthcare** | Clinical trial decisions, regulatory documentation | VP Engineering | $100-200K |
| **Government** | Institutional memory across administrations, policy continuity | Chief Digital Officer | $100-200K |
| **Large Tech Companies** | Engineering decision logs, on-prem requirement, scale | VP Engineering | $100-200K |

### What You Ship to Enterprise

```
One Docker container:
┌─────────────────────────────────────────┐
│ rabbit-server:v1.2                      │
│                                         │
│ Rabbit LLM (3.8B, 4-bit quantized)     │
│ FastEmbed (embeddings)                  │
│ Cohere Transcribe (audio, future)       │
│ Jina Reranker (search quality, future)  │
│ FastAPI server                          │
│                                         │
│ docker run --gpus all -p 8000:8000 \    │
│   rabbit-server:v1.2                    │
│                                         │
│ Client's data NEVER leaves this box.    │
└─────────────────────────────────────────┘
```

---

## Developer Community: Getting Coders as Core Customers

### Why Developers Are the Best First Customers

1. **They live in text** — Git commits, PR reviews, Slack, docs. All text. Perfect for Rabbit.
2. **They understand APIs** — No hand-holding needed. Give them docs, they build.
3. **They influence purchasing** — "I've been using Rabbit API, we should buy it for the team."
4. **They create content** — Blog posts, tweets, GitHub stars. Free marketing.
5. **They have the problem** — Every dev team has institutional knowledge loss.

### The Developer Hook: MCP Server

Reattend already has an MCP server. This means developers using **Cursor** or **Claude** can access their org memory while coding.

```
Developer is writing code in Cursor:
  → Types: "What was the decision on the auth architecture?"
  → Cursor calls Rabbit MCP → retrieves relevant memories
  → Developer gets: "In the March 15 meeting, team decided on OAuth2 + JWT.
     Sarah raised concerns about token rotation, resolved in the Apr 1 follow-up."
  → Developer codes with full context. No Slack searching.
```

**This is the viral loop.** Developer uses Rabbit in Cursor → tells team → team adopts Reattend → company buys enterprise.

### Developer Marketing Strategy

**Phase 1: Content (Month 1-2)**

1. **Blog post:** "How We Built a Memory LLM in 3 Days for $100"
   - Publish on Medium, Dev.to, Hacker News
   - Detail the architecture, training data pipeline, signals
   - Open-source the training scripts (NOT the model weights or data)
   - This establishes credibility and attracts developer attention

2. **GitHub README:** Make the rabbit repo public (scripts only, not weights)
   - Training pipeline as open-source
   - "Want the model? Use our API or train your own."
   - Stars = social proof

3. **Twitter/X thread:** "We built an LLM that remembers your org's decisions. Here's what we learned."
   - Technical audience. Show the architecture diagram.
   - Share a few impressive Rabbit outputs.

**Phase 2: Developer Tools (Month 2-3)**

1. **Rabbit SDK (Python)**
   ```python
   from rabbit import Rabbit
   
   r = Rabbit(api_key="rab_...")
   
   # Ingest a memory
   result = r.ingest("Met with Sarah from Acme. Budget approved at $45K.")
   print(result.entities)  # [Sarah, Acme, $45K]
   
   # Ask a question
   answer = r.query("What happened with Acme?", memories=[...])
   print(answer.text)     # Conversational response
   print(answer.sources)  # Cited memories
   print(answer.followups) # Suggested questions
   ```

2. **Rabbit SDK (TypeScript/Node)**
   ```typescript
   import { Rabbit } from '@reattend/rabbit';
   
   const rabbit = new Rabbit({ apiKey: 'rab_...' });
   const result = await rabbit.ingest({ content: '...' });
   const answer = await rabbit.query({ question: '...', memories: [...] });
   ```

3. **Rabbit MCP Server** (already exists in Reattend)
   - Package as standalone for Cursor/Claude users
   - "Add organizational memory to your AI coding assistant"

**Phase 3: Community (Month 3-6)**

1. **Discord/Slack community** for Rabbit developers
2. **"Built with Rabbit" showcase** — feature projects using the API
3. **Hackathon sponsorship** — "Best use of organizational memory AI"
4. **Weekly office hours** — live coding sessions integrating Rabbit

### Developer Pricing

| Tier | Price | Limits |
|---|---|---|
| **Free** | $0 | 1,000 API calls/month |
| **Pro** | $29/month | 50,000 API calls/month |
| **Team** | $99/month | 500,000 API calls/month + priority |
| **Enterprise** | Custom | Unlimited + on-prem option |

Free tier is generous enough to build a real integration. Pro is cheap enough for indie developers. This is the Stripe model.

---

## What To Do Next (Priority Order)

### This Week

| # | Task | Time | Outcome |
|---|---|---|---|
| 1 | Build benchmark comparison script | 2 hours | Know exactly where Rabbit beats/loses to Groq |
| 2 | Run 50-query benchmark | 1 hour | Quality scorecard |
| 3 | Fix answer latency (optimize inference) | 1 day | Get from 45s to 5-10s |
| 4 | Set up auto-restart on GCP (systemd service) | 1 hour | Server survives reboots |

### Next Week

| # | Task | Time | Outcome |
|---|---|---|---|
| 5 | Swap Reattend's easy signals to Rabbit (intent, sentiment, importance) | 1 day | First real traffic on Rabbit |
| 6 | Shadow test hard signals (answer, triage, extract) | 3 days | Compare quality in production |
| 7 | Add feedback logging (thumbs up/down) | 1 day | Start collecting training data |
| 8 | Build rabbit.reattend.com landing page | 2 days | Enterprise + developer entry point |

### Month 1

| # | Task | Time | Outcome |
|---|---|---|---|
| 9 | Compile on ingest (entity pages) | 1 week | 10x faster answers |
| 10 | Answers become knowledge | 2 days | Knowledge compounds |
| 11 | Lint pass (self-healing KB) | 1 week | Self-maintaining knowledge base |
| 12 | Publish "How We Built Rabbit" blog | 2 days | Developer attention |

### Month 2

| # | Task | Time | Outcome |
|---|---|---|---|
| 13 | First monthly retrain from real data | 1 day | Flywheel starts |
| 14 | Rabbit Python SDK | 3 days | Developer adoption |
| 15 | Add Cohere Transcribe to server | 2 days | Audio → memory pipeline |
| 16 | Add Jina Reranker | 1 day | Better search quality |
| 17 | First enterprise pilot (free) | 1 week | Case study |

### Month 3

| # | Task | Time | Outcome |
|---|---|---|---|
| 18 | Docker image for on-prem | 3 days | Enterprise product |
| 19 | First paying enterprise customer | 2 weeks | Revenue |
| 20 | DPO training from feedback pairs | 3 days | Quality jump |
| 21 | Rabbit v2 (trained on real data) | 1 week | Significantly better model |

---

## Financial Summary

### Costs (Monthly)

| Item | Cost |
|---|---|
| Google Cloud (T4 Spot VM) | $127 |
| Reattend hosting (Vercel) | $20 |
| RunPod (monthly retrain) | $2 |
| Domain + misc | $10 |
| **Total** | **~$160/month** |

### Revenue Targets

| Month | Revenue | Source |
|---|---|---|
| Month 1 | $0 | Building + benchmarking |
| Month 2 | $500 | 1-2 API customers |
| Month 3 | $2,000 | 5 API customers |
| Month 4 | $5,000 | 10 API + 1 enterprise pilot |
| Month 6 | $15,000 | 20 API + 1 paying enterprise |
| Month 12 | $50,000 | 50 API + 3 enterprise |

### Break-Even

```
Monthly costs: $160
Revenue needed: $160
Break-even: 1 API customer at $500/month

Every customer after that is 98%+ gross margin.
```

---

## The Story (For Everything — Investors, Enterprise, Developers, Accelerators)

> "Every AI system in the world has amnesia. ChatGPT forgets. Copilot forgets. Your Slack messages are buried. Your meeting decisions are lost. Your organization's collective intelligence degrades every day.
>
> We built Rabbit — a proprietary AI model trained specifically for organizational memory. It doesn't just store information. It extracts decisions, detects contradictions, links related context, and reasons over your team's entire history to give you conversational, cited answers.
>
> Rabbit processes 12 types of memory signals from a single model. It runs on a single GPU server. It works on-premise — nothing leaves your firewall. And it gets smarter with every interaction through an automated retraining flywheel.
>
> Reattend, our team product, proves it works with real users. The Rabbit API lets any developer add organizational memory to their app in one afternoon. Enterprise clients deploy it inside their firewall for complete data sovereignty.
>
> We built this in 3 days for $100. We're not asking for permission. We're building the memory layer for the AI era."

---

*Last updated: April 6, 2026*
*Rabbit v1.2 — 12 signals, 61K training examples, live on Google Cloud*
