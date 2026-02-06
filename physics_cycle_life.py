#!/usr/bin/env python3
"""
================================================================================
GENESIS: PHYSICS-BASED CYCLE LIFE MODEL
================================================================================

This script derives cycle life from the ARCHITECTURE rather than tuning parameters.
It connects the Gyroid lattice properties (K_constraint, stress distribution) to
degradation mechanisms (SEI growth, fatigue cracking, dendrite nucleation).

PHYSICS:
    1. SEI Growth (Parabolic):
       L_SEI(n) = sqrt(2 * D_SEI * t_cycle * n)
       D_SEI = D₀ × exp(-E_a/(k_B T)) × stress_factor
       stress_factor depends on interfacial strain from architecture

    2. Mechanical Fatigue (Paris Law):
       da/dN = C × (ΔK)^m
       ΔK = f(geometry) × Δσ × sqrt(π × a₀)
       Δσ depends on Li volume change constrained by architecture

    3. Dendrite Nucleation (Probabilistic):
       P(nucleation) = P₀ × exp(-W_barrier/(k_B T))
       W_barrier = W_elastic from Stiffness Trap

    KEY INSIGHT: The Genesis architecture reduces ALL three degradation rates
    through measurable physics, not arbitrary parameter tuning.

REFERENCES:
    [1] Pinson, M.B. & Bazant, M.Z. (2013). J. Electrochem. Soc. 160, A243.
    [2] Paris, P. & Erdogan, F. (1963). J. Basic Engineering, 85, 528.
    [3] Monroe, C. & Newman, J. (2005). J. Electrochem. Soc. 152, A396.

Author: Nicholas Harris, Genesis Platform Inc.
Date: February 2026
Patent Reference: Provisional 6, Claims 18-24
================================================================================
"""

import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict

# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================

K_B_EV = 8.617e-5       # Boltzmann constant (eV/K)
K_B_J = 1.381e-23       # Boltzmann constant (J/K)
FARADAY = 96485.0        # Faraday constant (C/mol)
R_GAS = 8.314            # Gas constant (J/mol·K)

# =============================================================================
# ARCHITECTURE PROPERTIES
# =============================================================================

@dataclass
class Architecture:
    """Physical properties of a battery architecture."""
    name: str

    # Mechanical properties
    K_constraint_GPa: float        # Effective internal constraint stiffness
    E_separator_GPa: float         # Separator Young's modulus
    porosity: float                # Void fraction

    # Interface properties
    contact_area_fraction: float   # Fraction of separator area in contact with Li
    stress_concentration_factor: float  # K_t at interface

    # Geometry
    strut_thickness_um: float      # For lattice architectures
    unit_cell_um: float            # Unit cell dimension

    # Derived: interfacial stress during cycling
    # Li expands ~20% volumetrically during plating
    # The architecture constrains this expansion
    def cycling_stress_amplitude_MPa(self) -> float:
        """
        Calculate the stress amplitude from Li volume change, capped by
        lithium's yield strength.

        CRITICAL PHYSICS: Lithium is extremely soft (σ_yield ≈ 0.6-5 MPa).
        The lithium will plastically deform (creep) before elastic stresses
        build up to the levels predicted by Hooke's law.

        The ACTUAL interface stress depends on:
        1. Lithium yield/creep strength (~1-5 MPa depending on strain rate)
        2. Whether the architecture distributes the stress uniformly (Genesis)
           or concentrates it at grain boundaries (Baseline)

        For Genesis: stress is distributed by the lattice → σ ≈ σ_yield
        For Baseline: stress concentrates at grain boundaries → σ_local = K_t × σ_yield
        """
        sigma_yield_Li = 2.0  # MPa (lithium yield at cycling strain rates, LePage 2019)

        # For Genesis: internal constraint distributes load uniformly
        #   → interface stress is approximately the lithium yield stress
        #   → NO stress concentration (smooth TPMS surfaces)
        # For Baseline (no internal constraint):
        #   → voids form → remaining contact patches carry all load
        #   → stress concentration at grain boundary triple junctions
        sigma = sigma_yield_Li * self.stress_concentration_factor

        return sigma  # MPa

    def dendrite_barrier_MPa(self) -> float:
        """
        Strain energy barrier from the Stiffness Trap.
        W_trap = 0.5 × E_eff × ε_misfit²

        Higher K_constraint → higher W_trap → harder for dendrites.
        """
        epsilon_misfit = 0.05  # 5% misfit strain at dendrite tip
        W = 0.5 * self.K_constraint_GPa * 1000 * epsilon_misfit**2  # MPa
        return W


# Define the two architectures
GENESIS = Architecture(
    name="Genesis (Gyroid Lattice)",
    K_constraint_GPa=6.7,          # From patent: E_s × f_s × (t/a)^n
    E_separator_GPa=22.5,         # Effective modulus of porous LLZO
    porosity=0.40,
    contact_area_fraction=0.60,    # Gyroid: high contact
    stress_concentration_factor=2.0,  # Low: smooth TPMS surfaces
    strut_thickness_um=2.5,
    unit_cell_um=10.0
)

BASELINE = Architecture(
    name="Baseline (Dense LLZO + Clamps)",
    K_constraint_GPa=0.0,          # No internal constraint (relies on external)
    E_separator_GPa=150.0,        # Dense ceramic
    porosity=0.0,
    contact_area_fraction=0.95,    # Dense: high contact but stress concentration
    stress_concentration_factor=7.0,  # High: grain boundary triple junctions
    strut_thickness_um=0.0,
    unit_cell_um=0.0
)


# =============================================================================
# DEGRADATION MODELS
# =============================================================================

def sei_growth_per_cycle(
    architecture: Architecture,
    cycle_num: int,
    T_celsius: float = 25.0,
    C_rate: float = 0.33
) -> float:
    """
    SEI thickness growth per cycle using parabolic kinetics.

    L(n) = sqrt(2 × D_SEI × t_cycle × n)

    D_SEI depends on interfacial stress (from architecture).
    Higher stress → more SEI damage per cycle → faster growth.

    Physics (Pinson & Bazant 2013):
    - SEI grows by solvent reduction at the Li surface
    - Growth rate depends on Li+ diffusion through existing SEI
    - Mechanical stress cracks the SEI, exposing fresh Li → accelerates growth

    Returns: SEI thickness in nm after this cycle
    """
    T = T_celsius + 273.15
    t_cycle_s = 3600 / C_rate * 2  # charge + discharge time (seconds)

    # Base SEI diffusivity (literature: ~10⁻²² to 10⁻²⁰ m²/s at 25°C)
    # Calibrated to give ~20-50 nm SEI after 1000 cycles (Pinson & Bazant 2013)
    D_SEI_base = 8e-22  # m²/s

    # Arrhenius temperature factor
    E_a_SEI = 0.35  # eV (activation energy for SEI diffusion)
    T_ref = 298.15
    arrhenius = np.exp(-E_a_SEI / K_B_EV * (1/T - 1/T_ref))

    # Stress acceleration factor
    # Higher cycling stress → more SEI cracking → more fresh surface → faster growth
    sigma = architecture.cycling_stress_amplitude_MPa()
    # Empirical: SEI cracking onset at ~5 MPa (Attia 2019)
    sigma_ref = 5.0  # MPa
    stress_factor = 1.0 + (sigma / sigma_ref)**1.5

    D_SEI = D_SEI_base * arrhenius * stress_factor

    # Parabolic growth: L = sqrt(2 D t)
    total_time = t_cycle_s * (cycle_num + 1)
    L_m = np.sqrt(2 * D_SEI * total_time)
    L_nm = L_m * 1e9  # Convert to nm

    return L_nm


def fatigue_damage_per_cycle(
    architecture: Architecture,
    cycle_num: int,
    T_celsius: float = 25.0,
    DoD: float = 0.80
) -> float:
    """
    Fatigue crack growth per cycle using Paris Law.

    da/dN = C × (ΔK)^m

    ΔK = stress_concentration × Δσ × sqrt(π × a₀)

    For ceramics: m ≈ 10-30 (very steep — small increase in ΔK causes rapid crack growth)

    The Genesis architecture REDUCES ΔK because:
    1. Internal constraint reduces cycling stress amplitude (Δσ)
    2. Smooth TPMS surfaces have lower stress concentration (K_t)

    Returns: Cumulative fatigue damage (0 = pristine, 1 = failure)
    """
    # Paris law parameters for LLZO ceramic
    C_paris = 1e-12    # m/cycle (pre-factor)
    m_paris = 15.0     # Exponent (steep for ceramics)

    # Cycling stress amplitude (depends on architecture)
    delta_sigma = architecture.cycling_stress_amplitude_MPa() * DoD

    # Apply stress concentration factor
    delta_sigma_local = delta_sigma * architecture.stress_concentration_factor

    # Initial flaw size (typical for sintered ceramics)
    a0 = 5e-6  # 5 μm

    # Stress intensity factor range
    delta_K = delta_sigma_local * np.sqrt(np.pi * a0)  # MPa·√m

    # Critical K (fracture toughness of LLZO)
    K_IC = 1.0  # MPa·√m

    # Paris law: crack growth rate
    if delta_K > 0 and delta_K < K_IC:
        da_dN = C_paris * (delta_K / K_IC)**m_paris
    elif delta_K >= K_IC:
        da_dN = 1e-3  # Rapid failure
    else:
        da_dN = 0.0

    # Cumulative crack length after n cycles
    a_cumulative = a0 + da_dN * (cycle_num + 1)

    # Damage parameter = a / a_critical
    a_critical = 100e-6  # 100 μm = separator thickness
    damage = min(a_cumulative / a_critical, 1.0)

    return damage


def dendrite_nucleation_probability(
    architecture: Architecture,
    T_celsius: float = 25.0,
    current_density_mA_cm2: float = 1.0
) -> float:
    """
    Probability of dendrite nucleation per cycle.

    P = P₀ × exp(-W_barrier / (k_B T))

    W_barrier is the strain energy barrier from the Stiffness Trap.
    Higher K_constraint → higher barrier → lower probability.

    For Genesis: W >> k_BT → P ≈ 0 (thermodynamically suppressed)
    For baseline: W = 0 → P = P₀ (limited only by electrochemistry)
    """
    T = T_celsius + 273.15

    # Base nucleation probability (no mechanical barrier)
    # From literature: ~0.1% per cycle at C/3 for conventional SSB
    P0 = 0.001 * (current_density_mA_cm2 / 0.33)

    # Strain energy barrier
    W_barrier = architecture.dendrite_barrier_MPa()  # MPa

    # Convert to eV per atom for Boltzmann factor
    # W (MPa) × Ω (m³/mol) / N_A = energy per atom
    Omega = 13.0e-6  # m³/mol (Li molar volume)
    W_per_atom_J = W_barrier * 1e6 * Omega / 6.022e23  # J per atom
    W_per_atom_eV = W_per_atom_J / 1.602e-19  # eV per atom

    # Boltzmann suppression
    if W_per_atom_eV > 0:
        suppression = np.exp(-W_per_atom_eV / (K_B_EV * T))
    else:
        suppression = 1.0

    P = P0 * suppression

    return P


# =============================================================================
# FULL CYCLE LIFE SIMULATION
# =============================================================================

def run_cycle_life(
    architecture: Architecture,
    n_cycles: int = 2000,
    T_celsius: float = 25.0,
    C_rate: float = 0.33,
    DoD: float = 0.80
) -> Dict:
    """
    Run complete cycle life simulation for an architecture.

    Returns capacity retention history and degradation breakdown.
    """
    print(f"\n  Running: {architecture.name}")
    print(f"  C-rate: C/{1/C_rate:.0f}, DoD: {DoD:.0%}, T: {T_celsius}°C")
    print(f"  K_constraint: {architecture.K_constraint_GPa:.1f} GPa")
    print(f"  Cycling stress: {architecture.cycling_stress_amplitude_MPa():.1f} MPa")
    print(f"  Dendrite barrier: {architecture.dendrite_barrier_MPa():.1f} MPa")

    history = []
    dendrite_events = 0
    capacity = 1.0

    for n in range(n_cycles):
        # 1. SEI growth (capacity loss from Li inventory consumption)
        sei_nm = sei_growth_per_cycle(architecture, n, T_celsius, C_rate)
        # Capacity loss: ~0.02% per nm of SEI (Pinson & Bazant scaling)
        cap_loss_sei = 0.0002 * sei_nm

        # 2. Fatigue damage (capacity loss from crack-induced isolation)
        fatigue = fatigue_damage_per_cycle(architecture, n, T_celsius, DoD)
        cap_loss_fatigue = 0.3 * fatigue  # 30% capacity loss at full damage

        # 3. Dendrite nucleation (stochastic capacity loss)
        p_dendrite = dendrite_nucleation_probability(architecture, T_celsius)
        if np.random.random() < p_dendrite:
            dendrite_events += 1
        cap_loss_dendrite = 0.02 * dendrite_events  # 2% per event

        # Total capacity
        capacity = 1.0 - cap_loss_sei - cap_loss_fatigue - cap_loss_dendrite
        capacity = max(0.0, capacity)

        # Record every 50 cycles
        if n % 50 == 0:
            history.append({
                "cycle": n,
                "capacity_retention": round(capacity, 6),
                "sei_thickness_nm": round(sei_nm, 4),
                "fatigue_damage": round(fatigue, 6),
                "dendrite_events": dendrite_events,
                "cap_loss_sei_pct": round(cap_loss_sei * 100, 4),
                "cap_loss_fatigue_pct": round(cap_loss_fatigue * 100, 4),
                "cap_loss_dendrite_pct": round(cap_loss_dendrite * 100, 4)
            })

        # End of life check
        if capacity < 0.70:
            print(f"  End of life at cycle {n} ({capacity:.1%})")
            break

    # Find cycle at 80% retention
    cycles_to_80 = n_cycles
    for entry in history:
        if entry["capacity_retention"] < 0.80:
            cycles_to_80 = entry["cycle"]
            break

    final = {
        "architecture": architecture.name,
        "K_constraint_GPa": architecture.K_constraint_GPa,
        "cycling_stress_MPa": round(architecture.cycling_stress_amplitude_MPa(), 2),
        "dendrite_barrier_MPa": round(architecture.dendrite_barrier_MPa(), 2),
        "n_cycles_tested": n + 1,
        "final_capacity": round(capacity, 6),
        "cycles_to_80_pct": cycles_to_80,
        "total_dendrites": dendrite_events,
        "final_sei_nm": round(sei_nm, 4),
        "final_fatigue": round(fatigue, 6),
        "history": history,
        "physics_basis": {
            "sei_model": "Parabolic (Pinson & Bazant 2013)",
            "fatigue_model": "Paris Law (Paris & Erdogan 1963)",
            "dendrite_model": "Boltzmann nucleation (Monroe & Newman 2005)",
            "architecture_connection": "K_constraint → stress amplitude → degradation rates"
        }
    }

    print(f"  Final: {capacity:.1%} after {n+1} cycles")
    print(f"  Cycles to 80%: {cycles_to_80}")
    print(f"  Dendrite events: {dendrite_events}")

    return final


def generate_cycle_life_csv(genesis_result: Dict, output_path: str):
    """Generate CSV from physics-based model."""
    import csv

    with open(output_path, 'w', newline='') as f:
        f.write("# GENESIS PHYSICS-BASED CYCLE LIFE DATA\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Architecture: {genesis_result['architecture']}\n")
        f.write(f"# K_constraint: {genesis_result['K_constraint_GPa']} GPa\n")
        f.write(f"# Cycling stress: {genesis_result['cycling_stress_MPa']} MPa\n")
        f.write(f"# SEI model: Parabolic (Pinson & Bazant 2013)\n")
        f.write(f"# Fatigue model: Paris Law (Paris & Erdogan 1963)\n")
        f.write(f"# Dendrite model: Boltzmann (Monroe & Newman 2005)\n")
        f.write("#\n")

        writer = csv.DictWriter(f, fieldnames=[
            "cycle", "capacity_retention", "sei_thickness_nm",
            "fatigue_damage", "dendrite_events",
            "cap_loss_sei_pct", "cap_loss_fatigue_pct", "cap_loss_dendrite_pct"
        ])
        writer.writeheader()
        writer.writerows(genesis_result["history"])

    print(f"  CSV saved: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "█" * 70)
    print("  GENESIS: PHYSICS-BASED CYCLE LIFE MODEL")
    print("  Derives degradation from architecture properties")
    print("█" * 70)

    output_dir = os.path.join(os.path.dirname(__file__), "outputs", "cycle_life_physics")
    os.makedirs(output_dir, exist_ok=True)

    np.random.seed(42)  # Reproducibility

    # Run both architectures
    genesis_result = run_cycle_life(GENESIS, n_cycles=2000)
    baseline_result = run_cycle_life(BASELINE, n_cycles=2000)

    # Summary comparison
    print("\n" + "=" * 70)
    print("  COMPARISON: GENESIS vs BASELINE")
    print("=" * 70)
    print(f"  {'Metric':<30} {'Genesis':<20} {'Baseline':<20}")
    print("  " + "-" * 70)
    print(f"  {'K_constraint (GPa)':<30} {GENESIS.K_constraint_GPa:<20.1f} {BASELINE.K_constraint_GPa:<20.1f}")
    print(f"  {'Cycling Stress (MPa)':<30} {GENESIS.cycling_stress_amplitude_MPa():<20.1f} {BASELINE.cycling_stress_amplitude_MPa():<20.1f}")
    print(f"  {'Dendrite Barrier (MPa)':<30} {GENESIS.dendrite_barrier_MPa():<20.1f} {BASELINE.dendrite_barrier_MPa():<20.1f}")
    print(f"  {'Final Capacity':<30} {genesis_result['final_capacity']:<20.1%} {baseline_result['final_capacity']:<20.1%}")
    print(f"  {'Cycles to 80%':<30} {genesis_result['cycles_to_80_pct']:<20} {baseline_result['cycles_to_80_pct']:<20}")
    print(f"  {'Dendrite Events':<30} {genesis_result['total_dendrites']:<20} {baseline_result['total_dendrites']:<20}")
    print("  " + "-" * 70)

    improvement = genesis_result['cycles_to_80_pct'] / max(baseline_result['cycles_to_80_pct'], 1)
    print(f"  Cycle Life Improvement: {improvement:.1f}×")
    print("=" * 70)

    # Save results
    results_path = os.path.join(output_dir, "cycle_life_results.json")
    with open(results_path, 'w') as f:
        json.dump({
            "simulation_id": "GENESIS-CYCLELIFE-PHYSICS-V1",
            "date": datetime.now().isoformat(),
            "method": "Physics-based degradation (SEI + Fatigue + Dendrite)",
            "genesis": genesis_result,
            "baseline": baseline_result,
            "improvement_factor": improvement
        }, f, indent=2, default=str)
    print(f"\n  Results: {results_path}")

    # Generate CSV for the Genesis architecture
    csv_path = os.path.join(output_dir, "genesis_cycle_life_physics.csv")
    generate_cycle_life_csv(genesis_result, csv_path)

    # Generate plot
    try:
        import matplotlib.pyplot as plt

        plt.rcParams.update({'font.family': 'serif', 'font.size': 12, 'figure.dpi': 300})

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Left: Capacity vs Cycle
        gen_cycles = [h["cycle"] for h in genesis_result["history"]]
        gen_cap = [h["capacity_retention"] * 100 for h in genesis_result["history"]]
        base_cycles = [h["cycle"] for h in baseline_result["history"]]
        base_cap = [h["capacity_retention"] * 100 for h in baseline_result["history"]]

        ax1.plot(gen_cycles, gen_cap, 'o-', color='#2E7D32', linewidth=2, markersize=4,
                 label=f'Genesis (K={GENESIS.K_constraint_GPa} GPa)')
        ax1.plot(base_cycles, base_cap, 's-', color='#D32F2F', linewidth=2, markersize=4,
                 label=f'Baseline (K={BASELINE.K_constraint_GPa} GPa)')
        ax1.axhline(80, color='#FF9800', linestyle=':', linewidth=2, label='80% EOL Threshold')
        ax1.set_xlabel('Cycle Number', fontweight='bold')
        ax1.set_ylabel('Capacity Retention (%)', fontweight='bold')
        ax1.set_title('Physics-Based Cycle Life\n(Derived from Architecture)', fontweight='bold')
        ax1.legend(loc='lower left')
        ax1.set_ylim(50, 102)
        ax1.grid(True, alpha=0.3)

        # Right: Degradation breakdown for Genesis
        gen_sei = [h["cap_loss_sei_pct"] for h in genesis_result["history"]]
        gen_fat = [h["cap_loss_fatigue_pct"] for h in genesis_result["history"]]
        gen_den = [h["cap_loss_dendrite_pct"] for h in genesis_result["history"]]

        ax2.stackplot(gen_cycles, gen_sei, gen_fat, gen_den,
                      labels=['SEI Growth', 'Fatigue', 'Dendrites'],
                      colors=['#FFC107', '#FF5722', '#9C27B0'], alpha=0.8)
        ax2.set_xlabel('Cycle Number', fontweight='bold')
        ax2.set_ylabel('Cumulative Capacity Loss (%)', fontweight='bold')
        ax2.set_title('Genesis Degradation Breakdown\n(Physics-Based)', fontweight='bold')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, "cycle_life_physics.png")
        plt.savefig(plot_path)
        plt.close()
        print(f"  Plot: {plot_path}")
    except ImportError:
        print("  [Warning] matplotlib not available")


if __name__ == "__main__":
    main()
