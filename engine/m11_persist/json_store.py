from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import cast

from engine.lib.config import Paths
from engine.lib.contracts import SaveStore, Snapshot

_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def safe_name(name: str) -> str:
    """Validate that ``name`` only contains safe characters.

    Allowed characters are ``[A-Za-z0-9_-]``. Any other character results in a
    ``ValueError`` being raised.
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"invalid save name: {name!r}")
    return name


class JsonSaveStore(SaveStore):
    """Minimal JSON-based persistence for :class:`Snapshot` objects.

    Snapshots are stored inside :data:`Paths.saves_dir` using ``{name}.json``
    filenames. Writes are performed atomically by first writing to a temporary
    file in the target directory and then replacing the final path.
    """

    def __init__(self, paths: Paths) -> None:
        self._dir = Path(paths.saves_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        safe_name(name)
        return self._dir / f"{name}.json"

    def save(self, snap: Snapshot, *, name: str) -> str:
        path = self._path_for(name)
        fd, tmp_path = tempfile.mkstemp(dir=self._dir, prefix=f".{name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as tmp:
                json.dump(snap, tmp)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        return str(path)

    def load(self, name: str) -> Snapshot:
        path = self._path_for(name)
        with path.open() as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or "meta" not in data or "state" not in data:
            raise ValueError("invalid snapshot")
        return cast(Snapshot, data)
