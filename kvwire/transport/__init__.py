"""Python-side transport interface. Backends: TCP (pure Python, control variant) and the native
C++ verbs backend loaded from `kvwire._transport` when built."""

from kvwire.transport.base import RemoteGrant, Transport, TransportStatus

__all__ = ["RemoteGrant", "Transport", "TransportStatus"]
