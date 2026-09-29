# kernels/ — KV pack / re-layout (M4, gated)

Why this and not fused attention: FlashAttention/FlashInfer already win there. Re-layout is
something disaggregation itself needs (prefill TP ≠ decode TP, block-size mismatch, SGE limits).

Each kernel ships with: PyTorch reference (`ref.py`), exhaustive shape tests, Nsight Compute
(DRAM BW vs peak, occupancy), and an Nsight Systems timeline showing pack/WRITE/prefill overlap.
