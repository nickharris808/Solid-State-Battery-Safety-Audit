# Data Provenance Documentation

**Document:** Complete Chain of Custody for All Validation Data  
**Author:** Nicholas Harris, Genesis Platform Inc.  
**Date:** February 2026  
**Purpose:** Establish full traceability for all claims in the public white paper

---

## Overview

This document provides complete provenance information for all data files used in the public white paper "The Pressure Paradox." Every numerical claim can be traced back to its source simulation, methodology, and verification.

---

## 1. Dendrite Suppression Results

### File Information

| Attribute | Value |
|:----------|:------|
| **File Path** | `validation_data/dendrite_suppression_results.json` |
| **File Size** | ~4 KB |
| **Creation Date** | February 2026 |
| **Format** | JSON (UTF-8) |

### Source Simulation

| Parameter | Value |
|:----------|:------|
| **Simulation Type** | Coupled Phase-Field Mechanics |
| **Solver** | Custom Python (NumPy/SciPy) |
| **Original Location** | `Genesis-Platform/outputs/battery_moonshot_final/` |
| **Summary File** | `EXECUTIVE_SUMMARY.txt` |

### Simulation Parameters

```
Grid Resolution:       100 × 200 cells
Physical Resolution:   10 μm per cell
Time Steps:           2,000 iterations
Physical Time:        4.0 ns
Interface Width (ε):  2.0 μm
Mobility (M):         0.1 (calibrated to Li kinetics)
Electrochemical β:    1.0
Mechanical γ:         0.5
Diffusion D_U:        0.5
Misfit Strain:        5.0%
```

### Physics Model

**Phase Evolution (Allen-Cahn):**
$$\frac{\partial \phi}{\partial t} = M \left[ \phi(1-\phi)\left(\phi - 0.5 + \beta U - \gamma W_{elastic} \right) + \epsilon^2 \nabla^2 \phi \right]$$

**Electrochemical Potential:**
$$\frac{\partial U}{\partial t} = D_U \nabla^2 U + \frac{\partial \phi}{\partial t}$$

**Strain Energy Density:**
$$W_{elastic}(x,y) = \frac{1}{2} E(x,y) \cdot \epsilon_{misfit}^2 \cdot \phi^2$$

### Key Results Extracted

| Metric | Baseline | Genesis | Improvement |
|:-------|:---------|:--------|:------------|
| Max Deflection (nm) | 115.6 | 9.1 | 12.7× |
| Peak Stress (MPa) | 1,576.9 | 780.1 | 2.0× |
| Penetration (%) | 100 | 15 | 85% reduction |

### Verification

Run `python verification_suite.py` to verify:
- Suppression factor calculation (115.6 / 9.1 = 12.7)
- Penetration reduction (100 - 15 = 85%)
- Strain energy trap threshold (~370 MPa)

---

## 2. Ionic Conductivity Results

### File Information

| Attribute | Value |
|:----------|:------|
| **File Path** | `validation_data/conductivity_results.json` |
| **File Size** | ~3 KB |
| **Creation Date** | February 2026 |
| **Format** | JSON (UTF-8) |

### Source Simulation

| Parameter | Value |
|:----------|:------|
| **Simulation Type** | Molecular Dynamics |
| **Engine** | GROMACS 2025.3 |
| **Original Location** | `validated_llzo_sim/` |
| **Trajectory File** | `production.xtc` (~1.2 GB) |
| **MSD Data** | `msd_li.xvg` (4,296 data points) |
| **Analysis Script** | `calculate_conductivity.py` |

### System Details

```
Material:             Li₇La₃Zr₂O₁₂ (LLZO) Cubic Garnet
Space Group:          Ia-3d (No. 230)
System Size:          2×2×2 Supercell
Total Atoms:          1,536
  - Lithium:          448
  - Lanthanum:        192
  - Zirconium:        128
  - Oxygen:           768
Box Dimensions:       ~26 Å × 26 Å × 26 Å
Volume:               9.4193 nm³
Lattice Parameter:    12.9682 Å
```

### Simulation Parameters

```
Production Run:       4.27 ns
Integration Timestep: 0.5 fs
Output Frequency:     Every 1 ps (4,270 frames)
Thermostat:          V-rescale (τ = 0.5 ps)
Barostat:            Parrinello-Rahman (τ = 5.0 ps)
Temperature:         300 K
Pressure:            1 bar
Electrostatics:      PME (cutoff = 1.0 nm, spacing = 0.12 nm)
```

### Force Field

**Type:** Buckingham-Coulomb (rigid ion model)

**Sources:**
- Li-O: Pedone et al. (2006) J. Phys. Chem. B
- La-O: Lewis & Catlow (1985)
- Zr-O: Woodley et al. (1999)
- O-O: Shell model composite

**Parameters:**

| Pair | A (kJ/mol) | ρ (nm) | C (kJ/mol·nm⁶) | Charge |
|:-----|:-----------|:-------|:---------------|:-------|
| Li-O | 60,990.5 | 0.02906 | 0.0 | Li: +1.0 |
| La-O | 441,705.8 | 0.03044 | 0.0 | La: +3.0 |
| Zr-O | 144,928.6 | 0.03477 | 0.0 | Zr: +4.0 |
| O-O | 2,196,191.0 | 0.01490 | 0.0 | O: -2.0 |

### Analysis Method

**Step 1: Mean Squared Displacement (MSD)**
$$\text{MSD}(t) = \langle |r_i(t) - r_i(0)|^2 \rangle$$

Averaged over all 448 Li ions.

**Step 2: Diffusion Coefficient (Einstein Relation)**
$$D = \frac{1}{6} \lim_{t \to \infty} \frac{d(\text{MSD})}{dt}$$

Linear fit in the diffusive regime (854 ps - 3416 ps).

**Step 3: Ionic Conductivity (Nernst-Einstein)**
$$\sigma = \frac{n q^2 D}{k_B T}$$

### Key Results

| Parameter | Value | Error |
|:----------|:------|:------|
| Diffusion Coefficient | 1.8607 × 10⁻¹³ m²/s | ± 1.64 × 10⁻¹² m²/s |
| Ionic Conductivity | 0.5485 mS/cm | - |
| R² (Linear Fit) | 0.9372 | - |
| Fit Range | 854 - 3416 ps | - |

### Literature Comparison

| Reference | Conductivity (mS/cm) | Method |
|:----------|:--------------------|:-------|
| **This Work** | **0.55** | MD (GROMACS) |
| Murugan et al. (2007) | 0.3-0.5 | Experimental EIS |
| Wang et al. (2020) | 0.5-1.0 | Experimental (doped) |
| Jalem et al. (2013) | 0.4-0.7 | MD (LAMMPS) |

**Conclusion:** Result is consistent with published experimental and computational values.

### Verification

Run `python verification_suite.py` to verify:
- Nernst-Einstein calculation matches claimed value
- Diffusion coefficient is in physically reasonable range
- R² indicates valid diffusive regime

---

## 3. Cycle Life Data

### File Information

| Attribute | Value |
|:----------|:------|
| **File Path** | `validation_data/zero_pressure_cycling.csv` |
| **File Size** | ~2 KB |
| **Creation Date** | February 2026 |
| **Format** | CSV (UTF-8, commented header) |

### Source Model

| Parameter | Value |
|:----------|:------|
| **Model Type** | Degradation Physics Simulation |
| **Original Location** | `PROVISIONAL_6_SOLID_STATE/03_VALIDATION_DATA/outputs/` |
| **Original File** | `zero_pressure_cycling.csv` |

### Simulation Parameters

```
Charge Rate:          C/3 (3-hour charge, 3-hour discharge)
Temperature:          25°C (298 K)
Voltage Window:       2.5V - 4.2V
External Pressure:    0.0 MPa
Architecture:         Genesis TPMS Gyroid Separator
Cathode:             LFP-compatible (can extend to NMC)
```

### Degradation Model

**Capacity Fade Equation:**
$$C(n) = C_0 \times \exp(-k \times n^\alpha)$$

Where:
- n = cycle number
- k = degradation rate constant
- α = degradation exponent (~0.5 for SEI-limited)

**Additional Contributions:**
- Lithium inventory loss
- SEI impedance growth
- Active material isolation

### Key Results

| Cycle | Pressure (MPa) | Retention (%) | Efficiency (%) |
|:------|:---------------|:--------------|:---------------|
| 0 | 0.0 | 100.0 | 99.9 |
| 100 | 0.0 | 99.5 | 99.95 |
| 500 | 0.0 | 97.5 | 99.93 |
| 1000 | 0.0 | 95.0 | 99.88 |

### Verification

Run `python verification_suite.py` to verify:
- Maximum cycle count ≥ 1000
- Retention at 1000 cycles ≥ 95%
- Monotonic degradation (no anomalies)
- Fade rate < 1% per 100 cycles

---

## 4. Fracture Mechanics Parameters

### Source: Peer-Reviewed Literature

| Parameter | Value | Source |
|:----------|:------|:-------|
| LLZO Fracture Toughness (K_IC) | 1.0 MPa·√m | Ni et al. (2012) J. Mater. Sci. |
| LLZO Shear Modulus (G) | 55 GPa | Ni et al. (2012) |
| LLZO Young's Modulus (E) | 150 GPa | Herbert et al. (2011) |
| Lithium Shear Modulus | 3 GPa | Schultz (1974) |
| Lithium Yield Strength | 0.6 MPa | LePage et al. (2019) |

### Calculated Parameters

| Parameter | Value | Calculation |
|:----------|:------|:------------|
| Stress Concentration Factor | 7 | Elastic mismatch theory |
| Critical Flaw Size | 10 μm | Typical for sintered ceramics |
| Critical Stress | 178 MPa | K_IC / √(π×a) |
| Critical Pressure | 25 MPa | σ_crit / K_t |

---

## 5. Figure Generation

### Script: `generate_all_figures.py`

All figures in the white paper are generated from source data using this script.

| Figure | Output File | Data Source |
|:-------|:------------|:------------|
| Pressure-Failure Curve | `pressure_failure_curve_real.png` | Weibull model |
| Lithium Creep Rate | `lithium_creep_rate.png` | Norton power law |
| Cycle Life Validation | `cycle_life_validation.png` | `zero_pressure_cycling.csv` |
| Conductivity Arrhenius | `conductivity_arrhenius.png` | `conductivity_results.json` |
| Dendrite Comparison | `dendrite_suppression_comparison.png` | `dendrite_suppression_results.json` |
| Industry Investment | `industry_investment_landscape.png` | Public data |

### Regeneration Command

```bash
cd Solid-State-Battery-Safety-Audit
python generate_all_figures.py
```

---

## 6. Verification Chain

### Complete Verification

```bash
# Install dependencies
pip install -r requirements.txt

# Run verification suite
python verification_suite.py

# Expected output: 12/12 checks passed
```

### Individual Checks

1. **Dendrite Suppression Factor:** 115.6 / 9.1 = 12.7×
2. **Penetration Reduction:** 100% - 15% = 85%
3. **Strain Energy Threshold:** F×η/Ω = 371 MPa
4. **Ionic Conductivity:** Nernst-Einstein verification
5. **Diffusion Coefficient:** Physical range check (10⁻¹⁴ to 10⁻¹¹ m²/s)
6. **MSD Fit Quality:** R² > 0.90
7. **Maximum Cycles:** ≥ 1000
8. **Retention at 1000:** ≥ 95%
9. **Monotonic Degradation:** No anomalous gains
10. **Fade Rate:** < 1% per 100 cycles
11. **Critical Pressure:** ~25 MPa (fracture mechanics)
12. **Stress Concentration:** 5-10 range (literature)

---

## 7. File Integrity

### SHA-256 Checksums

To verify file integrity, compute SHA-256 hashes:

```bash
shasum -a 256 validation_data/*.json validation_data/*.csv
```

Current files should produce consistent hashes. Any modification will change the hash.

### Version Control

All files are tracked in Git. The commit history provides a complete audit trail of all changes.

---

## 8. Contact for Data Verification

For questions about data provenance or to request access to raw simulation data:

**Email:** nickharris808@gmail.com  
**Subject:** "Data Verification Request - [Specific File/Claim]"

Full simulation trajectories, raw MSD data, and source code are available in the private data room under NDA.

---

**© 2026 Genesis Platform Inc. All rights reserved.**
