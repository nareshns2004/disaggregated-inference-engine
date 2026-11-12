"""The Python transport facade must mirror the C++ status codes exactly (CONTRIBUTING)."""

from __future__ import annotations

import re
from pathlib import Path

from kvwire.transport import TransportStatus

STATUS_H = Path(__file__).resolve().parents[2] / "transport/include/kvwire/transport/status.h"


def _cpp_codes() -> list[str]:
    body = re.search(r"enum class StatusCode[^{]*\{(.*?)\};", STATUS_H.read_text(), re.S)
    assert body, "StatusCode enum not found in status.h"
    names = re.findall(r"^\s*k([A-Za-z]+)", body.group(1), re.M)
    return [re.sub(r"(?<!^)(?=[A-Z])", "_", n).lower() for n in names]


def test_python_status_matches_cpp_status_code_in_order() -> None:
    assert [s.value for s in TransportStatus] == _cpp_codes()
