"""Checks that run before every upload (HF Project 2 booklet §8.2, ADR-0007).

Errors block publishing; warnings are printed and must be explained in the card.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Literal, Protocol, cast

from kvwire.export.build import Dataset
from kvwire.export.rows import COLUMN_UNITS, CONFIG_ROW_TYPES, TransferKey

#: Above this, efficiency against the same-size ceiling is physically implausible.
EFFICIENCY_SANITY_LIMIT = 1.0


class _Joinable(Protocol):
    @property
    def run_id(self) -> str: ...
    @property
    def env_hash(self) -> str: ...


@dataclass(frozen=True)
class Issue:
    level: Literal["error", "warning"]
    config: str
    check: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.config}: {self.check}: {self.message}"


def _numeric_columns(row_type: type) -> list[str]:
    cols: list[str] = []
    for f in dataclasses.fields(row_type):
        if f.type in ("TransferKey", TransferKey):
            cols.extend(_numeric_columns(TransferKey))
        elif {t.strip() for t in str(f.type).split("|")} & {"int", "float"}:
            cols.append(f.name)
    return cols


def validate(ds: Dataset) -> list[Issue]:
    issues: list[Issue] = []

    def err(config: str, check: str, msg: str) -> None:
        issues.append(Issue("error", config, check, msg))

    env_by_hash = {e.env_hash: e for e in ds.environments}

    # Units declared for every numeric column.
    for name, row_type in CONFIG_ROW_TYPES.items():
        for col in _numeric_columns(row_type):
            if col not in COLUMN_UNITS:
                err(name, "units", f"numeric column {col!r} has no declared unit")

    for name, rows in ds.configs().items():
        if name == "environments":
            continue
        for i, obj in enumerate(rows):
            row = cast(_Joinable, obj)
            run_id = row.run_id
            eh = row.env_hash
            if run_id not in ds.run_ids:
                err(name, "joinability", f"row {i}: run_id {run_id!r} was not an input run")
            env = env_by_hash.get(eh)
            if env is None:
                err(name, "joinability", f"row {i}: env_hash {eh!r} not in environments")
            elif env.is_rxe:
                err(name, "provenance", f"row {i}: SoftRoCE (rxe) row in a main config")

    for i, t in enumerate(ds.transfers):
        where = f"row {i} ({t.run_id}, {t.key.transport}, {t.key.message_bytes} B)"
        if t.ceiling_region_gb_per_s is None:
            err(
                "transfers",
                "ceiling coverage",
                f"{where}: no ceiling at the same NIC, message size, QP count and memory mode",
            )
        eff = t.efficiency_vs_region_ceiling
        if eff is not None and eff > EFFICIENCY_SANITY_LIMIT:
            issues.append(
                Issue(
                    "warning",
                    "transfers",
                    "physical sanity",
                    f"{where}: efficiency {eff:.3f} > 1.0 against the same-size ceiling",
                )
            )
        if t.host_staging != (t.key.gpudirect_mode == "host_staging"):
            err("transfers", "provenance", f"{where}: host-staging label inconsistent")

    if not ds.ceilings and (ds.transfers or ds.layer_timelines):
        err("ceilings", "ceiling coverage", "transfer data without any ceilings")
    return issues


def has_errors(issues: list[Issue]) -> bool:
    return any(i.level == "error" for i in issues)
