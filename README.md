# Trapped Ion Sim

Jupyter notebooks that compare multipole moments for ion-trap cross-sections, replicating **Table 3.2** (multipole ratios \(p_N/p_2\)) for eight trap geometries.

## Notebooks

| File | Description |
|------|-------------|
| [`multipole_table_replication.ipynb`](multipole_table_replication.ipynb) | Laplace solve on a 2-D grid (sparse solver), multipole fits for RF and pseudopotential. |
| [`multipole_BEM.ipynb`](multipole_BEM.ipynb) | Same comparison using a **boundary element method** (2-D log kernel), with physics checks (Laplace residual, electrode voltages, far-field decay). |

Default ion parameters in the notebooks use \(^{9}\mathrm{Be}^+\)-style mass scaling and representative RF drive settings (see the first code cells).

## Requirements

Typical stack: Python 3, NumPy, SciPy, Matplotlib, Pandas, and a Jupyter environment (`jupyter` or VS Code / Cursor notebook support).

## License

Add a license if you plan to distribute this repository publicly.
