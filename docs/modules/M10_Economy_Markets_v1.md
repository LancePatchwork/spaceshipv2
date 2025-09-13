# M10 — Economy & Markets — v1 (Frozen)

## Seed & Cadence
- Price seed rooted in modern benchmarks (iron ore, bauxite, copper, HRC steel, aluminum ingot).
- World updates **every 24h** (sim‑time) on a background worker with **atomic publish**.

## Model (MVP)
- Baseline price + regional multipliers + transport/spread + random walk bounded by fundamentals.
- **Exogenous events** (booms/crashes) are rare impulses with damped decay.

## Integration
- Mining/refining uses these prices for contracts and station boards.
- Snapshots are read‑only in UI; edits create **orders** or **contracts** via M02.

## Safety & Perf
- All computations off‑thread; UI displays last committed snapshot.
- Never partially update tables — replace entire dataset atomically.
