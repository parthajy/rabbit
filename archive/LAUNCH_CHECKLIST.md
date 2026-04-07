# Rabbit v1.2 → Launch Checklist

## Architecture

```
Google Cloud (₹30K free credits, ~2 months)
┌─────────────────────────────────────┐
│ Rabbit API Server (T4 GPU)          │
│                                     │
│ POST /v1/ingest   → triage, extract,│
│                     summarize,      │
│                     sentiment,      │
│                     importance      │
│ POST /v1/query    → intent, expand, │
│                     answer,         │
│                     multiturn,      │
│                     dontknow        │
│ POST /v1/embed    → fastembed       │
│ POST /v1/link     → linking         │
│ POST /v1/ambient  → ambient recall  │
│ POST /v1/pipeline → all-in-one      │
└──────────────┬──────────────────────┘
               │ HTTPS
               │
Cheap VPS ($6-12/month)
┌──────────────┴──────────────────────┐
│ Reattend.xyz (test instance)        │
│ Same codebase as reattend.com       │
│ LLM provider → Rabbit API on GCloud │
│ Same DB schema, same features       │
└─────────────────────────────────────┘

Production (untouched)
┌─────────────────────────────────────┐
│ Reattend.com (current prod)         │
│ LLM → Groq / OpenAI / Anthropic    │
│ DO NOT TOUCH until Rabbit validated │
└─────────────────────────────────────┘
```

---

## Phase 1: Train Rabbit v1.2 (add missing signals)

### 1.1 Train [LINK] signal
- [ ] Design linking training format (input: source + candidates, output: links with kind/weight)
- [ ] Generate 5,000 linking examples (synthetic)
- [ ] Quality filter
- [ ] Matches current Reattend schema: target_id, kind, weight, explanation
- [ ] Kinds: same_topic, depends_on, contradicts, continuation_of, same_people, causes, temporal

### 1.2 Train [AMBIENT] signal
- [ ] Design ambient recall format (input: screen text + memories, output: alert type + explanation)
- [ ] Generate 3,000 ambient recall examples
- [ ] Quality filter
- [ ] Alert types: contradiction, forgotten_commitment, critical_context, none

### 1.3 Retrain on RunPod
- [ ] Merge v1.1 data (53,901) + new linking + ambient data
- [ ] Train on A100 (~1 hour, ~$2)
- [ ] Test all 12 signals
- [ ] Upload to HuggingFace (reattend/rabbit-v1.2, private)
- [ ] Stop pod

---

## Phase 2: Build Rabbit API Server

### 2.1 Server code
- [ ] FastAPI server with OpenAI-compatible endpoints
- [ ] Load Rabbit model (LoRA adapters on Phi-3.5)
- [ ] Load fastembed for embeddings
- [ ] Endpoints:
  - POST /v1/ingest (triage + extract + summarize + sentiment + importance + embed)
  - POST /v1/query (intent + expand + answer)
  - POST /v1/embed (embedding only)
  - POST /v1/link (linking)
  - POST /v1/ambient (ambient recall)
  - POST /v1/pipeline (everything in one call)
- [ ] Request/response format matches OpenAI chat completions (easy swap)
- [ ] API key authentication
- [ ] Rate limiting
- [ ] Health check endpoint

### 2.2 Docker containerize
- [ ] Dockerfile with CUDA support
- [ ] Model weights baked in or downloaded on startup
- [ ] fastembed bundled
- [ ] docker-compose.yml for easy deployment

---

## Phase 3: Deploy Rabbit on Google Cloud

### 3.1 Setup
- [ ] Create GCP project
- [ ] Enable Compute Engine API
- [ ] Create VM: n1-standard-4 + T4 GPU
- [ ] Install NVIDIA drivers + CUDA
- [ ] Pull Docker image
- [ ] Start Rabbit server
- [ ] Configure firewall (allow port 8000 from reattend.xyz only)
- [ ] Set up HTTPS (Let's Encrypt or GCP load balancer)
- [ ] Test endpoints with curl

### 3.2 Monitoring
- [ ] Health check cron (every 5 min)
- [ ] Auto-restart on crash
- [ ] Log API calls (for retraining flywheel)
- [ ] Track latency per signal
- [ ] Alert if GPU memory > 90%

---

## Phase 4: Deploy Reattend.xyz

### 4.1 Fork & configure
- [ ] Clone reattend.com codebase
- [ ] Update llm.ts: add Rabbit provider as primary
- [ ] Point RABBIT_API_URL to Google Cloud Rabbit server
- [ ] Remove Groq/OpenAI/Anthropic as primary (keep as fallback)
- [ ] Deploy on cheap VPS ($6-12/month: Railway, Render, or DigitalOcean)
- [ ] Configure domain: reattend.xyz
- [ ] Same Supabase DB or separate test DB

### 4.2 Test basic flows
- [ ] Create account on reattend.xyz
- [ ] Connect Gmail / Slack (or paste test content)
- [ ] Verify triage works (memory gets classified)
- [ ] Verify extraction works (entities extracted)
- [ ] Verify search works (embeddings + intent + expand)
- [ ] Verify ask works (conversational answer with citations)
- [ ] Verify linking works (related memories connected)
- [ ] Verify weekly digest works
- [ ] Verify meeting brief works

---

## Phase 5: A/B Comparison

### 5.1 Build comparison tool
- [ ] Script that sends same query to both reattend.com and reattend.xyz
- [ ] Logs both responses side by side
- [ ] UI for thumbs up/down on each response
- [ ] Stores preferences in DB

### 5.2 Run comparison
- [ ] Test with 100 real queries from reattend.com (anonymized)
- [ ] Score each response pair
- [ ] Track per-signal quality:
  - Intent accuracy
  - Triage classification accuracy
  - Answer quality (narrative, citations, follow-ups)
  - Linking relevance
  - Extraction completeness
- [ ] Document where Rabbit wins / loses vs Groq+OpenAI

### 5.3 Quality gates
- [ ] Intent: >95% match with Groq → PASS
- [ ] Triage: >90% correct type classification → PASS
- [ ] Answer: >80% human preference over Groq → PASS
- [ ] Extract: >85% entity recall → PASS
- [ ] If any signal fails gate → retrain with targeted data

---

## Phase 6: Automated Retraining Flywheel

### 6.1 Feedback collection
- [ ] Add thumbs up/down to every Rabbit response in reattend.xyz
- [ ] Log: input, output, signal, feedback, timestamp
- [ ] Store in feedback table

### 6.2 Monthly retrain pipeline
- [ ] Script: collect positive feedback examples from past month
- [ ] Add to training dataset
- [ ] Quality filter
- [ ] Retrain on RunPod (~1 hour, ~$2/month)
- [ ] Deploy new version to Google Cloud
- [ ] A/B test new vs old for 48 hours
- [ ] If new is better → promote to production
- [ ] If worse → rollback

### 6.3 DPO (when enough data)
- [ ] Collect pairs: (question, good_answer, bad_answer) from feedback
- [ ] Need ~1,000 pairs minimum
- [ ] Train with DPO (Direct Preference Optimization)
- [ ] Expected quality jump: 10-20% on answer quality

---

## Phase 7: Ship to Production

### 7.1 Swap reattend.com to Rabbit
- [ ] All quality gates passed
- [ ] Rabbit matches or beats Groq+OpenAI on all signals
- [ ] Update reattend.com llm.ts: Rabbit as primary
- [ ] Keep Groq as fallback for first 2 weeks
- [ ] Monitor error rates and latency
- [ ] Remove Groq/OpenAI API keys after 2 weeks stable

### 7.2 Cost savings confirmed
- [ ] OpenAI API spend → $0
- [ ] Groq API spend → $0
- [ ] Anthropic API spend → $0
- [ ] Rabbit server cost documented
- [ ] Net savings calculated

---

## Phase 8: Enterprise & Landing Page

### 8.1 rabbit.reattend.com
- [ ] Landing page: what Rabbit does, live demo, pricing
- [ ] API docs (Swagger/OpenAPI)
- [ ] "Powered by Rabbit" badge
- [ ] Enterprise contact form

### 8.2 Benchmarks (for pitch deck)
- [ ] Run Rabbit vs GPT-4o-mini vs Llama 3.3 vs base Phi-3.5
- [ ] 100 test cases across all signals
- [ ] Publish results on landing page
- [ ] Include in pitch deck "Technology" slide

### 8.3 Enterprise offering
- [ ] Docker image for on-prem deployment
- [ ] Enterprise API tier with SLA
- [ ] Pricing: $500-2000/month API, $50-200K/year on-prem
- [ ] First pilot client

---

## Signals Inventory (v1.2 target)

| # | Signal | Status | Purpose |
|---|---|---|---|
| 1 | INTENT | v1.1 ✅ | Classify user query type |
| 2 | EXTRACT | v1.1 ✅ | Pull entities, dates, decisions |
| 3 | TRIAGE | v1.1 ✅ | Classify + summarize content |
| 4 | EXPAND | v1.1 ✅ | Expand vague queries |
| 5 | ANSWER | v1.1 ✅ | Conversational response with citations |
| 6 | SUMMARIZE | v1.1 ✅ | Standalone rich summary |
| 7 | SENTIMENT | v1.1 ✅ | Tone classification |
| 8 | IMPORTANCE | v1.1 ✅ | Score 1-5 with reason |
| 9 | MULTITURN | v1.1 ✅ | Follow-up conversation |
| 10 | DONTKNOW | v1.1 ✅ | Graceful gap handling |
| 11 | LINK | v1.2 🔲 | Memory relationship detection |
| 12 | AMBIENT | v1.2 🔲 | Contradiction/commitment detection |

---

## Timeline

| Week | What |
|---|---|
| Week 1 | Train v1.2 (link + ambient signals) |
| Week 2 | Build Rabbit API server + deploy on Google Cloud |
| Week 3 | Deploy reattend.xyz on cheap VPS |
| Week 4 | A/B comparison + first retrain cycle |
| Week 5 | Quality gates check → if pass, swap prod |
| Week 6+ | Flywheel running, enterprise landing page |
