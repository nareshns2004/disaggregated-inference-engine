"""Write a built dataset to disk (Parquet or JSONL) with its dataset card, and optionally push.

Parquet needs the ``export`` extra (``pyarrow``); ``--push`` needs the ``hub`` extra
(``huggingface_hub``). Both are imported lazily so the core stays dependency-free.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from importlib import resources
from pathlib import Path
from typing import Literal

from kvwire.export.build import Dataset
from kvwire.export.rows import COLUMN_UNITS, CONFIG_ROW_TYPES, flatten

Format = Literal["parquet", "jsonl"]
DEFAULT_REPO_ID = "nareshns2004/rdma-kv-transfer-traces"


def kvwire_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _write_config(rows: list[dict[str, object]], path: Path, fmt: Format) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jsonl":
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        return
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:  # pragma: no cover - depends on the environment
        raise SystemExit("Parquet output needs pyarrow: pip install 'kvwire[export]'") from e
    pq.write_table(pa.Table.from_pylist(rows), path)


def render_card(ds: Dataset, fmt: Format, commit: str) -> str:
    template = resources.files("kvwire.export").joinpath("DATASET_CARD.md").read_text("utf-8")
    present = [name for name, rows in ds.configs().items() if rows]
    configs_yaml = (
        "\n".join(f"  - config_name: {n}\n    data_files: {n}/*.{fmt}" for n in present) or "  []"
    )
    env_lines = [
        "| env_hash | GPU | NIC (fw) | link | GPUDirect | driver / CUDA |",
        "|---|---|---|---|---|---|",
    ]
    env_lines += [
        f"| `{e.env_hash}` | {e.gpu} | {e.nic_model} ({e.nic_fw}) | {e.link_gbps:g} Gb/s | "
        f"{e.gpudirect_mode} | {e.driver} / {e.cuda} |"
        for e in ds.environments
        if not e.is_rxe
    ]
    cols = ["| Column | Unit |", "|---|---|"] + [
        f"| `{c}` | {u} |" for c, u in COLUMN_UNITS.items()
    ]
    subs = {
        "configs_yaml": configs_yaml,
        "kvwire_commit": commit,
        "run_ids": ", ".join(f"`{r}`" for r in sorted(ds.run_ids)) or "(none)",
        "environments_table": "\n".join(env_lines),
        "column_table": "\n".join(cols),
        "n_envs": str(sum(not e.is_rxe for e in ds.environments)),
    }
    for k, v in subs.items():
        template = template.replace("{{" + k + "}}", v)
    return template


def write_dataset(ds: Dataset, out: Path, fmt: Format = "parquet") -> list[Path]:
    written: list[Path] = []
    for name, rows in ds.configs().items():
        assert name in CONFIG_ROW_TYPES
        if not rows:
            continue
        path = out / name / f"{name}.{fmt}"
        _write_config([flatten(r) for r in rows], path, fmt)
        written.append(path)
    card = out / "README.md"
    card.write_text(render_card(ds, fmt, kvwire_commit()), encoding="utf-8")
    written.append(card)
    return written


def push(out: Path, repo_id: str, confirm: Callable[[str], str] = input) -> bool:
    """Upload ``out`` to the HF dataset repo, only after the maintainer types the repo id."""
    answer = confirm(
        f"Upload {out} to https://huggingface.co/datasets/{repo_id}? Type the repo id to confirm: "
    )
    if answer.strip() != repo_id:
        print("not confirmed; nothing uploaded")
        return False
    try:
        from huggingface_hub import HfApi
    except ImportError as e:  # pragma: no cover
        raise SystemExit("--push needs huggingface_hub: pip install 'kvwire[hub]'") from e
    HfApi().upload_folder(
        folder_path=str(out),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message=f"Export from kvwire {kvwire_commit()}",
    )
    print(f"uploaded to https://huggingface.co/datasets/{repo_id}")
    return True
