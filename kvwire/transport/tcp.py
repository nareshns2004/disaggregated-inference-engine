"""TCP control variant in Python for CPU-only integration tests. The *measured* TCP baseline
(D1) is the C++ TcpTransport, so both backends share the same code path above the socket."""

# TODO(M2): minimal asyncio implementation of the Transport protocol for sim/integration tests.
