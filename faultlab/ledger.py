"""Append-only JSONL ledger of FaultInjection records: the ground truth that recovery and
corruption results are joined against. Same conventions as goodput (ADR-0004, ADR-0006)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from kvwire.schemas import FaultInjection


class Ledger:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: FaultInjection) -> None:
        """Append one record durably: an injected fault missing from the ledger after a
        harness crash would later look like a real (unscheduled) fault."""
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
