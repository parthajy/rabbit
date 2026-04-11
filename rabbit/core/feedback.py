"""
Feedback collection for Rabbit's training flywheel.

Captures user signals to improve the model over time:
- Explicit: thumbs up/down on answers
- Implicit: follow-up questions (suggests incomplete answer)
- Corrections: user provides better answer

All feedback is stored locally and used for:
1. Immediate retrieval tuning (boost/demote memories)
2. Monthly retraining (positive examples + DPO pairs)
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class FeedbackStore:
    """Stores user feedback for training data generation."""

    def __init__(self, storage_path: str = "~/.rabbit/data", tenant_id: str = "default"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / f"{tenant_id}_feedback.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                memory_ids TEXT DEFAULT '[]',
                signal TEXT DEFAULT 'answer',
                rating INTEGER DEFAULT 0,
                correction TEXT DEFAULT '',
                feedback_type TEXT DEFAULT 'rating',
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
            CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
        """)
        conn.commit()
        conn.close()

    def record(
        self,
        question: str,
        answer_text: str,
        rating: int,
        memory_ids: list[str] | None = None,
        correction: str = "",
        signal: str = "answer",
        metadata: dict[str, Any] | None = None,
    ):
        """Record feedback on an answer.

        Args:
            question: The question that was asked.
            answer_text: The answer Rabbit gave.
            rating: 1 (thumbs up) or -1 (thumbs down) or 0 (no rating).
            memory_ids: Which memories were used.
            correction: User-provided better answer (optional).
            signal: Which signal generated this (usually "answer").
            metadata: Additional context.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO feedback
               (question, answer_text, memory_ids, signal, rating,
                correction, feedback_type, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                question, answer_text,
                json.dumps(memory_ids or []),
                signal, rating, correction,
                "correction" if correction else "rating",
                json.dumps(metadata or {}),
                time.time(),
            ),
        )
        conn.commit()
        conn.close()

    def get_positive_examples(self, limit: int = 1000) -> list[dict]:
        """Get thumbs-up answers for retraining."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM feedback WHERE rating = 1 ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_dpo_pairs(self, limit: int = 500) -> list[dict]:
        """Get preference pairs for DPO training.

        Returns pairs where the user provided a correction (preferred)
        alongside the original answer (rejected).
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM feedback
               WHERE feedback_type = 'correction' AND correction != ''
               ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()

        pairs = []
        for r in rows:
            pairs.append({
                "question": r["question"],
                "chosen": r["correction"],    # user's preferred answer
                "rejected": r["answer_text"],  # rabbit's original answer
                "memory_ids": json.loads(r["memory_ids"]),
            })
        return pairs

    def stats(self) -> dict:
        """Get feedback statistics."""
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        positive = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = 1").fetchone()[0]
        negative = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = -1").fetchone()[0]
        corrections = conn.execute("SELECT COUNT(*) FROM feedback WHERE correction != ''").fetchone()[0]
        conn.close()

        return {
            "total_feedback": total,
            "thumbs_up": positive,
            "thumbs_down": negative,
            "corrections": corrections,
            "approval_rate": round(positive / max(total, 1), 2),
        }
