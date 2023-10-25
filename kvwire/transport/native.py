"""Lazy loader for the C++ extension. Returns None when it is not built (laptop tier)."""

from __future__ import annotations

import importlib
from types import ModuleType


def load() -> ModuleType | None:
    try:
        return importlib.import_module("kvwire._transport")
    except ImportError:
        return None
