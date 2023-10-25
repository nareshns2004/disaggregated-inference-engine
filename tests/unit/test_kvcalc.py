from __future__ import annotations

import json
from pathlib import Path

import pytest

from kvwire.kvcalc import PRESETS, KvLayout, ModelSpec, bytes_per_token, transfer_profile

L8B = PRESETS["llama-3.1-8b"]
KiB, MiB = 1024, 1024 * 1024


def test_bytes_per_token_matches_brief() -> None:
    # PROJECT_BRIEF §2: 2 * 32 * 8 * 128 * 2 B = 128 KiB (calculation)
    assert bytes_per_token(L8B) == 128 * KiB


def test_4k_prompt_is_512_mib() -> None:
    assert transfer_profile(L8B, 4096).total_bytes == 512 * MiB


def test_block_region_sizes_depend_on_layout() -> None:
    inter = transfer_profile(L8B, 4096, 16, KvLayout.KV_INTERLEAVED)
    sep = transfer_profile(L8B, 4096, 16, KvLayout.KV_SEPARATE)
    assert inter.region_bytes == 64 * KiB
    assert inter.total_regions == 8192
    assert sep.region_bytes == 32 * KiB
    assert sep.total_regions == 16384
    assert inter.total_bytes == sep.total_bytes


def test_tp_splits_kv_heads_and_replicates_beyond_kv_heads() -> None:
    assert transfer_profile(L8B, 4096, tp=2).total_bytes == 256 * MiB
    assert (
        transfer_profile(L8B, 4096, tp=16).total_bytes
        == transfer_profile(L8B, 4096, tp=8).total_bytes
    )
    with pytest.raises(ValueError, match="not divisible"):
        transfer_profile(L8B, 4096, tp=3)


def test_partial_last_block_padding() -> None:
    p = transfer_profile(L8B, 17, 16)
    assert p.blocks == 2
    assert p.padding_bytes == 15 * bytes_per_token(L8B)


def test_from_hf_config(tmp_path: Path) -> None:
    cfg = {
        "num_attention_heads": 32,
        "num_key_value_heads": 8,
        "hidden_size": 4096,
        "num_hidden_layers": 32,
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg))
    spec = ModelSpec.from_hf_config(tmp_path / "config.json")
    assert bytes_per_token(spec) == bytes_per_token(L8B)
