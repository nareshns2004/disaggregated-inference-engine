"""Build the dataset's six configs from `bench/results/<run_id>/` directories.

Input contract (what a run directory must contain for export; every file is optional
except ``manifest.json``, and a missing file just contributes no rows):

```
<run_id>/
  manifest.json                 environment (EnvironmentRow fields except env_hash)
  ceiling/ceilings.csv          nic,message_bytes,n_qps,memory,bw_gb_per_s,lat_us
  transfers_raw.csv             TransferKey columns + rep,total_bytes,duration_ns,cpu_ns
  prefill.csv                   model,context_len,batch,tp,gpu,rep,duration_ms
  transfer_events.jsonl         kvwire.schemas.TransferEvent; detail has req_id and layer
  prefill_layers.jsonl          {req_id, transfer_id, layer, start_ns, end_ns}
```

Percentiles use the nearest-rank method. With fewer than 100 repetitions p99 is close to
the maximum, which the dataset card states.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from kvwire.export.rows import (
    CeilingRow,
    EnvironmentRow,
    LayerTimelineRow,
    PrefillRow,
    TransferKey,
    TransferRawRow,
    TransferRow,
)

ENV_FIELDS = (
    "gpu",
    "driver",
    "cuda",
    "nic_model",
    "nic_fw",
    "link_gbps",
    "rdma_core",
    "kernel",
    "gpudirect_mode",
    "pcie_topo_hash",
    "vllm_commit",
    "is_rxe",
)
_INT_KEY_FIELDS = (
    "n_layers",
    "kv_heads",
    "head_dim",
    "context_len",
    "batch",
    "block_size",
    "tp",
    "message_bytes",
    "n_qps",
    "rails",
)


class ExportError(ValueError):
    """The input cannot be exported as-is (malformed or inconsistent run data)."""


@dataclass
class Dataset:
    """All six configs, plus the run ids that were read (for joinability checks)."""

    run_ids: set[str] = field(default_factory=set)
    environments: list[EnvironmentRow] = field(default_factory=list)
    ceilings: list[CeilingRow] = field(default_factory=list)
    transfers_raw: list[TransferRawRow] = field(default_factory=list)
    transfers: list[TransferRow] = field(default_factory=list)
    prefill: list[PrefillRow] = field(default_factory=list)
    layer_timelines: list[LayerTimelineRow] = field(default_factory=list)
    dropped_rxe_rows: int = 0

    def configs(self) -> dict[str, Sequence[object]]:
        return {
            "transfers": self.transfers,
            "transfers_raw": self.transfers_raw,
            "layer_timelines": self.layer_timelines,
            "ceilings": self.ceilings,
            "prefill": self.prefill,
            "environments": self.environments,
        }


def env_hash(env: dict[str, Any]) -> str:
    """Stable 16-hex-digit hash of the environment fields (order-independent)."""
    canon = json.dumps({k: env.get(k) for k in ENV_FIELDS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile, q in (0, 100]."""
    if not values:
        raise ExportError("percentile of an empty sample")
    ordered = sorted(values)
    rank = max(1, math.ceil(q / 100 * len(ordered)))
    return ordered[rank - 1]


def memory_mode(gpudirect_mode: str) -> str:
    return "host" if gpudirect_mode in ("host_staging", "none") else "gpu"


def _csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ExportError(f"{path}:{n}: {e}") from e
    return out


def _opt_int(v: str | None) -> int | None:
    return int(v) if v not in (None, "") else None


def _opt_float(v: str | None) -> float | None:
    return float(v) if v not in (None, "") else None


def _load_env(run_dir: Path) -> EnvironmentRow:
    path = run_dir / "manifest.json"
    if not path.exists():
        raise ExportError(f"{run_dir}: missing manifest.json (no manifest, no export)")
    raw = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in ENV_FIELDS if k not in raw and k != "vllm_commit"]
    if missing:
        raise ExportError(f"{path}: missing environment fields {missing}")
    return EnvironmentRow(
        env_hash=env_hash(raw),
        gpu=str(raw["gpu"]),
        driver=str(raw["driver"]),
        cuda=str(raw["cuda"]),
        nic_model=str(raw["nic_model"]),
        nic_fw=str(raw["nic_fw"]),
        link_gbps=float(raw["link_gbps"]),
        rdma_core=str(raw["rdma_core"]),
        kernel=str(raw["kernel"]),
        gpudirect_mode=raw["gpudirect_mode"],
        pcie_topo_hash=str(raw["pcie_topo_hash"]),
        vllm_commit=raw.get("vllm_commit"),
        is_rxe=bool(raw["is_rxe"]),
    )


def _transfer_key(r: dict[str, str]) -> TransferKey:
    ints = {k: int(r[k]) for k in _INT_KEY_FIELDS}
    return TransferKey(
        model=r["model"],
        dtype=r["dtype"],
        kv_layout=cast(Any, r["kv_layout"]),
        transport=cast(Any, r["transport"]),
        nic=r["nic"],
        gpudirect_mode=cast(Any, r["gpudirect_mode"]),
        **ints,
    )


def _layer_timelines(run_id: str, eh: str, run_dir: Path) -> list[LayerTimelineRow]:
    windows = _jsonl(run_dir / "prefill_layers.jsonl")
    events = _jsonl(run_dir / "transfer_events.jsonl")
    enq: dict[tuple[int, int], int] = {}
    sent: dict[tuple[int, int], int] = {}
    commit: dict[int, int] = {}
    for e in events:
        tid, kind, ts = int(e["transfer_id"]), e["kind"], int(e["ts_ns"])
        layer = e.get("detail", {}).get("layer")
        if kind == "committed":
            commit[tid] = ts
        elif layer is not None and kind in ("enqueued", "layer_sent"):
            (enq if kind == "enqueued" else sent)[(tid, int(layer))] = ts
    last_layer: dict[int, int] = defaultdict(int)
    for w in windows:
        last_layer[int(w["transfer_id"])] = max(last_layer[int(w["transfer_id"])], int(w["layer"]))
    rows = []
    for w in sorted(windows, key=lambda w: (str(w["req_id"]), int(w["layer"]))):
        tid, layer = int(w["transfer_id"]), int(w["layer"])
        end = int(w["end_ns"])
        s = sent.get((tid, layer))
        rows.append(
            LayerTimelineRow(
                run_id=run_id,
                env_hash=eh,
                req_id=str(w["req_id"]),
                transfer_id=tid,
                layer=layer,
                prefill_start_ns=int(w["start_ns"]),
                prefill_end_ns=end,
                enqueued_ns=enq.get((tid, layer)),
                sent_ns=s,
                commit_ns=commit.get(tid) if layer == last_layer[tid] else None,
                send_after_compute_ns=None if s is None else s - end,
            )
        )
    return rows


def build(run_dirs: Iterable[Path]) -> Dataset:
    ds = Dataset()
    envs: dict[str, EnvironmentRow] = {}
    raw_groups: dict[tuple[str, str, TransferKey], list[TransferRawRow]] = defaultdict(list)
    prefill_groups: dict[tuple[str, str, str, int, int, int, str], list[float]] = defaultdict(list)

    for run_dir in run_dirs:
        run_id = run_dir.name
        if run_id in ds.run_ids:
            raise ExportError(f"duplicate run id {run_id}")
        ds.run_ids.add(run_id)
        env = _load_env(run_dir)
        envs.setdefault(env.env_hash, env)
        eh = env.env_hash

        ceilings = [
            CeilingRow(
                run_id=run_id,
                env_hash=eh,
                nic=r["nic"],
                message_bytes=int(r["message_bytes"]),
                n_qps=int(r["n_qps"]),
                memory=cast(Any, r["memory"]),
                bw_gb_per_s=float(r["bw_gb_per_s"]),
                lat_us=_opt_float(r.get("lat_us")),
            )
            for r in _csv(run_dir / "ceiling" / "ceilings.csv")
        ]
        raws = [
            TransferRawRow(
                run_id=run_id,
                env_hash=eh,
                key=_transfer_key(r),
                rep=int(r["rep"]),
                total_bytes=int(r["total_bytes"]),
                duration_ns=int(r["duration_ns"]),
                cpu_ns=_opt_int(r.get("cpu_ns")),
            )
            for r in _csv(run_dir / "transfers_raw.csv")
        ]
        prefill = _csv(run_dir / "prefill.csv")
        timelines = _layer_timelines(run_id, eh, run_dir)

        if env.is_rxe:  # SoftRoCE is logic-only: keep the environment, drop every measurement
            ds.dropped_rxe_rows += len(ceilings) + len(raws) + len(prefill) + len(timelines)
            continue
        ds.ceilings.extend(ceilings)
        ds.transfers_raw.extend(raws)
        ds.layer_timelines.extend(timelines)
        for r in raws:
            raw_groups[(run_id, eh, r.key)].append(r)
        for p in prefill:
            k = (run_id, eh, p["model"], int(p["context_len"]), int(p["batch"]), int(p["tp"]))
            prefill_groups[(*k, p["gpu"])].append(float(p["duration_ms"]))

    ds.environments = sorted(envs.values(), key=lambda e: e.env_hash)
    ds.transfers = [_aggregate(k, rs, ds.ceilings) for k, rs in sorted(raw_groups.items(), key=str)]
    ds.prefill = [
        PrefillRow(
            run_id=run_id,
            env_hash=eh,
            model=model,
            context_len=ctx,
            batch=batch,
            tp=tp,
            gpu=gpu,
            n_reps=len(ms),
            duration_ms_p50=percentile(ms, 50),
            duration_ms_p99=percentile(ms, 99),
        )
        for (run_id, eh, model, ctx, batch, tp, gpu), ms in sorted(prefill_groups.items())
    ]
    return ds


def _aggregate(
    group: tuple[str, str, TransferKey], raws: list[TransferRawRow], ceilings: list[CeilingRow]
) -> TransferRow:
    run_id, eh, key = group
    sizes = {r.total_bytes for r in raws}
    if len(sizes) != 1:
        raise ExportError(f"{run_id}: repetitions of one config moved different byte counts")
    total = sizes.pop()
    durs = [float(r.duration_ns) for r in raws]
    p50 = int(percentile(durs, 50))
    thr = total / p50 if p50 > 0 else 0.0
    mem = memory_mode(key.gpudirect_mode)
    same_cfg = [
        c
        for c in ceilings
        if (c.env_hash, c.nic, c.n_qps, c.memory) == (eh, key.nic, key.n_qps, mem)
    ]
    region = [c.bw_gb_per_s for c in same_cfg if c.message_bytes == key.message_bytes]
    region_bw = key.rails * max(region) if region else None
    peak_bw = key.rails * max(c.bw_gb_per_s for c in same_cfg) if same_cfg else None
    cpu = [float(r.cpu_ns) for r in raws if r.cpu_ns is not None]
    return TransferRow(
        run_id=run_id,
        env_hash=eh,
        key=key,
        n_reps=len(raws),
        total_bytes=total,
        duration_ns_p50=p50,
        duration_ns_p99=int(percentile(durs, 99)),
        throughput_gb_per_s=thr,
        ceiling_region_gb_per_s=region_bw,
        ceiling_peak_gb_per_s=peak_bw,
        efficiency_vs_region_ceiling=thr / region_bw if region_bw else None,
        efficiency_vs_peak=thr / peak_bw if peak_bw else None,
        cpu_s_per_gb=percentile(cpu, 50) / total if cpu and len(cpu) == len(raws) else None,
        host_staging=key.gpudirect_mode == "host_staging",
    )
