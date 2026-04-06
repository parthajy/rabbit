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

## Current Infrastructure Status

| Component | On Google Cloud? | Status |
|---|---|---|
| Rabbit LLM (3.8B, 4-bit) | YES | Live, serving API at 34.93.210.241:8000 |
| FastEmbed (embeddings) | YES | Bundled in server, working |
| FastAPI server | YES | Running on port 8000 |
| Cohere Transcribe (audio) | NOT YET | Add after benchmark + swap |
| Jina Reranker (search quality) | NOT YET | Add after benchmark + swap |
| ColPali (visual docs) | NOT YET | Future addition |
| BGE-M3 (multilingual embed) | NOT YET | Future, for enterprise |

All future models fit on the same T4 GPU (16GB VRAM total, ~9GB used after all additions).

---

## v1.3 Engineering Features (No Retraining Needed)

These are code features in Reattend built ON TOP of Rabbit's existing signals.

### 1. Compile on Ingest

**What:** When a memory arrives, Rabbit updates pre-built entity/topic pages immediately.
**Why:** 90% of queries become instant reads (10ms) instead of real-time synthesis (5-45s).
**How:** Uses EXTRACT + SUMMARIZE + LINK signals already in Rabbit.
**Where:** New code in Reattend's ingestion pipeline.

### 2. Answers Become Knowledge

**What:** When Rabbit generates a great synthesis, save it as a compiled memory.
**Why:** Knowledge compounds. Same question never recomputed.
**How:** ANSWER output scored → if quality > 0.8 → saved with source links.
**Where:** New logic in Reattend's ask route.

### 3. Lint Pass (Self-Healing Knowledge Base)

**What:** Daily background job scans entire knowledge base.
**Why:** Catches contradictions, stale info, missing links, orphan memories.
**How:** Uses AMBIENT + LINK + ANSWER signals already in Rabbit.
**Where:** New cron job in Reattend.
**Output:** Daily report to workspace admin.

---

## Benchmarking Strategy

### Who Benchmarks?

**We do it ourselves first (internal benchmark).** Then validate with third parties.

#### Internal Benchmark (This Week)

We build a Python script that sends identical inputs to 3 providers:
- Rabbit (our model, http://34.93.210.241:8000)
- Groq (llama-3.3-70b, current Reattend provider)
- OpenAI (gpt-4o-mini, current Reattend provider)

50 test cases covering all signal types. Human scoring (Partha rates 1-5).

**This is standard practice.** Every AI company benchmarks internally first. OpenAI, Anthropic, Google all self-benchmark before publishing.

#### Third-Party Validation (Month 2-3)

| Platform | What It Does | Cost | How To Use |
|---|---|---|---|
| **Hugging Face Open LLM Leaderboard** | Standard benchmarks (MMLU, HellaSwag, etc.) | Free | Submit model for general benchmarks. Rabbit will rank low on general tasks (expected) but shows we're a real model. |
| **LMSys Chatbot Arena** | Blind human comparison | Free | Submit Rabbit for human preference ranking. Users compare answers without knowing which model is which. |
| **Custom eval on Reattend data** | Domain-specific benchmark | Free | Publish a "Memory Task Benchmark" dataset. Invite community to test their models. We set the benchmark others compete on. |
| **Customer testimonials** | Real-world validation | Free | "Company X replaced Groq with Rabbit and got 15% better extraction accuracy." |

#### The Smartest Benchmark Move

**Create the benchmark category ourselves.** There's no standard "organizational memory benchmark" today. We create one:

"MemoryBench: A Benchmark for Organizational Memory AI"
- 500 test cases across: extraction, triage, linking, Q&A, contradiction detection
- Publish the dataset (not the model)
- Run all major models against it
- Rabbit wins (because we trained for it)
- Other companies now compete on OUR benchmark

This is what every AI leader does — GLUE was created by NYU, SQuAD by Stanford, MMLU by Berkeley. We create MemoryBench by Reattend.

#### What Metrics We Report

| Metric | What It Measures | How We Measure |
|---|---|---|
| Intent accuracy | % correct classification | Compare to human-labeled ground truth |
| Entity extraction F1 | Precision + recall of extracted entities | Compare to manually annotated entities |
| Triage accuracy | % correct type classification | Compare to human labels |
| Answer quality | Human preference score (1-5) | Partha scores + later user feedback |
| Answer citation accuracy | % of citations that are correct | Manual check: does [1] actually support the claim? |
| Contradiction detection rate | % of contradictions caught | Inject known contradictions, measure detection |
| Link relevance | % of links that are meaningful | Manual review of linked memories |
| Latency (P50, P95) | Response time | Measured from API logs |
| Cost per 1K calls | Operational cost | Calculated from server costs |

---

## What To Do Next (Priority Order)

### Tomorrow (Day 1)

| # | Task | Time | Outcome |
|---|---|---|---|
| 1 | Build benchmark script (Rabbit vs Groq vs OpenAI, 50 queries) | 2 hours | Side-by-side comparison |
| 2 | Run benchmark and score | 1 hour | Know exactly where Rabbit wins/loses |
| 3 | Fix answer latency (45s → 5-10s) | 2 hours | Usable response times |
| 4 | Set up systemd auto-restart on GCP | 1 hour | Server survives reboots/preemption |

### This Week (Days 2-5)

| # | Task | Time | Outcome |
|---|---|---|---|
| 5 | Fix benchmark gaps with targeted training data | 1-2 days | Rabbit matches Groq on weak signals |
| 6 | Swap easy signals in Reattend (intent, sentiment, importance) | 1 day | First real traffic on Rabbit |
| 7 | Shadow test hard signals (answer, triage, extract) | 2 days | Quality comparison in production |
| 8 | Build rabbit.reattend.com landing page with benchmarks | 2 days | Enterprise + developer entry point |

### Next Week

| # | Task | Time | Outcome |
|---|---|---|---|
| 9 | Add feedback logging (thumbs up/down) in Reattend | 1 day | Start collecting training data |
| 10 | Apply to incubators (Google Accelerator, YC, NASSCOM, 100X.VC) | 2 days | Pipeline started |
| 11 | Full swap: all signals to Rabbit, Groq as fallback only | 1 day | Rabbit is primary |
| 12 | Start outreach to first enterprise prospect | 1 day | Revenue pipeline |

### Month 1

| # | Task | Time | Outcome |
|---|---|---|---|
| 13 | Compile on ingest (entity pages) | 1 week | 10x faster answers |
| 14 | Answers become knowledge | 2 days | Knowledge compounds |
| 15 | Lint pass (self-healing KB) | 1 week | Self-maintaining knowledge base |
| 16 | Publish "How We Built Rabbit" blog | 2 days | Developer attention, HN post |
| 17 | Create MemoryBench (public benchmark dataset) | 3 days | Own the benchmark category |

### Month 2

| # | Task | Time | Outcome |
|---|---|---|---|
| 18 | First monthly retrain from real data | 1 day | Flywheel starts |
| 19 | Rabbit Python SDK | 3 days | Developer adoption |
| 20 | Add Cohere Transcribe to GCP server | 2 days | Audio → memory pipeline |
| 21 | Add Jina Reranker to GCP server | 1 day | Better search quality |
| 22 | First enterprise pilot (free) | 1 week | Case study |

### Month 3

| # | Task | Time | Outcome |
|---|---|---|---|
| 23 | Docker image for on-prem | 3 days | Enterprise product |
| 24 | First paying enterprise customer | 2 weeks | Revenue |
| 25 | DPO training from feedback pairs | 3 days | Quality jump |
| 26 | Rabbit v2 (trained on real user data) | 1 week | Significantly better model |

---

## Incubators and Funding Targets

| Program | Deadline | What They Want | Our Pitch |
|---|---|---|---|
| **Google for Startups Accelerator (India)** | Rolling | AI/ML with traction | Own LLM, live API, real users |
| **Y Combinator** | Next batch | Technical founders, fast execution | Built + deployed LLM in 3 days |
| **Microsoft for Startups** | Rolling | Cloud-native startups | Portable to Azure for enterprise |
| **NASSCOM DeepTech Club** | Quarterly | Indian deep tech | Indian-built memory LLM |
| **Antler India** | Rolling | Pre-seed technical founders | Solo founder, working product |
| **100X.VC** | Rolling | Indian early stage | Deep tech, enterprise revenue path |
| **Techstars** | Batch-based | Scalable startups | API platform, infrastructure play |

### How Model Updates Work (Retraining → Deployment)

```
1. Collect new training data (feedback, real queries, new synthetic)
2. Train on RunPod A100 (~$2, ~1 hour)
3. Upload to HuggingFace (reattend/rabbit-v1.3)
4. SSH into GCP VM
5. Update RABBIT_REPO env var → "reattend/rabbit-v1.3"
6. Restart server (sudo systemctl restart rabbit)
7. New model live. Same URL. Same API key. Clients get update automatically.
```

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

## Open-Source Models to Add (Future)

| Model | What It Does | Size | License | When |
|---|---|---|---|---|
| **Cohere Transcribe** | Audio → text (better than Whisper) | 2B | Apache 2.0 | Month 2 |
| **Jina Reranker v2** | Re-rank search results for relevance | 137M | Apache 2.0 | Month 2 |
| **ColPali** | Visual doc understanding (PDFs, slides, charts) | 3B | MIT | Month 3 |
| **BGE-M3** | Multilingual embeddings (100+ languages) | 567M | MIT | Month 3 (enterprise) |
| **Florence-2** | Image captioning + OCR (whiteboards, screenshots) | 770M | MIT | Month 4 |

All fit on the same T4 GPU. Total VRAM after all additions: ~13GB / 16GB available.

---

## Competitive Landscape

| | **Rabbit** | **Glean** | **Notion AI** | **Cohere** |
|---|---|---|---|---|
| Owns the model | **YES** | No (rents GPT-4/Claude) | No (rents generic LLMs) | Yes |
| Auto-captures memories | **YES** | Partial (crawls apps) | No (manual) | No (sells API) |
| Memory graph | **YES** | No | No | No |
| On-prem deployment | **YES** | No | No | Yes |
| Offline capable | **YES** | No | No | N/A |
| Memory-specialized | **YES (12 signals)** | No (generic search) | No (generic AI) | No (general purpose) |
| Data flywheel | **YES** | No | No | Partial |
| Price at 20K users | ~$600/month | ~$200K/month | ~$150K/month | Pay per token |

---

## Legal: What's Proprietary vs Open-Source

| Component | License | Obligation | Proprietary? |
|---|---|---|---|
| Phi-3.5 Mini (base model) | MIT | Include license in codebase | Base is open, fine-tuned weights are OURS |
| Our LoRA weights | 100% ours | None | YES — never publish |
| Our training data | 100% ours | None | YES — never publish |
| 12-signal architecture | 100% ours | None | YES — trade secret |
| Cohere Transcribe | Apache 2.0 | Include license | Open source, free to use commercially |
| FastEmbed / nomic | Apache 2.0 | Include license | Open source, free to use commercially |
| Jina Reranker | Apache 2.0 | Include license | Open source, free to use commercially |

**What we say publicly:** "Rabbit is our proprietary memory model." (True.)
**What we say to investors:** "Built on open-source foundations with proprietary intelligence." (Smart.)
**What we say to enterprise:** "Runs on your server. No data leaves." (Selling point.)

---

*Last updated: April 6, 2026*
*Rabbit v1.2 — 12 signals, 61K training examples, live on Google Cloud at 34.93.210.241:8000*
