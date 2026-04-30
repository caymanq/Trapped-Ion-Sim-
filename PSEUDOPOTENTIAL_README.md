# RF Pseudopotential Implementation

## 📋 Quick Summary

This implementation adds **RF pseudopotential transformation** to your ion trap multipole analysis, matching the methodology from Chapter 5 of the reference thesis.

### Key Equation (Eq. 5.2):
```
φ_ps(r) = (q / (4 × m × Ω²_rf)) × |V_rf × ∇φ_rf(r)|²
```

---

## 🎯 Why This Matters

### Static Approximation (What You Had):
- Solves ∇²V = 0 with RF electrodes at ±1V
- **Misses** the |∇φ|² nonlinearity
- **Underestimates** higher-order multipoles (especially hexapole)
- Good for wrapped traps, **poor for surface traps**

### Pseudopotential (What You Need):
- Transforms static φ_rf → pseudopotential φ_ps
- **Captures** ponderomotive force physics
- **Amplifies** field line bending (|∇φ|² term)
- **Explains** why surface traps have p₃/p₂ ≈ 1.0

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `multipole_pseudopotential.py` | Core implementation module |
| `example_pseudopotential_usage.py` | Demo script with integration guide |
| `PSEUDOPOTENTIAL_README.md` | This file - quick reference |

---

## 🚀 Quick Start

### Option 1: Run the Example
```bash
cd "Trapped Ions"
python example_pseudopotential_usage.py
```

This will:
1. Show you the integration guide
2. Run a 4-wire surface trap example
3. Generate comparison plots
4. Demonstrate the difference between static vs pseudopotential

### Option 2: Use in Your Code
```python
# 1. Import
from multipole_pseudopotential import compute_pseudopotential, RF_VOLTAGE

# 2. After solving Laplace equation
V = solve_potential(nx, ny, electrodes, fixed, V)

# 3. Transform to pseudopotential
V_pseudo = compute_pseudopotential(V, X, Y, V_rf=RF_VOLTAGE)

# 4. Fit pseudopotential (not V!)
fit = fit_multipoles_2d(V_pseudo, X_shifted, Y_shifted, ...)
```

---

## 🔬 Default Parameters

Based on typical NIST ion trap experiments:

| Parameter | Value | Notes |
|-----------|-------|-------|
| Ion | ¹⁷¹Yb⁺ | 171 amu |
| RF Frequency | 30 MHz | Range: 10-50 MHz |
| RF Voltage | 500 V | Peak amplitude |
| Ion Charge | 1.602×10⁻¹⁹ C | Elementary charge |

### To Change Parameters:
```python
# Custom ion (e.g., ⁴⁰Ca⁺)
from scipy.constants import atomic_mass
custom_mass = 40 * atomic_mass  # kg

# Custom RF
custom_rf = 2 * np.pi * 25e6  # 25 MHz
custom_v_rf = 300.0  # 300V

V_pseudo = compute_pseudopotential(V, X, Y, 
                                   V_rf=custom_v_rf,
                                   m_ion=custom_mass,
                                   Omega_rf=custom_rf)
```

---

## 📊 Expected Results

### Wrapped Traps (a-e):
| Trap | Geometry | Expected p₃/p₂ |
|------|----------|---------------|
| (a) | 2-layer | ~0.0015 |
| (b) | Balanced 2-layer | ~0.0011 |
| (c) | 3-layer | ~0.0006 |
| (d) | AlGaAs | ~0.0026 |
| (e) | In-plane 4-wire | ~0.0008 |

**Why small?** Symmetric geometry → hexapole cancels by symmetry

### Surface Traps (f-h):
| Trap | Geometry | Expected p₃/p₂ |
|------|----------|---------------|
| (f) | 4-wire surface | **~0.973** |
| (g) | 5-wire symmetric | **~0.996** |
| (h) | 5-wire asymmetric | **~1.010** |

**Why large?** Field lines must bend to reach surface electrodes → |∇φ|² is large near electrodes → hexapole component necessary

---

## 🔧 Integration into Your Notebook

### Minimal Changes Required:

**BEFORE:**
```python
def simulate_trap(...):
    # ... solve Laplace equation ...
    V = solve_potential(nx, ny, electrodes, fixed, V, max_iter=max_iter, tol=1e-3)
    
    # ... setup fitting region ...
    
    # Fit static potential
    fit = fit_multipoles_2d(
        V, X_shifted, Y_shifted,  # ❌ Static potential
        r_fit_um=r_fit,
        ion_elc_dis_um=ion_elc_dis,
        n_max=8,
        exclude_mask=exclude_mask
    )
```

**AFTER:**
```python
def simulate_trap(...):
    # ... solve Laplace equation ...
    V = solve_potential(nx, ny, electrodes, fixed, V, max_iter=max_iter, tol=1e-3)
    
    # *** ADD THIS ***
    from multipole_pseudopotential import compute_pseudopotential, RF_VOLTAGE
    V_pseudo = compute_pseudopotential(V, X, Y, V_rf=RF_VOLTAGE)
    
    # ... setup fitting region ...
    
    # Fit pseudopotential
    fit = fit_multipoles_2d(
        V_pseudo, X_shifted, Y_shifted,  # ✅ Pseudopotential
        r_fit_um=r_fit,
        ion_elc_dis_um=ion_elc_dis,
        n_max=8,
        exclude_mask=exclude_mask
    )
```

**That's it!** Just 2 lines changed.

---

## 🧪 Validation

### How to Know It's Working:

1. **Surface traps should have p₃/p₂ ≈ 1.0**
   - If still small (< 0.1), pseudopotential not being used
   
2. **Wrapped traps should stay small**
   - p₃/p₂ < 0.01 (numerical precision)
   
3. **Center pseudopotential should be minimum**
   - φ_ps(0,0) should be a local minimum (trapping!)
   
4. **Visual check:**
   - Static potential: symmetric quadrupole
   - Pseudopotential: shows field line curvature

---

## 📐 Physical Intuition

### Why |∇φ|² Matters:

```
Surface Trap Electric Field:
  ┌─────────────────┐
  │    Free Space   │  ← Field lines must bend
  │        ↓↘↓      │     to reach electrodes
  │      (ion)      │
  ╞═══╤═══╤═══╤════╡  ← All electrodes in plane
  │RF+│GND│GND│RF- │
  └───┴───┴───┴────┘

|∇φ|² is LARGE where field bends sharply
  → Hexapole term must be present
  → p₃ ≈ p₂ (same magnitude!)
```

### Mathematical View:

```
Quadrupole only:
  φ = A·(x² - y²)
  |∇φ|² = 4A²(x² + y²)  ← Not enough curvature

Quadrupole + Hexapole:
  φ = A·(x² - y²) + B·(x³ - 3xy²)
  |∇φ|² includes x⁴, x²y², y⁴ terms
    → More curvature freedom
    → Can match surface geometry
```

---

## ⚙️ Performance Notes

| Grid Size | Time | Accuracy | Recommendation |
|-----------|------|----------|----------------|
| 101×101 | ~30 sec | Good | Quick tests |
| 201×201 | ~2 min | Better | Standard |
| 401×401 | ~10 min | Best | Publication quality |

**Pseudopotential computation:** < 1 second (just gradient calculation)

---

## 🐛 Troubleshooting

### Problem: Import Error
```python
ModuleNotFoundError: No module named 'multipole_pseudopotential'
```
**Solution:** Make sure `multipole_pseudopotential.py` is in the same directory as your notebook

### Problem: Results unchanged
**Check:**
1. Did you pass `V_pseudo` (not `V`) to `fit_multipoles_2d`?
2. Did you actually call `compute_pseudopotential()`?
3. Print max/min of V vs V_pseudo - they should differ!

### Problem: Pseudopotential looks wrong
**Check:**
1. Units: X, Y should be in µm (micrometers)
2. V should be dimensionless (φ_rf at 1V)
3. RF_VOLTAGE should be in Volts (not mV or kV)

### Problem: p₃/p₂ is huge (> 10)
**Possible causes:**
1. Fitting radius too large (includes electrode region)
2. Ion position wrong (not at potential minimum)
3. Electrode mask not excluded from fit

---

## 📚 References

### From Thesis:
- **Eq. 5.2:** Pseudopotential formula
- **Chapter 3:** Multipole comparison (Table 3.2)
- **Chapter 5:** BEM modeling methodology
- **Figure 3.6:** Field line bending in surface traps

### Physics Background:
- Ponderomotive force in RF fields
- Time-averaged potentials
- Harmonic expansion of potentials
- Boundary element method (BEM)

---

## 💡 Tips

1. **Start simple:** Test on one trap (e.g., 4-wire surface) first
2. **Compare plots:** Visual inspection often reveals issues
3. **Check symmetry:** p₃/p₂ should be ~0 for symmetric traps
4. **Validate physics:** φ_ps minimum should be at ion position
5. **Grid resolution:** Higher grid → better ∇φ → better pseudopotential

---

## ✅ Checklist for Integration

- [ ] Copy `multipole_pseudopotential.py` to Trapped Ions folder
- [ ] Import module at top of notebook
- [ ] Add `compute_pseudopotential()` after solving Laplace
- [ ] Change `fit_multipoles_2d()` to use `V_pseudo` instead of `V`
- [ ] Run one trap as test
- [ ] Verify surface trap has p₃/p₂ ≈ 1.0
- [ ] Run all 8 traps
- [ ] Compare with Table 3.2 reference values

---

## 📞 Support

If results still don't match Table 3.2 after using pseudopotential:
1. Check electrode dimensions match paper
2. Verify ion height (especially for surface traps)
3. Ensure fitting radius is appropriate
4. Consider 3D effects (may need BEM for exact match)

Remember: 2D pseudopotential is much better than 2D static, but still an approximation of full 3D BEM!

---

**Good luck with your simulations! 🚀**

