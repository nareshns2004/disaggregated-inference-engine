"""Append-only JSONL ledger of FaultInjection records: the ground truth that recovery and
corruption results are joined against. Same schema idea as goodput (ADR-0004)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from kvwire.schemas import FaultInjection


class Ledger:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: FaultInjection) -> None:
        with self._path.open("a") as f:
            f.write(json.dumps(asdict(rec), sort_keys=True) + "\n")
