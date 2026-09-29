"""faultlab-lite: scenario-driven fault injection with a ground-truth ledger.

Safety rule (CLAUDE.md §6): every injection registers its revert BEFORE acting and auto-reverts
on timeout. `tc netem`/iptables do not affect RDMA traffic (kernel bypass); use port state,
competing RDMA traffic, or transport test hooks.
"""
