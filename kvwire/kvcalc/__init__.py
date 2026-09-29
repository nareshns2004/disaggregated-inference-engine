"""KV-cache size and message-size calculator.

Every figure this module produces is a *calculation* from model config, not a measurement.
Label it that way wherever it is quoted (CLAUDE.md rule 3).
"""

from kvwire.kvcalc.calc import KvLayout, TransferProfile, bytes_per_token, transfer_profile
from kvwire.kvcalc.models import PRESETS, ModelSpec

__all__ = [
    "PRESETS",
    "KvLayout",
    "ModelSpec",
    "TransferProfile",
    "bytes_per_token",
    "transfer_profile",
]
