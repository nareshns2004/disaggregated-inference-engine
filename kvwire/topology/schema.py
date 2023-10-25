"""topology.json schema. Link types follow `nvidia-smi topo -m`: PIX < PXB < PHB < NODE < SYS."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

TOPOLOGY_SCHEMA_VERSION = 1


class Link(enum.IntEnum):  # ordered: lower is closer
    NV = 0  # NVLink (GPU-GPU only)
    PIX = 1
    PXB = 2
    PHB = 3
    NODE = 4
    SYS = 5


@dataclass(frozen=True, slots=True)
class Gpu:
    index: int
    pci_bus_id: str
    numa_node: int
    name: str


@dataclass(frozen=True, slots=True)
class Nic:
    name: str  # e.g. mlx5_0
    netdev: str | None
    pci_bus_id: str
    numa_node: int
    link_layer: str  # "InfiniBand" | "Ethernet"
    rate_gbps: float | None


@dataclass(slots=True)
class Topology:
    host: str
    gpus: list[Gpu] = field(default_factory=list)
    nics: list[Nic] = field(default_factory=list)
    gpu_nic_link: dict[tuple[int, str], Link] = field(default_factory=dict)
    version: int = TOPOLOGY_SCHEMA_VERSION

    def nearest_nic(self, gpu: int) -> str | None:
        cands = [(link, nic) for (g, nic), link in self.gpu_nic_link.items() if g == gpu]
        return min(cands)[1] if cands else None
