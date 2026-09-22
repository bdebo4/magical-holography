# Holographic codes: SC8 / WH10 / WH16 reproducibility capsule

## Scope

This capsule reproduces the hardware-analysis and figure-generation workflows for three
holographic-code experiments reported in the manuscript:

| Workflow | Qubits | Hardware grid | Tomography |
|---|---:|---|---|
| SC8 (single-copy reduced code) | 8 | 5 theta x 3 magic | 27 shared post-recovery 3-qubit settings |
| WH10 (two-copy wormhole code) | 10 | 3 theta x 3 magic | 81 boundary + 9 bulk settings |
| WH16 (16-qubit two-copy code) | 16 | 2 theta x 2 magic | 81 boundary + 81 bulk settings |

It runs from data staged under `/data`. See "Further detail" below and
each module's own docstring for the specific evidence behind any nontrivial design choice.

## One-command reproduction

```bash
code/run
```

This validates every staged input's checksum, runs all three hardware analyses from the staged raw counts, validates the staged reference-simulation files, regenerates the main figures, and writes a machine-readable `run_report.json` under
`/results` (or `HOLOGRAPHIC_CODES_RESULT_ROOT` during local development). It does not run the expensive full simulations.

Individual steps:

```bash
python -m holographic_codes.cli validate-inputs
python -m holographic_codes.cli validate-simulations
python -m holographic_codes.cli analyze-hardware --experiment {sc8,wh10,wh16}
python -m holographic_codes.cli simulate --experiment {sc8,wh10,wh16} --mode quick
python -m holographic_codes.cli simulate --experiment {sc8,wh10,wh16} --mode full
python -m holographic_codes.cli make-figures
python -m pytest code/tests
```

## Quick vs. full simulation

- **quick**: uses reduced trajectory counts (`K`), shots, and bootstrap repeats, to
  prove the simulation pipeline executes end to end. Output filenames include `quick`.
- **full**: uses the exact production parameters recovered from each staged reference simulation
  JSON's own `_meta` block (theta/magic grids, `qst_trajectory_batch_K`, shots-per-magic, bootstrap
  repeats/seed) -- see `code/configs/{sc8,wh10,wh16}_simulation_full.yaml`. Because the original Monte Carlo trajectory is not recoverable from the audited source, regenerated arrays are compared to the staged reference with a statistical tolerance; this is expensive (K up to 200 trajectories per Pauli setting) and is not part of the default `code/run`.

## SC8: shared post-recovery tomography

SC8's 27 executed circuits per condition (named `bound_XXX` .. `bound_ZZZ`) already includes the recovery/decode step; the boundary entropy reconstructs the full 3-qubit post-recovery state from all 27 settings, and the bulk (1-qubit) entropy reuses exactly 3 of those same settings (`P Z Z` for P in {X,Y,Z}) as a marginal single-qubit estimator (drop the classical bits of the two Z-measured qubits and keep only the third). There is no separate 3-circuit SC8 bulk dataset. See `code/src/holographic_codes/analysis/sc8.py`.

## WH10: data exclusions

The final WH10 hardware grid excludes two data groups of 200 shots
each, due to low two-qubit fidelity spot checks: group 12 (`theta=0393, mu=027`) and group 13 (`theta=0393, mu=000`). 
`data/manifests/selected_hardware_jobs.csv` defines
the analyzed dataset.

## WH16: nominal vs. actual shots, and the magic=0.0 recovery-ordering bug

WH16 experiment shots are nominally ~1000/setting (only `theta=0785, mu=000` has 950 shots).

The WH16 circuits are also named with a `_bound_` substring on disk even for the 81 "bulk" settings (a
historical filename quirk, kept for provenance); `measurement_role` in the manifest distinguishes
them semantically.

For `magic=0.0`, a circuit-construction bug caused the boundary-tomography circuits to include the recovery operation, even though boundary tomography was intended to be performed on the pre-recovery encoded state. This does **not** change the boundary observable ideally as the recovery acts only on the 12 qubits complementary to the four boundary qubits being measured, leaving their reduced density matrix unchanged. Numerical checks confirm agreement at floating-point precision. The main consequence is therefore only additional circuit depth, which may introduce extra hardware noise; that noise is already present in the recorded experimental counts and is preserved in this capsule. It is also reflected in the simulations, which simulate the same data circuits that are run on the quantum hardware.

## Outputs

`code/run` writes to `/results` (or `HOLOGRAPHIC_CODES_RESULT_ROOT` during local development):

| Output | Path |
|---|---|
| Hardware entropy summaries (SC8, WH10, WH16) | `results/summaries/*_entropy_summary.generated.json` |
| Manuscript figures (boundary/bulk/QES vs. theta) | `results/figures/{sc8,wh10,wh16}_main.png` |
| Numerical arrays behind the figures | `results/numerical/{sc8,wh10,wh16}_main.json` |
| Per-step run report | `results/run_report.json` |

Figures and numerical arrays are produced by `figures/{sc8,wh10,wh16}_main.py`; the generated
summaries are produced by `analysis/{sc8,wh10,wh16}.py` + `io/summaries.py`. The default run takes
on the order of tens of minutes, dominated by bootstrap resampling in the hardware analysis; full-mode
simulation (above) is separate and is not required to reproduce the main results.

## Reproducibility notes

- **Bit ordering / qubit mapping**: raw hardware counts are 36-bit IonQ ion-register bitstrings; the
  ion-to-qubit mapping is recorded per job in `data/manifests/selected_hardware_jobs.csv` and applied
  by `data/bit_order.py` (tested in `code/tests/test_bit_order.py`), never re-derived at runtime.
- **Randomness**: all bootstrap resampling uses a seeded `numpy.random.Generator`
  (`bootstrap_seed` in `code/configs/*.yaml`, default `12345`, matching every staged reference
  simulation's own seed). No code path uses an unseeded RNG.
- **Software environment**: `qiskit` is pinned to `2.2.3` to match the version embedded in the
  staged executed QPY circuits' headers.
- **Circuit regression**: every selected circuit is checked against its staged, previously-executed
  QPY file for measurement-probability equivalence (full batch: 1,863/1,863 pass, 0 failures --
  `data/manifests/circuit_regression_report.json`; `code/tests/test_circuit_regression.py` runs a
  representative sample by default).
- **Reference comparison**: `analyze-hardware` compares each generated summary against the frozen
  summary in `data/reference_summaries/` to a numerical tolerance and reports pass/fail.

## Licensing and attribution

Dependencies (Qiskit, qiskit-ionq, Qiskit Aer, Cirq, NumPy/SciPy, pandas, Matplotlib, QuTiP, PyYAML)
are permissively licensed (Apache-2.0 / BSD-3-Clause / MIT-family) and installed from PyPI; none are
vendored into this repository. Circuit-construction and analysis logic, and all staged
hardware/simulation data, originate from the manuscript authors' own research code; this capsule is
a reproducibility artifact for that manuscript rather than an independently-licensed release. No
third-party code beyond these dependencies and the manuscript's own logic is included.

## Further detail

- **Provenance**: `code/provenance/` records which source repository and notebook cell each module
  was derived from; every staged input is checksummed in `data/checksums/SHA256SUMS`. The original
  private research repositories are not required to run this capsule.
- **Parameterization**: exact historical grids, qubit indices, and shot expectations per experiment
  are in `code/configs/*.yaml`.
- **Selected data**: `data/manifests/selected_circuits.csv` and `selected_hardware_jobs.csv` define
  exactly which circuits and hardware jobs are analyzed; `conditions.yaml` summarizes the grid.
- **Tests**: `code/tests/` (`pytest code/tests`) covers bit-order/mapping correctness, circuit
  regression, hardware-analysis regression against frozen references, and CLI smoke tests.
