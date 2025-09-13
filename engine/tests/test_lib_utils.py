from __future__ import annotations

import time
from datetime import datetime

from engine.lib.result import Err, Ok
from engine.lib.rng import seed_for
from engine.lib.timeutil import now_iso, utc_ms_now


def test_result_truthiness() -> None:
    assert Ok(1)
    err = Err("boom")
    assert isinstance(err, Err)


def test_seed_for_determinism() -> None:
    r1 = seed_for(42, "a", 1)
    r2 = seed_for(42, "a", 1)
    seq1 = [r1.random() for _ in range(3)]
    seq2 = [r2.random() for _ in range(3)]
    assert seq1 == seq2

    r3 = seed_for(42, "a", 2)
    seq3 = [r3.random() for _ in range(3)]
    assert seq1 != seq3


def test_time_utils() -> None:
    t1 = utc_ms_now()
    time.sleep(0.01)
    t2 = utc_ms_now()
    assert t2 > t1

    iso = now_iso()
    parsed = datetime.fromisoformat(iso)
    assert parsed.tzinfo is not None
