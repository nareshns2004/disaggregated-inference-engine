"""Model shapes relevant to KV size. Verify presets against the config.json you actually serve."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModelSpec:
    name: str
    num_layers: int
    num_kv_heads: int
    head_dim: int
    dtype_bytes: int = 2  # bf16/fp16; fp8 KV cache = 1

    @classmethod
    def from_hf_config(cls, path: str | Path, dtype_bytes: int = 2) -> ModelSpec:
        """Build from a Hugging Face ``config.json`` (no network, no transformers import)."""
        cfg = json.loads(Path(path).read_text())
        heads = int(cfg["num_attention_heads"])
        head_dim = int(cfg.get("head_dim") or cfg["hidden_size"] // heads)
        return cls(
            name=str(cfg.get("_name_or_path") or Path(path).parent.name),
            num_layers=int(cfg["num_hidden_layers"]),
            num_kv_heads=int(cfg.get("num_key_value_heads", heads)),
            head_dim=head_dim,
            dtype_bytes=dtype_bytes,
        )


PRESETS: dict[str, ModelSpec] = {
    "llama-3.1-8b": ModelSpec("llama-3.1-8b", num_layers=32, num_kv_heads=8, head_dim=128),
    "llama-3.1-70b": ModelSpec("llama-3.1-70b", num_layers=80, num_kv_heads=8, head_dim=128),
}
