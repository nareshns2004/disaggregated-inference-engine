# Security and safety policy

## Reporting a vulnerability

Please **do not** open a public issue. Report privately through GitHub's
[private vulnerability reporting](https://github.com/nareshns2004/disaggregated-inference-engine/security/advisories/new)
on this repository. We aim to acknowledge reports within 7 days.

Supported versions: the project is pre-release; only the `main` branch receives fixes.

## What counts as a security issue here

kvwire moves KV-cache bytes between machines with one-sided RDMA, where the NIC writes
memory the remote CPU believes it owns. In scope:

- **Cross-request data exposure or corruption**: any way for a write from one transfer
  (including an aborted or timed-out one) to land in KV blocks owned by another request.
  Preventing this is a design invariant (ADR-0005, `docs/TRANSPORT.md` §5, fault K07).
- **Memory-registration scope**: remote keys or memory windows that grant access beyond
  the blocks reserved for a transfer.
- **Fault-injection safety**: any way around the host allowlist, the revert-before-act
  rule, or the timeout auto-revert in `faultlab/`.

## Fault-injection safety model

`faultlab` deliberately breaks things: it kills processes, takes RDMA ports down and forces
QPs into error. It must:

- act only on hosts listed in the allowlist (`docs/ENVIRONMENT.md`);
- register a revert before changing any host state, and auto-revert on timeout;
- write every injection to an append-only, fsynced ledger.

The following are **never** automated and always need a human to confirm at the time:
driver, firmware or OFED changes; `nvidia-peermem`, IOMMU, ACS or BIOS changes; NIC or
switch configuration (PFC, ECN, MTU, GID); reboots; GPU resets.

Disabling ACS or the IOMMU for GPUDirect RDMA is a security trade-off (it removes PCIe
peer-to-peer isolation). The environment manifest records it; never do it on shared hosts.

## Data

Published results and fixtures come only from hardware cleared for public use. Scrub
hostnames, IP addresses, GIDs, serial numbers and usernames from captured data.
