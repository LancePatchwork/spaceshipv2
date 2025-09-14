from __future__ import annotations

import time
from typing import cast

from engine.lib.contracts import Snapshot, SnapshotSource


class PollingSnapshotProvider:
    """Cache snapshots from a source, polling at a fixed interval.

    Consumers call :meth:`get_latest` to retrieve the most recent snapshot. The
    underlying source is polled at most once per ``interval_ms`` to avoid
    unnecessary work, in line with the snapshot pattern from M07 where
    consumers only see *atomic* snapshots.
    """

    def __init__(self, source: SnapshotSource, interval_ms: int = 500) -> None:
        self._source = source
        self.interval_ms = interval_ms
        self._cached: Snapshot | None = None
        self._last_poll_ms = 0.0

    def get_latest(self) -> Snapshot | None:
        """Return the most recently cached snapshot.

        The underlying source is polled if more than ``interval_ms`` has elapsed
        since the last poll. Otherwise the previously cached snapshot is
        returned.
        """

        now_ms = time.monotonic() * 1000
        if now_ms - self._last_poll_ms >= self.interval_ms:
            self._cached = self._source.get_latest()
            self._last_poll_ms = now_ms
        return self._cached


class SnapshotProviderAdapter:
    """Adapt a :class:`PollingSnapshotProvider` to the UI protocol."""

    def __init__(self, provider: PollingSnapshotProvider) -> None:
        self._provider = provider

    def get_latest(self) -> dict[str, object] | None:
        return cast(dict[str, object] | None, self._provider.get_latest())
