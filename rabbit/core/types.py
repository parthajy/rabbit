"""
Core data types for Rabbit.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _memory_id() -> str:
    return f"mem_{uuid.uuid4().hex[:16]}"


def _now() -> float:
    return time.time()


@dataclass
class Extraction:
    """Structured information extracted from content."""
    people: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    action_items: list[dict[str, str]] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)


@dataclass
class MemoryLink:
    """A relationship between two memories."""
    target_id: str
    kind: str  # same_topic, depends_on, contradicts, continuation_of, same_people, causes, temporal
    weight: float = 0.5
    explanation: str = ""


@dataclass
class Memory:
    """A single memory stored in Rabbit."""
    id: str = field(default_factory=_memory_id)
    content: str = ""
    source: str = "unknown"  # meeting, email, slack, note, pdf, audio, image, etc.
    source_type: str = "text"  # text, audio, pdf, image, document, web, code, email, calendar

    # Processed fields (filled by ingestion pipeline)
    summary: str = ""
    triage_type: str = ""  # meeting, decision, task, update, question, idea, etc.
    tags: list[str] = field(default_factory=list)
    extraction: Extraction = field(default_factory=Extraction)
    sentiment: str = ""  # positive, negative, neutral, tense, urgent
    importance: int = 3  # 1-5
    importance_reason: str = ""
    links: list[MemoryLink] = field(default_factory=list)

    # Vector embedding
    embedding: list[float] = field(default_factory=list, repr=False)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_now)
    tenant_id: str = "default"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type,
            "summary": self.summary,
            "triage_type": self.triage_type,
            "tags": self.tags,
            "extraction": {
                "people": self.extraction.people,
                "organizations": self.extraction.organizations,
                "decisions": self.extraction.decisions,
                "action_items": self.extraction.action_items,
                "dates": self.extraction.dates,
                "topics": self.extraction.topics,
            },
            "sentiment": self.sentiment,
            "importance": self.importance,
            "importance_reason": self.importance_reason,
            "links": [
                {"target_id": l.target_id, "kind": l.kind, "weight": l.weight, "explanation": l.explanation}
                for l in self.links
            ],
            "metadata": self.metadata,
            "created_at": self.created_at,
            "tenant_id": self.tenant_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Memory:
        ext_data = d.get("extraction", {})
        extraction = Extraction(
            people=ext_data.get("people", []),
            organizations=ext_data.get("organizations", []),
            decisions=ext_data.get("decisions", []),
            action_items=ext_data.get("action_items", []),
            dates=ext_data.get("dates", []),
            topics=ext_data.get("topics", []),
        )
        links = [
            MemoryLink(
                target_id=l["target_id"], kind=l["kind"],
                weight=l.get("weight", 0.5), explanation=l.get("explanation", ""),
            )
            for l in d.get("links", [])
        ]
        return cls(
            id=d.get("id", _memory_id()),
            content=d.get("content", ""),
            source=d.get("source", "unknown"),
            source_type=d.get("source_type", "text"),
            summary=d.get("summary", ""),
            triage_type=d.get("triage_type", ""),
            tags=d.get("tags", []),
            extraction=extraction,
            sentiment=d.get("sentiment", ""),
            importance=d.get("importance", 3),
            importance_reason=d.get("importance_reason", ""),
            links=links,
            embedding=d.get("embedding", []),
            metadata=d.get("metadata", {}),
            created_at=d.get("created_at", _now()),
            tenant_id=d.get("tenant_id", "default"),
        )


@dataclass
class Answer:
    """Response from Rabbit's query pipeline."""
    text: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    followups: list[str] = field(default_factory=list)
    intent: str = ""
    expanded_query: str = ""
    memories_used: list[Memory] = field(default_factory=list)
    latency_ms: int = 0


@dataclass
class AmbientAlert:
    """Result from ambient contradiction/context detection."""
    show: bool = False
    reason: str = ""  # contradiction, forgotten_commitment, critical_context
    context: str = ""
    memory_indices: list[int] = field(default_factory=list)


@dataclass
class HealthReport:
    """Result from lint/health audit."""
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    stale_items: list[dict[str, Any]] = field(default_factory=list)
    knowledge_gaps: list[dict[str, Any]] = field(default_factory=list)
    total_memories: int = 0
    health_score: float = 1.0  # 0-1


@dataclass
class ProcessedInput:
    """Output from an input processor (audio, PDF, image, etc.)."""
    text: str = ""
    source_type: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[str] = field(default_factory=list)  # for long documents
