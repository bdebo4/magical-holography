"""Command-line entry points (01_IMPLEMENTATION_SPEC.md section 10).

    python -m holographic_codes.cli validate-inputs
    python -m holographic_codes.cli analyze-hardware --experiment sc8
    python -m holographic_codes.cli simulate --experiment sc8 --mode quick
    python -m holographic_codes.cli simulate --experiment sc8 --mode full
    python -m holographic_codes.cli make-figures
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .io.checksums import verify_checksum
from .io.summaries import build_summary, compare_summaries, load_summary, write_summary
from .paths import DATA_ROOT, PROJECT_ROOT, manifests_dir, result_root
from .simulation.schemas import validate_simulation_schema

EXPERIMENTS = ("sc8", "wh10", "wh16")

MEASUREMENT_SCHEME_META = {
    "sc8": dict(measurement_scheme="shared_post_recovery_equal_depth", num_executed_settings=27, bulk_from_same_tomography=True),
    "wh10": dict(measurement_scheme="separate_boundary_bulk", num_executed_settings=90, bulk_from_same_tomography=False),
    "wh16": dict(measurement_scheme="separate_boundary_bulk_shared_filename_quirk", num_executed_settings=162, bulk_from_same_tomography=False),
}


def _analysis_module(experiment: str):
    if experiment == "sc8":
        from .analysis import sc8 as mod
    elif experiment == "wh10":
        from .analysis import wh10 as mod
    elif experiment == "wh16":
        from .analysis import wh16 as mod
    else:
        raise ValueError(f"Unknown experiment {experiment!r}")
    return mod


def _simulation_module(experiment: str):
    if experiment == "sc8":
        from .simulation import sc8 as mod
    elif experiment == "wh10":
        from .simulation import wh10 as mod
    elif experiment == "wh16":
        from .simulation import wh16 as mod
    else:
        raise ValueError(f"Unknown experiment {experiment!r}")
    return mod


def _figure_module(experiment: str):
    if experiment == "sc8":
        from .figures import sc8_main as mod
    elif experiment == "wh10":
        from .figures import wh10_main as mod
    elif experiment == "wh16":
        from .figures import wh16_main as mod
    else:
        raise ValueError(f"Unknown experiment {experiment!r}")
    return mod


def cmd_validate_inputs(args: argparse.Namespace) -> int:
    problems = []
    for path in [
        manifests_dir() / "selected_circuits.csv",
        manifests_dir() / "selected_hardware_jobs.csv",
        DATA_ROOT / "checksums" / "SHA256SUMS",
    ]:
        if not path.is_file():
            problems.append(f"missing required manifest file: {path}")

    checksum_file = DATA_ROOT / "checksums" / "SHA256SUMS"
    n_checked = 0
    if checksum_file.is_file():
        for line in checksum_file.read_text().splitlines():
            if not line.strip():
                continue
            digest, relpath = line.split(None, 1)
            full = DATA_ROOT / relpath.strip()
            if not full.is_file():
                problems.append(f"staged file missing: {relpath}")
                continue
            if not verify_checksum(full, digest):
                problems.append(f"checksum mismatch: {relpath}")
            n_checked += 1

    for experiment in EXPERIMENTS:
        cfg = load_config(f"{experiment}_hardware")
        ref_path = DATA_ROOT / cfg.reference_summary
        if not ref_path.is_file():
            problems.append(f"{experiment}: missing reference summary {ref_path}")

    report = {"checked_files": n_checked, "problems": problems, "status": "ok" if not problems else "failed"}
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1


def cmd_validate_simulations(args: argparse.Namespace) -> int:
    """Load and schema-validate every staged production simulation JSON
    (01_IMPLEMENTATION_SPEC.md section 7's default-run step: "load staged
    saved simulations; validate schema/checksum")."""
    problems = []
    checked = []
    seen_paths: set[str] = set()

    for experiment in EXPERIMENTS:
        for mode in (f"{experiment}_simulation_full",):
            cfg = load_config(mode)
            if not cfg.reference_simulation:
                continue
            rel = cfg.reference_simulation
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            path = DATA_ROOT / rel
            if not path.is_file():
                problems.append(f"{experiment}: missing reference simulation {path}")
                continue
            try:
                sim_json = load_summary(path)
            except json.JSONDecodeError as exc:
                problems.append(f"{experiment}: {path} is not valid JSON: {exc}")
                continue
            schema_problems = validate_simulation_schema(sim_json)
            checked.append({"experiment": experiment, "path": str(path), "schema_valid": not schema_problems})
            problems.extend(f"{experiment}: {path.name}: {p}" for p in schema_problems)

    # WH16 has a second staged reference simulation (K5, a lower-trajectory-count
    # companion run to the K50 file already checked above via its config) --
    # 01_IMPLEMENTATION_SPEC.md section 9 lists both explicitly.
    wh16_k5 = DATA_ROOT / "reference_simulations" / (
        "WH16_constructed_coherr_000_000_randerr_000_125_5theta_mu000-010_optEnc_optReco_K5_shots1000_runs5_boot10_combined_typical_count.json"
    )
    if wh16_k5.is_file():
        sim_json = load_summary(wh16_k5)
        schema_problems = validate_simulation_schema(sim_json)
        checked.append({"experiment": "wh16", "path": str(wh16_k5), "schema_valid": not schema_problems})
        problems.extend(f"wh16: {wh16_k5.name}: {p}" for p in schema_problems)
    else:
        problems.append(f"wh16: missing K5 companion reference simulation {wh16_k5}")

    report = {"checked": checked, "problems": problems, "status": "ok" if not problems else "failed"}
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1


def cmd_analyze_hardware(args: argparse.Namespace) -> int:
    experiment = args.experiment
    cfg = load_config(f"{experiment}_hardware")
    mod = _analysis_module(experiment)
    results = mod.run_hardware_analysis(cfg)

    tag = "SC" if experiment == "sc8" else experiment.upper()
    provenance = {
        "config_name": cfg.name,
        "config_version": cfg.version,
        "selected_circuits_manifest": cfg.selected_circuits_manifest,
        "selected_jobs_manifest": cfg.selected_jobs_manifest,
        "bootstrap_seed": cfg.bootstrap_seed,
        "bootstrap_repeats": cfg.bootstrap_repeats,
        "n_conditions_analyzed": len(results),
    }
    summary = build_summary(
        tag, results, cfg.theta_codes, cfg.theta_values, cfg.magic_values,
        **MEASUREMENT_SCHEME_META[experiment],
        extra_meta={"provenance": provenance},
    )
    out_dir = result_root() / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{tag}_entropy_summary.generated.json"
    write_summary(summary, out_path)

    reference = load_summary(DATA_ROOT / cfg.reference_summary)
    comparison = compare_summaries(summary, reference, tag)

    report = {
        "experiment": experiment,
        "n_conditions": len(results),
        "generated_summary": str(out_path),
        "reference_summary": str(DATA_ROOT / cfg.reference_summary),
        "max_boundary_mean_diff": comparison.max_boundary_mean_diff,
        "max_bulk_mean_diff": comparison.max_bulk_mean_diff,
        "max_qes_mean_diff": comparison.max_qes_mean_diff,
        "within_tolerance": comparison.within_tolerance,
    }
    print(json.dumps(report, indent=2))
    return 0 if comparison.within_tolerance else 1


def cmd_simulate(args: argparse.Namespace) -> int:
    experiment = args.experiment
    cfg = load_config(f"{experiment}_simulation_{args.mode}")
    mod = _simulation_module(experiment)

    results = mod.run_simulation(cfg)
    out_dir = result_root() / "simulations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{experiment}_{args.mode}_simulation.json"
    with open(out_path, "w") as f:
        json.dump(
            [dataclass_to_dict(r) for r in results],
            f, indent=2,
        )

    report = {
        "experiment": experiment, "mode": args.mode,
        "n_conditions": len(results), "output": str(out_path),
        "note": "quick mode is a pipeline smoke test, not a production reproduction" if args.mode == "quick" else
                "full mode uses production parameters but is not guaranteed bitwise-identical to the staged reference, because the original per-trajectory RNG state is not recoverable from the audited source; comparison uses a statistical tolerance",
    }
    print(json.dumps(report, indent=2))
    return 0


def dataclass_to_dict(obj) -> dict:
    import dataclasses
    return {f.name: getattr(obj, f.name) for f in dataclasses.fields(obj)}


def cmd_make_figures(args: argparse.Namespace) -> int:
    outputs = []
    for experiment in EXPERIMENTS:
        cfg = load_config(f"{experiment}_hardware")
        tag = "SC" if experiment == "sc8" else experiment.upper()
        summary_path = result_root() / "summaries" / f"{tag}_entropy_summary.generated.json"
        if not summary_path.is_file():
            print(f"skip {experiment}: run analyze-hardware first ({summary_path} missing)", file=sys.stderr)
            continue
        summary = load_summary(summary_path)
        mod = _figure_module(experiment)
        arrays = mod.make_figure(summary, cfg)
        outputs.append(experiment)
    print(json.dumps({"figures_written": outputs}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="holographic_codes")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate-inputs").set_defaults(func=cmd_validate_inputs)
    sub.add_parser("validate-simulations").set_defaults(func=cmd_validate_simulations)

    p = sub.add_parser("analyze-hardware")
    p.add_argument("--experiment", choices=EXPERIMENTS, required=True)
    p.set_defaults(func=cmd_analyze_hardware)

    p = sub.add_parser("simulate")
    p.add_argument("--experiment", choices=EXPERIMENTS, required=True)
    p.add_argument("--mode", choices=("quick", "full"), required=True)
    p.set_defaults(func=cmd_simulate)

    sub.add_parser("make-figures").set_defaults(func=cmd_make_figures)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
