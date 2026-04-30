"""
Quick test of the corrected ion trap multipole analysis
"""

import sys
sys.path.append('.')

# Import the corrected module
from iontrap_multipoles_corrected import *

print("="*80)
print("TESTING CORRECTED ION TRAP MULTIPOLE ANALYSIS")
print("="*80)

# Test with just one trap to verify it works
print("\nCreating trap geometries...")
traps = create_trap_geometries()

# Test with the 2-layer trap (simplest)
print("\nTesting with 2-layer trap...")
trap = traps['2-layer']

print(f"Trap: {trap.name}")
print(f"Number of electrodes: {len(trap.electrodes)}")
print(f"Trap center: {trap.trap_center}")

# Solve Laplace equation (smaller grid for quick test)
print("\nSolving Laplace equation (test grid: 201x201)...")
V, x, y = solve_laplace_2d(trap, grid_size=201, domain_size=3.0)

# Extract multipoles
print("\nExtracting multipoles...")
multipole_coeffs, ratios, V_samples, theta_samples = extract_multipoles_polar(
    V, x, y, trap.trap_center, sample_radius=0.05, n_theta=180, max_order=8
)

# Print results
print("\n" + "="*80)
print("RESULTS FOR 2-LAYER TRAP")
print("="*80)
print(f"\n{'Order':<10} {'Calculated':<15} {'Reference':<15} {'Rel. Error':<15}")
print("-" * 60)

for n in range(3, 9):
    calc = ratios[f'p{n}/p2']
    ref = reference_data['2-layer'][f'p{n}/p2']
    error = abs(calc - ref) / (ref + 1e-10) * 100
    print(f"p{n}/p2{'':<4} {calc:<15.4f} {ref:<15.4f} {error:<14.1f}%")

print("\n" + "="*80)
print("TEST COMPLETE!")
print("="*80)
print("\nIf you see reasonable results above (errors < 100%), the corrected code is working.")
print("To analyze all traps with full resolution, run: python iontrap_multipoles_corrected.py")

