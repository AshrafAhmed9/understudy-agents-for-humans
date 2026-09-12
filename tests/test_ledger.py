"""Acceptance criteria: six concurrent requests yield at
most five deliveries; duplicates use one slot; restart retains spending and
queue; midnight uses the configured timezone; resolution does not refund;
uncertain sends do not duplicate; exhausted items remain accessible.
"""

import tempfile
from pathlib import Path

import pytest

from understudy.policy.ledger import Ledger, local_day


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.sqlite3"


def test_six_requests_yield_at_most_five_reservations(db_path):
    ledger = Ledger(db_path, daily_cap=5)
    day = "2026-09-12"
    results = [ledger.try_reserve(day, f"issue-{i}") for i in range(6)]
    assert results.count(True) == 5
    assert results.count(False) == 1
    counts = ledger.counts(day)
    assert counts.reserved == 5
    # the 6th is queued, not lost
    assert counts.queued == 1


def test_duplicate_key_consumes_only_one_slot(db_path):
    ledger = Ledger(db_path, daily_cap=5)
    day = "2026-09-12"
    first = ledger.try_reserve(day, "issue-1")
    second = ledger.try_reserve(day, "issue-1")
    assert first is True
    assert second is True
    assert ledger.counts(day).reserved == 1


def test_restart_retains_spending_and_queue(db_path):
    day = "2026-09-12"
    ledger = Ledger(db_path, daily_cap=5)
    for i in range(6):
        ledger.try_reserve(day, f"issue-{i}")
    ledger.close()

    reopened = Ledger(db_path, daily_cap=5)
    counts = reopened.counts(day)
    assert counts.reserved == 5
    assert counts.queued == 1


def test_midnight_rollover_uses_configured_timezone():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    late = datetime(2026, 9, 12, 23, 59, tzinfo=ZoneInfo("UTC"))
    just_after = datetime(2026, 9, 13, 0, 1, tzinfo=ZoneInfo("UTC"))
    assert local_day("UTC", late) == "2026-09-12"
    assert local_day("UTC", just_after) == "2026-09-13"

    # Same instant, different maintainer timezone => different local day.
    moment = datetime(2026, 9, 13, 2, 0, tzinfo=ZoneInfo("UTC"))
    assert local_day("America/Los_Angeles", moment) == "2026-09-12"
    assert local_day("Asia/Kolkata", moment) == "2026-09-13"


def test_new_day_gets_a_fresh_cap_without_deleting_prior_pending_work(db_path):
    ledger = Ledger(db_path, daily_cap=5)
    day1, day2 = "2026-09-12", "2026-09-13"
    for i in range(5):
        assert ledger.try_reserve(day1, f"d1-{i}") is True
    ledger.resolve(day1, "d1-0")  # resolved, but doesn't free a slot (below)

    for i in range(5):
        assert ledger.try_reserve(day2, f"d2-{i}") is True

    assert ledger.counts(day1).reserved == 5
    assert ledger.counts(day2).reserved == 5
    # day1's resolved item is gone from `pending`, but still counted as spent
    pending_day1 = [dict(r) for r in ledger.pending(day1)]
    assert "d1-0" not in {r["key"] for r in pending_day1}


def test_resolution_does_not_refund_a_slot(db_path):
    ledger = Ledger(db_path, daily_cap=1)
    day = "2026-09-12"
    assert ledger.try_reserve(day, "only-slot") is True
    ledger.resolve(day, "only-slot")
    # Cap is still exhausted — resolving is not the same as refunding.
    assert ledger.try_reserve(day, "another-issue") is False
    assert ledger.counts(day).reserved == 1


def test_ambiguous_delivery_does_not_free_the_slot(db_path):
    ledger = Ledger(db_path, daily_cap=1)
    day = "2026-09-12"
    assert ledger.try_reserve(day, "flaky-send") is True
    ledger.mark_ambiguous(day, "flaky-send")
    # Still reserved, still costs the cap — not returned to the pool on a maybe.
    assert ledger.counts(day).reserved == 1
    assert ledger.try_reserve(day, "second-issue") is False


def test_ambiguous_then_retry_does_not_duplicate(db_path):
    ledger = Ledger(db_path, daily_cap=5)
    day = "2026-09-12"
    ledger.try_reserve(day, "issue-x")
    ledger.mark_ambiguous(day, "issue-x")
    # A retry of the same logical send reuses the same key — idempotent,
    # no second slot spent even though delivery was uncertain.
    again = ledger.try_reserve(day, "issue-x")
    assert again is True
    assert ledger.counts(day).reserved == 1


def test_exhausted_items_remain_visible_in_pending(db_path):
    ledger = Ledger(db_path, daily_cap=2)
    day = "2026-09-12"
    ledger.try_reserve(day, "a")
    ledger.try_reserve(day, "b")
    assert ledger.try_reserve(day, "c") is False  # cap hit, gets queued instead
    keys = {dict(r)["key"] for r in ledger.pending(day)}
    assert "c" in keys  # not lost


def test_confirm_delivered_moves_out_of_reserved(db_path):
    ledger = Ledger(db_path, daily_cap=5)
    day = "2026-09-12"
    ledger.try_reserve(day, "issue-1")
    ledger.confirm_delivered(day, "issue-1")
    counts = ledger.counts(day)
    assert counts.delivered == 1
    assert counts.reserved == 0
    # But delivered still counts against the cap.
    for i in range(4):
        ledger.try_reserve(day, f"filler-{i}")
    assert ledger.try_reserve(day, "one-too-many") is False
