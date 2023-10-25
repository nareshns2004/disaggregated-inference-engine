"""PyTorch reference for pack/unpack. The kernels are tested exhaustively against this.

Imports torch lazily; requires the `gpu` extra.
"""

from __future__ import annotations

from typing import Any


def pack_ref(kv_layer: Any, block_ids: Any, head_slice: slice | None = None) -> Any:
    """Gather `block_ids` of one layer (optionally a head subset for TP re-partition) into a
    contiguous buffer. Define the exact input layout from the pinned vLLM backend first."""
    raise NotImplementedError("M4")


def unpack_ref(buf: Any, kv_layer: Any, block_ids: Any, head_slice: slice | None = None) -> None:
    raise NotImplementedError("M4")
