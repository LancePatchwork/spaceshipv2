# Starship Simulator — M05 Materials & Armor DB (v0.3)

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
- Use **real data first** (handbooks, vendor datasheets, peer‑reviewed papers). Extrapolate only when needed; mark `is_theoretical:true` with an anchor and method.
- Define **canonical properties** (mechanical, thermal, optical, radiation, cost) with **source metadata & quality grades**.
- Provide **computed ratings** for MVP: **Ballistic (BR)**, **Laser (LR)**, **Explosion (XR)** to keep combat fast while plausible.
- Describe **Armor Stacks** (layered composites) and how to compute effective properties.

---

## 2) Data Schema

### 2.0 Units
All inputs in **SI**: Pa, kg/m³, W/m·K, J/kg·K, K; optics at **λ = 1.06 µm** (default laser) plus optional `0.5 µm` and `10.6 µm` bands.

### 2.1 Material (atomic)
```json
{
  "id": "ti_6al_4v",
  "name": "Ti-6Al-4V",
  "category": "structural|armor|radiator|ablative|insulator",
  "density_kg_m3": 4430,
  "yield_strength_Pa": 9.0e8,
  "ultimate_strength_Pa": 9.5e8,
  "hardness_HB": 330,
  "youngs_E_Pa": 1.1e11,
  "shear_G_Pa": 4.2e10,
  "fracture_toughness_MPa_sqrtm": 55,
  "spall_resistance": 0.7,
  "explosion_resistance": 0.6,
  "k_W_mK": 6.7,
  "c_J_kgK": 560,
  "melting_K": 1933,
  "boiling_K": 3560,
  "latent_fusion_J_kg": 3.7e5,
  "latent_vapor_J_kg": 9.0e6,
  "emissivity": 0.3,
  "reflectivity_laser": {"0.5um": 0.5, "1.06um": 0.35, "10.6um": 0.2},
  "radiation_shield_coeff": 0.4,
  "cost_cr_per_kg": 12,
  "rarity": "common|uncommon|rare|exotic",
  "process_state": "annealed|tempered|sintered|laminate",
  "source": {
    "vendor": "MatWeb|Handbook|Paper|Estimation",
    "citation": "string",
    "year": 2020,
    "quality": "A|B|C|D|E"
  },
  "is_theoretical": false,
  "notes": "assumptions or temp"
}
```

### 2.2 Armor Stack (layered)
```json
{
  "id": "armor_stack_example",
  "layers": [
    {"material_id":"b4c_ceramic", "thickness_m":0.015},
    {"material_id":"ti_6al_4v", "thickness_m":0.010},
    {"material_id":"aerogel_foam", "thickness_m":0.020}
  ]
}
```

**Effective properties** (per stack):
- **Mass/area**: Σ `density × thickness`.
- **Thermal**: series/parallel approximations (M04 will pull `k`, `c`, `emissivity`).
- **Ballistic**: §3.1.
- **Laser**: §3.2.
- **Explosion**: §3.3.

---

## 3) Computed Ratings (MVP)
> Collapse complex physics into scalars for fast combat. Calibrate constants with **real anchor points** (RHA steel, Al‑Li sheet, B4C tile).

### 3.1 Ballistic Rating (BR → RHAe mm)
- **Model** (Lambert–Jonas/Okun‑style collapse):
  `BR_mm = Σ (K_b(material) × thickness_m × f_hardness × f_toughness × sqrt(yield_strength_Pa / 1e9)) × 1000`
  where `f_hardness = 1 + (hardness_HB − 200)/600`, `f_toughness = clamp(fracture_toughness/50, 0.6, 1.4)`.
- **Calibration**: choose `K_b` so **RHA steel** maps to `1 mm → 1 mm RHAe`; ceramics 1.3–1.5× (front‑load only first layer), Ti ~0.85×, composites ~0.6×.

### 3.2 Laser Rating (LR → MJ/m²)
- **Interpretation**: lasers are **heat at a focal point**. If they **don’t** perforate, absorbed power becomes **ship heat** → M04.
- **Lumped enthalpy model**:
  `H_eff = c·(T_m−T_0) + L_f + η_v·L_v`
  `LR_MJ_m2 = (ρ · H_eff · thickness_m) / (1 − R_λ) ÷ 1e6 · Φ(k)`
  with `R_λ = reflectivity_laser[1.06um]`, `η_v` ≈ 0–0.2 (metals), 0.2–0.6 (ablators/ceramics), and **conduction penalty** `Φ(k)` (1.0–1.5) increasing with thermal conductivity.
- **Time‑to‑burn‑through** for a beam `{P, spot_d}`: `t ≈ (LR_MJ_m2 × A_spot) / P_MJ_s` (emit `ThermalAlertEvent` with `heat_kW = P·(1−R_λ)` while heating).

### 3.3 Explosion Rating (XR → 0..100)
- **Goal**: standoff/blast attenuation proxy.
- **Model**: Hopkinson–Cranz scaling → simple stack:
  `XR = clamp( Σ (explosion_resistance × thickness_m × 1000) + foam_bonus, 0, 100 )`
  with `foam_bonus = +5 per 10 mm` of aerogel/foam layers. Calibrate to steel plates at common scaled distances.

**Build‑time**: store `BR_mm`, `LR_MJ_m2`, `XR_0_100` and constants used (`K_b`, `Φ`).

---

## 4) Starter Materials (real anchors + flagged estimates)
> Rows include **source metadata** and **quality grade**. Estimates set `is_theoretical:true` and list their anchor.

| id | name | category | density | yield (GPa) | hardness HB | k (W/mK) | c (J/kgK) | melt K | boil K | Lf (kJ/kg) | Lv (MJ/kg) | ε | R@1.06µm | source | Q |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|:--:|
| ti_6al_4v | Ti‑6Al‑4V | structural | 4430 | 0.90 | 330 | 6.7 | 560 | 1933 | 3560 | 370 | 9.0 | 0.30 | 0.35 | TBD | A |
| al_li | Al‑Li Alloy | structural | 2550 | 0.50 | 150 | 80 | 900 | 900 | 2740 | 400 | 10.5 | 0.10 | 0.30 | TBD | B |
| maraging_steel | Maraging Steel | armor | 8000 | 1.90 | 600 | 25 | 460 | 1800 | 3100 | 270 | 6.3 | 0.25 | 0.30 | TBD | A |
| b4c_ceramic | Boron Carbide | armor | 2500 | 0.30 | 2700 | 30 | 800 | 3036 | 3500 | 140 | 7.0 | 0.80 | 0.20 | TBD | B |
| wc_carbide | Tungsten Carbide | armor | 15600 | 0.70 | 1700 | 84 | 280 | 3143 | 6200 | 110 | 6.0 | 0.20 | 0.30 | TBD | A |
| cfrp_sandwich | Carbon Composite | structural | 1600 | 0.60 | 200 | 5 | 800 | 2000 | 3800 | 300 | 12.0 | 0.85 | 0.50 | TBD | B |
| aerogel_foam | Aerogel Foam | insulator | 100 | 0.01 | 10 | 0.02 | 1200 | 1200 | 2200 | 0 |  | 0.90 | 0.50 | TBD | C |
| ablative_resin | Ablative Resin | ablative | 1200 | 0.02 | 20 | 0.2 | 1500 | 1000 | 3000 | 250 | 12.0 | 0.60 | 0.10 | TBD | C |
| radiator_panel | High‑ε Radiator | radiator | 2700 | 0.30 | 100 | 150 | 900 | 900 | 2740 | 400 | 10.5 | 0.95 | 0.20 | TBD | B |

*Cells marked TBD will be filled from handbooks/papers; anything estimated will be tagged and documented.*

---

## 5) Armor Stack Examples
- **Ceramic‑Metal‑Foam** (b4c + Ti + aerogel): good against slugs & lasers; ok vs blasts.
- **Carbide‑Steel** (WC + Maraging): extreme KE resistance; heavy; weak thermal response.
- **Ablator‑Composite** (ablative + CFRP): great vs lasers; poor vs KE unless thick.

### 5.5 Component Vulnerability Profiles (targets that “make sense” to snipe)
> Maps external features to stacks and failure hooks. Used by M09 (Combat) & M02 (Events).

| Component | Typical material stack | Failure modes (MVP) | Hooks |
|---|---|---|---|
| **Radiator panel** | radiator_panel over CFRP truss | Laser heats/ablates; slug perforates → coolant loss → `ThermalAlertEvent` | M04 heat drop; SRS heat backlog |
| **Engine bell/nozzle** | WC/ceramic liner + Ti shell | Slug fractures liner; laser heats → throat erosion → thrust loss | `Update:IntegrityDegraded(engine)` ; `PowerDrop` if turbomachinery hit |
| **PDC/CIWS turret** | Ti shell + ceramic tile + ablative visor | Laser blinds sensors; slug jams turret; missile frag disables | `Task:Repair`, `Task:ReplaceBarrel` |
| **Antenna/radar** | CFRP mast + radome | Laser/slug sever → comms/sensor loss | `CommsDegraded`; reroute events |
| **Thermal louvers** | B4C tiles + ablative resin | Laser strips; slug jams | `ThermalAlertEvent` + checklist |
| **Externals (pipes, cables)** | exposed metal/polymer | Any hit severs; leaks/shorts | `SRSAlert:*`, `RepairEvent` |

**Damage propagation**
- **Lasers**: if `P_abs = P·(1−R_λ) < P_burn`, no perforation; inject `P_abs` as **heat load** to M04 (ship becomes hotter). If `P_abs ≥ P_burn`, compute **time‑to‑burn‑through** and sever/destroy component, spawning events.
- **Slugs**: compare KE & diameter vs stack **BR (RHAe)**. On penetration, damage modules/SRS lines along the path, with **spall chance** scaled by `spall_resistance`.
- **Missiles**: evaluate **XR** vs standoff; apply impulse/frag; trigger fires/decompression if lines/compartments are breached.

---

## 6) Interfaces
- **M03 Geometry**: pulls densities & thickness for mass/area; no effect on inner volume.
- **M04 Thermal**: uses `k(T)`, `c(T)`, ε, Tm, Tb, and latent heats to convert laser absorption into **transient heat** and possible ablation.
- **M09 Combat**: reads `BR/LR/XR` + **vulnerability profiles**.
- **M11 Data**: versioned schemas; material packs moddable; sources stored alongside materials.

---

## 7) Acceptance Criteria (MVP)
1) Every material row includes **source metadata** and a **quality grade**; unit tests reject missing/invalid units.
2) Armor stacks precompute `BR_mm`, `LR_MJ_m2`, `XR_0_100`; changing thickness or layer order updates them.
3) Given a beam `{P, d}`, the system reports **time‑to‑burn‑through** for a target stack and emits a `ThermalAlertEvent` with locus/heat input to M04/M02 while heating.
4) Kinetic hits scale plausibly with density/yield/toughness (e.g., WC outperforms Al‑Li for BR at equal thickness).
5) All *theoretical* entries are flagged and list an anchor material used for extrapolation.

---

## 8) Data Sourcing & QA
- **Primary sources**: materials handbooks, MatWeb/vendor datasheets, peer‑reviewed papers.
- **Per‑row metadata mandatory**: citation, year, source type, quality grade (A=handbook/paper consensus, B=vendor datasheet, C=single paper, D=estimate, E=theoretical).
- **Sanity checks**: unit tests validate unit ranges (`k`, `c`, Tm, Tb); cross‑check density×volume vs mass budgets.
- **Extrapolation rules**: any `is_theoretical:true` entry must list an **anchor** material and the rule used (e.g., Ti alloy +10% yield, −20% k).
- **Laser bands**: default **1.06 µm**; optional **0.5 µm** and **10.6 µm** if provided.

---

## 9) Cutlines
- No wavelength‑by‑wavelength laser model in MVP; single 1.06 µm band + optional 0.5/10.6 µm entries.
- No full transient heat diffusion; **lumped enthalpy** + conduction penalty Φ for perforation time.
- No ductile failure micromodel; BR uses calibrated heuristic.
- No TNT chemistry; XR uses scaled distance calibration.
