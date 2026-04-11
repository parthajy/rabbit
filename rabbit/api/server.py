"""
Rabbit API Server.

The public-facing HTTP API. Two core endpoints:
    POST /v1/remember  — ingest content into memory
    POST /v1/ask       — query memories

Plus management endpoints for memories, stats, and health.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import json

from fastapi import Depends, FastAPI, File, Form, HTTPException, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from rabbit.api.auth import InvalidKeyError, KeyManager, RateLimitError, Tenant, TIER_LIMITS
from rabbit.core.engine import RabbitCore

# ── Config ─────────────────────────────────────────────────────────────────

MODEL_PATH = os.environ.get("RABBIT_MODEL", "reattend/rabbit-v1.4-merged")
STORAGE_PATH = os.environ.get("RABBIT_STORAGE", "~/.rabbit/data")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Rabbit API",
    description="Memory infrastructure for the world. Two operations: remember and ask.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ─────────────────────────────────────────────────────


@app.exception_handler(InvalidKeyError)
async def invalid_key_handler(request, exc):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": str(exc)})


# ── State ──────────────────────────────────────────────────────────────────

key_manager = KeyManager(db_path=os.environ.get("RABBIT_KEYS_DB", "~/.rabbit/keys.db"))
security = HTTPBearer()

# Cache of RabbitCore instances per tenant
_engines: dict[str, RabbitCore] = {}


def _get_engine(tenant_id: str) -> RabbitCore:
    """Get or create a RabbitCore engine for a tenant."""
    if tenant_id not in _engines:
        _engines[tenant_id] = RabbitCore(
            model_path=MODEL_PATH,
            storage_path=STORAGE_PATH,
            tenant_id=tenant_id,
            hf_token=HF_TOKEN,
        )
    return _engines[tenant_id]


async def get_tenant(credentials: HTTPAuthorizationCredentials = Security(security)) -> Tenant:
    """Validate API key and return tenant."""
    return key_manager.validate_key(credentials.credentials)


# ── Request Models ─────────────────────────────────────────────────────────


class RememberRequest(BaseModel):
    content: str
    source: str = "unknown"
    metadata: dict[str, Any] | None = None


class AskRequest(BaseModel):
    question: str
    limit: int = 5
    stream: bool = False
    reasoning: bool = False


class CheckRequest(BaseModel):
    context: str


class CompileRequest(BaseModel):
    entity: str


# ── Core Endpoints ─────────────────────────────────────────────────────────


@app.post("/v1/remember")
async def remember(req: RememberRequest, tenant: Tenant = Depends(get_tenant)):
    """Ingest content into memory.

    Runs the full pipeline: triage → extract → summarize → sentiment →
    importance → embed → store → link.
    """
    key_manager.check_rate_limit(tenant, "remember")
    engine = _get_engine(tenant.tenant_id)

    memory = engine.remember(
        content=req.content,
        source=req.source,
        metadata=req.metadata or {},
    )

    return {
        "id": memory.id,
        "summary": memory.summary,
        "triage_type": memory.triage_type,
        "tags": memory.tags,
        "extraction": {
            "people": memory.extraction.people,
            "organizations": memory.extraction.organizations,
            "decisions": memory.extraction.decisions,
            "action_items": memory.extraction.action_items,
            "dates": memory.extraction.dates,
            "topics": memory.extraction.topics,
        },
        "sentiment": memory.sentiment,
        "importance": memory.importance,
        "importance_reason": memory.importance_reason,
        "links": [
            {"target_id": l.target_id, "kind": l.kind, "weight": l.weight}
            for l in memory.links
        ],
        "latency_ms": memory.metadata.get("ingestion_latency_ms", 0),
    }


@app.post("/v1/remember/file")
async def remember_file(
    file: UploadFile = File(...),
    source: str = Form("unknown"),
    tenant: Tenant = Depends(get_tenant),
):
    """Ingest a file into memory.

    Supports: audio (.mp3, .wav), PDF, DOCX, PPTX, images (.png, .jpg),
    HTML, Markdown, code, email (.eml), calendar (.ics).
    """
    key_manager.check_rate_limit(tenant, "remember_file")

    # Check file size
    max_size = tenant.limits["max_file_size_mb"] * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {tenant.limits['max_file_size_mb']}MB",
        )

    # Save to temp file for processing
    import tempfile
    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        engine = _get_engine(tenant.tenant_id)
        memories = engine.remember_file(tmp_path, source=source)

        return {
            "memories": [
                {
                    "id": m.id,
                    "summary": m.summary,
                    "source_type": m.metadata.get("source_type", "unknown"),
                }
                for m in memories
            ],
            "count": len(memories),
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.post("/v1/ask")
async def ask(req: AskRequest, tenant: Tenant = Depends(get_tenant)):
    """Ask a question over stored memories.

    Runs: intent → expand → retrieve → graph walk → answer.
    Set stream=true for Server-Sent Events streaming.
    """
    key_manager.check_rate_limit(tenant, "ask")
    engine = _get_engine(tenant.tenant_id)

    if req.stream:
        return _stream_ask(engine, req.question, req.limit)

    answer = engine.ask(question=req.question, limit=req.limit, reasoning=req.reasoning)

    return {
        "text": answer.text,
        "sources": answer.sources,
        "followups": answer.followups,
        "intent": answer.intent,
        "expanded_query": answer.expanded_query,
        "memories_used": len(answer.memories_used),
        "latency_ms": answer.latency_ms,
    }


def _stream_ask(engine: RabbitCore, question: str, limit: int):
    """Stream the ask response as Server-Sent Events.

    Sends incremental events as each pipeline stage completes,
    then streams the answer text in chunks.
    """
    import asyncio

    async def event_generator():
        start = time.time()

        # Stage 1: Intent
        intent = engine.llm.generate("intent", question).strip().lower()
        yield {"event": "intent", "data": json.dumps({"intent": intent})}

        # Stage 2: Expand
        expanded = engine.llm.generate("expand", question)
        yield {"event": "expand", "data": json.dumps({"expanded_query": expanded})}

        # Stage 3: Retrieve
        query_embedding = engine._embed(expanded)
        candidate_memories = engine.store.search_hybrid(
            query=expanded, query_embedding=query_embedding, limit=limit * 2,
        )

        # Graph walk
        graph_memories = []
        for mem in candidate_memories[:3]:
            connected = engine.store.get_connected(mem.id, hops=1)
            graph_memories.extend(connected)
        seen_ids = {m.id for m in candidate_memories}
        for gm in graph_memories:
            if gm.id not in seen_ids:
                candidate_memories.append(gm)
                seen_ids.add(gm.id)

        # Rerank
        from rabbit.core import reranker
        if reranker.is_available() and len(candidate_memories) > limit:
            docs = [{"text": m.summary or m.content[:512], "memory": m} for m in candidate_memories]
            reranked = reranker.rerank(question, docs, limit=limit)
            top_memories = [d["memory"] for d in reranked]
        else:
            top_memories = candidate_memories[:limit]

        yield {"event": "retrieve", "data": json.dumps({"memories_found": len(top_memories)})}

        if not top_memories:
            answer_text = engine.llm.generate("dontknow", f"Question: {question}\nMemories: [None available]")
            yield {"event": "answer", "data": json.dumps({"text": answer_text})}
            yield {"event": "done", "data": json.dumps({"latency_ms": int((time.time() - start) * 1000)})}
            return

        # Stage 4: Generate answer
        memory_text = "\n".join(
            f"[{i+1}] {m.summary or m.content[:300]}"
            for i, m in enumerate(top_memories)
        )
        answer_input = f"Question: {question}\n\nMemories:\n{memory_text}"
        answer_text = engine.llm.generate("answer", answer_input)

        # Stream answer in chunks (~50 char chunks to simulate token streaming)
        chunk_size = 50
        for i in range(0, len(answer_text), chunk_size):
            chunk = answer_text[i:i + chunk_size]
            yield {"event": "answer_chunk", "data": json.dumps({"chunk": chunk})}
            await asyncio.sleep(0.01)  # Small delay for smooth streaming

        # Final event with full response
        from rabbit.core.engine import _parse_answer_sections
        sources, followups = _parse_answer_sections(answer_text, top_memories)

        yield {"event": "done", "data": json.dumps({
            "text": answer_text,
            "sources": sources,
            "followups": followups,
            "intent": intent,
            "expanded_query": expanded,
            "memories_used": len(top_memories),
            "latency_ms": int((time.time() - start) * 1000),
        })}

    return EventSourceResponse(event_generator())


@app.post("/v1/check")
async def check(req: CheckRequest, tenant: Tenant = Depends(get_tenant)):
    """Check for contradictions or forgotten commitments."""
    key_manager.check_rate_limit(tenant, "check")
    engine = _get_engine(tenant.tenant_id)

    alert = engine.check(context=req.context)

    return {
        "show": alert.show,
        "reason": alert.reason,
        "context": alert.context,
        "memory_indices": alert.memory_indices,
    }


# ── Memory Management ─────────────────────────────────────────────────────


@app.get("/v1/memories")
async def list_memories(
    limit: int = 50,
    offset: int = 0,
    source: str | None = None,
    tenant: Tenant = Depends(get_tenant),
):
    """List stored memories."""
    engine = _get_engine(tenant.tenant_id)
    memories = engine.store.list_memories(limit=limit, offset=offset, source=source)

    return {
        "memories": [m.to_dict() for m in memories],
        "count": len(memories),
        "total": engine.store.count(),
    }


@app.get("/v1/memories/{memory_id}")
async def get_memory(memory_id: str, tenant: Tenant = Depends(get_tenant)):
    """Get a specific memory."""
    engine = _get_engine(tenant.tenant_id)
    memory = engine.get_memory(memory_id)

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return memory.to_dict()


@app.delete("/v1/memories/{memory_id}")
async def delete_memory(memory_id: str, tenant: Tenant = Depends(get_tenant)):
    """Delete a memory."""
    engine = _get_engine(tenant.tenant_id)
    deleted = engine.forget(memory_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {"deleted": True, "id": memory_id}


@app.get("/v1/graph/{memory_id}")
async def get_graph(memory_id: str, hops: int = 2, tenant: Tenant = Depends(get_tenant)):
    """Get a memory's connections in the knowledge graph."""
    engine = _get_engine(tenant.tenant_id)

    memory = engine.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    connected = engine.store.get_connected(memory_id, hops=hops)

    return {
        "memory": memory.to_dict(),
        "connections": [m.to_dict() for m in connected],
        "total_connections": len(connected),
    }


# ── Knowledge Base ─────────────────────────────────────────────────────────


@app.post("/v1/compile/{entity}")
async def compile_entity(entity: str, tenant: Tenant = Depends(get_tenant)):
    """Compile a wiki page for an entity."""
    key_manager.check_rate_limit(tenant, "compile")
    engine = _get_engine(tenant.tenant_id)

    wiki_page = engine.compile(entity)

    return {"entity": entity, "content": wiki_page}


@app.post("/v1/lint")
async def lint(tenant: Tenant = Depends(get_tenant)):
    """Run a health audit on stored memories."""
    key_manager.check_rate_limit(tenant, "lint")
    engine = _get_engine(tenant.tenant_id)

    report = engine.lint()

    return {
        "total_memories": report.total_memories,
        "health_score": report.health_score,
        "contradictions": report.contradictions,
        "stale_items": report.stale_items,
        "knowledge_gaps": report.knowledge_gaps,
    }


# ── Stats & Health ─────────────────────────────────────────────────────────


@app.get("/v1/stats")
async def stats(tenant: Tenant = Depends(get_tenant)):
    """Get usage and memory statistics."""
    engine = _get_engine(tenant.tenant_id)
    store_stats = engine.stats()
    usage = key_manager.get_usage(tenant.tenant_id)

    return {
        **store_stats,
        **usage,
        "tier": tenant.tier,
        "limits": tenant.limits,
    }


@app.get("/health")
async def health():
    """Service health check."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "model": MODEL_PATH,
    }


# ── Key Management (admin) ────────────────────────────────────────────────


@app.post("/v1/keys/generate")
async def generate_key(tier: str = "test"):
    """Generate a new API key. For initial setup — will be protected later."""
    if tier not in ("test", "live"):
        raise HTTPException(status_code=400, detail="Tier must be 'test' or 'live'")

    key, tenant_id = key_manager.generate_key(tier=tier)

    return {
        "key": key,
        "tenant_id": tenant_id,
        "tier": tier,
        "limits": TIER_LIMITS[tier],
        "message": f"Save this key — it won't be shown again. Use as: Authorization: Bearer {key}",
    }


# ── Legacy Compatibility ──────────────────────────────────────────────────
# Keep /v1/chat/completions for backward compatibility with existing Reattend


@app.post("/v1/chat/completions")
async def chat_completions(req: dict, tenant: Tenant = Depends(get_tenant)):
    """OpenAI-compatible endpoint for backward compatibility."""
    from rabbit.core.signals import SIGNAL_PREFIXES

    messages = req.get("messages", [])
    signal = req.get("signal", "answer")
    user_content = ""

    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            for sig, prefix in SIGNAL_PREFIXES.items():
                if content.startswith(prefix):
                    signal = sig
                    content = content[len(prefix):].strip()
                    break
            user_content = content
            break

    if not user_content:
        raise HTTPException(status_code=400, detail="No user message found")

    engine = _get_engine(tenant.tenant_id)
    start = time.time()
    response_text = engine.llm.generate(signal, user_content)

    return {
        "id": f"rabbit-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "rabbit-v1.4",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop",
        }],
        "signal": signal,
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.post("/v1/embeddings")
async def embeddings(req: dict, tenant: Tenant = Depends(get_tenant)):
    """Generate embeddings. Backward compatible."""
    engine = _get_engine(tenant.tenant_id)
    texts = req.get("input", [])
    if isinstance(texts, str):
        texts = [texts]

    model = engine._get_embed_model()
    vectors = list(model.embed(texts))

    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()}
            for i, v in enumerate(vectors)
        ],
        "model": "nomic-embed-text-v1.5",
    }


# ── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Pre-load the model on startup."""
    # Create a default engine to trigger model loading
    default_engine = _get_engine("_warmup")
    default_engine.llm.load()
    print("\nRabbit API Server ready!")
    print(f"  Model: {MODEL_PATH}")
    print(f"  Storage: {STORAGE_PATH}")
    print(f"  Endpoints: /v1/remember, /v1/ask, /v1/check")
    print(f"  Generate a key: POST /v1/keys/generate")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
