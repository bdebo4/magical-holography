# Data directory

Everything under this directory is a staged, checksummed, immutable copy of the inputs this
capsule's hardware analyses and figures are built from: executed circuits, raw hardware counts,
optimized calibration artifacts, and the manuscript's own saved reference outputs. SHA-256
checksums for every staged file are in `checksums/SHA256SUMS` and are verified by
`holographic_codes.cli validate-inputs` before any analysis runs.

```text
data/
├── manifests/              # which jobs/circuits are analyzed, plus a circuit-regression report
├── executed_circuits/      # staged QPY circuits, by experiment/condition
├── hardware_counts/        # staged raw 36-bit IonQ count JSONs, by experiment/condition
├── optimized_artifacts/    # pickled optimized recovery circuits + x_best_010.npy
├── reference_simulations/  # staged production simulation JSONs (regression oracles)
├── reference_summaries/    # staged hardware-analysis summary JSONs (regression oracles)
├── checksums/SHA256SUMS    # one line per staged file, verified by `validate-inputs`
└── plot_design_settings.json
```

`executed_circuits/` and `hardware_counts/` are the raw inputs to `analyze-hardware`, restricted to
exactly the circuits and jobs listed in `manifests/selected_circuits.csv` and
`selected_hardware_jobs.csv`. `reference_simulations/` and `reference_summaries/` are frozen outputs
from the original manuscript analysis that `code/run` checks newly generated results against, not
files this capsule regenerates.

Nothing under this directory is written to at runtime by `holographic_codes` -- all outputs go to
`/results` (or `HOLOGRAPHIC_CODES_RESULT_ROOT`). Do not edit files here by hand: they are immutable,
checksummed regression fixtures, and every module that consumes them documents its own source in
`code/provenance/`.
