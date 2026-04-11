"""
Rabbit Core Engine.

The central class that ties together:
- Input processors (text, audio, PDF, images, etc.)
- LLM signals (12 specialized tasks)
- Storage (Qdrant vectors + SQLite metadata/graph)
- Retrieval (hybrid search + graph walk + reranking)

Two core operations: remember() and ask().
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from rabbit.core.llm import RabbitLLM, parse_json_output
from rabbit.core.types import (
    AmbientAlert,
    Answer,
    Extraction,
    HealthReport,
    Memory,
    MemoryLink,
    ProcessedInput,
)
from rabbit.processors.router import process_input
from rabbit.storage.memory_store import MemoryStore


class RabbitCore:
    """The Rabbit memory engine.

    Usage:
        rabbit = RabbitCore()
        rabbit.remember("Sarah delayed the launch to March 15.", source="meeting")
        answer = rabbit.ask("When is the launch?")
        print(answer.text)
    """

    def __init__(
        self,
        model_path: str = "reattend/rabbit-v1.4-merged",
        storage_path: str = "~/.rabbit/data",
        tenant_id: str = "default",
        hf_token: str = "",
        device: str = "auto",
    ):
        self.llm = RabbitLLM(model_path=model_path, device=device, hf_token=hf_token)
        self.store = MemoryStore(storage_path=storage_path, tenant_id=tenant_id)
        self.tenant_id = tenant_id

        # Embedding model (lazy loaded)
        self._embed_model = None

    def _get_embed_model(self):
        if self._embed_model is None:
            from fastembed import TextEmbedding
            self._embed_model = TextEmbedding(model_name="nomic-ai/nomic-embed-text-v1.5")
        return self._embed_model

    def _embed(self, text: str) -> list[float]:
        model = self._get_embed_model()
        vectors = list(model.embed([text]))
        return vectors[0].tolist()

    # ── REMEMBER ───────────────────────────────────────────────────────────

    def remember(self, content: str, source: str = "unknown", metadata: dict | None = None) -> Memory:
        """Ingest text content into memory.

        Runs the full pipeline: triage → extract → summarize → sentiment →
        importance → embed → store → link.

        Args:
            content: Text content to remember.
            source: Source label (meeting, email, slack, note, etc.)
            metadata: Additional metadata.

        Returns:
            The stored Memory object.
        """
        start = time.time()
        metadata = metadata or {}

        # Create memory object
        memory = Memory(content=content, source=source, metadata=metadata, tenant_id=self.tenant_id)

        # Run all ingestion signals
        memory = self._run_ingestion_pipeline(memory)

        # Generate embedding
        memory.embedding = self._embed(content)

        # Find and store links to existing memories
        memory.links = self._find_links(memory)

        # Store everything
        self.store.store(memory)

        latency = int((time.time() - start) * 1000)
        memory.metadata["ingestion_latency_ms"] = latency

        return memory

    def remember_file(self, file_path: str | Path, source: str = "unknown", metadata: dict | None = None) -> list[Memory]:
        """Ingest a file into memory.

        Supports: audio (.mp3, .wav, .m4a), PDF, DOCX, PPTX, XLSX,
        images (.png, .jpg), HTML, Markdown, code, email (.eml), calendar (.ics).

        For long documents, creates multiple memories (one per chunk).

        Args:
            file_path: Path to the file.
            source: Source label.
            metadata: Additional metadata.

        Returns:
            List of stored Memory objects (one per chunk, or one if short).
        """
        metadata = metadata or {}

        # Process the file into text
        processed = process_input(file_path, source=source, metadata=metadata)

        # If the document was chunked, create a memory for each chunk
        if processed.chunks:
            memories = []
            for i, chunk in enumerate(processed.chunks):
                chunk_metadata = {
                    **processed.metadata,
                    "chunk_index": i,
                    "total_chunks": len(processed.chunks),
                    "source_type": processed.source_type,
                }
                memory = self.remember(chunk, source=source, metadata=chunk_metadata)
                memories.append(memory)
            return memories
        else:
            memory = self.remember(
                processed.text,
                source=source,
                metadata={**processed.metadata, "source_type": processed.source_type},
            )
            return [memory]

    def _run_ingestion_pipeline(self, memory: Memory) -> Memory:
        """Run all ingestion signals on a memory."""
        content = memory.content

        # 1. Triage — classify content type + summary + tags
        triage_raw = self.llm.generate("triage", content)
        triage = parse_json_output(triage_raw)
        memory.triage_type = _clean_triage_type(triage.get("type", ""))
        if not memory.summary:
            memory.summary = triage.get("summary", "")
        memory.tags = _clean_tags(triage.get("tags", []))

        # 2. Extract — pull out entities and facts
        extract_raw = self.llm.generate("extract", content)
        ext = parse_json_output(extract_raw)
        memory.extraction = Extraction(
            people=ext.get("people", []),
            organizations=ext.get("organizations", []),
            decisions=ext.get("decisions", []),
            action_items=ext.get("action_items", []),
            dates=ext.get("dates", []),
            topics=ext.get("topics", []),
        )

        # 3. Summarize — rich standalone summary
        raw_summary = self.llm.generate("summarize", content)
        memory.summary = _clean_summary(raw_summary)

        # 4. Sentiment — tone classification
        sentiment_raw = self.llm.generate("sentiment", content).strip().lower()
        # Model sometimes adds explanation after the word — take first word only
        memory.sentiment = sentiment_raw.split()[0] if sentiment_raw else "neutral"

        # 5. Importance — score 1-5
        importance_raw = self.llm.generate("importance", content)
        importance = parse_json_output(importance_raw)
        try:
            memory.importance = max(1, min(5, int(importance.get("score", 3))))
        except (ValueError, TypeError):
            memory.importance = 3
        memory.importance_reason = importance.get("reason", "")

        return memory

    def _find_links(self, memory: Memory) -> list[MemoryLink]:
        """Find links between a new memory and existing memories."""
        # Get candidate memories via vector search
        candidates = self.store.search_vector(memory.embedding, limit=10)
        if not candidates:
            return []

        # Build context for the LINK signal
        candidate_memories = []
        for mem_id, _ in candidates:
            candidate = self.store.get(mem_id)
            if candidate:
                candidate_memories.append(candidate)

        if not candidate_memories:
            return []

        # Format for the model
        source_text = f"Source: {memory.content[:500]}"
        candidate_text = "\n".join(
            f"[{i+1}] (id={m.id}) {m.content[:200]}"
            for i, m in enumerate(candidate_memories[:5])
        )
        link_input = f"{source_text}\n\nCandidates:\n{candidate_text}"

        link_raw = self.llm.generate("link", link_input)
        link_data = parse_json_output(link_raw)

        # Handle both {"links": [...]} and bare [...]
        if isinstance(link_data, list):
            link_list = link_data
        elif isinstance(link_data, dict):
            link_list = link_data.get("links", [])
        else:
            link_list = []

        links = []
        for link_info in link_list:
            # Map the index-based target_id to actual memory IDs
            target_id = link_info.get("target_id", "")
            # If model returned an index like "1", map to actual ID
            if target_id.isdigit():
                idx = int(target_id) - 1
                if 0 <= idx < len(candidate_memories):
                    target_id = candidate_memories[idx].id
                else:
                    continue

            # Check if target_id exists in candidates
            valid_ids = {m.id for m in candidate_memories}
            if target_id not in valid_ids:
                # Try to match by prefix
                for m in candidate_memories:
                    if m.id.startswith(target_id) or target_id.startswith(m.id):
                        target_id = m.id
                        break
                else:
                    continue

            links.append(MemoryLink(
                target_id=target_id,
                kind=link_info.get("kind", "related_to"),
                weight=float(link_info.get("weight", 0.5)),
                explanation=link_info.get("explanation", ""),
            ))

            # Store bidirectional link
            self.store.store_link(
                memory.id, target_id,
                link_info.get("kind", "related_to"),
                float(link_info.get("weight", 0.5)),
                link_info.get("explanation", ""),
            )

        return links

    # ── ASK ─────────────────────────────────────────────────────────────────

    def ask(self, question: str, limit: int = 5) -> Answer:
        """Ask a question over stored memories.

        Runs: intent → expand → retrieve (hybrid) → graph walk → answer.

        Args:
            question: Natural language question.
            limit: Max number of memories to use for answering.

        Returns:
            Answer object with text, sources, and follow-up suggestions.
        """
        start = time.time()

        # 1. Classify intent
        intent = self.llm.generate("intent", question).strip().lower()

        # 2. Expand query
        expanded = self.llm.generate("expand", question)

        # 3. Embed the expanded query
        query_embedding = self._embed(expanded)

        # 4. Hybrid search: vector + BM25 + importance + recency
        candidate_memories = self.store.search_hybrid(
            query=expanded,
            query_embedding=query_embedding,
            limit=limit * 2,
        )

        # 5. Graph walk — get connected memories (1 hop)
        graph_memories = []
        for mem in candidate_memories[:3]:  # Walk from top 3 results
            connected = self.store.get_connected(mem.id, hops=1)
            graph_memories.extend(connected)

        # Deduplicate and merge
        seen_ids = {m.id for m in candidate_memories}
        for gm in graph_memories:
            if gm.id not in seen_ids:
                candidate_memories.append(gm)
                seen_ids.add(gm.id)

        # 6. Rerank candidates (if reranker available, otherwise just take top-K)
        from rabbit.core import reranker
        if reranker.is_available() and len(candidate_memories) > limit:
            docs = [{"text": m.summary or m.content[:512], "memory": m} for m in candidate_memories]
            reranked = reranker.rerank(question, docs, limit=limit)
            top_memories = [d["memory"] for d in reranked]
        else:
            top_memories = candidate_memories[:limit]

        if not top_memories:
            # No memories found — use DONTKNOW signal
            answer_text = self.llm.generate("dontknow", f"Question: {question}\nMemories: [None available]")
            return Answer(
                text=answer_text,
                intent=intent,
                expanded_query=expanded,
                latency_ms=int((time.time() - start) * 1000),
            )

        # 7. Build context and generate answer
        memory_text = "\n".join(
            f"[{i+1}] {m.summary or m.content[:300]}"
            for i, m in enumerate(top_memories)
        )
        answer_input = f"Question: {question}\n\nMemories:\n{memory_text}"

        answer_text = self.llm.generate("answer", answer_input)

        # 8. Parse sources and follow-ups from answer
        sources, followups = _parse_answer_sections(answer_text, top_memories)

        return Answer(
            text=answer_text,
            sources=sources,
            followups=followups,
            intent=intent,
            expanded_query=expanded,
            memories_used=top_memories,
            latency_ms=int((time.time() - start) * 1000),
        )

    # ── CHECK (Ambient) ───────────────────────────────────────────────────

    def check(self, context: str) -> AmbientAlert:
        """Check for contradictions or forgotten commitments.

        Args:
            context: Current screen text or conversation context.

        Returns:
            AmbientAlert with show=True if an alert should be displayed.
        """
        # Find related memories
        context_embedding = self._embed(context)
        related = self.store.search_hybrid(
            query=context,
            query_embedding=context_embedding,
            limit=5,
        )

        if not related:
            return AmbientAlert(show=False)

        memory_text = "\n".join(
            f"[{i+1}] {m.summary or m.content[:300]}"
            for i, m in enumerate(related)
        )
        ambient_input = f"Screen context: {context}\n\nRelated memories:\n{memory_text}"

        result_raw = self.llm.generate("ambient", ambient_input)
        result = parse_json_output(result_raw)

        return AmbientAlert(
            show=result.get("show", False),
            reason=result.get("reason", ""),
            context=result.get("context", ""),
            memory_indices=result.get("memory_indices", []),
        )

    # ── COMPILE ────────────────────────────────────────────────────────────

    def compile(self, entity: str) -> str:
        """Compile a wiki page for an entity (person, project, topic).

        Searches all memories mentioning the entity and generates a
        comprehensive summary page.

        Args:
            entity: The entity name to compile (e.g., "Sarah", "Project Phoenix").

        Returns:
            Compiled wiki page text.
        """
        # Search for all memories mentioning this entity
        entity_embedding = self._embed(entity)
        memories = self.store.search_hybrid(
            query=entity,
            query_embedding=entity_embedding,
            limit=20,
        )

        if not memories:
            return f"No memories found about '{entity}'."

        memory_text = "\n".join(
            f"[{i+1}] ({m.source}, {_format_timestamp(m.created_at)}) {m.summary or m.content[:300]}"
            for i, m in enumerate(memories)
        )

        compile_prompt = (
            f"Compile everything known about '{entity}' into a comprehensive wiki page. "
            f"Include: role/description, key decisions, action items, relationships, "
            f"timeline of events. Use **bold** for key facts. Cite sources as [1][2][3].\n\n"
            f"Memories:\n{memory_text}"
        )

        return self.llm.generate("answer", compile_prompt)

    # ── LINT ───────────────────────────────────────────────────────────────

    def lint(self) -> HealthReport:
        """Audit memory health: contradictions, stale info, gaps.

        Returns:
            HealthReport with issues found.
        """
        report = HealthReport()
        report.total_memories = self.store.count()

        if report.total_memories == 0:
            return report

        # Get all memories (in batches for large stores)
        all_memories = self.store.list_memories(limit=100)

        # Check for contradictions — find memories linked with "contradicts"
        conn = self.store._get_conn()
        contradictions = conn.execute(
            "SELECT source_id, target_id, explanation FROM memory_links WHERE kind = 'contradicts'"
        ).fetchall()
        conn.close()

        for c in contradictions:
            source = self.store.get(c[0])
            target = self.store.get(c[1])
            if source and target:
                report.contradictions.append({
                    "memory_1": {"id": source.id, "summary": source.summary},
                    "memory_2": {"id": target.id, "summary": target.summary},
                    "explanation": c[2],
                })

        # Check for stale action items (importance >= 4, older than 30 days)
        now = time.time()
        for mem in all_memories:
            age_days = (now - mem.created_at) / 86400
            if age_days > 30 and mem.importance >= 4:
                if mem.extraction.action_items:
                    report.stale_items.append({
                        "id": mem.id,
                        "summary": mem.summary,
                        "age_days": round(age_days),
                        "action_items": mem.extraction.action_items,
                    })

        # Health score
        issue_count = len(report.contradictions) + len(report.stale_items) + len(report.knowledge_gaps)
        report.health_score = max(0, 1.0 - (issue_count / max(report.total_memories, 1)))

        return report

    # ── UTILITIES ──────────────────────────────────────────────────────────

    def memories(self, limit: int = 50, source: str | None = None) -> list[Memory]:
        """List stored memories."""
        return self.store.list_memories(limit=limit, source=source)

    def get_memory(self, memory_id: str) -> Memory | None:
        """Get a specific memory by ID."""
        return self.store.get(memory_id)

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        return self.store.delete(memory_id)

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        return self.store.stats()


# ── Helpers ────────────────────────────────────────────────────────────────


def _clean_summary(text: str) -> str:
    """Remove model bleed from summaries.

    The model sometimes appends [DETAILED EXPLANATION], [INSTRUCTION],
    or restarts the prompt after a good summary.
    """
    # Cut at known bleed markers
    for marker in ["\n\n[DETAILED", "\n\n[INSTRUCTION", "\n\n------", "\n\n[SUMMARY", "\n\nAs Rab"]:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx]
    return text.strip()


def _clean_triage_type(triage_type: str) -> str:
    """Clean triage type — remove signal prefix echoes."""
    if not triage_type:
        return ""
    # Strip signal names that the model echoes
    cleaned = triage_type.strip()
    signal_names = {"TRIAGE", "EXTRACT", "SUMMARIZE", "SENTIMENT", "IMPORTANCE", "INTENT", "ANSWER", "LINK", "AMBIENT"}
    if cleaned.upper() in signal_names:
        return ""  # No useful type, let it be empty rather than wrong
    return cleaned.lower()


def _clean_tags(tags: list) -> list[str]:
    """Remove signal prefixes and duplicates from tags."""
    if not tags:
        return []
    signal_names = {"triage", "extract", "summarize", "sentiment", "importance", "intent", "answer", "link", "ambient"}
    cleaned = []
    seen = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        t = tag.strip()
        if t.lower() in signal_names:
            continue  # Skip signal name tags
        if t.lower() not in seen:
            cleaned.append(t)
            seen.add(t.lower())
    return cleaned


def _parse_answer_sections(answer_text: str, memories: list[Memory]) -> tuple[list[dict], list[str]]:
    """Parse Sources and Follow-up questions from an answer."""
    sources = []
    followups = []

    # Parse sources section
    sources_match = re.search(r'Sources?:\s*\n(.*?)(?:\n\s*\n|Follow-up|$)', answer_text, re.DOTALL)
    if sources_match:
        for line in sources_match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("["):
                # Extract index
                idx_match = re.match(r'\[(\d+)\]', line)
                if idx_match:
                    idx = int(idx_match.group(1)) - 1
                    source_info = {"citation": line}
                    if 0 <= idx < len(memories):
                        source_info["memory_id"] = memories[idx].id
                    sources.append(source_info)

    # Parse follow-up questions
    followup_match = re.search(r'Follow-up questions?:\s*\n(.*?)$', answer_text, re.DOTALL)
    if followup_match:
        for line in followup_match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("→") or line.startswith("-") or line.startswith("•"):
                followups.append(line.lstrip("→-• ").strip())
            elif line:
                followups.append(line)

    return sources, followups


def _format_timestamp(ts: float) -> str:
    """Format a Unix timestamp as a readable date."""
    import datetime
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d")
