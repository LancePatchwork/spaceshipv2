### What changed
-

### Spec refs
- M07: Async & atomic snapshots (lines L6–L10, L26–L28)
- M11: Atomic save & versioning (lines L14–L24)
- M02: Event queues, preemption, determinism (lines L21–L36, L44–L47)
- M01: Acceptance criteria #[X]

### Checklist
- [ ] Tests for acceptance criteria
- [ ] No UI->engine calls (UI posts Events only)
- [ ] Snapshots are immutable & atomically published
- [ ] Save/Load is atomic; versions & checksums maintained
