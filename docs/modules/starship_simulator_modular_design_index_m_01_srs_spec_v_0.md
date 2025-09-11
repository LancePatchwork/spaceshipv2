# Starship Simulator — Modular Design Index + M01 SRS Spec (v0.1)

> Goal: split the growing GDD into **focused, interlocking module docs** and begin refining each to implementation‑ready specs. This file is the **Index** and contains the **first refined module (M01: SRS)**. Future modules will live as separate docs.

---

## Repository Docs Layout (proposed)
```
/docs
  /index.md                       ← this file (module map + status)
  /modules
    /M01_SRS.md                   ← Ship Resource Service spec (this doc’s second half)
    /M02_Event_System.md          ← Event backbone & access control
    /M03_Geometry_Layout.md       ← Ellipsoid hull, decks, corridors, placement solver
    /M04_Thermal_Radiation.md     ← Thermal battery, radiation, hull/armor coupling
    /M05_Materials_Armor_DB.md    ← Materials schema + initial dataset
    /M06_Ship_Sizes_Decking.md    ← Size categories and deck calculations
    /M07_Mining_Refinery_Loop.md  ← Mine→Refine→Trade loop & economy slice
    /M08_Crew_AI.md               ← Roles, doctrine, pathing (needs Event System)
    /M09_Combat_MVP.md            ← Time‑based combat; damage; no minigame
    /M10_UI_Dashboards.md         ← Engineering, Navigation, Tactical, Ops
    /M11_Data_Persistence.md      ← JSON schemas; versioning; migrations
    /M12_Production_Milestones.md ← Roadmap; risks; telemetry
  /archive
    /brainstorming_v*.md
    /legacy_GDD_v*.md
```

**Workflow**
- Each module doc includes: *Scope*, *Interfaces*, *Data Schemas*, *Algorithms*, *Acceptance Criteria*, *Cutlines*, *Open Questions*.
- Cross‑module dependencies listed up top. All cross‑module APIs live in **M11_Data_Persistence.md**.

---

## Module Map & Status
- **M01 SRS (Ship Resource Service)** — *Now: refined spec below.*  
- **M02 Event System** — queue model, categories, audience scopes, preemption, audit log. *Next up.*  
- **M03 Geometry & Layout** — ellipsoid, deck count, corridor graph, placement constraints.  
- **M04 Thermal & Radiation** — heat as resource, Stefan–Boltzmann, material states.  
- **M05 Materials & Armor DB** — schema + starter materials; armor stacks.  
- **M06 Ship Sizes & Decking** — size categories; deck height rules; surface‑area budgets.  
- **M07 Mining/Refining Loop** — subsystem behavior, ore/ingot IO, contracts, price drift.  
- **M08 Crew & AI** — MVP (no needs beyond Life Support); behavior through Events.  
- **M09 Combat MVP** — engagements, damage routing, "hard to kill" hulks policy.  
- **M10 UI Dashboards** — data‑dense Aurora‑style dashboards and explainers.  
- **M11 Data & Persistence** — schemas, save compatibility, modding hooks.  
- **M12 Production** — milestones, risks, telemetry.

---

# M01 — Ship Resource Service (SRS) — Implementation Spec (v0.1)

### 1. Scope
A **resource‑agnostic flow system** that auto‑wires module inputs/outputs at runtime and solves per‑tick transfers subject to **rate limits, capacities, priorities, and losses**. Handles **power, heat, atmosphere, fluids, solids (ore/ingots), data**. Integrates with **Thermal** (M04), **Geometry/Placement** (M03), **Event System** (M02), **Mass/Propulsion** (M06).

### 2. Design Principles
- **Declarative modules**: Modules declare ports (inputs/outputs), capacities, and rate limits; no hardcoded pipelines.
- **Auto‑detection**: When a module is installed, SRS matches compatible resource types and extends the graph.
- **Deterministic**: Same inputs → same flows. Tick‑driven, single‑threaded solver for reproducible saves.
- **Local first**: Prefer short routes and in‑bay trunks before global backbones; minimize crossings & losses.

### 3. Core Concepts & Types (canonical units)
- **ResourceType**: `{ id, phase: power|heat|fluid|atmo|solid|data, unit, density?, specific_heat?, emissivity?, conductivity?, stackable?:bool }`
- **Port**: `{ id, module_id, direction: input|output|bidirectional, resource_type_id, rate_max, buffer_cap, priority (0..100), losses_per_m, losses_fixed }`
- **Link**: `{ id, from_port, to_port, max_rate, length_m, resistance?, enabled }` (SRS may synthesize internal links inside a module rack.)
- **Buffer**: per‑port storage; **for power/heat** this is virtual (capacitors, thermal mass via M04). For fluids/solids, buffer maps to tanks/cargo volumes.
- **Node (Module)**: `{ id, name, surface_area_m2, mass_kg, ports[], controller_ref }`.
- **Flow**: per‑tick actual transfer `{ link_id, resource_type_id, rate_actual, delta_buffer_src, delta_buffer_dst }`.
- **Priorities**: smaller number = higher priority (0 critical). Default mapping: Life Support=0, Engine=10, Weapons=20, Refinery=40, Cargo ops=70.

### 4. Tick Solver (per Δt)
1) **Advertise Supply/Demand**: Each port posts `(need, offer)` considering its buffer, rate limit, and controller state (e.g., Engine at 60% thrust).
2) **Matchmaking**: For each ResourceType, build bipartite sets (sources ↔ sinks). Sort by **priority then distance**. Compute provisional flows by min of: source rate, sink rate, link capacity, downstream buffer room, upstream buffer available.
3) **Losses & Propagation**: Apply link losses; update provisional flows.
4) **Commit**: Apply buffer deltas and record `Flow` events. Emit **SRSUpdate** to Event System (M02) for dashboards/telemetry.
5) **Backpressure**: If sinks starve, raise **SRSAlert** with cause chain (e.g., "Shield output throttled due to HeatLoop saturated by Refinery").

### 5. Built‑In Behaviors
- **Powerplant**: exposes `output:Power (kW)` limited by core temp (via M04) and fuel feed (fluid input). Can blackstart batteries.
- **Battery/Capacitor**: `input:Power`, `output:Power`, buffers (kWh). Brownout logic: shed low‑priority loads.
- **Life Support**: `input:Power`, `input:Waste`, `output:Water`, `output:Air`. Air goes to **Interior Reservoir** (virtual tank with hull‑volume bound). Consumption drain: `crew_count × air_rate`.
- **Mining Rig**: `output:Ore (kg/s)`; heat/power as additional inputs/outputs.
- **Refinery**: `input:Ore`, `output:Ingots`, `byproduct:Heat`; conversion efficiency + latency.
- **Cargo/Tanks**: sink/source for `solid`/`fluid`, enforce mass/volume; connect to **Mass Model** for Δm effects.
- **Heat**: treated as ResourceType with buffers from **Thermal Mass** (M04). Modules dump to **Hull → Armor** chains; radiators add high‑ε area.

### 6. JSON Schemas (M11 defines canonical versioned forms)
- **ResourceType.json** (excerpt)
```json
{
  "id": "power",
  "phase": "power",
  "unit": "kW"
}
```
- **Module (Ports) excerpt**
```json
{
  "id": "life_support_v1",
  "surface_area_m2": 12,
  "ports": [
    {"id":"ls_pwr_in","direction":"input","resource_type_id":"power","rate_max":50,"buffer_cap":0,"priority":0},
    {"id":"ls_air_out","direction":"output","resource_type_id":"air","rate_max":8,"buffer_cap":2,"priority":0},
    {"id":"ls_water_out","direction":"output","resource_type_id":"water","rate_max":2,"buffer_cap":1,"priority":20}
  ]
}
```

### 7. Interfaces
- **To M02 (Events)**: emits `SRSUpdate`, `SRSAlert`, `FlowCommitted`, subscribes to `Order:SetModuleThrottle`, `Order:Open/CloseValve`, `Order:PrioritySet`.
- **To M03 (Geometry)**: requests path lengths and penalties for trunk routing; receives keep‑outs and max run lengths.
- **To M04 (Thermal)**: queries layer temperatures; publishes heat dumps; receives radiator capacity updates.
- **To M06 (Mass/Propulsion)**: publishes resource mass deltas per tick.
- **To M10 (UI)**: structured telemetry for dashboards (per resource, bottlenecks, cause chains).

### 8. Acceptance Criteria (MVP)
1) Installing a **Mining Rig** and **Refinery** with a **Cargo Hold** results in automatic **Ore→Ingot** flow without hand wiring.  
2) Life Support sustains `crew_count` by maintaining `Interior Reservoir` ≥ threshold; on power loss, **batteries** cover for N minutes, then `SRSAlert: LifeSupportStarved` fires.  
3) Increasing **Engine** throttle sheds low‑priority consumers if generation is capped; a dashboard explains exactly which consumers were shed and why.  
4) Heat from **Refinery** raises **Hull** temperature; Radiators bring it back down following `εσA(T⁴−T_space⁴)`.  
5) Save/Load round‑trip yields identical flows (deterministic replay for a fixed seed/input).

### 9. Cutlines (MVP→Post)
- No multi‑fluid phase change simulation (boil/freeze) in MVP; treat as scalar resources.  
- No pressure dynamics; treat atmosphere as rates with a simple volume bound.  
- Pathfinding cost ignores maintenance clearance until M03 v0.2.

### 10. Open Questions
- Do we allow **manual hard links** (player‑placed hoses/patch cables) for emergency routing?  
- Priority resolution tie‑breakers beyond distance (e.g., doctrine tags)?  
- Should **data** be modeled through SRS or handled separately with latency/jitter (post‑MVP)?

---

## Migration Plan (big file → modules)
1) **Freeze** the current monolithic GDD as `/docs/archive/legacy_GDD_v0.3.md`.  
2) Create module docs M02–M12 with stubs (Scope, Interfaces, TODOs).  
3) Move each corresponding section out of the legacy doc into its module.  
4) Keep **/docs/index.md** as the canonical map (statuses: Draft, Refined, Frozen).  
5) Enforce PR check: any new feature must update a module doc + acceptance tests.

---

## Engineering Guardrails (to prevent repo nukes)
- **Protected branches** with required PR reviews; CI fails if schemas change without migrations.  
- **Delete‑safe scripts**: destructive scripts must require `--yes-iam-sure` + path allowlist.  
- **Schema version gating**: SRS/Event/M04 changes bump `content_schema_version`; loader refuses mixed versions.  
- **Backups**: automated daily doc snapshots.

