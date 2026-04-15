"""
Rabbit Python SDK.

Usage:
    from rabbit import Rabbit

    # Hosted API
    rab = Rabbit("rab_test_abc123")

    # Self-hosted
    rab = Rabbit("rab_live_xyz", base_url="https://rabbit.yourcompany.com")

    # Fully local (no API, runs model locally)
    rab = Rabbit.local(model_path="reattend/rabbit-v2.0")

    # Core operations
    rab.remember("Sarah delayed the launch to March 15.", source="meeting")
    answer = rab.ask("When is the launch?")
    print(answer.text)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx


@dataclass
class RabbitAnswer:
    """Response from rab.ask()."""
    text: str = ""
    sources: list[dict] = field(default_factory=list)
    followups: list[str] = field(default_factory=list)
    intent: str = ""
    expanded_query: str = ""
    memories_used: int = 0
    latency_ms: int = 0


@dataclass
class RabbitMemory:
    """A stored memory from rab.remember()."""
    id: str = ""
    summary: str = ""
    triage_type: str = ""
    tags: list[str] = field(default_factory=list)
    extraction: dict = field(default_factory=dict)
    sentiment: str = ""
    importance: int = 3
    importance_reason: str = ""
    links: list[dict] = field(default_factory=list)
    latency_ms: int = 0


@dataclass
class RabbitAlert:
    """Response from rab.check()."""
    show: bool = False
    reason: str = ""
    context: str = ""


class Rabbit:
    """Rabbit SDK — Memory infrastructure client.

    Args:
        api_key: Your Rabbit API key (rab_test_* or rab_live_*).
        base_url: API base URL. Defaults to rabbit.reattend.com.
        timeout: Request timeout in seconds.
    """

    DEFAULT_BASE_URL = "http://api.rabbit.reattend.com:8000"

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 120):
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    @classmethod
    def local(cls, model_path: str = "reattend/rabbit-v2.0",
              storage_path: str = "~/.rabbit/data", hf_token: str = "") -> RabbitLocal:
        """Create a fully local Rabbit instance (no API calls)."""
        return RabbitLocal(model_path=model_path, storage_path=storage_path, hf_token=hf_token)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an API request."""
        resp = self._client.request(method, path, **kwargs)
        if resp.status_code == 429:
            raise RabbitRateLimitError(resp.json().get("detail", "Rate limit exceeded"))
        if resp.status_code == 401:
            raise RabbitAuthError("Invalid API key")
        if resp.status_code >= 400:
            raise RabbitAPIError(f"API error {resp.status_code}: {resp.text}")
        return resp.json()

    # ── Core Operations ────────────────────────────────────────────────────

    def remember(self, content: str, source: str = "unknown", metadata: dict | None = None) -> RabbitMemory:
        """Ingest content into memory.

        Args:
            content: Text to remember.
            source: Source label (meeting, email, slack, note, etc.)
            metadata: Additional metadata.

        Returns:
            RabbitMemory with processed results.
        """
        data = self._request("POST", "/v1/remember", json={
            "content": content,
            "source": source,
            "metadata": metadata or {},
        })

        return RabbitMemory(
            id=data.get("id", ""),
            summary=data.get("summary", ""),
            triage_type=data.get("triage_type", ""),
            tags=data.get("tags", []),
            extraction=data.get("extraction", {}),
            sentiment=data.get("sentiment", ""),
            importance=data.get("importance", 3),
            importance_reason=data.get("importance_reason", ""),
            links=data.get("links", []),
            latency_ms=data.get("latency_ms", 0),
        )

    def remember_file(self, file_path: str | Path, source: str = "unknown") -> list[RabbitMemory]:
        """Ingest a file into memory.

        Supports: audio, PDF, DOCX, images, HTML, Markdown, code, email, calendar.

        Args:
            file_path: Path to the file.
            source: Source label.

        Returns:
            List of RabbitMemory objects (one per chunk for long docs).
        """
        path = Path(file_path)
        with open(path, "rb") as f:
            data = self._request("POST", "/v1/remember/file", files={
                "file": (path.name, f),
            }, data={"source": source})

        return [
            RabbitMemory(id=m.get("id", ""), summary=m.get("summary", ""))
            for m in data.get("memories", [])
        ]

    def ask(self, question: str, limit: int = 5, reasoning: bool = False) -> RabbitAnswer:
        """Ask a question over stored memories.

        Args:
            question: Natural language question.
            limit: Max memories to use for answering.
            reasoning: If True, route to a stronger model (Groq/OpenAI) for
                deep analysis, pattern recognition, and strategic suggestions.
                Rabbit still handles all retrieval — only the final answer
                generation uses the external model.

        Returns:
            RabbitAnswer with text, sources, and follow-ups.
        """
        data = self._request("POST", "/v1/ask", json={
            "question": question,
            "limit": limit,
            "reasoning": reasoning,
        })

        return RabbitAnswer(
            text=data.get("text", ""),
            sources=data.get("sources", []),
            followups=data.get("followups", []),
            intent=data.get("intent", ""),
            expanded_query=data.get("expanded_query", ""),
            memories_used=data.get("memories_used", 0),
            latency_ms=data.get("latency_ms", 0),
        )

    def ask_stream(self, question: str, limit: int = 5):
        """Ask a question with streaming response.

        Yields events as each pipeline stage completes, then streams
        answer chunks in real-time.

        Args:
            question: Natural language question.
            limit: Max memories to use.

        Yields:
            dict with "event" and "data" keys.
        """
        import json as _json

        with self._client.stream(
            "POST", "/v1/ask",
            json={"question": question, "limit": limit, "stream": True},
        ) as resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        yield {"event": event_type, "data": _json.loads(data_str)}
                    except (ValueError, UnboundLocalError):
                        pass

    def check(self, context: str) -> RabbitAlert:
        """Check for contradictions or forgotten commitments.

        Args:
            context: Current screen text or conversation.

        Returns:
            RabbitAlert with show=True if contradiction detected.
        """
        data = self._request("POST", "/v1/check", json={"context": context})

        return RabbitAlert(
            show=data.get("show", False),
            reason=data.get("reason", ""),
            context=data.get("context", ""),
        )

    # ── Feedback ────────────────────────────────────────────────────────────

    def thumbs_up(self, question: str, answer_text: str, memory_ids: list[str] | None = None):
        """Mark an answer as good. Feeds the training flywheel."""
        self._request("POST", "/v1/feedback", json={
            "question": question, "answer_text": answer_text,
            "rating": 1, "memory_ids": memory_ids or [],
        })

    def thumbs_down(self, question: str, answer_text: str,
                     correction: str = "", memory_ids: list[str] | None = None):
        """Mark an answer as bad. Optionally provide the correct answer."""
        self._request("POST", "/v1/feedback", json={
            "question": question, "answer_text": answer_text,
            "rating": -1, "correction": correction, "memory_ids": memory_ids or [],
        })

    # ── Knowledge Base ─────────────────────────────────────────────────────

    def compile(self, entity: str) -> str:
        """Compile a wiki page for an entity."""
        data = self._request("POST", f"/v1/compile/{entity}")
        return data.get("content", "")

    def lint(self) -> dict:
        """Run a health audit on memories."""
        return self._request("POST", "/v1/lint")

    # ── Memory Management ──────────────────────────────────────────────────

    def memories(self, limit: int = 50, source: str | None = None) -> list[dict]:
        """List stored memories."""
        params = {"limit": limit}
        if source:
            params["source"] = source
        data = self._request("GET", "/v1/memories", params=params)
        return data.get("memories", [])

    def get_memory(self, memory_id: str) -> dict:
        """Get a specific memory."""
        return self._request("GET", f"/v1/memories/{memory_id}")

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        self._request("DELETE", f"/v1/memories/{memory_id}")
        return True

    def graph(self, memory_id: str, hops: int = 2) -> dict:
        """Get a memory's connections."""
        return self._request("GET", f"/v1/graph/{memory_id}", params={"hops": hops})

    def stats(self) -> dict:
        """Get usage and memory statistics."""
        return self._request("GET", "/v1/stats")

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class RabbitLocal:
    """Fully local Rabbit — no API calls, runs model on your machine.

    Same interface as Rabbit, but uses RabbitCore directly.
    """

    def __init__(self, model_path: str = "reattend/rabbit-v2.0",
                 storage_path: str = "~/.rabbit/data", hf_token: str = ""):
        from rabbit.core.engine import RabbitCore
        self._engine = RabbitCore(
            model_path=model_path,
            storage_path=storage_path,
            hf_token=hf_token,
        )

    def remember(self, content: str, source: str = "unknown", metadata: dict | None = None) -> RabbitMemory:
        memory = self._engine.remember(content, source=source, metadata=metadata)
        return RabbitMemory(
            id=memory.id,
            summary=memory.summary,
            triage_type=memory.triage_type,
            tags=memory.tags,
            extraction=memory.extraction.__dict__,
            sentiment=memory.sentiment,
            importance=memory.importance,
            importance_reason=memory.importance_reason,
            links=[{"target_id": l.target_id, "kind": l.kind} for l in memory.links],
        )

    def remember_file(self, file_path: str | Path, source: str = "unknown") -> list[RabbitMemory]:
        memories = self._engine.remember_file(file_path, source=source)
        return [
            RabbitMemory(id=m.id, summary=m.summary)
            for m in memories
        ]

    def ask(self, question: str, limit: int = 5) -> RabbitAnswer:
        answer = self._engine.ask(question, limit=limit)
        return RabbitAnswer(
            text=answer.text,
            sources=answer.sources,
            followups=answer.followups,
            intent=answer.intent,
            expanded_query=answer.expanded_query,
            memories_used=len(answer.memories_used),
            latency_ms=answer.latency_ms,
        )

    def check(self, context: str) -> RabbitAlert:
        alert = self._engine.check(context)
        return RabbitAlert(show=alert.show, reason=alert.reason, context=alert.context)

    def compile(self, entity: str) -> str:
        return self._engine.compile(entity)

    def lint(self) -> dict:
        report = self._engine.lint()
        return {
            "total_memories": report.total_memories,
            "health_score": report.health_score,
            "contradictions": report.contradictions,
            "stale_items": report.stale_items,
        }

    def memories(self, limit: int = 50, source: str | None = None) -> list[dict]:
        mems = self._engine.memories(limit=limit, source=source)
        return [m.to_dict() for m in mems]

    def forget(self, memory_id: str) -> bool:
        return self._engine.forget(memory_id)

    def stats(self) -> dict:
        return self._engine.stats()


# ── Exceptions ─────────────────────────────────────────────────────────────

class RabbitAPIError(Exception):
    pass

class RabbitAuthError(RabbitAPIError):
    pass

class RabbitRateLimitError(RabbitAPIError):
    pass
