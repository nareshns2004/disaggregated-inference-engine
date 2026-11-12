# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/) once it reaches 0.1.0.

## [Unreleased]

### Added
- Repository scaffold: `kvwire` control plane (KV calculator, schemas, transfer state table,
  registry), C++20 verbs transport interfaces with retransmit-horizon arithmetic, faultlab,
  bench harness, design docs and ADRs 0001–0005.
- GitHub Actions CI: Python 3.10–3.12 (ruff, mypy --strict, tests, number-provenance guard,
  CLI smoke, build) and the C++ transport with ASan/UBSan, with and without rdma-core.
- Pre-commit config, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, PR and issue templates,
  Dependabot.
- ADR-0006 (provenance labels); `docs/OPEN_QUESTIONS.md` (replaces REVIEW_NOTES);
  `docs/prior_art.md` draft with sourced entries for Mooncake and NIXL.
- Unit test keeping Python `TransportStatus` in lockstep with C++ `StatusCode`.

### Changed
- Licence stated as Apache-2.0 throughout (the LICENSE file already was).
- TRANSPORT §5 and the C++ `FenceMechanism` aligned with ADR-0005: the fence is on the
  responder; sender-side QP reset plus lease is supplementary only.
- Metric #1 reports both denominators (ceiling at the region size and large-message peak).
- FAULT_MATRIX: faultlab-scheduled faults relabelled `I`; horizon formula corrected to
  (retry_cnt + 1) attempts; K07 required with ≥ 2 rails.
- faultlab ledger flushes and fsyncs every record.
- Personal, interview and employer framing removed from tracked files.
