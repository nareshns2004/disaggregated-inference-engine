"""Hardware-tier markers: gpu / multinode / rxe tests are skipped unless explicitly enabled."""

from __future__ import annotations

import pytest

TIERS = ("gpu", "multinode", "rxe")


def pytest_addoption(parser: pytest.Parser) -> None:
    for t in TIERS:
        parser.addoption(f"--run-{t}", action="store_true", default=False, help=f"run {t} tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for t in TIERS:
        if config.getoption(f"--run-{t}"):
            continue
        skip = pytest.mark.skip(reason=f"needs --run-{t}")
        for item in items:
            if t in item.keywords:
                item.add_marker(skip)
