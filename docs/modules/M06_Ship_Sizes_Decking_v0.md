# Starship Simulator — M06 Ship Sizes & Decking (v0.2)

**Status:** Frozen (v0.3)

> A data‑driven library of structural, armor, radiator, and ablative materials with properties used by **M03 Geometry**, **M04 Thermal**, **M07 Combat/Economy**, and crafting. Uses **real‑world data wherever possible** and clearly flags/extrapolates theoretical materials.

## Final Overview (MVP)
- **Data fidelity**: SI units; mandatory source metadata (citation, year, quality A–E) for every row; theoretical entries flagged with an anchor and rule.
- **Schema**: adds toughness, E/G moduli, melting/boiling, latent heats, and laser reflectivity bands (0.5, 1.06, 10.6 µm).
- **Computed ratings**: 
  - **BR (RHAe mm)** for slugs; calibrated so RHA steel maps 1:1, with toughness/hardness scaling and ceramic front‑loading.
  - **LR (MJ/m²)** for lasers; provides **time‑to‑burn‑through**; non‑perforating beams inject absorbed **heat** to M04.
  - **XR (0–100)** for blasts; foam/aerogel bonuses; anchored to scaled‑distance behavior.
- **Vulnerability profiles**: externals (radiators, engine bells, PDCs, antennae, louvers, exposed lines) map to stacks + failure hooks so “sniping” behaves sensibly.
- **Integration hooks**: 
  - To **M04 Thermal**: absorbed laser power → `ThermalAlertEvent` + heat load; ablation when thresholds reached.
  - To **M02 Events**: repair/scram/checklist signals on damage; selective SRS wake by resource kind.
  - To **M01 SRS**: severed lines emit `SRSAlert:*` (power/heat/fluids/data), enabling reroutes and hardlinks.
  - To **M09 Combat**: uses BR/LR/XR and component profiles for fast resolution.
- **Moddability**: materials JSON + armor stacks compile to cached ratings at build; tuning constants (`K_b`, Φ, η_v) are data‑driven.
- **Cutlines**: per‑wavelength laser physics, full transient diffusion, ductile failure micromodels, TNT chemistry (not in MVP).

---

## 1) Scope
- Standardize **size classes** for content scaling and solver inputs.
- Provide **defaults** for: aspect ratios (L:W:H), deck pitch via `t_ceiling`, corridor reserve, riser spacing, ring‑frame spacing and longeron count.
- Offer **reference profiles** that set `a_max_g`, armor bias, radiator posture, and safety factors.

---

## 2) Size Bands & Roles (nominal hull dimensions)
| Class | Length L (m) | Width W (m) | Height H (m) | Crew (typ.) |
|---|---:|---:|---:|---:|
| tiny_craft | 8–30 | 3–9 | 3–6 | 1–6 |
| light_vessel | 30–80 | 8–20 | 8–14 | 10–60 |
| medium_vessel | 80–150 | 14–28 | 14–24 | 60–300 |
| heavy_vessel | 150–280 | 24–45 | 20–38 | 300–800 |
| capital_vessel | 280–380 | 40–60 | 34–50 | 800–2,000 |
| dreadnought_vessel | 380–650 | 60–110 | 48–80 | 2,000–6,000+ |

*Aspect ratio guidance*: baseline `W ≈ 0.25–0.35 L`, `H ≈ 0.18–0.28 L`. Designers can deviate; M03 handles ellipsoid math generically. *Terminology:* we use **size** (not "class") and **role** (combatant/hauler/explorer) to avoid confusion with code "class" types.

---

## 3) Deck Pitch & Ceiling (service plenum)
- **Fixed headroom** `h_clear = 3.0 m` on every deck.  
- **Size plenum thickness** `t_ceiling` (structure + service plenum + insulation):  
  tiny **0.32** | light **0.42** | medium **0.60** | heavy **0.75** | capital **0.95** | dread **1.15** (meters).  
- **Deck pitch** `p_deck = h_clear + t_ceiling`.
- **Corridor reserve** `f_corr = 0.20` (15–25% allowed).  
- **Riser spacing**: shafts at corridor intersections, ~every **20 m** in plan; ≥ **2** per deck.

---

## 4) Structural Defaults (export to M03)
- **Frame spacing (base)** `s_frame_base` (m): tiny **1.0**, light **1.2**, medium **1.5**, heavy **2.0**, capital **3.0**, dread **4.0**.
- **Longerons** `n_long`: tiny **8**, light **12**, medium **16**, heavy **24**, capital **32**, dread **48**.
- **Acceleration thickness floor** `t_accel_floor = α_size · a_max_g` with `α_size` (m/g): tiny **0.006**, light **0.008**, medium **0.012**, heavy **0.018**, capital **0.024**, dread **0.030**.
- **Effective frame spacing (ties to g)**: reduce spacing for higher sustained g:  
  `s_frame_eff = s_frame_base × clamp( (2.0 / a_max_g)^0.5, 0.70, 1.20 )`  
  (≤30% tighter for hard‑burn ships; exported to mass budget, not geometry.)
- **Pressure hull thickness** is computed in M03 (thin‑shell + safety factors) then `max`’d with `t_accel_floor`.

---

## 5) Reference Profiles (design presets)
> Profiles set sensible defaults across modules. They’re **flavorful presets**, not hard canon: tweak per ship or mission.

### 5.1 Expanse‑like (Hard‑Burn Frigate)
- **Target size**: medium_vessel.  
- **Acceleration**: `a_max_g = 3.5 g` sustained; **emergency** `a_burst_g = 8 g` for ≤ 30 s (affects Event/crew systems and frame mass budget via `s_frame_eff`, not geometry thickness).  
- **Structure**: use `α_size` from §4; recommend `FoS_material = 1.6`, `FoS_design = 1.30`.  
- **Thermal posture**: radiator area bias **+20–30%** vs baseline; SRS priority: **heat → power → life support → engines → refinery** under overtemp.  
- **Armor**: moderate; favor **sloped** external geometry; `t_armor` modest, rely on maneuver + DC.

### 5.2 BSG‑like (Armor‑Heavy Battlestar)
- **Target size**: capital_vessel or dreadnought_vessel.  
- **Acceleration**: `a_max_g = 2.0 g` sustained; **burst** up to `5 g` ≤ 10 s.  
- **Structure**: higher frame mass; recommend `FoS_material = 1.8`, `FoS_design = 1.35`.  
- **Thermal posture**: internal heat batteries (hull/armor) favored; radiator exposure conservative.  
- **Armor**: heavy layered stacks (M05), high `t_armor`, large keep‑outs for flight decks.

### 5.3 Hauler (Bulk Freighter)
- **Target size**: heavy_vessel.  
- **Acceleration**: `a_max_g = 0.5 g` sustained; **no** high‑g bursts.  
- **Structure**: light frames; recommend `FoS_material = 1.4`, `FoS_design = 1.20`.  
- **Thermal posture**: oversized radiators when stationary; minimal during cruise.  
- **Armor**: minimal; rely on convoy/escorts.

**Applying a profile** sets: `a_max_g`, recommended safety factors, radiator/armor bias hints for M04/M05, and doctrine defaults for event checklists (`thermal_overtemp`, `reactor_scram_response`).

---

## 6) Module Surface‑Area Budgets (per deck)
- Packing uses **usable floor area** `A_use_k` from M03.  
- A **rule of thumb** for planning: reserve **30–40%** of `A_use_k` for machinery modules (power, engines, refinery), **20–30%** for life support & utilities, **20–30%** for crew/cargo, remainder for buffers/egress. Tune per ship.

---

## 7) Outputs
- Expose a `size_defaults.json` blob with: `t_ceiling`, `f_corr`, `s_frame`, `n_long`, and **profile** presets. M03 consumes these and computes decks/volumes. M04/M05 read radiator/armor biases as hints. M03 consumes these and computes decks/volumes. M04/M05 read radiator/armor biases as hints.

---

## 8) Acceptance Criteria (MVP)
1) Selecting a **profile** and **size** produces a consistent parameter set (deck pitch, structural floors, riser spacing) that M03 can solve without warnings.  
2) Increasing from Hauler → Expanse‑like raises `a_max_g` and increases computed `t_struct_final`, reducing deck count for a fixed outer hull size.  
3) Changing **size** changes `t_ceiling`, frame spacing, and longeron count accordingly. `t_ceiling`, frame spacing, and longeron count accordingly.

---

## 9) Cutlines
- No per‑bay local reinforcements in MVP; global defaults only.  
- Radiator/armor **biases** are hints; detailed thermal/armor sizing happens in M04/M05.  
- Profiles are **non‑IP** homages; numbers are gameplay‑driven, not licensed stats.

