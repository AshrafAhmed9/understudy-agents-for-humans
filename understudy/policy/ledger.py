"""Durable interruption budget: a SQLite ledger, not an in-memory counter.

Each proactive human interruption costs
exactly one integer unit. No harm x urgency / confidence scoring (the inputs
aren't calibrated and division at zero confidence is undefined) and no
refunds — dismissing a delivered notification does not undo it.

Three states per (day, key):
  queued    — free, unlimited. Something the agent wants to eventually tell
              a human, before it has spent a budget slot to do so.
  reserved  — a slot has been spent. Idempotent: reserving the same key twice
              on the same day does not spend a second slot.
  delivered — the notification was confirmed sent. Ambiguous delivery (we
              don't know if it went through) stays at "reserved", not
              "queued" and not "delivered" — the slot is not returned to the
              pool on a maybe.

Resolution (a human clicking "mark reviewed" / "defer" on a decision card) is
tracked separately and never changes reserved/delivered counts.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

DEFAULT_DAILY_CAP = 5

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    day TEXT NOT NULL,
    key TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('queued', 'reserved', 'delivered')),
    ambiguous INTEGER NOT NULL DEFAULT 0,
    resolved_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (day, key)
);
"""


def local_day(tz_name: str, at: datetime | None = None) -> str:
    """The calendar day string (YYYY-MM-DD) in the maintainer's configured
    timezone. This is what the daily cap rolls over on — never UTC blindly,
    and never the host machine's local zone if that differs from the
    maintainer's."""
    at = at or datetime.now(ZoneInfo(tz_name))
    if at.tzinfo is None:
        at = at.replace(tzinfo=ZoneInfo(tz_name))
    else:
        at = at.astimezone(ZoneInfo(tz_name))
    return at.strftime("%Y-%m-%d")


@dataclass(frozen=True)
class Counts:
    queued: int
    reserved: int
    delivered: int


class Ledger:
    """Opens (or creates) a SQLite file and enforces the budget against it.

    Safe to reopen against the same path after a restart — state persists on
    disk, not in process memory.
    """

    def __init__(self, db_path: Path | str, daily_cap: int = DEFAULT_DAILY_CAP):
        self.daily_cap = daily_cap
        self._conn = sqlite3.connect(str(db_path), isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _tx(self):
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield self._conn
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def queue(self, day: str, key: str, category: str = "") -> None:
        """Free. Always succeeds. Idempotent — queuing an existing key again
        does not create a duplicate row or change its status."""
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO items (day, key, category, status) "
                "VALUES (?, ?, ?, 'queued') "
                "ON CONFLICT(day, key) DO NOTHING",
                (day, key, category),
            )

    def try_reserve(self, day: str, key: str, category: str = "") -> bool:
        """Attempt to spend one budget slot for this key today.

        Returns True if a slot is held (whether just spent now, or already
        held from an earlier call — reservation is idempotent per key so
        duplicate delivery attempts never double-spend). Returns False if the
        daily cap is already exhausted; the item, if not already queued,
        is queued instead so it stays visible and is not lost.
        """
        with self._tx() as conn:
            row = conn.execute(
                "SELECT status FROM items WHERE day = ? AND key = ?", (day, key)
            ).fetchone()
            if row is not None and row[0] in ("reserved", "delivered"):
                return True

            spent = conn.execute(
                "SELECT COUNT(*) FROM items WHERE day = ? AND status IN ('reserved', 'delivered')",
                (day,),
            ).fetchone()[0]

            if spent >= self.daily_cap:
                conn.execute(
                    "INSERT INTO items (day, key, category, status) "
                    "VALUES (?, ?, ?, 'queued') "
                    "ON CONFLICT(day, key) DO NOTHING",
                    (day, key, category),
                )
                return False

            conn.execute(
                "INSERT INTO items (day, key, category, status, updated_at) "
                "VALUES (?, ?, ?, 'reserved', datetime('now')) "
                "ON CONFLICT(day, key) DO UPDATE SET status='reserved', updated_at=datetime('now')",
                (day, key, category),
            )
            return True

    def confirm_delivered(self, day: str, key: str) -> None:
        """Mark a reserved item as confirmed delivered. Idempotent."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE items SET status='delivered', updated_at=datetime('now') "
                "WHERE day = ? AND key = ? AND status = 'reserved'",
                (day, key),
            )

    def mark_ambiguous(self, day: str, key: str) -> None:
        """Delivery outcome unknown. The slot stays reserved — it is NOT
        returned to the pool and the item does NOT move to delivered."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE items SET ambiguous=1, updated_at=datetime('now') "
                "WHERE day = ? AND key = ?",
                (day, key),
            )

    def resolve(self, day: str, key: str) -> None:
        """A human acted on this item (mark reviewed / defer). Never spends
        or refunds a slot — purely a display/tracking concern."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE items SET resolved_at=datetime('now'), updated_at=datetime('now') "
                "WHERE day = ? AND key = ?",
                (day, key),
            )

    def counts(self, day: str) -> Counts:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) FROM items WHERE day = ? GROUP BY status", (day,)
        ).fetchall()
        by_status = {status: n for status, n in rows}
        return Counts(
            queued=by_status.get("queued", 0),
            reserved=by_status.get("reserved", 0),
            delivered=by_status.get("delivered", 0),
        )

    def pending(self, day: str) -> list[sqlite3.Row]:
        """Everything not yet resolved, oldest first — for the digest and the
        decision inbox. Exhausted (queued-but-capped) items remain accessible
        here, never silently dropped."""
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            "SELECT * FROM items WHERE day = ? AND resolved_at IS NULL "
            "ORDER BY created_at ASC",
            (day,),
        )
        return cur.fetchall()
