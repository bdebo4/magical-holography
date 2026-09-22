"""Filesystem roots for the capsule.

All paths are resolved relative to the package location so the capsule works
identically inside Code Ocean (``/code`` + ``/data`` + ``/results``) and in a
local development checkout (``code-ocean-code/code`` + ``.../data`` +
``.../results``). No path in this module ever points outside the capsule's
own ``code/`` and ``data/`` trees, and nothing here imports from or reads
the original construction/execution source repositories this capsule was
migrated from -- those are historical inputs to the migration, not a
runtime dependency of ``holographic_codes``.

Result-root policy (see :func:`result_root`): inside Code Ocean, outputs
always go to ``/results`` (pre-mounted by the platform). Outside Code Ocean,
outputs go to ``HOLOGRAPHIC_CODES_RESULT_ROOT`` if set, else to a
``local_results/`` directory created next to this project. Nothing under
``code/`` or ``data/`` (or in ``pytest code/tests``, which always pins an
explicit temporary result root) ever reads from ``local_results/`` --
deleting it has no effect on a fresh run, which simply recreates it.
"""
from __future__ import annotations

import os
from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file until a directory containing ``data/`` and
    ``code/`` siblings is found (the ``code-ocean-code`` project root)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data").is_dir() and (parent / "code").is_dir():
            return parent
    # Fallback: Code Ocean capsule layout mounts /code and /data directly.
    return Path("/")


PROJECT_ROOT = _find_project_root()
CODE_ROOT = PROJECT_ROOT / "code"
DATA_ROOT = Path(os.environ.get("HOLOGRAPHIC_CODES_DATA_ROOT", PROJECT_ROOT / "data"))
CONFIG_ROOT = CODE_ROOT / "configs"


def result_root() -> Path:
    """Runtime output root: the single source of truth used by every writer
    in this package (and by ``code/run``, which asks this function for the
    path rather than hard-coding its own copy of this logic).

    Resolution order:

    1. ``HOLOGRAPHIC_CODES_RESULT_ROOT``, if set -- always wins, for tests
       and local development that want an explicit, isolated output
       directory.
    2. ``/results``, if it already exists as a directory -- true inside
       Code Ocean, which pre-mounts it before the capsule runs.
    3. Otherwise, ``local_results/`` next to this project -- a local
       development convenience only; nothing reads from it, and deleting it
       has no effect beyond recreating it on the next run.

    The directory is created if missing before being returned, so callers
    never need their own ``mkdir``.
    """
    override = os.environ.get("HOLOGRAPHIC_CODES_RESULT_ROOT")
    if override:
        root = Path(override)
    else:
        code_ocean_results = Path("/results")
        root = code_ocean_results if code_ocean_results.is_dir() else PROJECT_ROOT / "local_results"
    root.mkdir(parents=True, exist_ok=True)
    return root


def manifests_dir() -> Path:
    return DATA_ROOT / "manifests"


def executed_circuits_dir() -> Path:
    return DATA_ROOT / "executed_circuits"


def hardware_counts_dir() -> Path:
    return DATA_ROOT / "hardware_counts"


def reference_summaries_dir() -> Path:
    return DATA_ROOT / "reference_summaries"


def reference_simulations_dir() -> Path:
    return DATA_ROOT / "reference_simulations"


def optimized_artifacts_dir() -> Path:
    return DATA_ROOT / "optimized_artifacts"


def numerical_results_dir() -> Path:
    d = result_root() / "numerical"
    d.mkdir(parents=True, exist_ok=True)
    return d


def figures_dir() -> Path:
    d = result_root() / "figures"
    d.mkdir(parents=True, exist_ok=True)
    return d
