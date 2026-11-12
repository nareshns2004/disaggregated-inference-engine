from __future__ import annotations

import json
from pathlib import Path

from faultlab.ledger import Ledger
from kvwire.schemas import FaultInjection, FaultLabel


def test_append_writes_one_json_line_per_record(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "sub" / "faults.jsonl")
    for i in range(2):
        ledger.append(FaultInjection(f"f{i}", "K07", FaultLabel.INDUCED, "prefill:0", t_start_ns=i))
    lines = (tmp_path / "sub" / "faults.jsonl").read_text().splitlines()
    assert [json.loads(x)["id"] for x in lines] == ["f0", "f1"]
    assert json.loads(lines[0])["label"] == "induced"
