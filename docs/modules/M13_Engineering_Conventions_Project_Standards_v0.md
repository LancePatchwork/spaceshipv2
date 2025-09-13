# M13 — Engineering Conventions & Project Standards (v1, Python‑first)

**Status:** Draft → propose lock after 1–2 sprints

## 0) Goals
- Enable multi‑dev collaboration with **deterministic sim**, strong typing, and fast feedback.
- Python‑first stack; UI in **Qt for Python (PySide6)** using a **widget‑driven** architecture (M12‑P).
- Prefer **pure functions + immutable snapshots** in engine; side‑effects at edges (event I/O, persistence).

---

## 1) Languages & Tooling
- **Python**: 3.11+ (3.12 preferred).
- **Packaging**: `uv` or `poetry` (choose one; default: `uv`).
- **Type checking**: `mypy --strict`.
- **Lint/Format**: `ruff` (lint + import sort) and `black` (line length 100).
- **Tests**: `pytest`, `pytest-qt` (UI), `hypothesis` (property tests for solvers), `freezegun` (time).
- **Schemas**: `pydantic v2` for event payloads and save‑file chunks.
- **CLI/dev**: `typer` for tools, `rich`/`textual` for debug TUI.

---

## 2) Repo Layout (monorepo)
```
/pyproject.toml
/uv.lock or poetry.lock
/.editorconfig /.pre-commit-config.yaml /.ruff.toml /.env.example

/engine/                # simulation + systems (pure/core)
  __init__.py
  m01_srs/
  m02_events/
  m03_geometry/
  m04_thermal/
  m05_materials/
  m06_layout/
  m08_crew/
  m09_combat/
  m10_market/
  m11_persist/
  lib/                  # rng, units, result, time, scheduler
  workers/              # asyncio tasks, thread/process pools
  tests/

/ui/                    # PySide6: widget registry + containers
  __init__.py
  core/                 # registry, tiles, docking, theme
  widgets/              # each widget folder owns its code
    port_monitor/
    srs_ports_table/
    srs_flows/
    crew_table/
    event_log/
  windows/              # window templates (layout only)
  resources/            # qss, icons, fonts
  tests/

/data/                  # materials, size defaults, checklists (json)
/tools/                 # codegen, migrations, importers
/docs/                  # exported M01..M13, RFCs
```

---

## 3) Naming & Style
- **Modules/files**: `snake_case.py`.  **Classes**: `PascalCase`.  **func/vars**: `snake_case`.
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `SRS_EPSILON`, `DEFAULT_DECK_HEIGHT_M`).
- **Enums**: `Enum` subclasses (PascalCase members).
- **Tests**: `test_*.py` colocated in `tests/` mirroring package tree.

---

## 4) Units & Types
- Use **SI only**. Suffix persistent numeric fields with units in name (`*_W`, `*_Lps`, `*_kgps`, `*_m`, `*_m2`, `*_m3`, `*_K`).
- Provide light type aliases (not runtime):
```py
Watts = float; LitersPerSecond = float; Kelvin = float
```
- For runtime checks where needed, validate with **pydantic** models.

---

## 5) Event System (M02) Conventions
- **Type names**: dot‑namespaced strings: `m02.order.repair`, `srs.power.shortage`, `alerts.red`.
- **Base model** (pydantic):
```py
class Event(BaseModel):
    id: str  # ULID
    type: str
    ts_ms: int
    issuer: str | None = None
    audience_scope: list[str] = []  # e.g., "department:engineering", "shipwide"
    category: str | None = None
    priority: int = 50  # 0 highest
    max_request_priority: int | None = None
    preemptible: bool = True
    deadline: datetime | None = None
    ttl_seconds: int | None = None
    dependencies: list[str] = []
    state: Literal['queued','routed','claimed','active','suspended','done','failed','expired','cancelled'] = 'queued'
    taker: str | None = None
    team_size: int = 1
    parent_id: str | None = None
    group_id: str | None = None
    idempotency_key: str | None = None
    progress: float = 0.0
    eta_s: int | None = None
    severity: Literal['info','warn','critical'] | None = None
    qualifiers: list[str] = []
    preconditions: list[str] = []
    payload: dict[str, Any] = {}
```
- **Determinism**: seeded PRNG via `random.Random(save_seed ^ hash(actor_id) ^ hash(event_id))` for tie‑breaks.
- **Queues**: central append‑only store + indexed views (by audience/category); personal heaps per actor.

---

## 6) SRS Conventions (M01)
- Ports are single‑resource; edges connect matching kinds only.
- Tie‑breaker: sink with higher **max_priority** wins on equal demand.
- Quiescence: solve ~10s then sleep; **scoped wakes** only.
- Hardlink wear: 3–4h to failure, throughput‑weighted.

---

## 7) UI Architecture (M12‑P)
- **Widget registry** (backend) defines behavior; windows are **containers** with **tiles** pointing to **instances**.
- Context menus supplied by widget; containers add generic actions (Remove/Duplicate/Open).
- Extraction: any table/row can spawn a `WidgetInstance` and drop a tile into any container.
- **Signals/slots** (Qt) for user actions; **atomic snapshot** from engine updates model in the registry.

---

## 8) Async & Snapshots (M07)
- Use **asyncio** for I/O and scheduling; CPU‑heavy work in **ProcessPoolExecutor**.
- Publish **immutable snapshots** (frozen dataclasses / tuples). UI reads **last committed** snapshot; never mid‑update.
- Cadence: combat batches 50–200 ms; SRS localized; market 24h; charts ≥100 ms.

---

## 9) Persistence (M11)
- Save **instances** + **window layouts** separately from engine state.
- Atomic write: tmp → `os.replace()`; per‑chunk checksum; per‑module version keys (`m01_version`, `m12_version`, …).
- Schemas are **pydantic** models with migrations.

---

## 10) Coding Guidelines
- Engine: pure functions where possible; avoid hidden globals; pass context explicitly.
- Errors: return `Result[T,E]` (`Ok(value)`/`Err(error)`) or raise inside boundaries, never across worker/process.
- Logging: structured via `structlog` or `logging` JSON formatter.
- Comments: module header + docstrings (PEP257); public functions/classes have docstrings.

---

## 11) Testing
- **Unit**: solvers, allocators, event routing (80%+ coverage target).
- **Component (UI)**: `pytest-qt` with fake `WidgetCtx`.
- **Integration**: event chains post→effect→spawn; persistence round‑trip.
- **E2E**: smoke flows (bridge, damage control, SRS inspector, extraction).
- **Determinism**: seed RNGs; compare snapshot hashes with FP tolerance.

---

## 12) Git & PR Workflow
- Branch names: `feat/m09-salvo-solver`, `fix/m12-contextmenu`, `chore/…`.
- Conventional Commits enforced via pre‑commit hook (optional `commitizen`).
- PRs must include tests and screenshots/GIFs for UI.
- CI: ruff, black, mypy, pytest must pass.

---

## 13) Pre‑commit
Use **pre‑commit** with hooks: ruff, black, mypy (fast mode), trailing‑whitespace, end‑of‑file‑fixer.

---

## 14) Theming & UX
- Single QSS theme file; no hard‑coded colors in widgets.
- Accessibility: keyboard focus visible; context menus `Esc` closes; drag handles large enough.
- Perf budget: avg frame ≤ 4 ms; log spikes.

---

## 15) Examples
### 15.1 Result type
```py
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar('T'); E = TypeVar('E')
@dataclass
class Ok(Generic[T]):
    value: T
@dataclass
class Err(Generic[E]):
    error: E
Result = Union[Ok[T], Err[E]]
```

### 15.2 Event schema example
```py
class PowerShortage(Event):
    type: Literal['srs.power.shortage'] = 'srs.power.shortage'
    port_id: str
    deficit_W: float
```

### 15.3 Atomic publish
```py
from threading import Lock

_current_snapshot = None
_lock = Lock()

def publish_snapshot(snap):
    global _current_snapshot
    with _lock:
        _current_snapshot = snap  # atomic swap from readers' perspective

def get_snapshot():
    return _current_snapshot
```

---

## 16) Change Control & Locks
- Frozen modules (M01, M02, M09, M12‑P, etc.) change only via RFC referencing origin doc, with migrations.

---

## 17) Open Questions
- Docking grid + resize spec for tiles.
- Generator for event enums + pydantic models from a single source.
- Unit handling (`pint` vs light conventions).

