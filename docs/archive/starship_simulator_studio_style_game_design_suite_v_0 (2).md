# Starship Simulator — Studio-Style Game Design Suite (v0.1)

> This is a *studio-style* design package built from your brainstorming notes, organized top‑down so we can refine in layers. v0.1 = high‑level; lower sections include MVP specs and cutlines. We’ll iterate on each section.

---

## 1) One‑Pager (Executive Summary)
**High Concept**  
Command a realistic, modular starship in a living universe. Time, crew movement, and systems matter—decisions ripple through power, heat, resources, morale, and politics.

**Target Player**  
Fans of deep sims (Aurora 4X, Distant Worlds, Highfleet vibes) who prefer thoughtful planning over twitch combat.

**Design Differentiators**
- Realistic time‑based operations and crew movement (no instant actions)
- Fully simulated ship architecture (power/heat/resources flow through real networks)
- Career flexibility (merchant, military, privateer, explorer) with a strong “captain experience”

**Top Risks**  
Complexity bloat, performance, onboarding. (Mitigations in §12.)

**MVP Promise**  
One ship, one complete career loop (miner first), one solar system, and a full captain‑on‑the‑bridge experience.

---

## 2) Design Pillars
1. **Time Has Weight** – Orders, travel, power‑ups/downs, repairs take time; distance and inertia matter.  
2. **People Make the Ship** – Officers/crew have roles, skills, shifts, morale; absence/skill deficits change outcomes.  
3. **Plausible Tech** – No magic systems; modules have limits, trade‑offs, and failure modes.  
4. **Systems Interlock** – Power, heat, fluids, storage, structural integrity are connected; damage cascades.  
5. **Living Context** – Factions, trade, and events proceed even when the player is idle.

---

## 3) Player Experience Goals
- Feel like a captain, not a cursor: give orders, set doctrine, manage people.  
- Strategic tension from timing, logistics, and risk management.  
- Clear feedback: dashboards explain *why* a system is underperforming.  
- Fewer but weighty choices; avoid micromanagement traps where possible.

---

## 4) Core Loops
**Operations Loop** → Plan → Allocate power/crew/resources → Execute over time → Monitor telemetry → Adjust → Maintain.  
**Mining Loop (MVP)** → Survey asteroids → Deploy mining subsystem → Extract ore → Refine to ingots → Sell cargo → Repair/upgrade → Repeat.
**Combat Loop** → Detect → Maneuver → Allocate power/heat → Fire/defend → Damage control → Withdraw or board.  
**Progression Loop** → Earn XP/rep → Train crew → Unlock modules/permits → Tackle harder contracts.

---

## 5) Scope & Cutlines
**Must‑Have (MVP)**  
- One playable ship hull with modular internals  
- Core systems: power plant, distribution, batteries/caps; main engine + RCS; avionics; life support; hull; cargo  
- Crew roles: Captain, First Officer, Chief Engineer, Medical Officer (plus minimal supporting staff)  
- Single‑system navigation; sensors; basic comms  
- Mining/refining/trade loop; basic economy (supply/demand curves, shortages, price drift)  
- Simple combat: 1–2 weapon families, shields/armor, localized damage & repairs  
- Data‑heavy UI with dashboards and logs (low art burden)

**Should‑Have (v0.x)**  
- Boarding actions; anomaly scanning; faction rep  
- Additional officer specializations (Tactical, Ops, Comms)  
- More module variants and upgrade tiers

**Won’t‑Have (for MVP)**  
- Freeform FTL; large fleets; deep diplomacy trees; manufacturing chains; aliens first pass  
- "Component Quality" stat as a standalone attribute — replaced with *Reliability & Wear* model (see §7.3).

---

## 6) Feature List (MoSCoW w/ Acceptance)
- **MUST**  
  - Modular ship with resource networks (power/heat/fluids). *AC:* components route flow; failure isolates per‑node.  
  - Time‑based orders + crew traversal. *AC:* pathing, station assignments, shift fatigue.  
  - Miner loop end‑to‑end (mine→refine→trade). *AC:* asteroid targeted → ore extracted → ore refined → cargo sold → upkeep → next job.
  - Localized damage & repairs. *AC:* specific modules disabled; repair requires parts, time, and skill.  
- **SHOULD**  
  - Tactical UI for combat energy/shield arcs and salvo timing.  
- **COULD**  
  - distress calls; random ship failures.  
- **WON’T (MVP)**  
  - Planetary landings; player‑owned stations; fleet command; basic faction standing; anomaly mini‑events.

---

## 7) Systems Design (v0.1 Overviews)
### 7.1 Ship Architecture & Ship Resource Service (SRS)
- **Modules**: interchangeable parts mounted to **surface area (m²)** budgets rather than S/M/L slots.
- **SRS (resource-agnostic)**: every module declares **inputs/outputs** with **rate limits** and **capacities**. The SRS auto-wires resources at runtime by matching compatible types (power, heat, fluids, atmosphere, solids, data).
  - **Powerplant**: rate-limited **output** (kW) bounded by reactor capacity and heat ceiling.
  - **Battery/Capacitor**: rate-limited **input/output** with storage capacity; supports brownout/blackstart logic.
  - **Life Support**: rate-limited **input: power**, **input: waste**, **output: water**, **output: air** routed to a virtual **“Ship Interior Reservoir”** (unlimited rate, bounded by hull volume). Crew consumption pulls from Interior Reservoir at **#crew × per‑capita air rate**.
  - **Mining Module**: produces **Ore** (solid) as a rate-limited **output**.
  - **Refinery Module**: consumes **Ore** (input) and produces **Ingots** (output) with heat/power byproducts.
  - **Cargo/Tanks**: default **sinks** for solids/liquids; enforce mass/volume limits.
- **Auto-detection**: when a new module is installed, its declared IO causes SRS to extend the graph; flows are solved per tick with priorities and throttling.

### 7.2 Mass & Propulsion Coupling
- **Dynamic Mass**: total ship mass updates each tick from hull, modules, fuel, **ore/ingots**, cargo, and crew.
- **Flight Model**: thrust and Δv compute against current mass; refining ore to ingots changes mass/volume and affects maneuvering.

### 7.3 Reliability & Wear (replaces “Quality”)
- **State** = *Health* (damage) × *Reliability* (prob. of failure) × *Calibration* (efficiency).  
- **Drivers**: age, cycles, environment (heat/rad), maintenance history, part grade.  
- **Gameplay**: preventive maintenance windows; risky overclocks raise failure odds.

### 7.4 Crew & AI
- **MVP Simplification**: no personal needs beyond what **Life Support** supplies (no food/morale systems yet).
- Roles, skills, shifts; officers set doctrine; crew pathfind to stations.
- **Event-driven behavior**: each actor maintains a personal queue with priorities and preemption (e.g., Red Alert preempts Sleep). See §10.1.

### 7.5 Combat
- Long‑range, time‑based engagements; meaningful pre‑combat prep (cooling, capacitor charge).
- Localized hits cause cascading outages; damage control is event‑driven (no minigame). Players set priorities; crew executes via §10.1.

### 7.6 Economy & World
- Price fields per station with drift and shocks; contracts spawned by shortages/surpluses.  
- Factions as simple supply graphs at MVP; expand to politics later.
- **Salvage & Hulks** (design intent): ships are rarely vaporized; unless a powerplant goes critical, combat produces **lifeless hulks** that persist in-world as salvage targets, research assets, or navigation hazards. Economy spawns contracts to tow, strip, or secure hulks.

### 7.7 Ship Sizes, Geometry & Decking
- **Ship Size Categories** (scales content, budgets, crew):  
  - `tiny_craft` — 8–30 m; shuttles/fighters/lifepods; crew 1–6.  
  - `light_vessel` — 30–80 m; crew 10–60.  
  - `medium_vessel` — 80–150 m; crew 60–300.  
  - `heavy_vessel` — 150–280 m; crew 300–800.  
  - `capital_vessel` — 280–380 m; crew 800–2,000.  
  - `dreadnought_vessel` — 380–650 m; carrier-scale; crew 2,000–6,000+.
- **Hull Shape & Surface Area**: hull approximated as an **ellipsoid** with semi-axes `a=length/2`, `b=width/2`, `c=height/2`. Surface area uses Knud Thomsen’s approximation:  
  `S ≈ 4π * ((a^p b^p + a^p c^p + b^p c^p)/3)^(1/p)` with `p≈1.6075`.  
  Surface area (m²) is the **module budget** for exterior/edge-mount systems.
- **Decking**: choose `deck_height_m ∈ [3,4]`; compute `deck_count = floor(height / deck_height_m)`.  
  Per-deck usable area ≈ interior cross-section minus structural corridors. Reserve **15–25%** for corridors, ladders, lift shafts, air ducts, and trunking. Round **down** to avoid overfill.

### 7.8 Thermal & Radiation Model
- **Thermal Battery Ship**: the SRS treats **heat** as a resource. Modules dump heat to **hull**; hull conducts to **armor**; consumers (e.g., life support heaters) can pull heat back if beneficial.
- **Thermal Capacity**: track per-layer mass `m` and specific heat `c`; capacity `C = Σ(mᵢ·cᵢ)`.  
- **Material States**: each layer tracks temperature bands: *cool* → *hot* → *critical* → **melted** (at `T ≥ T_melt`), impacting integrity and seals.
- **Radiative Emission**: deep space radiates via **Stefan–Boltzmann** law (your “IR emission thing”):  
  `P_rad = ε σ A (T⁴ − T_space⁴)` where emissivity `ε` is material-dependent, `σ` is the constant, `A` is radiating area, and `T_space` defaults to ~3 K (intergalactic background). Radiator modules boost `A` and `ε`.
- **Conduction/Convection**: internal conduction uses material `k` (thermal conductivity). No convection in vacuum; docking/atmospheres enable it contextually.

### 7.9 Materials & Armor Database (MVP Schema)
Each material entry defines:  
`name`, `density`, `yield_strength`, `ultimate_strength`, `hardness`, `fracture_toughness`, `spall_resistance`, `shock/explosion_resistance`, `thermal_conductivity (k)`, `specific_heat (c)`, `melting_point`, `emissivity`, `reflectivity/absorptivity vs laser λ`, `radiation_shielding_coeff`, `cost`, `rarity`.
- **Starter Set** (examples; numbers TBD):  
  - *Ti‑6Al‑4V* (titanium alloy): strong/medium‑k/low‑ε.  
  - *Al‑Li alloy*: light/high‑k/good hull frames.  
  - *Maraging steel*: high toughness/armor backing.  
  - *Tungsten carbide ceramic*: ablative/laser‑resistant tiles (high absorptivity, high `T_melt`).  
  - *Carbon composite sandwich*: structural skin, low density, directionally anisotropic k.  
  - *Boron carbide*: kinetic penetrator resistance.  
  - *Aerogel laminate*: thermal buffer/insulation.  
  - *Ablator resin*: sacrificial anti‑laser coating.
- **Armor Stacks**: define layers with thicknesses; SRS heat flow respects layer `k` and `ε`; combat resolves penetration/spall per layer.

### 7.10 Physics Simplifications (Toggleable)
- **Inertial Bleed (“space jello”)**: optional damping `dv/dt = −κ v` with tunable time constant; off in *Simulation* mode, on in *Story* mode for easier piloting.
- **Structural Grace**: ships are **hard to kill**; default outcome is **powerless hulk** unless catastrophic reactor failure triggers *critical event*.

---

## 8) Content Spec (MVP)
**Ship**: 1 frigate‑class hull with modular internals allocated by **surface area (m²)**.  
**Modules (initial)**: power plant, power distribution, battery, capacitor, main engine, RCS, avionics, sensors, comms, life support, hull, cargo, basic shield/armor, **mining rig, refinery**.
**Resources**: fuel, spare parts, supplies/food, meds, ammo, **raw ore, ingots**.
**Weapons**: kinetic battery + beam variant (simple) with distinct heat/power profiles.  
**Locations**: 1 star system, 4–6 stations/colonies with varied prices, 2 travel hazards.  
**NPCs**: pirates/raiders, patrol, merchants.

---

## 9) UX/UI Direction
- **Aurora‑style data‑forward UI**: tables, charts, logs; minimal animations.  
- **Dashboards**: Engineering (power/heat), Navigation, Tactical, Crew & Ops, Cargo & Contracts.  
- **Explainability**: hover tooltips show upstream/downstream causes (e.g., low shield due to heat throttle).  
- **Time Controls**: pause/1x/3x/fast while preserving order queue integrity.

---

## 10) Technical Design (Overview)
- **Architecture**: data‑driven modules & networks; **event‑queue–backed** simulation tick; deterministic core for saves/replays.  
- **Data**: JSON/CSV prototypes for modules/resources/contracts; versioned schema for save compatibility.  
- **Performance**: fixed‑step sim thread, UI thread, coarse LOD for off‑screen systems.  
- **Modding**: load modules/resources from data packs; scripted content hooks.  
- **Persistence**: rolling autosaves; backward‑compatible migrations.

### 10.1 Event System (Backbone)
- **Single source of truth**: All orders, AI intents, system ticks, alerts, and UI notifications are **Events** on a central queue; entities keep **references** to the same event in their personal queues for prioritization.
- **Flow**: Player issues order → Event enqueued (addressed to Officer role) → Officer consumes, emits child events (tasks) → Crew claim tasks; progress generates updates → Completion cascades follow‑ups.
- **Preemption**: Personal queues allow **active event** to be suspended by higher‑priority events (e.g., Red Alert, Life Support Critical). Suspended events remain in the queue.
- **Templates**: `RepairEvent`, `RouteEvent`, `FireControlEvent`, `PowerRerouteEvent`, `RedAlertEvent`, `SleepEvent`, `MineEvent`, `RefineEvent`, `SalvageEvent`.
  - **Required fields (example `RepairEvent`)**: `id`, `issuer`, `category`, `audience_scope`, `attention_to` (dept/officer/crew tags), `target`, `priority`, `time_to_complete`, `taker` (nullable), `dependencies`, `created_at`, `deadline`, `preemptible`, `state` (queued|active|suspended|done|failed), `notes`.
- **Categories & Scopes (for fast filtering)**:  
  - `category`: `bridge`, `engineering`, `medical`, `security`, `navigation`, `ops/logistics`, `damage_control`, `crew_admin`, `alerts`.  
  - `audience_scope`: `captain`, `officers`, `department:<name>`, `crew:<role>`, `private:<person_id>`.  
  - **Access control**: Captain sees all; Chiefs see their departments; individuals see only events they can act on. Med events default `private` except summary alerts.
- **Indexing**: per‑dept queues + per‑actor queues; O(1) lookup by `audience_scope`; global topic streams for UI dashboards.
- **Acceptance**: determinism on replay; multiple listeners referencing the **same event instance**; human‑readable audit log; priority inversion protection.

### 10.2 Geometry & Layout Solver
- **Inputs**: `length, width, height`, deck height range (3–4 m), propulsion footprint, corridor budget %, lift/ladder count, module surface‑area budgets, keep‑outs.
- **Steps**:  
  1) **Ellipsoid shell** from dimensions; compute interior volume & per‑deck cross‑sections.  
  2) **Deck generation**: `deck_count=floor(height/deck_height_m)`; lay structural rings/longitudinals.  
  3) **Corridor graph**: reserve spine and ring corridors; place **lift shafts** and ladders to ensure vertical connectivity every N meters.  
  4) **Propulsion constraint**: place main engine block touching the aft exterior surface (rear wall) with required clearance.  
  5) **Module packing**: greedy + local search to allocate modules onto decks meeting **surface‑area budgets**; each module must border a corridor node (door).  
  6) **SRS wiring**: auto-route shortest paths for resource trunks; penalize crossings; enforce max run lengths.  
  7) **Validation**: ensure pathfinding from corridors to every module; ensure evacuation routes; compute maintenance access.
- **Outputs**: per‑module transform, connected corridor graph, trunk routes, reserved areas; reports for overfill/overweight.

---

## 11) Production Plan & Milestones
**M0 – Prototype (4–6 weeks)**  
- Box ship + networks + power/heat flow; crew pathing; console/UI mock; one mining job.

**M1 – Vertical Slice (6–8 weeks)**  
- Miner loop complete (mine→refine→trade); simple combat; damage control; dashboards usable end‑to‑end.

**M2 – Alpha (8–10 weeks)**  
- Economy tuning; more module variants; faction prices; tutorial & tooltips.

**M3 – Beta (6–8 weeks)**  
- Stability, UX polish, performance passes, accessibility basics.

---

## 12) Risks & Mitigations
- **Complexity Bloat** → MoSCoW + hard cutlines; one career complete before adding others.  
- **Perf/Sim Load** → profiling early, LOD for background systems, cap crew count for MVP.  
- **Onboarding** → interactive tutorial, contextual tips, “why is X failing?” inspector.  
- **Data Volatility** → schema versioning + migrations; automated tests for save/load.

---

## 13) Telemetry & Tuning (MVP)
- Session length, contract success/fail, heat/power brownouts, crew fatigue incidents, repair queue wait times, player cashflow.  
- Use logs to detect difficulty spikes or economy exploits.

---

## 14) Accessibility & Options (first pass)
- Rebindable controls; color‑agnostic palette; scalable fonts; reduced flicker/animation mode; auto‑pause on alerts.

---

## 15) Content Roadmap (Post‑MVP Ideas)
- Boarding & security gameplay; anomaly investigations; research labs; diplomacy layer; multi‑ship support; manufacturing and mining chains.

---

## 16) Glossary
- **Module**: a physical system with interfaces.  
- **Surface Area (m²)**: mounting budget for modules replacing S/M/L slot sizes.  
- **Ellipsoid Hull**: shape defined by semi‑axes a,b,c; surface area by Knud Thomsen approximation.  
- **Deck Height**: vertical clearance per deck (3–4 m); `deck_count = floor(height/deck_height)`.  
- **SRS (Ship Resource Service)**: resource‑agnostic IO graph that auto‑wires module inputs/outputs and enforces rate/capacity (includes **heat** flows).  
- **Stefan–Boltzmann Radiation**: formula for radiative heat loss `εσA(T⁴−T_space⁴)`.  
- **Inertial Bleed**: optional gameplay damping `dv/dt=−κv`.  
- **Event Category/Scope**: tags and access controls limiting who sees/acts on which events.

---

## 17) Changelog
v0.3 – Add ship size categories; ellipsoid hull & decking; thermal/ radiation model with hull as thermal battery; materials/armor DB; inertial bleed toggle; salvageable hulks; event categories & access control; geometry & layout solver.

v0.2 – Miner-first MVP; add SRS; switch to m² surface area; event system as backbone; simplify crew needs; remove damage-control minigame; update scope & milestones.

v0.1 – Initial studio‑style pass; replaces “Quality” with Reliability & Wear model; locks MVP scope.

