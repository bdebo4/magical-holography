{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset0 Menlo-Bold;\f1\fnil\fcharset0 Menlo-Regular;\f2\fnil\fcharset0 Menlo-Italic;
}
{\colortbl;\red255\green255\blue255;\red90\green96\blue214;\red255\green255\blue255;\red0\green0\blue0;
}
{\*\expandedcolortbl;;\cssrgb\c42745\c47451\c87059;\cssrgb\c100000\c100000\c100000;\cssrgb\c0\c0\c0;
}
\margl1440\margr1440\vieww29700\viewh17280\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\b\fs24 \cf2 \cb3 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 # Holographic codes: SC8 / WH10 / WH16 reproducibility capsule
\f1\b0 \cf0 \cb1 \strokec4 \
\

\f0\b \cf2 \cb3 \strokec2 ## Scope
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 This capsule reproduces the hardware-analysis and figure-generation workflows for three\cb1 \
\cb3 holographic-code experiments reported in the manuscript:\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 | Workflow | Qubits | Hardware grid | Tomography |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |---|---:|---|---|
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  SC8 (single
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 copy reduced code) 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  8 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  5 theta x 3 magic 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  27 shared post
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 recovery 3
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 qubit settings 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  WH10 (two
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 copy wormhole code) 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  10 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  3 theta x 3 magic 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  81 boundary + 9 bulk settings 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  WH16 (16
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 qubit two
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 copy code) 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  16 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  2 theta x 2 magic 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  81 boundary + 81 bulk settings 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 It runs from data staged under 
\f2\i `/data`
\f1\i0 . See "Further detail" below and\cb1 \
\cb3 each module's own docstring for the specific evidence behind any nontrivial design choice.\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## One-command reproduction
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 ```bash\cb1 \
\cb3 code/run\cb1 \
\cb3 ```\cb1 \
\
\cb3 This validates every staged input's checksum, runs all three hardware analyses from the staged raw counts, validates the staged reference-simulation files, regenerates the main figures, and writes a machine-readable 
\f2\i `run_report.json`
\f1\i0  under\cb1 \
\pard\pardeftab720\partightenfactor0

\f2\i \cf0 \cb3 `/results`
\f1\i0  (or 
\f2\i `HOLOGRAPHIC_CODES_RESULT_ROOT`
\f1\i0  during local development). It does not run the expensive full simulations.\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 Individual steps:\cb1 \
\
\cb3 ```bash\cb1 \
\cb3 python -m holographic_codes.cli validate-inputs\cb1 \
\cb3 python -m holographic_codes.cli validate-simulations\cb1 \
\cb3 python -m holographic_codes.cli analyze-hardware --experiment \{sc8,wh10,wh16\}\cb1 \
\cb3 python -m holographic_codes.cli simulate --experiment \{sc8,wh10,wh16\} --mode quick\cb1 \
\cb3 python -m holographic_codes.cli simulate --experiment \{sc8,wh10,wh16\} --mode full\cb1 \
\cb3 python -m holographic_codes.cli make-figures\cb1 \
\cb3 python -m pytest code/tests\cb1 \
\cb3 ```\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## Quick vs. full simulation
\f1\b0 \cf0 \cb1 \strokec4 \
\

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **quick**
\f1\b0 : uses reduced trajectory counts (
\f2\i `K`
\f1\i0 ), shots, and bootstrap repeats, to\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   prove the simulation pipeline executes end to end. Output filenames include 
\f2\i `quick`
\f1\i0 .\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **full**
\f1\b0 : uses the exact production parameters recovered from each staged reference simulation\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   JSON's own 
\f2\i `_meta`
\f1\i0  block (theta/magic grids, 
\f2\i `qst_trajectory_batch_K`
\f1\i0 , shots-per-magic, bootstrap\cb1 \
\cb3   repeats/seed) -- see 
\f2\i `code/configs/\{sc8,wh10,wh16\}_simulation_full.yaml`
\f1\i0 . Because the original Monte Carlo trajectory is not recoverable from the audited source, regenerated arrays are compared to the staged reference with a statistical tolerance; this is expensive (K up to 200 trajectories per Pauli setting) and is not part of the default 
\f2\i `code/run`
\f1\i0 .\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## SC8: shared post-recovery tomography
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 SC8's 27 executed circuits per condition (named 
\f2\i `bound_XXX`
\f1\i0  .. 
\f2\i `bound_ZZZ`
\f1\i0 ) already includes the recovery/decode step; the boundary entropy reconstructs the full 3-qubit post-recovery state from all 27 settings, and the bulk (1-qubit) entropy reuses exactly 3 of those same settings (
\f2\i `P Z Z`
\f1\i0  for P in \{X,Y,Z\}) as a marginal single-qubit estimator (drop the classical bits of the two Z-measured qubits and keep only the third). There is no separate 3-circuit SC8 bulk dataset. See 
\f2\i `code/src/holographic_codes/analysis/sc8.py`
\f1\i0 .\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## WH10: data exclusions
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 The final WH10 hardware grid excludes two data groups of 200 shots\cb1 \
\cb3 each, due to low two-qubit fidelity spot checks: group 12 (
\f2\i `theta=0393, mu=027`
\f1\i0 ) and group 13 (
\f2\i `theta=0393, mu=000`
\f1\i0 ). \cb1 \
\pard\pardeftab720\partightenfactor0

\f2\i \cf0 \cb3 `data/manifests/selected_hardware_jobs.csv`
\f1\i0  defines\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 the analyzed dataset.\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## WH16: nominal vs. actual shots, and the magic=0.0 recovery-ordering bug
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 WH16 experiment shots are nominally ~1000/setting (only 
\f2\i `theta=0785, mu=000`
\f1\i0  has 950 shots).\cb1 \
\
\cb3 The WH16 circuits are also named with a 
\f2\i `_bound_`
\f1\i0  substring on disk even for the 81 "bulk" settings (a\cb1 \
\cb3 historical filename quirk, kept for provenance); 
\f2\i `measurement_role`
\f1\i0  in the manifest distinguishes\cb1 \
\cb3 them semantically.\cb1 \
\
\cb3 For 
\f2\i `magic=0.0`
\f1\i0 , a circuit-construction bug caused the boundary-tomography circuits to include the recovery operation, even though boundary tomography was intended to be performed on the pre-recovery encoded state. This does 
\f0\b **not**
\f1\b0  change the boundary observable ideally as the recovery acts only on the 12 qubits complementary to the four boundary qubits being measured, leaving their reduced density matrix unchanged. Numerical checks confirm agreement at floating-point precision. The main consequence is therefore only additional circuit depth, which may introduce extra hardware noise; that noise is already present in the recorded experimental counts and is preserved in this capsule. It is also reflected in the simulations, which simulate the same data circuits that are run on the quantum hardware.\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## Outputs
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0

\f2\i \cf0 \cb3 `code/run`
\f1\i0  writes to 
\f2\i `/results`
\f1\i0  (or 
\f2\i `HOLOGRAPHIC_CODES_RESULT_ROOT`
\f1\i0  during local development):\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 | Output | Path |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |---|---|
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  Hardware entropy summaries (SC8, WH10, WH16) 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  
\f2\i `results/summaries/*_entropy_summary.generated.json`
\f1\i0  
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  Manuscript figures (boundary/bulk/QES vs. theta) 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  
\f2\i `results/figures/\{sc8,wh10,wh16\}_main.png`
\f1\i0  
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  Numerical arrays behind the figures 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  
\f2\i `results/numerical/\{sc8,wh10,wh16\}_main.json`
\f1\i0  
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \

\f0\b \cf2 \cb3 \strokec2 |
\f1\b0 \cf0 \strokec4  Per
\f0\b \cf2 \strokec2 -
\f1\b0 \cf0 \strokec4 step run report 
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \strokec4  
\f2\i `results/run_report.json`
\f1\i0  
\f0\b \cf2 \strokec2 |
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 Figures and numerical arrays are produced by 
\f2\i `figures/\{sc8,wh10,wh16\}_main.py`
\f1\i0 ; the generated\cb1 \
\cb3 summaries are produced by 
\f2\i `analysis/\{sc8,wh10,wh16\}.py`
\f1\i0  + 
\f2\i `io/summaries.py`
\f1\i0 . The default run takes\cb1 \
\cb3 on the order of tens of minutes, dominated by bootstrap resampling in the hardware analysis; full-mode\cb1 \
\cb3 simulation (above) is separate and is not required to reproduce the main results.\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## Reproducibility notes
\f1\b0 \cf0 \cb1 \strokec4 \
\

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Bit ordering / qubit mapping**
\f1\b0 : raw hardware counts are 36-bit IonQ ion-register bitstrings; the\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   ion-to-qubit mapping is recorded per job in 
\f2\i `data/manifests/selected_hardware_jobs.csv`
\f1\i0  and applied\cb1 \
\cb3   by 
\f2\i `data/bit_order.py`
\f1\i0  (tested in 
\f2\i `code/tests/test_bit_order.py`
\f1\i0 ), never re-derived at runtime.\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Randomness**
\f1\b0 : all bootstrap resampling uses a seeded 
\f2\i `numpy.random.Generator`
\f1\i0 \cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   (
\f2\i `bootstrap_seed`
\f1\i0  in 
\f2\i `code/configs/*.yaml`
\f1\i0 , default 
\f2\i `12345`
\f1\i0 , matching every staged reference\cb1 \
\cb3   simulation's own seed). No code path uses an unseeded RNG.\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Software environment**
\f1\b0 : 
\f2\i `qiskit`
\f1\i0  is pinned to 
\f2\i `2.2.3`
\f1\i0  to match the version embedded in the\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   staged executed QPY circuits' headers.\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Circuit regression**
\f1\b0 : every selected circuit is checked against its staged, previously-executed\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   QPY file for measurement-probability equivalence (full batch: 1,863/1,863 pass, 0 failures --\cb1 \
\cb3   
\f2\i `data/manifests/circuit_regression_report.json`
\f1\i0 ; 
\f2\i `code/tests/test_circuit_regression.py`
\f1\i0  runs a\cb1 \
\cb3   representative sample by default).\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Reference comparison**
\f1\b0 : 
\f2\i `analyze-hardware`
\f1\i0  compares each generated summary against the frozen\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   summary in 
\f2\i `data/reference_summaries/`
\f1\i0  to a numerical tolerance and reports pass/fail.\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## Licensing and attribution
\f1\b0 \cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf0 \cb3 Dependencies (Qiskit, qiskit-ionq, Qiskit Aer, Cirq, NumPy/SciPy, pandas, Matplotlib, QuTiP, PyYAML)\cb1 \
\cb3 are permissively licensed (Apache-2.0 / BSD-3-Clause / MIT-family) and installed from PyPI; none are\cb1 \
\cb3 vendored into this repository. Circuit-construction and analysis logic, and all staged\cb1 \
\cb3 hardware/simulation data, originate from the manuscript authors' own research code; this capsule is\cb1 \
\cb3 a reproducibility artifact for that manuscript rather than an independently-licensed release. No\cb1 \
\cb3 third-party code beyond these dependencies and the manuscript's own logic is included.\cb1 \
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 ## Further detail
\f1\b0 \cf0 \cb1 \strokec4 \
\

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Provenance**
\f1\b0 : 
\f2\i `code/provenance/`
\f1\i0  records which source repository and notebook cell each module\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   was derived from; every staged input is checksummed in 
\f2\i `data/checksums/SHA256SUMS`
\f1\i0 . The original\cb1 \
\cb3   private research repositories are not required to run this capsule.\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Parameterization**
\f1\b0 : exact historical grids, qubit indices, and shot expectations per experiment\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   are in 
\f2\i `code/configs/*.yaml`
\f1\i0 .\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Selected data**
\f1\b0 : 
\f2\i `data/manifests/selected_circuits.csv`
\f1\i0  and 
\f2\i `selected_hardware_jobs.csv`
\f1\i0  define\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   exactly which circuits and hardware jobs are analyzed; 
\f2\i `conditions.yaml`
\f1\i0  summarizes the grid.\cb1 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \cb3 \strokec2 - \cf0 \strokec4 **Tests**
\f1\b0 : 
\f2\i `code/tests/`
\f1\i0  (
\f2\i `pytest code/tests`
\f1\i0 ) covers bit-order/mapping correctness, circuit\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3   regression, hardware-analysis regression against frozen references, and CLI smoke tests.\cb1 \
}