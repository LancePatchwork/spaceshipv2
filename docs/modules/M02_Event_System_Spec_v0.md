# Starship Simulator — M02 Event System Spec (v0.2)

**Status:** Frozen (v0.2)

> Backbone that coordinates *orders → officer intent → crew tasks → system updates* using a single canonical **Event** instance referenced by multiple queues (global + department + personal). Designed for determinism, filtering (no O(N) scans), and preemption.

---

## 1) Scope
- Provide a **central event backbone** for all gameplay: player orders, AI intents, alerts, tasks, timers, updates.  
- Guarantee **deterministic** execution (seeded tie‑breaks) and **access control** so actors only see actionable events.  
- Support **preemption** (e.g., Red Alert interrupts Sleep), **deadlines**, **dependencies**, and **audit logs**.  
- Integrate tightly with **M01 SRS (Frozen)** for wake triggers + orders; feed UI dashboards.

---

## 2) Design Goals
1. **One event, many views**: a single Event object lives on the central queue and is *referenced* in department and personal queues.  
2. **Filter first**: actors subscribe to **audience scopes** and **categories**; they never scan the full queue.  
3. **Deterministic scheduling**: identical inputs + seed → identical outcomes.  
4. **Preemption without chaos**: well‑defined suspend/resume semantics; no orphaned work.  
5. **Low overhead**: O(1) publish, O(1) subscribe enqueue, O(k) personal dequeue where k ≪ N (k = relevant events).

---

## 3) Object Model & Terminology
### 3.1 Event (base)
```json
{
  "id": "01J...ULID",
  "type": "RepairEvent",
  "category": "engineering",
  "audience_scope": ["captain","officers","department:engineering","private:crew_123"],
  "issuer": "actor_id",
  "attention_to": ["dept.officer","dept.crew","bridge.officer"],
  "target": "module_or_coord_id",
  "priority": 10,
  "max_request_priority": 10,
  "preemptible": true,
  "deadline": "ISO8601",
  "ttl_seconds": 600,
  "dependencies": ["event_id"],
  "state": "queued",
  "taker": null,
  "team_size": 1,
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "parent_id": null,                  // NEW: parent event relationship
  "group_id": null,                   // NEW: checklist/playbook run id
  "idempotency_key": null,           // NEW: prevent duplicate spawns
  "progress": 0.0,                   // NEW: 0..1 progress for UI
  "eta_s": null,                     // NEW: estimated remaining seconds
  "severity": null,                  // NEW: info|warn|critical (alerts)
  "qualifiers": ["skill:dc","clearance:eng"], // NEW: claim requirements
  "preconditions": ["suit:on"],     // NEW: must hold before start
  "payload": {"freeform": true},
  "audit": []
}
```

### 3.2 Categories & Types
- **Categories**: `bridge, engineering, medical, security, navigation, ops, damage_control, crew_admin, alerts, environment, comms`.
- **Event types** (non‑exhaustive): `Order:*`, `Task:*`, `Alert:*`, `Update:*`, `Signal:*`, `Timer:*`.

### 3.3 Audience Scopes (filter keys) (filter keys)
- `captain`, `officers`, `department:<name>`, `rank:<e.g., chief>`, `crew:<role>`, `private:<actor_id>`, `shipwide`.

### 3.4 Actors & Access
- **Captain**: sees *all*.  
- **Chiefs** (e.g., Chief Engineer): see `officers`, their `department:*`, and any `alerts`.  
- **Crew**: see events scoped to their department/role or private id.  
- **Medical privacy**: medical events default to `private` + anonymized shipwide summary alerts.

### 3.5 State Machine
```
queued → routed → claimed → active → done
   ↘          ↘          ↘
  expired   cancelled   suspended → active (resume)
                         ↘
                        failed
```

---

## 4) Queues, Routing & Subscriptions
- **Central Queue**: append‑only ring buffer of Event objects.  
- **Indexes**: hash maps from each **audience scope** and **category** to lists of event IDs (maintained on publish/update).  
- **Department Queues**: lightweight views (ID lists) keyed by `department:*`.  
- **Personal Queues**: each actor maintains a local priority queue of *references* to relevant events.  
- **Routing**: on publish, compute `audience_scope` from template + issuer; push event ID into the corresponding indexes; push refs to subscribers.

**No global scans**: crew consume from their **personal queue** only; new items arrive via subscription pushes (or on login, via indexed backfill).

---

## 5) Scheduling, Priority & Preemption
- **Priority number**: lower is higher (0..100). Inherit from parent (orders) unless overridden by officers/captain doctrine.  
- **Preemption**: starting an event with higher priority **suspends** the current active event if `preemptible=true`; suspended event returns to personal queue with state `suspended`.  
- **Tie‑breakers**: 1) lower `max_request_priority`; 2) seeded PRNG (`save_seed + actor_id + event_id`).  
- **Deadlines/TTL**: events crossing `deadline` or `ttl_seconds` auto‑emit alerts and change state (`expired`).
- **Starvation guard (NEW)**: **priority aging** raises the effective priority of long‑waiting noncritical tasks to prevent permanent starvation during long alerts.
- **Claim TTL (NEW)**: after `claim_ttl_s`, unprogressed active tasks auto‑return to queue and **escalate** to officers.

**Example**: `SleepEvent` is `preemptible=true` and priority 90; `RedAlertEvent` priority 0 arrives → Sleep suspends; actor moves to station.

---

## 6) Determinism & Audit
- **IDs**: ULIDs allow time‑ordered, globally unique IDs reproducible in tests.  
- **Seeded randomness**: all ties and stochastic choices use a PRNG seeded by `save_seed`.  
- **Audit entries**: `{ts, actor_id, action, details}` appended on every transition; used for replays and debugging.

---

## 7) Integration — M01 SRS Hooks (frozen)
**Emits (from SRS)**: `SRSUpdate`, `SRSAlert:<reason>`, `FlowCommitted`, `SRSState:sleeping|active`.  
**Consumes (to SRS)**: `Order:SetModuleThrottle`, `Order:SetPortEnabled`, `Order:SetMaxRequestPriority`, `Order:OverridePriority`, `Order:PlaceHardlink`, `Order:RemoveHardlink`.

### 7.1 Selective Wake (Resource‑targeted)
**Signal:WakeSRS** — target resource kinds only; keep unrelated solvers asleep.
```json
{ "resource_kinds": ["power","heat","fluid","atmo","solid","data"], "reason": "string" }
```
- Examples: throttle change → `["power","heat"]`; hardlink power → `["power"]`; LS threshold → `["power","atmo"]`.

### 7.2 Wake Triggers (MVP)
Publishing any of the following issues a targeted `Signal:WakeSRS`: Orders that touch modules/ports/priorities/throttles; power state changes; storage thresholds; module topology changes; critical alerts; flight profile changes; hardlink events.

---

## 8) Event Templates (MVP Set)
> Templates define required/optional payload fields and default audience/priority.

### 8.1 `RepairEvent` (engineering|damage_control)
Payload: `{ component_id, fault_code, est_time_s, tools:[id], parts:[id], location, hazard:bool }`  
Qualifiers: `["skill:dc"]`. Preconditions: `["suit:on"]` if in vacuum.  
Defaults: `priority=15`, `preemptible=false`, `audience=[department:engineering, damage_control, officers]`.  
Claiming: `team_size` configurable; `taker` set on claim.

### 8.2 `PowerRerouteEvent` (engineering)
Payload: `{ from_module_id?, to_module_id?, amount_kW?, doctrine:"shed_low|protect_high" }`  
Defaults: `priority=10`, `preemptible=true`, `audience=[department:engineering, officers]`.

### 8.3 `RouteEvent` (navigation)
Payload: `{ from, to, profile:"econ|standard|burn", eta_s }`  
Defaults: `priority=20`, `preemptible=true`, `audience=[bridge, navigation, captain]`.

### 8.4 `MineEvent` (ops)
Payload: `{ asteroid_id, rig_id, target_mass_kg, rate_override?, safety:"normal|overclock" }`  
Defaults: `priority=25`, `preemptible=true`, `audience=[ops, engineering, officers]`.

### 8.5 `RefineEvent` (ops)
Payload: `{ refinery_id, input:"ore", output:"ingot", batch_kg, efficiency, heat_kW }`  
Defaults: `priority=30`, `preemptible=true`, `audience=[ops, engineering]`.

### 8.6 `SalvageEvent` (ops|security)
Payload: `{ hulk_id, tow?:bool, strip_list?:[module_id], safety:"normal|caution" }`  
Defaults: `priority=35`, `preemptible=true`, `audience=[ops, security, engineering]`.

### 8.7 `FireControlEvent` (tactical)
Payload: `{ target_id, weapon_id, salvo:"single|linked|rolling", aim_mode, cease_on:"order|timer|event" }`  
Defaults: `priority=12`, `preemptible=true`, `audience=[tactical, officers]`.

### 8.8 `RedAlertEvent` (alerts)
Payload: `{ reason:"combat|collision|boarders|life_support", auto_stations:bool }`  
Defaults: `priority=0`, `preemptible:false`, `audience=[shipwide]`.  
Effects: toggling on publishes `Signal:Checklist("red_alert_on")`; toggling off publishes `Signal:Checklist("red_alert_off")`.

### 8.9 `SleepEvent` (crew_admin)
Payload: `{ actor_id, duration_s }`  
Defaults: `priority=90`, `preemptible:true`, `audience=[private:<actor_id>]`.

### 8.10 `MedTriageEvent` (medical)
Payload: `{ patient_id, severity:"minor|serious|critical", location }`  
Defaults: `priority=5..40` (by severity), `preemptible:false`, `audience=[department:medical, officers]`. Privacy required.

### 8.11 `DecompressionEvent` (alerts|damage_control|environment)
Payload: `{ zone_id, severity:"minor|major|catastrophic", auto_bulkheads:bool, LS_pullback:bool }`  
Effects: spawns checklist `decompression_response` (seal bulkheads; LS isolate; route DC teams).  
Defaults: `priority=0..5` (by severity), `preemptible:false`, `audience=[shipwide, damage_control, engineering, officers]`.

### 8.12 `FireEvent` (alerts|damage_control)
Payload: `{ zone_id, class:"A|B|C|D|E", suppressant:"foam|halon|vent", auto_vent:bool }`  
Effects: checklist `fire_response` (activate suppression; vent if safe; isolate power; muster DC).  
Defaults: `priority=0..10`, `preemptible:false`, `audience=[damage_control, engineering, officers]`.

### 8.13 `RadiationSpikeEvent` (alerts|environment)
Payload: `{ source:"solar|reactor|weapon", zone_id?, shielding_req:"none|crew|all", est_duration_s }`  
Effects: `Task:ShelterInPlace` to crew; `Task:RaiseRadiators` may be **inhibited**.  
Defaults: `priority=3`, `preemptible:false`, `audience=[shipwide, medical, engineering, officers]`.

### 8.13b `ThermalAlertEvent` (alerts|engineering)
Payload: `{ locus:"hull|armor|radiator|heat_loop|module:<id>", source:"reactor|refinery|weapons|environment|unknown", metric:"temperature|heat_flux", value_K, threshold_K, severity:"warning|hot|critical" }`  
Effects: publishes `Signal:Checklist("thermal_overtemp", {severity})` and `Signal:WakeSRS{"resource_kinds":["heat","power"]}`.  
Defaults: `priority=2..8` by severity; `preemptible:false`; `audience=[engineering, officers, damage_control]`.

### 8.14 `ReactorScramEvent` (alerts|engineering) (alerts|engineering)
Payload: `{ reactor_id, reason:"overheat|manual|fault" }`  
Effects: pushes `SRSAlert:PowerDrop`; spawns `PowerRerouteEvent`; checklist `reactor_scram_response`.  
Defaults: `priority=1`, `preemptible:false`, `audience=[engineering, officers]`.

### 8.15 `DockingEvent` (navigation|ops)
Payload: `{ target_station_id, mode:"approach|dock|undock", hardpoints:[id], airlock_pair:[id,id] }`  
Preconditions: `suit:on` for EVA modes.  
Defaults: `priority=20`, `preemptible:true`, `audience=[navigation, ops, captain]`.

### 8.16 `AirlockCycleEvent` (ops|security)
Payload: `{ airlock_id, direction:"in|out", evac:bool }`  
Preconditions: `suit:on` if vacuum outside; `seal_ok` required.  
Defaults: `priority=15`, `preemptible:false`, `audience=[ops, security]`.

### 8.17 `EVAEvent` (ops|damage_control)
Payload: `{ team:[actor_id], tether:"yes|no", task:"repair|inspect|salvage", target }`  
Preconditions: `suit:on`, `tether:yes` for repair/salvage unless doctrine overrides.  
Defaults: `priority=12`, `preemptible:false`, `audience=[ops, damage_control, officers]`.

### 8.18 `CargoTransferEvent` (ops)
Payload: `{ from_hold, to_hold, resource_id, rate, mass_kg }`  
Defaults: `priority=40`, `preemptible:true`, `audience=[ops]`.

### 8.19 `FuelTransferEvent` (ops|engineering)
Payload: `{ from_tank, to_tank, resource_id, rate_Lps }`  
Defaults: `priority=25`, `preemptible:true`, `audience=[engineering, ops]`.

### 8.20 `JettisonEvent` (ops)
Payload: `{ target:"cargo|ballast|module", mass_kg, reason }`  
Defaults: `priority=10`, `preemptible:false`, `audience=[ops, captain]`.

### 8.21 `SensorContactEvent` (bridge|tactical|navigation)
Payload: `{ contact_id, classification:"ship|debris|asteroid|signal", confidence:0..1, bearing, range }`  
Effects: optional checklist (collision avoidance).  
Defaults: `priority=30→5` (auto‑raises if collision risk grows), `audience=[bridge, navigation, tactical]`.

### 8.22 `BoardingEvent` (security)
Payload: `{ side:"friendly|hostile", entry_point, est_count, ROE:"nonlethal|standard|deadly" }`  
Defaults: `priority=2`, `preemptible:false`, `audience=[security, officers]`.

### 8.23 `CalibrationEvent` (engineering)
Payload: `{ module_id, procedure:"sensor_align|weapon_boresight|engine_trim", est_time_s }`  
Defaults: `priority=50`, `preemptible:true`, `audience=[engineering]`.

### 8.24 `DiagnosticEvent` (engineering)
Payload: `{ module_id, test_suite:"power|heat|data|integrity", est_time_s }`  
Defaults: `priority=55`, `preemptible:true`, `audience=[engineering]`.

### 8.25 `SoftwareRebootEvent` (engineering|comms)
Payload: `{ system_id, reboot_mode:"warm|cold", expected_downtime_s }`  
Defaults: `priority=20`, `preemptible:false`, `audience=[engineering, comms, officers]`.

### 8.26 `TimerEvent` (system)
Payload: `{ timer_id, due_at, action:"signal|spawn|cancel", target }`  
Defaults: `priority=99`, `preemptible:false`, `audience=[system]`.

---

## 9) Access Control & Visibility Matrix (MVP)
| Role | Sees |
|---|---|
| Captain | All categories & scopes |
| First Officer | officers, shipwide, all department summaries |
| Chiefs | their department, officers, alerts |
| Crew | their department, their role, private |
| Medical | medical + alerts + summaries; privacy exceptions logged |

**Notes**: Filtering is enforced server‑side via subscriptions; client cannot fetch outside scopes.

---

## 10) Personal Scheduler (per actor)
- Maintains **active**, **suspended**, **queued** lists.  
- New arrivals are sorted by `(priority, deadline, seeded_tie)`; if `preemptible` and higher‑priority task arrives, **swap**.  
- **Auto‑resume**: when higher‑priority task completes, resume highest priority suspended task.

---

## 11) Performance Targets
- Publish: ≤ 50 µs avg per event (in tests).  
- Subscription enqueue: ≤ 5 µs per audience scope.  
- Personal dequeue step: O(log k) (heap).  
- Memory: central ring buffer sized for last 10k events; older archived.

---

## 11.1 Signals & Checklists (spawn-on-signal)
**Signal:Checklist(name, params?, idempotency_key?)** — data‑driven spawns with **idempotency** to prevent duplicate floods.
```json
{ "name": "red_alert_on", "params": {"auto_stations": true}, "idempotency_key": "redalert:01" }
```
**Checklist Definition** (`/data/checklists/*.json`)
```json
{
  "name": "red_alert_on",
  "spawns": [
    { "type": "Task:DonVacSuit", "audience": ["shipwide"], "priority": 0, "preemptible": false, "idempotency_key": "donvac:shipwide" },
    { "type": "Task:DistributeCrew", "audience": ["department:engineering"], "priority": 5, "preemptible": true, "payload": {"pattern": "repair-ready"}, "idempotency_key": "eng:distribute" },
    { "type": "Task:SecureCargo", "audience": ["department:ops"], "priority": 10, "preemptible": true, "idempotency_key": "ops:secure" },
    { "type": "PowerRerouteEvent", "audience": ["department:engineering"], "priority": 10, "payload": {"doctrine": "protect_high"}, "idempotency_key": "eng:protect_high" },
    { "type": "Task:RaiseShields", "audience": ["tactical"], "priority": 8, "preemptible": true, "idempotency_key": "tac:raise" },
    { "type": "Task:WarmWeapons", "audience": ["tactical"], "priority": 8, "preemptible": true, "idempotency_key": "tac:warm" }
  ],
  "on_clear": [
    { "type": "Task:DoffVacSuit", "audience": ["shipwide"], "priority": 10, "preemptible": true, "idempotency_key": "donvac:off" },
    { "type": "Task:StandDownShields", "audience": ["tactical"], "priority": 12, "preemptible": true, "idempotency_key": "tac:standdown" }
  ]
}
```
**Additional Checklists (examples)**
- `decompression_response`: seal bulkheads; LS isolate; route DC teams; muster.  
- `fire_response`: select suppressant; isolate power; vent if safe; evacuate.  
- `reactor_scram_response`: secure core; shed noncritical loads; bring batteries online.  
- `thermal_overtemp`: raise radiators; shed low‑priority heat sources (e.g., refinery); throttle engines/weapons; open internal heat shunts; evac hotspots if *critical*.  
- `collision_imminent`: evasive route; secure cargo; brace; lock bulkheads.  
- `docking_ops`: approach profile; mag‑clamp; cycle airlock; cargo/fuel transfer tasks.  
- `eva_ops`: suit checks; tether; airlock cycle; timed check‑ins.

**Suppression & Hysteresis**: checklist signals support **debounce windows** and **hysteresis** to avoid alert thrash.

---

## 11.2 Watchers (Auto‑Spawn)
Background monitors transform raw telemetry into events/signals. Each watcher enforces idempotency and selective wake.
- **ReactorWatcher**: temps/flux → `ReactorScramEvent` or `SRSAlert:PowerDrop` + `ThermalAlertEvent` if overtemp without scram.
- **AtmoWatcher**: pressure/leaks → `DecompressionEvent`.
- **ThermalWatcher**: hull/armor/radiator temps & heat loop balance → `ThermalAlertEvent(severity)`; also raises `SRSAlert:HeatSaturation` for SRS; may inhibit radiator extension during radiation spikes.
- **CollisionWatcher**: contact solutions → `SensorContactEvent` and checklist `collision_imminent`.
- **FireWatcher**: heat/smoke sensors → `FireEvent`.
- **DockingWatcher**: relative pose/thrust → `DockingEvent` transitions.
- **SecurityWatcher**: unauthorized access → `BoardingEvent` (hostile) or `SecurityAlert`.
- **IntegrityWatcher**: stress/strain → `Update:IntegrityDegraded` and `RepairEvent` suggestions.

