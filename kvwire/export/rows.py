"""Row types for the six configs of the `rdma-kv-transfer-traces` dataset (ADR-0007).

Plain frozen dataclasses, like the rest of `kvwire.schemas`: the core stays dependency-free.
Every row carries ``run_id`` and ``env_hash`` so it joins back to `bench/results/` and to
the ``environments`` config. Units are part of the contract: ``COLUMN_UNITS`` must cover
every numeric column (a test enforces it), and the dataset card's column dictionary is
generated from it.

Throughput is decimal GB/s (1 GB/s = 1 byte/ns). Durations are integer nanoseconds unless
the column name says otherwise. All ``layer_timelines`` timestamps are CLOCK_MONOTONIC on
the prefill host, so they are comparable with each other and with nothing else.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Literal

DATASET_SCHEMA_VERSION = 1

Memory = Literal["gpu", "host"]
#: Transports as named in EVALUATION §2 / TRANSPORT §4.
Transport = Literal["rdma_a", "rdma_b", "rdma_c", "rdma_d", "tcp", "nixl", "reference"]
#: How GPU memory reaches the NIC (ADR-0002). ``host_staging`` rows are the labelled fallback.
GpuDirectMode = Literal["dmabuf", "peermem", "host_staging", "none"]


@dataclass(frozen=True, slots=True)
class EnvironmentRow:
    env_hash: str
    gpu: str
    driver: str
    cuda: str
    nic_model: str
    nic_fw: str
    link_gbps: float
    rdma_core: str
    kernel: str
    gpudirect_mode: GpuDirectMode
    pcie_topo_hash: str
    vllm_commit: str | None
    is_rxe: bool  # SoftRoCE: logic-only, never enters the main configs


@dataclass(frozen=True, slots=True)
class CeilingRow:
    run_id: str
    env_hash: str
    nic: str
    message_bytes: int
    n_qps: int
    memory: Memory
    bw_gb_per_s: float
    lat_us: float | None


@dataclass(frozen=True, slots=True)
class TransferKey:
    """The configuration a transfer measurement is aggregated over."""

    model: str
    n_layers: int
    kv_heads: int
    head_dim: int
    dtype: str
    context_len: int
    batch: int
    block_size: int
    kv_layout: Literal["interleaved", "separate"]
    tp: int
    transport: Transport
    nic: str
    message_bytes: int  # region size: one WR's payload in the naive strategy
    n_qps: int  # per rail
    rails: int
    gpudirect_mode: GpuDirectMode


@dataclass(frozen=True, slots=True)
class TransferRawRow:
    run_id: str
    env_hash: str
    key: TransferKey
    rep: int
    total_bytes: int
    duration_ns: int
    cpu_ns: int | None  # sender CPU time spent on the transfer, if measured


@dataclass(frozen=True, slots=True)
class TransferRow:
    run_id: str
    env_hash: str
    key: TransferKey
    n_reps: int
    total_bytes: int
    duration_ns_p50: int
    duration_ns_p99: int
    throughput_gb_per_s: float  # total_bytes / duration_ns_p50
    ceiling_region_gb_per_s: float | None  # rails x same-size ceiling
    ceiling_peak_gb_per_s: float | None  # rails x large-message peak (headline denominator)
    efficiency_vs_region_ceiling: float | None
    efficiency_vs_peak: float | None
    cpu_s_per_gb: float | None
    host_staging: bool


@dataclass(frozen=True, slots=True)
class PrefillRow:
    run_id: str
    env_hash: str
    model: str
    context_len: int
    batch: int
    tp: int
    gpu: str
    n_reps: int
    duration_ms_p50: float
    duration_ms_p99: float


@dataclass(frozen=True, slots=True)
class LayerTimelineRow:
    run_id: str
    env_hash: str
    req_id: str
    transfer_id: int
    layer: int
    prefill_start_ns: int
    prefill_end_ns: int
    enqueued_ns: int | None
    sent_ns: int | None
    commit_ns: int | None  # set on the last layer's row only
    send_after_compute_ns: int | None  # sent_ns - prefill_end_ns: transfer not hidden by compute


COLUMN_UNITS: dict[str, str] = {
    "link_gbps": "Gb/s (line rate)",
    "message_bytes": "bytes",
    "n_qps": "count (per rail)",
    "bw_gb_per_s": "GB/s (decimal; 1 GB/s = 1 byte/ns)",
    "lat_us": "µs",
    "n_layers": "count",
    "kv_heads": "count",
    "head_dim": "elements",
    "context_len": "tokens",
    "batch": "requests",
    "block_size": "tokens per KV block",
    "tp": "tensor-parallel degree",
    "rails": "count",
    "rep": "index",
    "total_bytes": "bytes",
    "duration_ns": "ns",
    "cpu_ns": "ns (CPU time)",
    "n_reps": "count",
    "duration_ns_p50": "ns",
    "duration_ns_p99": "ns",
    "throughput_gb_per_s": "GB/s (decimal)",
    "ceiling_region_gb_per_s": "GB/s (decimal)",
    "ceiling_peak_gb_per_s": "GB/s (decimal)",
    "efficiency_vs_region_ceiling": "ratio (throughput / same-size ceiling)",
    "efficiency_vs_peak": "ratio (throughput / large-message peak)",
    "cpu_s_per_gb": "CPU seconds per GB moved",
    "duration_ms_p50": "ms",
    "duration_ms_p99": "ms",
    "transfer_id": "id",
    "layer": "index",
    "prefill_start_ns": "ns (CLOCK_MONOTONIC, prefill host)",
    "prefill_end_ns": "ns (CLOCK_MONOTONIC, prefill host)",
    "enqueued_ns": "ns (CLOCK_MONOTONIC, prefill host)",
    "sent_ns": "ns (CLOCK_MONOTONIC, prefill host)",
    "commit_ns": "ns (CLOCK_MONOTONIC, prefill host)",
    "send_after_compute_ns": "ns",
}

CONFIG_ROW_TYPES: dict[str, type] = {
    "transfers": TransferRow,
    "transfers_raw": TransferRawRow,
    "layer_timelines": LayerTimelineRow,
    "ceilings": CeilingRow,
    "prefill": PrefillRow,
    "environments": EnvironmentRow,
}


def flatten(row: object) -> dict[str, object]:
    """Row → flat column dict (``TransferKey`` fields are inlined)."""
    out: dict[str, object] = {}
    for f in dataclasses.fields(row):  # type: ignore[arg-type]
        v = getattr(row, f.name)
        if dataclasses.is_dataclass(v) and not isinstance(v, type):
            out.update(flatten(v))
        else:
            out[f.name] = v
    return out
