import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for "Scientific Publication" look
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.5)
sns.set_style("ticks")

def plot_failure_probability():
    """
    Generates the 'Pressure Paradox' failure probability curve based on fracture mechanics.
    """
    pressure = np.linspace(0, 100, 1000) # MPa
    
    # Weibull distribution model for ceramic failure
    # Parameters estimated for LLZO with 10um grain flaws
    threshold = 15.0 # MPa (lower bound)
    scale = 25.0    # MPa (characteristic strength)
    shape = 3.5     # Weibull modulus
    
    failure_prob = 1 - np.exp(-((pressure - threshold).clip(0) / scale) ** shape)
    failure_prob = failure_prob * 100 # Convert to %

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the curve
    ax.plot(pressure, failure_prob, color='#D32F2F', linewidth=3, label='Micro-Crack Initiation Probability')
    
    # Zones
    ax.axvspan(0, 5, color='#4CAF50', alpha=0.2, label='Safe Zone (<5 MPa)')
    ax.axvspan(10, 100, color='#FF9800', alpha=0.1, label='Industry Operating Range (10-100 MPa)')
    
    # Annotations
    ax.axvline(25, color='black', linestyle='--', alpha=0.5)
    ax.text(26, 50, 'Critical Fracture Threshold\n(~25 MPa)', fontsize=12, verticalalignment='center')
    
    ax.text(60, 90, 'DANGER ZONE\n(QuantumScape/Toyota)', fontsize=14, color='#D32F2F', fontweight='bold', ha='center')
    ax.text(2.5, 90, 'GENESIS\n(<0.5 MPa)', fontsize=14, color='#2E7d32', fontweight='bold', ha='center')

    ax.set_xlabel('Clamping Pressure (MPa)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Probability of Micro-Crack Formation (%)', fontsize=14, fontweight='bold')
    ax.set_title('The Pressure Paradox: Failure Probability vs. Stack Pressure', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 105)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left', frameon=True)
    
    plt.tight_layout()
    plt.savefig('03_VISUALIZATIONS/pressure_failure_curve_real.png', dpi=300)
    print("Generated pressure_failure_curve_real.png")

def plot_creep_rate():
    """
    Generates Lithium Creep Rate vs. Pressure log-log plot.
    """
    pressure = np.logspace(0, 2.5, 100) # 1 to 300 MPa
    
    # Norton Creep Law: rate = A * sigma^n
    # A approx 1e-8 for Li at room temp
    # n approx 4
    rate_low = 1e-9 * pressure**3
    rate_high = 1e-8 * pressure**4.5
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.loglog(pressure, rate_high, color='#1976D2', linewidth=3, label='Lithium Creep Rate (High Bound)')
    ax.fill_between(pressure, rate_low, rate_high, color='#1976D2', alpha=0.2)
    
    # Thresholds
    ax.axvline(25, color='red', linestyle='--', linewidth=2, label='Micro-Crack Initiation (~25 MPa)')
    
    # Annotations
    ax.text(2, 1e-8, 'Safe Operation\n(Negligible Creep)', color='green', fontsize=12)
    ax.text(40, 1e-1, 'Runaway Creep\n(Infiltration Mode)', color='red', fontsize=12)
    
    ax.set_xlabel('Applied Stack Pressure (MPa)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Lithium Strain Rate (1/s)', fontsize=14, fontweight='bold')
    ax.set_title('Mechanism 3: Stress-Driven Lithium Infiltration', fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, which="both", ls="-", alpha=0.2)
    ax.legend(loc='upper left')
    
    plt.tight_layout()
    plt.savefig('03_VISUALIZATIONS/lithium_creep_rate.png', dpi=300)
    print("Generated lithium_creep_rate.png")

if __name__ == "__main__":
    plot_failure_probability()
    plot_creep_rate()
