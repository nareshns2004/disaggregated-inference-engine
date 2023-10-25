#!/usr/bin/env python3
"""Collect an environment manifest using READ-ONLY probes. Missing tools are recorded, not fatal.

python scripts/env_manifest.py                      # print JSON
python scripts/env_manifest.py --write docs/ENVIRONMENT.md   # fill the GENERATED block
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
from pathlib import Path

PROBES: dict[str, list[str]] = {
    "kernel": ["uname", "-r"],
    "gpu": [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,pci.bus_id",
        "--format=csv,noheader",
    ],
    "gpu_topo": ["nvidia-smi", "topo", "-m"],
    "nvcc": ["nvcc", "--version"],
    "ibv_devinfo": ["ibv_devinfo"],
    "rdma_link": ["rdma", "link", "show"],
    "ofed": ["ofed_info", "-s"],
    "peermem": ["sh", "-c", "lsmod | grep -E 'nvidia_peermem|nv_peer_mem' || true"],
    "iommu": ["sh", "-c", "cat /proc/cmdline"],
    "perftest": [
        "sh",
        "-c",
        "ib_write_bw --help 2>&1 | grep -i -- '--use_cuda' || echo 'no --use_cuda'",
    ],
    "vllm": ["python3", "-c", "import vllm; print(vllm.__version__)"],
}


def run(cmd: list[str]) -> str:
    if shutil.which(cmd[0]) is None:
        return f"<{cmd[0]} not found>"
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
        return (out.stdout or out.stderr).strip()
    except subprocess.TimeoutExpired:
        return "<timeout>"


def collect() -> dict[str, str]:
    m = {"host_arch": platform.machine(), "python": platform.python_version()}
    m.update({k: run(v) for k, v in PROBES.items()})
    m["topology_hash"] = hashlib.sha256(m["gpu_topo"].encode()).hexdigest()[:16]
    return m


def write_block(doc: Path, manifest: dict[str, str]) -> None:
    body = "```json\n" + json.dumps(manifest, indent=2) + "\n```"
    text = doc.read_text()
    new = re.sub(
        r"(<!-- GENERATED:BEGIN -->).*?(<!-- GENERATED:END -->)",
        lambda mt: f"{mt.group(1)}\n{body}\n{mt.group(2)}",
        text,
        flags=re.S,
    )
    doc.write_text(new)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", type=Path)
    args = ap.parse_args()
    m = collect()
    if args.write:
        write_block(args.write, m)
    else:
        print(json.dumps(m, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
