"""
API key authentication and tenant management.

Key format:
    rab_test_<24 random chars>  → Free tier, ephemeral
    rab_live_<24 random chars>  → Production tier, persistent

Each key maps to a tenant with isolated storage and rate limits.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class InvalidKeyError(Exception):
    """Raised when an API key is not valid."""
    pass


class RateLimitError(Exception):
    """Raised when a tenant exceeds their rate limit."""
    pass

# Rate limits per tier
TIER_LIMITS = {
    "test": {
        "calls_per_day": 100,
        "calls_per_month": 1000,
        "max_memories": 1000,
        "max_file_size_mb": 10,
        "data_retention_days": 7,
    },
    "live": {
        "calls_per_day": 10000,
        "calls_per_month": 100000,
        "max_memories": 1000000,
        "max_file_size_mb": 100,
        "data_retention_days": -1,  # permanent
    },
    "internal": {
        "calls_per_day": -1,  # unlimited
        "calls_per_month": -1,
        "max_memories": -1,
        "max_file_size_mb": 500,
        "data_retention_days": -1,
    },
}


@dataclass
class Tenant:
    """A tenant (user/org) identified by an API key."""
    key: str
    tenant_id: str
    tier: str  # test, live, internal
    created_at: float
    metadata: dict[str, Any]

    @property
    def limits(self) -> dict:
        return TIER_LIMITS.get(self.tier, TIER_LIMITS["test"])


class KeyManager:
    """Manages API keys and tenant mapping."""

    def __init__(self, db_path: str = "~/.rabbit/keys.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_hash TEXT PRIMARY KEY,
                key_prefix TEXT NOT NULL,
                tenant_id TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL DEFAULT 'test',
                created_at REAL NOT NULL,
                last_used REAL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS usage_log (
                tenant_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                timestamp REAL NOT NULL,
                latency_ms INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_usage_tenant ON usage_log(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_usage_time ON usage_log(timestamp);
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def generate_key(self, tier: str = "test", metadata: dict | None = None) -> tuple[str, str]:
        """Generate a new API key. Returns (key, tenant_id)."""
        prefix = f"rab_{tier}_"
        random_part = secrets.token_urlsafe(18)  # ~24 chars
        key = prefix + random_part
        tenant_id = f"tenant_{secrets.token_hex(8)}"
        key_hash = self._hash_key(key)

        conn = self._get_conn()
        conn.execute(
            """INSERT INTO api_keys (key_hash, key_prefix, tenant_id, tier, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (key_hash, key[:12] + "...", tenant_id, tier, time.time(), json.dumps(metadata or {})),
        )
        conn.commit()
        conn.close()

        return key, tenant_id

    def validate_key(self, key: str) -> Tenant:
        """Validate an API key and return the tenant."""
        key_hash = self._hash_key(key)

        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,)
        ).fetchone()

        if not row:
            conn.close()
            raise InvalidKeyError("Invalid API key")

        # Update last_used
        conn.execute(
            "UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
            (time.time(), key_hash),
        )
        conn.commit()
        conn.close()

        return Tenant(
            key=key[:12] + "...",
            tenant_id=row["tenant_id"],
            tier=row["tier"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def check_rate_limit(self, tenant: Tenant, endpoint: str) -> bool:
        """Check if a tenant is within rate limits. Returns True if allowed."""
        limits = tenant.limits
        if limits["calls_per_day"] == -1:
            return True  # Unlimited

        conn = self._get_conn()
        now = time.time()

        # Check daily limit
        day_ago = now - 86400
        daily_count = conn.execute(
            "SELECT COUNT(*) FROM usage_log WHERE tenant_id = ? AND timestamp > ?",
            (tenant.tenant_id, day_ago),
        ).fetchone()[0]

        if daily_count >= limits["calls_per_day"]:
            conn.close()
            raise RateLimitError(
                f"Daily rate limit exceeded ({limits['calls_per_day']} calls/day). Upgrade to rab_live for higher limits."
            )

        # Log this call
        conn.execute(
            "INSERT INTO usage_log (tenant_id, endpoint, timestamp) VALUES (?, ?, ?)",
            (tenant.tenant_id, endpoint, now),
        )
        conn.commit()
        conn.close()
        return True

    def get_usage(self, tenant_id: str) -> dict:
        """Get usage stats for a tenant."""
        conn = self._get_conn()
        now = time.time()

        daily = conn.execute(
            "SELECT COUNT(*) FROM usage_log WHERE tenant_id = ? AND timestamp > ?",
            (tenant_id, now - 86400),
        ).fetchone()[0]

        monthly = conn.execute(
            "SELECT COUNT(*) FROM usage_log WHERE tenant_id = ? AND timestamp > ?",
            (tenant_id, now - 86400 * 30),
        ).fetchone()[0]

        conn.close()
        return {"daily_calls": daily, "monthly_calls": monthly}

    @staticmethod
    def _hash_key(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def parse_tier(key: str) -> str:
        """Extract tier from key prefix."""
        if key.startswith("rab_test_"):
            return "test"
        elif key.startswith("rab_live_"):
            return "live"
        elif key.startswith("rab_internal_"):
            return "internal"
        return "test"
