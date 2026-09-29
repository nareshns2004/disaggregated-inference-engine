"""kvwire connector for vLLM.

Method names follow vLLM V1's KV connector base class as understood at scaffold time. VERIFY
against the pinned vLLM version (ADR-0001) before M3 — this API has churned across releases.
vLLM is imported lazily so the package stays importable without it.
"""

from __future__ import annotations

from typing import Any


class KvwireConnector:
    """Adapter: vLLM connector hooks -> kvwire.transport.Transport. Keep it thin."""

    def __init__(self, vllm_config: Any, role: Any) -> None:
        self._role = role  # scheduler-side vs worker-side instance
        # TODO(M3): build Transport from config; register KV pool once (TRANSPORT.md §3).

    # ---- worker side: send (prefill) ----
    def save_kv_layer(self, layer_name: str, kv_layer: Any, attn_metadata: Any, **kw: Any) -> None:
        """Per-layer hook: record a CUDA event; hand (layer, blocks) to the transport.

        [OWNER-CORE] (M3: layer-wise trigger and overlap logic).
        """
        raise NotImplementedError("M3")

    def wait_for_save(self) -> None:
        raise NotImplementedError("M3")

    # ---- worker side: receive (decode) ----
    def start_load_kv(self, forward_context: Any, **kw: Any) -> None:
        raise NotImplementedError("M3")

    def wait_for_layer_load(self, layer_name: str) -> None:
        raise NotImplementedError("M3")

    # ---- scheduler side ----
    def get_num_new_matched_tokens(self, request: Any, num_computed_tokens: int) -> Any:
        raise NotImplementedError("M3")

    def update_state_after_alloc(self, request: Any, blocks: Any, num_external_tokens: int) -> None:
        raise NotImplementedError("M3")

    def build_connector_meta(self, scheduler_output: Any) -> Any:
        raise NotImplementedError("M3")

    def request_finished(self, request: Any, block_ids: list[int]) -> Any:
        """Must not free blocks until the transfer is committed or fenced."""
        raise NotImplementedError("M3")
