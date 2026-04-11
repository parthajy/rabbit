# Reattend — Your AI Memory

> Reattend remembers everything so you don't have to.
> Powered by Rabbit, Reattend's own memory AI.

---

## Architecture

```
reattend.ai              → Next.js app (landing page + SaaS)
rabbit.reattend.ai       → Rabbit landing page + API key signup + docs
api.rabbit.reattend.ai   → Rabbit API (GCP T4, already running)
```

Hosting:
- **DO Droplet ($12/month):** reattend.ai + rabbit.reattend.ai (both Next.js)
- **GCP T4 ($142/month):** api.rabbit.reattend.ai (the AI engine)

Reattend is a Rabbit SDK client. It calls `api.rabbit.reattend.ai` for everything.
No AI logic lives in the Reattend codebase — Rabbit handles it all.

---

## rabbit.reattend.ai (Build First)

The Rabbit developer platform. Where developers get API keys and docs.

### Pages

| Page | URL | What It Does |
|------|-----|-------------|
| Landing | `/` | What is Rabbit, pitch, code examples, "Get API Key" |
| Auth | `/login` | Resend OTP login (email → 6-digit code) |
| Keys | `/dashboard/keys` | Generate rab_test/rab_live keys, see active keys |
| Usage | `/dashboard/usage` | Calls today/month, memory count, latency |
| Test Console | `/dashboard/playground` | Type remember/ask, see live results |
| Docs | `/docs` | API reference, quickstart, guides |

### Tech

- Next.js 14 (App Router)
- Tailwind CSS
- Resend OTP for auth
- Calls Rabbit API for all AI operations
- PostgreSQL (Neon free tier) for user accounts + key mapping

---

## reattend.ai (Build After rabbit.reattend.ai Works)

The consumer/team product. Where individuals and teams use their AI memory.

### Core Flow

```
1. User signs up (Resend OTP)
2. Creates a project ("Work", "Personal", "Project Phoenix")
3. Adds memories:
   - Type/paste text
   - Upload files (PDF, audio, images, docs)
   - Paste a URL (scraped and ingested)
   - Later: auto-ingest from Gmail, Slack, Calendar
4. Rabbit processes everything automatically:
   - Classify → Extract → Summarize → Sentiment → Importance → Embed → Link
   - Agent log shows each step with timing
   - Memory appears in timeline + knowledge graph
5. User asks questions across all memories
   - Conversational answers with citations
   - Reasoning mode for deep analysis (Groq under the hood, invisible to user)
6. Rabbit surfaces insights proactively:
   - Contradictions detected
   - Daily digest
   - Weekly health report
```

### Features

#### Memory Creation
- **Text input** — paste meeting notes, thoughts, decisions
- **File upload** — PDF, audio (.mp3, .wav), images, DOCX, PPTX
- **URL ingestion** — paste a link, Rabbit scrapes and remembers it
- **Quick capture** — keyboard shortcut, type, hit enter, done

#### Memory Intelligence (visible to user)
- **Agent log** — shows what Rabbit did: "Classified as meeting (240ms), Extracted 3 people (450ms), Linked to 2 memories (500ms)"
- **Knowledge graph** — force-directed graph showing all memories and their connections. Click nodes to explore. Filter by project/source/person.
- **Memory card** — each memory shows: summary, type, tags, people, decisions, action items, importance, sentiment, links

#### Ask (Conversational)
- Chat interface across all memories
- Answers with [1][2] citations linking to source memories
- Follow-up questions suggested
- "Deep think" toggle → reasoning mode (Groq, invisible to user)
- Users do NOT know Groq exists. It's all "Rabbit" to them.

#### Auto-Compiled Pages
- **People pages** — click any person → auto-generated dossier (interactions, decisions, action items)
- **Project pages** — click any project → full timeline, status, blockers, decisions
- **Topic pages** — click any topic → everything known, across all sources

#### Proactive Intelligence
- **Daily digest** — morning email: "Here's what happened yesterday"
- **Contradiction alerts** — "You told Sarah $50K but the board approved $40K"
- **Weekly health report** — contradictions, stale items, knowledge gaps
- **Ambient mode** (desktop app, later) — watches your screen, pops up relevant context

#### Auto-Ingestion (later, via connectors)
- **Gmail** — emails auto-ingested, decisions and action items extracted
- **Google Calendar** — meetings auto-ingested with attendees and agenda
- **Slack** — messages and threads auto-ingested
- **Obsidian** — vault synced, notes become queryable
- **Chrome extension** — save any webpage to memory
- **Desktop app** — capture anything on screen

### What Rabbit Does vs What the User Sees

| Under the Hood (Rabbit) | What User Sees |
|--------------------------|---------------|
| TRIAGE signal (300ms) | "Type: Meeting" badge on memory card |
| EXTRACT signal (450ms) | People, decisions, action items shown on card |
| SUMMARIZE signal (400ms) | Summary paragraph at top of card |
| SENTIMENT signal (240ms) | Tone indicator (emoji or color) |
| IMPORTANCE signal (300ms) | Priority badge (1-5 stars) |
| EMBED + Qdrant | "Related memories" sidebar |
| LINK signal (500ms) | Lines in knowledge graph |
| INTENT + EXPAND | Better search results |
| ANSWER signal | Chat response with citations |
| Groq (reasoning mode) | Same chat, deeper analysis (user doesn't know) |
| AMBIENT signal | Pop-up alert: "Contradiction detected" |
| COMPILE | Auto-generated people/project/topic pages |
| LINT | Weekly health report email |

### Agent Log (transparency feature)

Every memory creation shows a collapsible log:

```
🤖 Rabbit processed your memory in 2.1s

  ✓ Classified as: meeting                    240ms
  ✓ Extracted: Sarah, Tom, Acme Corp          450ms
  ✓ Decisions: "Delay launch to March 15"     —
  ✓ Action items: "Tom to fix auth by Monday" —
  ✓ Summarized: "Launch delayed to March..."  380ms
  ✓ Tone: tense                               240ms
  ✓ Importance: 4/5 — "key launch decision"   300ms
  ✓ Linked to: 2 related memories             500ms
      → "Q1 Budget Meeting" (same_topic)
      → "Auth Security Review" (depends_on)
```

---

## Pricing

| Tier | Price | Memories | Asks | Projects | Features |
|------|-------|----------|------|----------|----------|
| **Free** | $0 | 500 | 20/day | 1 | Core features, agent log |
| **Pro** | $15/month | 50,000 | Unlimited | 5 | + Reasoning mode, daily digest, compiled pages |
| **Team** | $12/user/mo (min 3) | Unlimited | Unlimited | Unlimited | + Shared projects, team memory, admin |
| **Enterprise** | Custom | Unlimited | Unlimited | Unlimited | + On-prem, SSO, RBAC, custom training |

---

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Framework | Next.js 14 (App Router) | SSR, API routes, one codebase |
| Styling | Tailwind CSS | Fast, responsive |
| Auth | Resend OTP (email) | Simple, no passwords |
| Database | PostgreSQL (Neon) | Users, projects, key mapping |
| AI Backend | Rabbit API (api.rabbit.reattend.ai) | Our own model, all intelligence |
| Reasoning | Groq (llama-3.3-70b) | Deep analysis, invisible to user |
| Payments | Stripe | Subscriptions, usage billing |
| Graph Viz | react-force-graph | Knowledge graph visualization |
| Email | Resend | OTP, daily digest, health reports |
| Hosting | DO Droplet ($12/month) | Next.js app |

---

## Build Order

### Phase 1: rabbit.reattend.ai (this week)
1. Landing page — what is Rabbit, code examples, pitch
2. Resend OTP auth
3. API key generation (rab_test → dashboard)
4. Basic usage dashboard

### Phase 2: reattend.ai MVP (next 2 weeks)
1. Landing page — what is Reattend, pitch, signup
2. Auth (same Resend OTP)
3. Projects — create, list, switch
4. Memory creation — text input + file upload
5. Memory cards — summary, tags, people, importance, agent log
6. Ask — conversational Q&A over memories
7. Memory timeline — chronological view
8. Knowledge graph — basic force-directed visualization

### Phase 3: Polish + Launch (week after)
1. URL ingestion (paste link → scrape → remember)
2. People/project/topic compiled pages
3. Daily digest email
4. Stripe integration (free → pro upgrade)
5. Docs at rabbit.reattend.ai/docs
6. Launch: Product Hunt, Hacker News, Twitter/X

### Phase 4: Growth
1. Gmail connector
2. Slack connector
3. Google Calendar connector
4. Chrome extension
5. Desktop app (Electron or Tauri)
6. Teams features
7. Weekly health report (LINT)

---

## Domain Setup

| Domain | Points To | What |
|--------|----------|------|
| reattend.ai | DO Droplet | Reattend SaaS |
| rabbit.reattend.ai | DO Droplet | Rabbit developer platform |
| api.rabbit.reattend.ai | GCP T4 (35.200.167.8) | Rabbit API |
| reattend.com | Redirect → reattend.ai | Legacy redirect |

---

## The Vision

Reattend is the first AI product where the AI owns the memory.

Not a chatbot that forgets. Not a notes app with AI sprinkled on.
A system that captures, understands, links, and reasons over everything
you and your team have ever discussed, decided, or done.

Powered entirely by Rabbit — our own model, our own infrastructure,
our own training data. No dependency on OpenAI. No per-token costs.
Just memory that gets smarter with every interaction.
