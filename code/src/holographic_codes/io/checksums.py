"""SHA-256 helpers for validating staged inputs at runtime.

Used by ``validate-inputs`` (01_IMPLEMENTATION_SPEC.md section 10) to confirm
every file a config references still matches its manifest-recorded checksum
before any analysis runs -- catching silent corruption/substitution of
staged data, independent of the Phase-1 migration tooling under ``tools/``.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(path: str | Path, expected_sha256: str) -> bool:
    return sha256_of_file(path) == expected_sha256
