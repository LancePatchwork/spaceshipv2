# Starship Simulator — Modular Design Index + M01 SRS Spec (v0.2)

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
- **M01 SRS (Ship Resource Service)** — **Status: Frozen (v0.2)** — spec below.
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

# M01 — Ship Resource Service (SRS) — Implementation Spec (v0.2)

**Status:** Frozen

### 1. Scope
A **resource‑agnostic flow system** that auto‑wires module inputs/outputs at runtime and solves per‑tick transfers subject to **rate limits, capacities, priorities, and losses**. Handles **power, heat, atmosphere, fluids, solids (ore/ingots), data**. Integrates with **Thermal** (M04), **Geometry/Placement** (M03), **Event System** (M02), **Mass/Propulsion** (M06).

### 2. Design Principles
- **Declarative modules**: Modules declare ports (inputs/outputs) and rate limits; no hardcoded pipelines.
- **Auto‑detection**: When a module is installed, SRS matches compatible resources and extends the graph.
- **Deterministic**: Same inputs → same flows. Tick‑driven, single‑threaded solver for reproducible saves.
- **Port‑gated, perfect network**: The **network itself is ideal** (no losses, no distance costs); throttling and arbitration happen **only at ports** to keep CPU usage low.
- **Data goes through SRS**: treat data like any other resource. Bandwidth/latency are represented by **port rate limits** (and later, optional QoS), not by network geometry.

### 3. Core Concepts & Types (minimal forms)
- **ResourceType**: `{ id, kind }` where `kind ∈ { power, heat, fluid, atmo, solid, data }`.
- **Port**: `{ id, module_id, direction: input|output|bidirectional, resource_type_id, rate_max, max_request_priority }`
  *`max_request_priority` caps how “high” this port may bid for a resource (prevents a refinery from stealing shield power unless overridden by officers/captain).*
- **Module (Node)**: `{ id, name, surface_area_m2, mass_kg, ports[], controller_ref, storages?[] }`
  Storage (batteries, tanks, cargo) is **module‑level**, not per‑port.
- **Flow (record)**: `{ resource_type_id, source_port_id, sink_port_id, rate_actual }` for the last committed tick.
- **HardlinkPolicy (table, MVP)**: external config keyed by `resource_type_id` → `{ allowed: bool }`. Defaults: **power=true, data=true, heat=false** (fluids TBD).
- **Priorities**: smaller number = higher priority (0 critical). Defaults: Life Support=0, Engine=10, Weapons=20, Refinery=40, Cargo=70.
- **Units & Conventions**: Power=kW, Heat=kW, **Fluids=L/s**, Atmosphere=kg/s, Solids=kg/s, Data=Mbit/s. Time=s, Mass=kg.

### 4. Tick Solver (per Δt)
1) **Advertise Supply/Demand**: Each port posts `(need, offer)` considering its storage, `rate_max`, and controller state (e.g., Engine at 60% thrust).
2) **Matchmaking** (perfect bus): For each ResourceType, pair sources ↔ sinks. Sort sinks by **current request priority** (lower is higher). **Tie‑breaker**: lower `max_request_priority` wins (so Life Support beats Refinery if equal). Final tie uses a **seeded PRNG** (`save_seed` + entity IDs) for deterministic replays.
3) **Commit**: Transfer at `min(source.rate_max, sink.rate_max, source_available, sink_space)`; update storages; record `Flow`.
4) **Backpressure & Alerts**: If critical sinks starve, emit `SRSAlert` with cause chain; otherwise, throttle low‑priority consumers.
5) **Determinism**: Same inputs + same seed → same flows.

### 5. Built‑In Behaviors
- **Powerplant**: exposes `output:Power (kW)` limited by core temp (via M04) and fuel feed (fluid input). Can blackstart batteries.
- **Battery/Capacitor**: `input:Power`, `output:Power`, buffers (kWh). Brownout logic: shed low‑priority loads.
- **Life Support**: `input:Power`, `input:Waste`, `output:Water (L/s)`, `output:Air (kg/s)`. Air goes to **Interior Reservoir** (virtual tank with hull‑volume bound). Consumption drain: `crew_count × air_rate`.
  **Interior Reservoir Capacity Rule**: size storage for **12–24 hours** of maximum crew usage, but cap total LS storage footprint to **≤ 1/3 of Life Support module space**.
- **Mining Rig**: `output:Ore (kg/s)`; heat/power as additional inputs/outputs.
- **Refinery**: `input:Ore (kg/s)`, `output:Ingots (kg/s)`, `byproduct:Heat (kW)`; conversion efficiency + latency.
- **Cargo/Tanks**: sink/source for `solid`/`fluid`, enforce mass/volume; connect to **Mass Model** for Δm effects.
- **Heat**: treated as ResourceType with buffers from **Thermal Mass** (M04). Modules dump to **Hull → Armor** chains; radiators add high‑ε area.
- **Data/Computers**: `output:Data`, `input:Data`; port `rate_max` acts as **bandwidth**. MVP models bandwidth only; jitter/latency later at the **port level**.
- **Module Buffer Defaults (General)**: by default, critical modules should provision storage for **12–24 hours at max throughput**, with any single module’s storage footprint capped at **≤ 1/3 of its module space** unless overridden by design.

### 6. JSON Schemas (M11 defines canonical versioned forms)
- **ResourceType.json** (minimal)
```json
{ "id": "power", "kind": "power" }
```
- **Port excerpt** (minimal)
```json
{ "id": "ls_pwr_in", "module_id": "life_support_v1", "direction": "input", "resource_type_id": "power", "rate_max": 50, "max_request_priority": 0 }
```
- **Module excerpt**
```json
{
  "id": "life_support_v1",
  "surface_area_m2": 12,
  "ports": [
    {"id":"ls_pwr_in","module_id":"life_support_v1","direction":"input","resource_type_id":"power","rate_max":50,"max_request_priority":0},
    {"id":"ls_air_out","module_id":"life_support_v1","direction":"output","resource_type_id":"air","rate_max":8,"max_request_priority":0}
  ],
  "storages": [
    {"id":"interior_air","resource_type_id":"air","capacity": 5000}
  ]
}
```

### 7. Interfaces
- **To M02 (Events)** — *emits*: `SRSUpdate`, `SRSAlert`, `FlowCommitted`, `SRSState`.
  *consumes*: `Order:SetModuleThrottle`, `Order:SetPortEnabled`, `Order:SetMaxRequestPriority`, `Order:OverridePriority` (scoped, TTL), `Order:PlaceHardlink`, `Order:RemoveHardlink`.
- **To M03 (Geometry)**: requests trunk lengths/keep‑outs if/when geometry costs are enabled (post‑MVP); MVP ignores geometry.
- **To M04 (Thermal)**: queries layer temperatures; publishes heat dumps; receives radiator capacity updates.
- **To M06 (Mass/Propulsion)**: publishes resource mass deltas per tick.
- **To M10 (UI)**: structured telemetry for dashboards (per resource, bottlenecks, cause chains).

### 8. Acceptance Criteria (MVP)
1) Installing a **Mining Rig** and **Refinery** with a **Cargo Hold** results in automatic **Ore→Ingot** flow without hand wiring.
2) Life Support sustains `crew_count` by maintaining `Interior Reservoir` ≥ threshold; on power loss, **batteries** cover for N minutes, then `SRSAlert: LifeSupportStarved` fires.
3) Increasing **Engine** throttle sheds low‑priority consumers if generation is capped; a dashboard explains exactly which consumers were shed and why.
4) Heat from **Refinery** raises **Hull** temperature; Radiators bring it back down following `εσA(T⁴−T_space⁴)`.
5) Save/Load round‑trip yields identical flows (deterministic replay with seeded tie‑breaks).
6) **Priority cap works**: Refinery cannot request power above `max_request_priority` unless an officer/captain `Order:OverridePriority` is active.
7) **Sleep/Wake**: Under steady state, SRS enters sleep; any **wake trigger** (below) revives it, recomputes for ≥ **5 s**, then sleeps again if stable for **≥ 3 s**.
8) **Manual Hardlinks**: Power/Data hardlinks function as temporary modules and **fail** within **3–4 hours** of heavy use; alerts are emitted before failure.
9) **Life Support Reservoir** proves out: with crew at max usage and power down, reservoir lasts between **12–24 h** (tunable), then triggers starvation alerts.

### 9. Cutlines (MVP→Post)
- No link topology, distance, or transmission losses in MVP.
- No multi‑fluid phase change simulation (boil/freeze) in MVP; treat as scalar resources.
- No pressure dynamics; treat atmosphere as rates with a simple volume bound.
- Geometry costs for routing deferred to M03 v0.2.

### 10. Open Questions
- Replace random tie‑breakers with doctrine/heuristics later?
- Officer/captain override UX: global doctrine vs per‑module temporary override?
- Should **fluids** allow hardlinks (emergency hoses) in MVP or defer to post‑MVP?

### 11. Sleep/Wake & Caching (Performance)
- **Quiescence detector**: if all module storages and port allocations change by < **ε = 1% of port `rate_max`** for **≥ 3 s**, SRS **sleeps**.
- **Active window**: on wake, run solver for **≥ 5 s** before checking quiescence again.
- **Wake triggers** (MVP):
  1) `Order:*` affecting modules/ports/priorities/throttles.
  2) **Power state changes**: generation loss/restore; battery low/high thresholds.
  3) **Storage thresholds**: any storage crosses low/high watermarks.
  4) **Module topology**: install/remove/enable/disable; damage/repair.
  5) **Critical Alerts**: Red Alert; Life Support Critical; Reactor Hot.
  6) **Flight profile**: throttle changes; docking/undocking; entering/exiting hazards.
  7) **Hardlink** placement/removal/failure.
- **Cache**: last stable allocations per resource are cached; on wake, re‑seed from cache to reduce convergence time.
- **Life Support background drain**: while sleeping, LS decrements reservoir by expected consumption; dropping below thresholds triggers a wake + `SRSAlert`.
- **Telemetry**: emit `SRSState: sleeping|active` to UI for debugging.

### 12. Manual Hardlinks (Emergency Routing)
- **Definition**: a *temporary module* with two ports of the same `resource_type_id` that directly bridges a source and sink. Treated like any other module in SRS.
- **Policy**: governed by **HardlinkPolicy** (MVP: power ✅, data ✅, heat ❌, fluids TBD). Created via `Order:PlaceHardlink` and removed via `Order:RemoveHardlink`.
- **Priority**: hardlinks default to a **high request cap** (subject to override) so they can bypass low-priority throttling.
- **Deterioration & Failure**:
  - Maintain a scalar **wear** in [0,∞). Increment each tick as:
    `wear += (rate_actual / rate_max)^1.5 * (dt / base_life_seconds)` with `base_life_seconds ≈ 3.5 h` at 100% utilization.
    When `wear ≥ 1.0` → failure; emit `SRSAlert: HardlinkFailed`.
  - **Usage‑sensitivity**: a shield hardlink at near‑max rate fails **much faster** than a kitchen hardlink at idle.
  - Pre‑failure warning at `wear ≥ 0.8`.
- **Example (module excerpt)**:
```json
{
  "id": "hardlink_power_temp",
  "ports": [
    {"id":"hl_in","module_id":"hardlink_power_temp","direction":"input","resource_type_id":"power","rate_max":200,"max_request_priority":5},
    {"id":"hl_out","module_id":"hardlink_power_temp","direction":"output","resource_type_id":"power","rate_max":200,"max_request_priority":5}
  ]
}
```

### 13. Priority Semantics & Overrides
- **Request priority**: each port bids with a **current request priority** but may not exceed `max_request_priority`.
- **Officer override**: `Order:OverridePriority` can temporarily raise/lower a port’s cap **within a department**; default TTL **300 s** (renewable). Audit logged.
- **Captain doctrine**: `Order:SetMaxRequestPriority` can set global caps per category (e.g., *Combat Doctrine*: Life Support ≤ 0, Engine ≤ 10, Weapons ≤ 15, Refinery ≥ 50). Persists until changed.
- **Tie‑break rule**: if two sinks share the same current request priority, the one with **lower `max_request_priority`** wins.

### 14. Notes & Cutlines
- **MVP** ignores network topology and losses entirely; all gating is at ports. Geometry costs may be enabled post‑MVP.
- **Jitter/latency for data** are out of scope for MVP.
