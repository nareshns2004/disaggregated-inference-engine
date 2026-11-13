"""`kvwire` command-line entry point. Subcommands are added as milestones land."""

from __future__ import annotations

import argparse
import sys

from kvwire.kvcalc import PRESETS, KvLayout, ModelSpec, bytes_per_token, transfer_profile


def _human(n: int) -> str:
    x = float(n)
    for unit in ("B", "KiB", "MiB"):
        if x < 1024:
            return f"{int(x)} B" if unit == "B" else f"{x:.2f} {unit}"
        x /= 1024
    return f"{x:.2f} GiB"


def _cmd_kv_size(args: argparse.Namespace) -> int:
    spec = ModelSpec.from_hf_config(args.hf_config) if args.hf_config else PRESETS[args.preset]
    p = transfer_profile(spec, args.prompt, args.block_size, KvLayout(args.layout), args.tp)
    print(f"# calculation (not a measurement) — {spec}")
    print(f"KV per token (all ranks)     : {_human(bytes_per_token(spec))}")
    print(f"prompt tokens / blocks       : {p.prompt_tokens} / {p.blocks} (block={p.block_size})")
    print(f"per-rank (tp={p.tp}) total        : {_human(p.total_bytes)}")
    layer = f"{_human(p.bytes_per_layer)} in {p.regions_per_layer} regions"
    print(f"per layer                    : {layer}")
    print(f"region size ({p.layout.value:<11})    : {_human(p.region_bytes)}")
    print(f"total regions (WRs if naive) : {p.total_regions}")
    print(f"tail padding if whole blocks : {_human(p.padding_bytes)}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    from pathlib import Path

    from kvwire.export import build, has_errors, validate
    from kvwire.export.write import push, write_dataset

    ds = build(Path(r) for r in args.runs)
    issues = validate(ds)
    for issue in issues:
        print(issue, file=sys.stderr)
    if ds.dropped_rxe_rows:
        print(f"dropped {ds.dropped_rxe_rows} SoftRoCE (rxe) rows", file=sys.stderr)
    if has_errors(issues):
        print("validation failed; nothing written", file=sys.stderr)
        return 1
    if args.validate_only:
        print("validation passed")
        return 0
    for path in write_dataset(ds, Path(args.out), args.format):
        print(f"wrote {path}")
    if args.push:
        push(Path(args.out), args.repo_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kvwire")
    sub = parser.add_subparsers(dest="cmd", required=True)

    kv = sub.add_parser("kv-size", help="KV size / message-size calculator")
    src = kv.add_mutually_exclusive_group(required=True)
    src.add_argument("--preset", choices=sorted(PRESETS))
    src.add_argument("--hf-config", help="path to a Hugging Face config.json")
    kv.add_argument("--prompt", type=int, required=True)
    kv.add_argument("--block-size", type=int, default=16)
    kv.add_argument("--layout", choices=[x.value for x in KvLayout], default="interleaved")
    kv.add_argument("--tp", type=int, default=1)
    kv.set_defaults(func=_cmd_kv_size)

    ex = sub.add_parser("export", help="build the rdma-kv-transfer-traces dataset from runs")
    ex.add_argument("--runs", nargs="+", required=True, help="bench/results/<run_id> dirs")
    ex.add_argument("--out", default="out/rdma-kv-transfer-traces")
    ex.add_argument("--format", choices=["parquet", "jsonl"], default="parquet")
    ex.add_argument("--validate-only", action="store_true", help="run the checks; write nothing")
    ex.add_argument("--push", action="store_true", help="upload after an interactive confirm")
    ex.add_argument("--repo-id", default="nareshns2004/rdma-kv-transfer-traces")
    ex.set_defaults(func=_cmd_export)

    # TODO(M1): `kvwire topo`, `kvwire manifest`; TODO(M3): `kvwire router`, `kvwire worker`.
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
