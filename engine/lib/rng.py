from __future__ import annotations

import hashlib
import random
from typing import Any


def _stable_hash(obj: Any) -> int:
    """Return a stable 64-bit hash for any object."""
    data = repr(obj).encode("utf-8")
    digest = hashlib.blake2b(data, digest_size=8).digest()
    return int.from_bytes(digest, "big")


def seed_for(save_seed: int, *ids: object) -> random.Random:
    """Return a deterministic PRNG for the given save seed and identifiers."""
    seed = save_seed & 0xFFFFFFFFFFFFFFFF
    for obj in ids:
        seed ^= _stable_hash(obj)
    return random.Random(seed)


__all__ = ["seed_for"]
