"""
Memory storage layer.

Combines:
- Qdrant (vector search)
- SQLite (metadata, memory graph, BM25 search)

Each tenant gets an isolated namespace. Works locally with zero config.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Any

from rabbit.core.types import Memory, MemoryLink


class MemoryStore:
    """Persistent memory storage with vector + keyword + graph search."""

    def __init__(self, storage_path: str = "~/.rabbit/data", tenant_id: str = "default"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.tenant_id = tenant_id

        # SQLite for metadata + graph + BM25
        self.db_path = self.storage_path / f"{tenant_id}.db"
        self._init_db()

        # Qdrant for vectors (lazy init)
        self._qdrant_client = None
        self._collection_name = f"rabbit_{tenant_id}"

    def _init_db(self):
        """Initialize SQLite database with tables."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'unknown',
                source_type TEXT DEFAULT 'text',
                summary TEXT DEFAULT '',
                triage_type TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                extraction TEXT DEFAULT '{}',
                sentiment TEXT DEFAULT '',
                importance INTEGER DEFAULT 3,
                importance_reason TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at REAL,
                tenant_id TEXT DEFAULT 'default'
            );

            CREATE TABLE IF NOT EXISTS memory_links (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                weight REAL DEFAULT 0.5,
                explanation TEXT DEFAULT '',
                created_at REAL,
                PRIMARY KEY (source_id, target_id, kind),
                FOREIGN KEY (source_id) REFERENCES memories(id),
                FOREIGN KEY (target_id) REFERENCES memories(id)
            );

            CREATE INDEX IF NOT EXISTS idx_memories_tenant ON memories(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
            CREATE INDEX IF NOT EXISTS idx_links_source ON memory_links(source_id);
            CREATE INDEX IF NOT EXISTS idx_links_target ON memory_links(target_id);

            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id, content, summary, tags,
                content='memories',
                content_rowid='rowid'
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(id, content, summary, tags)
                VALUES (new.id, new.content, new.summary, new.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, id, content, summary, tags)
                VALUES ('delete', old.id, old.content, old.summary, old.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, id, content, summary, tags)
                VALUES ('delete', old.id, old.content, old.summary, old.tags);
                INSERT INTO memories_fts(id, content, summary, tags)
                VALUES (new.id, new.content, new.summary, new.tags);
            END;
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── Qdrant ─────────────────────────────────────────────────────────────

    def _init_qdrant(self):
        """Initialize Qdrant client (local file-based storage)."""
        if self._qdrant_client is not None:
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            qdrant_path = self.storage_path / "qdrant"
            self._qdrant_client = QdrantClient(path=str(qdrant_path))

            # Create collection if it doesn't exist
            collections = [c.name for c in self._qdrant_client.get_collections().collections]
            if self._collection_name not in collections:
                self._qdrant_client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=768,  # nomic-embed-text-v1.5 dimension
                        distance=Distance.COSINE,
                    ),
                )
        except ImportError:
            # Qdrant not installed — vector search disabled, BM25 only
            self._qdrant_client = None

    # ── Store & Retrieve ───────────────────────────────────────────────────

    def store(self, memory: Memory):
        """Store a memory with its vector embedding."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, content, source, source_type, summary, triage_type, tags,
                extraction, sentiment, importance, importance_reason, metadata,
                created_at, tenant_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.id, memory.content, memory.source, memory.source_type,
                memory.summary, memory.triage_type, json.dumps(memory.tags),
                json.dumps({
                    "people": memory.extraction.people,
                    "organizations": memory.extraction.organizations,
                    "decisions": memory.extraction.decisions,
                    "action_items": memory.extraction.action_items,
                    "dates": memory.extraction.dates,
                    "topics": memory.extraction.topics,
                }),
                memory.sentiment, memory.importance, memory.importance_reason,
                json.dumps(memory.metadata), memory.created_at, memory.tenant_id,
            ),
        )

        # Store links
        for link in memory.links:
            conn.execute(
                """INSERT OR REPLACE INTO memory_links
                   (source_id, target_id, kind, weight, explanation, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (memory.id, link.target_id, link.kind, link.weight,
                 link.explanation, time.time()),
            )

        conn.commit()
        conn.close()

        # Store vector in Qdrant
        if memory.embedding:
            self._store_vector(memory.id, memory.embedding, {
                "content_preview": memory.content[:200],
                "source": memory.source,
                "importance": memory.importance,
                "created_at": memory.created_at,
            })

    def _store_vector(self, memory_id: str, embedding: list[float], payload: dict):
        """Store a vector in Qdrant."""
        self._init_qdrant()
        if self._qdrant_client is None:
            return

        from qdrant_client.models import PointStruct

        # Use memory_id hash as point ID
        point_id = abs(hash(memory_id)) % (2**63)

        self._qdrant_client.upsert(
            collection_name=self._collection_name,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload={"memory_id": memory_id, **payload},
            )],
        )

    def get(self, memory_id: str) -> Memory | None:
        """Get a memory by ID."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_memory(row)

    def delete(self, memory_id: str) -> bool:
        """Delete a memory and its links."""
        conn = self._get_conn()
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.execute("DELETE FROM memory_links WHERE source_id = ? OR target_id = ?",
                      (memory_id, memory_id))
        conn.commit()
        deleted = conn.total_changes > 0
        conn.close()

        # Delete from Qdrant
        self._init_qdrant()
        if self._qdrant_client:
            point_id = abs(hash(memory_id)) % (2**63)
            try:
                from qdrant_client.models import PointIdsList
                self._qdrant_client.delete(
                    collection_name=self._collection_name,
                    points_selector=PointIdsList(points=[point_id]),
                )
            except Exception:
                pass

        return deleted

    def list_memories(self, limit: int = 50, offset: int = 0, source: str | None = None) -> list[Memory]:
        """List memories with optional filtering."""
        conn = self._get_conn()
        query = "SELECT * FROM memories WHERE tenant_id = ?"
        params: list[Any] = [self.tenant_id]

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        conn.close()

        return [self._row_to_memory(row) for row in rows]

    def count(self) -> int:
        """Count total memories for this tenant."""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM memories WHERE tenant_id = ?",
                           (self.tenant_id,)).fetchone()
        conn.close()
        return row[0] if row else 0

    # ── Search ─────────────────────────────────────────────────────────────

    def search_vector(self, query_embedding: list[float], limit: int = 20) -> list[tuple[str, float]]:
        """Search by vector similarity. Returns list of (memory_id, score)."""
        self._init_qdrant()
        if self._qdrant_client is None:
            return []

        results = self._qdrant_client.search(
            collection_name=self._collection_name,
            query_vector=query_embedding,
            limit=limit,
        )

        return [(r.payload["memory_id"], r.score) for r in results]

    def search_bm25(self, query: str, limit: int = 20) -> list[tuple[str, float]]:
        """Search by BM25 keyword matching using FTS5."""
        conn = self._get_conn()

        # Tokenize query for FTS5
        tokens = re.findall(r'\w+', query.lower())
        if not tokens:
            conn.close()
            return []

        fts_query = " OR ".join(tokens)

        try:
            rows = conn.execute(
                """SELECT id, rank FROM memories_fts
                   WHERE memories_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, limit),
            ).fetchall()
            conn.close()

            # Normalize FTS5 rank scores to 0-1
            if not rows:
                return []

            max_rank = max(abs(r[1]) for r in rows) or 1
            return [(r[0], abs(r[1]) / max_rank) for r in rows]
        except Exception:
            conn.close()
            return []

    def search_hybrid(self, query: str, query_embedding: list[float], limit: int = 10,
                       vector_weight: float = 0.6, bm25_weight: float = 0.4) -> list[Memory]:
        """Hybrid search combining vector similarity and BM25 keyword matching."""
        # Get candidates from both sources
        vector_results = self.search_vector(query_embedding, limit=limit * 2)
        bm25_results = self.search_bm25(query, limit=limit * 2)

        # Combine scores
        scores: dict[str, float] = {}
        for memory_id, score in vector_results:
            scores[memory_id] = scores.get(memory_id, 0) + score * vector_weight
        for memory_id, score in bm25_results:
            scores[memory_id] = scores.get(memory_id, 0) + score * bm25_weight

        # Apply importance and recency boosts
        conn = self._get_conn()
        now = time.time()
        for memory_id in scores:
            row = conn.execute(
                "SELECT importance, created_at FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
            if row:
                importance = row[0] or 3
                created_at = row[1] or now
                # Importance boost: score * (1 + importance/10)
                scores[memory_id] *= (1 + importance / 10)
                # Recency boost: slight preference for recent memories
                age_days = (now - created_at) / 86400
                recency_factor = 1.0 / (1.0 + math.log1p(age_days) * 0.1)
                scores[memory_id] *= recency_factor
        conn.close()

        # Sort by combined score, take top-K
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        # Fetch full memories
        memories = []
        for memory_id, _ in ranked:
            memory = self.get(memory_id)
            if memory:
                memories.append(memory)

        return memories

    # ── Graph Operations ───────────────────────────────────────────────────

    def get_links(self, memory_id: str) -> list[MemoryLink]:
        """Get all links from a memory."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT target_id, kind, weight, explanation FROM memory_links WHERE source_id = ?",
            (memory_id,),
        ).fetchall()
        conn.close()

        return [MemoryLink(
            target_id=r[0], kind=r[1], weight=r[2], explanation=r[3],
        ) for r in rows]

    def get_connected(self, memory_id: str, hops: int = 2) -> list[Memory]:
        """Walk the memory graph N hops from a starting memory."""
        visited: set[str] = {memory_id}
        frontier = [memory_id]
        found: set[str] = set()

        for _ in range(hops):
            next_frontier = []
            for mid in frontier:
                conn = self._get_conn()
                rows = conn.execute(
                    """SELECT target_id FROM memory_links WHERE source_id = ?
                       UNION
                       SELECT source_id FROM memory_links WHERE target_id = ?""",
                    (mid, mid),
                ).fetchall()
                conn.close()
                for r in rows:
                    neighbor = r[0]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        found.add(neighbor)
                        next_frontier.append(neighbor)
            frontier = next_frontier

        memories = []
        for mid in found:
            memory = self.get(mid)
            if memory:
                memories.append(memory)

        return memories

    def store_link(self, source_id: str, target_id: str, kind: str, weight: float = 0.5, explanation: str = ""):
        """Store a link between two memories."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO memory_links
               (source_id, target_id, kind, weight, explanation, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_id, target_id, kind, weight, explanation, time.time()),
        )
        conn.commit()
        conn.close()

    # ── Stats ──────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM memories WHERE tenant_id = ?",
                             (self.tenant_id,)).fetchone()[0]
        link_count = conn.execute("SELECT COUNT(*) FROM memory_links").fetchone()[0]

        sources = conn.execute(
            "SELECT source, COUNT(*) FROM memories WHERE tenant_id = ? GROUP BY source",
            (self.tenant_id,),
        ).fetchall()

        sentiments = conn.execute(
            "SELECT sentiment, COUNT(*) FROM memories WHERE tenant_id = ? GROUP BY sentiment",
            (self.tenant_id,),
        ).fetchall()

        avg_importance = conn.execute(
            "SELECT AVG(importance) FROM memories WHERE tenant_id = ?",
            (self.tenant_id,),
        ).fetchone()[0]

        conn.close()

        return {
            "total_memories": total,
            "total_links": link_count,
            "sources": {r[0]: r[1] for r in sources},
            "sentiments": {r[0]: r[1] for r in sentiments if r[0]},
            "avg_importance": round(avg_importance or 0, 2),
        }

    # ── Internal ───────────────────────────────────────────────────────────

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """Convert a SQLite row to a Memory object."""
        from rabbit.core.types import Extraction

        ext_data = json.loads(row["extraction"]) if row["extraction"] else {}
        extraction = Extraction(
            people=ext_data.get("people", []),
            organizations=ext_data.get("organizations", []),
            decisions=ext_data.get("decisions", []),
            action_items=ext_data.get("action_items", []),
            dates=ext_data.get("dates", []),
            topics=ext_data.get("topics", []),
        )

        tags = json.loads(row["tags"]) if row["tags"] else []
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        # Get links
        conn = self._get_conn()
        link_rows = conn.execute(
            "SELECT target_id, kind, weight, explanation FROM memory_links WHERE source_id = ?",
            (row["id"],),
        ).fetchall()
        conn.close()

        links = [MemoryLink(
            target_id=r[0], kind=r[1], weight=r[2], explanation=r[3],
        ) for r in link_rows]

        return Memory(
            id=row["id"],
            content=row["content"],
            source=row["source"],
            source_type=row["source_type"],
            summary=row["summary"],
            triage_type=row["triage_type"],
            tags=tags,
            extraction=extraction,
            sentiment=row["sentiment"],
            importance=row["importance"],
            importance_reason=row["importance_reason"],
            links=links,
            metadata=metadata,
            created_at=row["created_at"],
            tenant_id=row["tenant_id"],
        )
