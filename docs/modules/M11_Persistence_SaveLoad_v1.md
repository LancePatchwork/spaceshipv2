# M11 — Persistence (Save/Load) — v1 (Frozen)

## What We Save
- **Ship**: geometry (M03), hull/armor state (M04/M05), SRS (M01) ports/edges/demand/hardlinks/wear, propulsion state
- **Crew**: roster, skills, dept priorities, current tasks
- **Event System** (M02): queues, outstanding tasks, timers
- **Combat** (M09): pending salvos/batches snapshot
- **Economy** (M10): current market snapshot + RNG seeds
- **UI** (M12): widgets `instances` + window `tiles` layouts (with version)

## Format & Versioning
- JSON (chunked) or binary w/ schema. Include `version` per module; provide **migrations**.

## Atomic Write
1) Serialize to temp file
2) fsync
3) Rename over previous (atomic)
4) Emit `save_completed` event

## Load
- Validate versions; apply migrations; publish snapshots atomically.

## Integrity
- Checksum per chunk; refuse partial loads; roll back to last known good.
