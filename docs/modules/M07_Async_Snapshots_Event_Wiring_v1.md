# M07 — Async Simulation & Atomic Snapshots — v1 (Frozen)

## Goal
Eliminate main‑loop stutter by doing **heavy work off‑thread** and publishing **atomic snapshots** to consumers (UI, AI, logs).

## Pattern
1. Worker computes a **complete snapshot** (e.g., SRS flows, market prices, charts).
2. When done, **atomically swap** the reference used by consumers.
3. UI widgets re‑render on **identity change** only.

## Where We Apply It
- **SRS solver** (partitioned; localized wake)
- **Combat damage resolution** (queue hits, resolve batches; 50–200ms cadence OK)
- **Market/economy updates** (24h cadence, see M10)
- **Charts/graphs** (load datasets async, publish once complete)
- **Save/Load** (M11) performs write to temp → fsync → atomic rename.

## Event Hooks
- `on_snapshot_ready(topic)` (e.g., `srs`, `market`, `combat_batch`) → publish event for observers.
- **Signals** like `red_alert` spawn **checklists** via M02 (EVAs, station manning, secure cargo).

## Quiescence & Wake
- Subsystem sleeps if deltas < epsilon for N seconds.
- Wake triggers are **scoped** (M01): only relevant partitions wake.

## Safety
- Mid‑update reads use **previous** snapshot.
- Null‑ref guard: UI widgets wait for snapshot presence; show loading skeleton.
