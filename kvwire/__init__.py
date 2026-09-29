"""kvwire: RDMA KV-cache transport and failure-aware coordination for disaggregated inference.

Importing this package must never import vLLM, torch, triton or the native extension; those
live behind optional extras and are imported lazily where needed.
"""

__version__ = "0.0.1"
