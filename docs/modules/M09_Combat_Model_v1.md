# M09 — Combat Model — v1 (Frozen)

## Overview
- **No per‑module HP.** Damage maps to **maintenance level**, faults, and SRS disruptions.
- Weapons: **Lasers** (thermal load / component sniping), **Slug throwers** (penetration with relative‑velocity), **Missiles** (HE/kinetic effects).

## Salvo Resolution
- For ballistic/PDC: we simulate **salvo envelopes**; determine hit chance, then resolve **hit count** on impact (not per bullet).
- Crew skill influences **track quality**, lead error, salvo dispersion.

## Relative Velocity
- Penetration & lethality depend on **relative velocity** at impact (frame‑corrected).

## Radiators
- **Retract** under red alert unless overridden (trade cooling vs. survivability).

## Damage → Maintenance
- Each hit translates into maintenance deltas on affected subsystems (hull, modules, SRS ports/edges). Critical failures generate **events** (M02).

## Async
- Hit queues batched and resolved **async**; applying damage can lag by 50–200ms without affecting feel.
