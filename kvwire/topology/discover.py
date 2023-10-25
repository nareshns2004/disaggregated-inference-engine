"""Discover topology with read-only probes (`nvidia-smi topo -m`, /sys/class/infiniband).

Run via `make topo`. Never modifies system state.
"""

from __future__ import annotations

import argparse
import shutil
import sys

from kvwire.topology.schema import Topology


def parse_nvidia_smi_topo(text: str) -> dict[tuple[int, str], str]:
    """Parse the `nvidia-smi topo -m` matrix into {(gpu, nic_label): link}. TODO(M1)."""
    raise NotImplementedError("M1: add a captured fixture under tests/fixtures/ first")


def discover() -> Topology:
    raise NotImplementedError("M1")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.parse_args(argv)
    if shutil.which("nvidia-smi") is None:
        print(
            "nvidia-smi not found: topology discovery needs a GPU host (tier 2).", file=sys.stderr
        )
        return 1
    raise NotImplementedError("M1")


if __name__ == "__main__":
    sys.exit(main())
