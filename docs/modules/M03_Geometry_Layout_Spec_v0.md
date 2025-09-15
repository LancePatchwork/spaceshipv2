# Starship Simulator — M03 Geometry & Layout Spec (v0.1)

**Status:** Draft

> Defines the ship’s physical geometry, hull/armor thickness, deck pitch, ceiling service plenum, corridor graph, propulsion placement, and module packing. Outputs per‑deck usable area and volumes for SRS/thermal calculations.

---

## 1) Scope
- Parametric ellipsoid hull (`a=L/2, b=W/2, c=H/2`).
- **Headroom rule**: fixed **3.0 m clear** per deck **plus** a ceiling (service plenum) thickness.
- Compute **hull thickness** to get inner serviceable volume.
- Derive **deck count/pitch**, corridor & shaft reserves, propulsion‑aft constraint, and per‑deck usable areas for module placement.

---

## 2) Inputs
```
class ∈ { tiny_craft, light_vessel, medium_vessel, heavy_vessel, capital_vessel, dreadnought_vessel }
L (length, m), W (width, m), H (height, m)
material: { name, yield_strength (Pa), FoS_material }
pressure_internal P_int (Pa)  // default 101325 (1 atm)
armor_stack_thickness t_armor (m) // optional external layers (see M05)
ceiling policy by class (see §4)
corridor_reserve_fraction f_corr  // default 0.20 (20%)
lift/ladder spacing (m) // default shafts every 20 m in plan, at least 2 per deck
**a_max_g** (maximum sustained acceleration in g for maneuvering/mission) // default 2.0 g
```

---

## 3) Constants & Defaults
- **Headroom** `h_clear = 3.0 m` (fixed).
- **Deck ceiling thickness** `t_ceiling` by class (service plenum + floor structure + insulation):
  - tiny_craft: **0.30–0.35 m** (default 0.32)
  - light_vessel: **0.40–0.45 m** (default 0.42)
  - medium_vessel: **0.55–0.65 m** (default 0.60)
  - heavy_vessel: **0.70–0.80 m** (default 0.75)
  - capital_vessel: **0.90–1.00 m** (default 0.95)
  - dreadnought_vessel: **1.10–1.25 m** (default 1.15)
- **Deck pitch** `p_deck = h_clear + t_ceiling` (this ensures 3 m headroom everywhere).
- **Manufacturing min hull thickness** `t_min_class` (structural inner hull only):
  - tiny: 0.010 m, light: 0.015 m, medium: 0.020 m, heavy: 0.030 m, capital: 0.040 m, dread: 0.050 m.
- **Knud Thomsen surface area** parameter `p≈1.6075`.

---

## 4) Hull Thickness (structural inner hull)
We approximate the pressurized hull as a thin shell. Use a conservative **spherical equivalent radius** for the ellipsoid:
```
r_eq = (a·b·c)^(1/3)
σ_allow = yield_strength / FoS_material
// Internal pressure case (vacuum outside), spherical thin‑shell formula:
t_press = (P_int · r_eq) / (2 · σ_allow)
```
Then apply the **class minimum** and any design margin FoS_design (default 1.25):
```
t_struct = max( t_press · FoS_design, t_min_class )
```
### 4.1 Acceleration Load Case (high‑G maneuvers)
Internal pressure is often **not** the limiting case; high‑G maneuvers impose inertial loads on decks, frames, and the hull. For MVP we capture this with a simple **acceleration floor** and a **frame system** requirement:

- **Acceleration floor (thickness)**
  `t_accel_floor = α_class · a_max_g`
  Recommended `α_class` (m per g): tiny **0.006**, light **0.008**, medium **0.012**, heavy **0.018**, capital **0.024**, dread **0.030**.

- **Final structural thickness**
  `t_struct_final = max( t_struct, t_accel_floor )`
  (Designers can increase further for local reinforcements.)

- **Frames & longerons (carry most inertial load)**
  Require a ring‑frame spacing `s_frame` and longeron count `n_long` by class:
  - `s_frame` (m): tiny **1.0**, light **1.2**, medium **1.5**, heavy **2.0**, capital **3.0**, dread **4.0**.
  - `n_long`: tiny **8**, light **12**, medium **16**, heavy **24**, capital **32**, dread **48**.
  Each frame/longeron set sizes its cross‑section area from `a_max_g` and local span; detailed sizing is post‑MVP, but **mass budget** must account for them (see §12 Cutlines).

**Notes**
- `t_struct_final` is the **inner structural hull** thickness. External **armor**/ablators/radiators are modeled separately as `t_armor` (M05/M04) and do **not** reduce interior volume.
- Advanced (post‑MVP): replace `t_accel_floor` with an equivalent‑pressure estimate `p_eq ≈ ρ_eff · (a_max_g·g) · R_axis` to derive thickness per axis.

---

## 5) Inner Geometry & Volumes
- **Outer semi‑axes**: `a=L/2`, `b=W/2`, `c=H/2`.
- **Inner semi‑axes** (serviceable pressure hull):
  `a_i = a − t_struct`, `b_i = b − t_struct`, `c_i = c − t_struct`  *(thin‑shell approximation; t ≪ {a,b,c}).*
- **Inner volume**: `V_inner = 4/3 · π · a_i · b_i · c_i`.
- **Mid‑deck area** (z=0): `A_mid = π · a_i · b_i`.
- **Surface area** (outer): `S_out ≈ 4π · ((a^p b^p + a^p c^p + b^p c^p)/3)^(1/p)`.

---

## 6) Deck Count, Positions, and Areas
1) **Deck pitch**: `p_deck = 3.0 + t_ceiling` (from §3).
2) **Inner height**: `H_inner = 2 · c_i`.
3) **Deck count**: `N = floor( H_inner / p_deck )`. (Always round **down**.)
4) **Deck z‑positions** (centerlines), bottom to top:
```
for k in 1..N:
  z_k = -c_i + (k - 0.5) · p_deck  // centered per deck
```
5) **Deck ellipse area** at height `z_k`:
```
A_k = π · a_i · b_i · (1 − (z_k^2 / c_i^2))   // 0 at tips, max at mid
```
6) **Usable floor area** after corridor/shaft reserve: `A_use_k = A_k · (1 − f_corr)` with `f_corr ∈ [0.15, 0.25]` (default 0.20).
7) **Per‑deck headroom volume**: `V_head_k = A_k · 3.0`.
8) **Per‑deck plenum volume**: `V_plenum_k = A_k · t_ceiling`.

**Totals**: `V_head_total = Σ V_head_k`, `V_plenum_total = Σ V_plenum_k`.

---

## 7) Service Plenum Policies (Ceilings)
- All **horizontal routing** lives in the ceiling plenum; walls remain mostly structural.
- **Segregation**: HV power separated from fluids/atmo via barriers or ≥0.1 m standoff plus drip trays.
- **Firebreaks**: hard stops every 5 m (tiny/light) or 10 m (medium+) with auto‑caps.
- **Redundancy**: A/B trunks on opposite sides of the corridor spine.
- **Access**: inspection hatches every 2 m; **crawlable** plenum (≥1.0 m) for capital/dreadnought.

---

## 8) Propulsion & Keep‑Outs
- Main propulsion complex **must touch the aft outer surface** (rear wall) with required clearances.
- **Surface‑area budgeting**: propulsion consumes **interior** surface‑area budget only (pumps, turbomachinery, control, mounts). The **external nozzle/bell** and afterbody are **abstracted** and do not consume interior surface area, but they **reserve an external aperture** (keep‑out) on the aft surface.
- Reserve extra ceiling depth near machinery spaces (+0.1–0.2 m) to handle larger heat/propellant trunks and shunts.
- Define keep‑out volumes for engine bells, radiator deployment arcs, and airlocks so the solver avoids illegal placement.

---

## 9) Module Packing (Surface‑Area Budget + Corridor Adjacency)
- Each module consumes **surface area (m²)** from its deck’s `A_use_k`.
- Every module must **border a corridor node** (door adjacency) for pathfinding and maintenance.
- SRS trunk endpoints are placed along corridor spines; modules auto‑connect by nearest trunk point.

---

## 10) Outputs
- `N` decks with `{z_k, A_k, A_use_k, V_head_k, V_plenum_k}`.
- Corridor/lift/ladder graph and reserved shafts.
- Keep‑out volumes, propulsion position, radiator arcs.

---

## 11) Acceptance Criteria (MVP)
1) Given (L,W,H,class,material), solver returns `t_struct`, inner axes `(a_i,b_i,c_i)`, `N`, per‑deck areas/volumes, and totals.
2) Headroom stays **exactly 3.0 m** on all decks; plenum is added **on top** of that.
3) Increasing `P_int` or decreasing material strength increases `t_struct` and **reduces** `N` and `V_head_total` accordingly.
4) Corridor reserve reduces per‑deck usable area by `f_corr` and ensures lift/ladder connectivity across all decks.
5) Propulsion is placed touching aft surface; no module intersects keep‑outs.

---

## 12) Cutlines (MVP → Post)
- No detailed frame/longeron modeling; hull treated as continuous thin shell; **however** mass budget placeholders for frames/longerons must be included by class and `a_max_g` (export to M06).
- Uniform `t_struct_final` everywhere; no local reinforcement (add later for engine mounts/airlocks).
- No decompression buckling analysis; pressurization is the limiting case.
- Armor/radiator stacks excluded from interior volume; handled in M05/M04 for mass/thermal.
- Optional advanced method (post‑MVP): equivalent‑pressure method for axis‑dependent acceleration loads; FEA‑style local checks.
