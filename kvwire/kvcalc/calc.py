"""KV arithmetic for paged, per-layer transfer.

Layout matters for the transport: it decides how many contiguous regions (hence work requests or
SGEs) a transfer needs. vLLM attention backends differ, e.g. a per-layer tensor shaped
``[2, num_blocks, block, heads, dim]`` (K and V separate) vs ``[num_blocks, 2, block, heads, dim]``
(K and V adjacent per block). Confirm the layout of the pinned vLLM version and backend.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass

from kvwire.kvcalc.models import ModelSpec


class KvLayout(str, enum.Enum):
    KV_SEPARATE = "separate"  # K region and V region per (layer, block)
    KV_INTERLEAVED = "interleaved"  # one K+V region per (layer, block)


def bytes_per_token(spec: ModelSpec) -> int:
    """Total KV bytes per token across all layers and all TP ranks."""
    return 2 * spec.num_layers * spec.num_kv_heads * spec.head_dim * spec.dtype_bytes


def kv_heads_per_rank(spec: ModelSpec, tp: int) -> int:
    """KV heads held by one TP rank. When tp > num_kv_heads, heads are replicated."""
    if tp < 1:
        raise ValueError("tp must be >= 1")
    if tp <= spec.num_kv_heads and spec.num_kv_heads % tp != 0:
        raise ValueError(f"num_kv_heads={spec.num_kv_heads} not divisible by tp={tp}")
    return max(1, spec.num_kv_heads // tp)


@dataclass(frozen=True, slots=True)
class TransferProfile:
    """What one TP rank must move for one prompt. All values are calculations."""

    model: str
    prompt_tokens: int
    block_size: int
    layout: KvLayout
    tp: int
    blocks: int
    regions_per_layer: int
    region_bytes: int
    bytes_per_layer: int
    total_regions: int
    total_bytes: int
    padding_bytes: int  # bytes moved for the unfilled tail of the last block, if whole blocks move


def transfer_profile(
    spec: ModelSpec,
    prompt_tokens: int,
    block_size: int = 16,
    layout: KvLayout = KvLayout.KV_INTERLEAVED,
    tp: int = 1,
) -> TransferProfile:
    if prompt_tokens < 1 or block_size < 1:
        raise ValueError("prompt_tokens and block_size must be >= 1")
    heads = kv_heads_per_rank(spec, tp)
    per_token_per_layer_kv = 2 * heads * spec.head_dim * spec.dtype_bytes
    blocks = math.ceil(prompt_tokens / block_size)
    block_layer_bytes = block_size * per_token_per_layer_kv
    parts = 2 if layout is KvLayout.KV_SEPARATE else 1
    regions_per_layer = blocks * parts
    bytes_per_layer = blocks * block_layer_bytes
    return TransferProfile(
        model=spec.name,
        prompt_tokens=prompt_tokens,
        block_size=block_size,
        layout=layout,
        tp=tp,
        blocks=blocks,
        regions_per_layer=regions_per_layer,
        region_bytes=block_layer_bytes // parts,
        bytes_per_layer=bytes_per_layer,
        total_regions=regions_per_layer * spec.num_layers,
        total_bytes=bytes_per_layer * spec.num_layers,
        padding_bytes=(blocks * block_size - prompt_tokens)
        * per_token_per_layer_kv
        * spec.num_layers,
    )
