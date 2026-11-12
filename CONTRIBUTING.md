# Contributing to kvwire

Thanks for your interest. kvwire is judged on how trustworthy its numbers and its
correctness claims are, so the rules below are stricter than most.

## Ground rules

1. **No number without a run.** No latency, bandwidth, TTFT, TPOT, goodput or success-rate
   figure in code comments, docs or commit messages unless it comes from
   `bench/results/<run_id>/` with its environment manifest. Calculations (e.g. KV-size
   arithmetic) and literature values are labelled as such, with a source.
   `scripts/check_numbers.py` enforces this heuristically in CI and pre-commit.
2. **Perf claims need a ceiling.** Every transport number sits next to the perftest
   ceiling (`ib_write_bw` / `ib_write_lat`, same NIC, message size, QP count and GPU vs host
   memory mode). Every kernel number sits next to the DRAM-bandwidth roofline.
3. **Correctness is a gate.** A change that alters generated tokens under greedy decoding
   versus the reference, beyond the documented numerics tolerance, does not merge,
   whatever the speedup.
4. **Label provenance.** Every fault is `real`, `induced` or `synthetic`
   ([ADR-0006](docs/adr/0006-provenance-labels.md)).
5. **Safety.** Fault injection and hardware commands act only on allowlisted hosts and
   register a revert before acting. See [SECURITY.md](SECURITY.md).
6. **Clean-room.** Contribute only code and data you have the right to publish. No
   proprietary code, internal hostnames, IPs, logs or data from any employer or third party.

## Development setup

The repo is tiered so most correctness-critical logic runs without RDMA hardware:

| Tier | Needs | Command |
|---|---|---|
| 0 · laptop | Python ≥ 3.10 | `make setup && make check` |
| 1 · + rdma-core | CMake ≥ 3.22, C++20 compiler, `libibverbs-dev`, optional SoftRoCE | `make transport && make test-transport` |
| 2/3 · GPU + RDMA NIC(s) | CUDA, GPUDirect, perftest, allowlisted hosts | `make test-gpu`, `make test-multinode`, `make ceiling` |

SoftRoCE (`rxe`) results are logic tests only and are always labelled *non-performance*.

## Code conventions

- **C++20** in `transport/`: RAII for every verbs object; no exceptions across the C ABI or
  the pybind11 boundary (return `Status`); `-Wall -Wextra -Werror -Wpedantic`; CI builds
  with ASan and UBSan. The hot path does not allocate, lock or log per work request.
- **Python ≥ 3.10**, fully typed, `ruff` (line length 100) and `mypy --strict`.
- Importing `kvwire` never imports vLLM, torch, Triton or the native extension; all
  vLLM-version-specific code lives in `kvwire/connector/` (ADR-0001).
- `kvwire/transport/base.py` mirrors `transport/include/kvwire/transport/*.h`; a unit test
  keeps the status codes in lockstep.
- Cross-process messages are versioned schemas (`kvwire/schemas/`, `kSchemaVersion` in
  `types.h`). Durations use monotonic clocks; cross-host correlation uses UTC epoch-ns.

## Tests

- Coordinator and scheduler logic: CPU-only tests with the simulated engine.
- Transport logic: loopback or SoftRoCE tests marked `rxe`; timing only on real hardware.
- Kernels: exhaustive shape tests against the PyTorch reference.
- Hardware tests are marked `gpu`, `multinode` or `rxe` and skipped unless enabled
  (`--run-gpu`, `--run-multinode`, `--run-rxe`).

## Documentation moves with code

- Interface change → `docs/ARCHITECTURE.md` / `docs/TRANSPORT.md` in the same PR.
- New decision → an ADR in `docs/adr/` (start from `0000-template.md`).
- Metric change → `docs/EVALUATION.md` only.
- Design docs for non-trivial components go in `docs/design/` before implementation.

## Commits and pull requests

- [Conventional Commits](https://www.conventionalcommits.org/); one logical change per
  commit; the message says *why*.
- **Sign off every commit** (`git commit -s`) to certify the
  [Developer Certificate of Origin](https://developercertificate.org/).
- Fill in the PR template checklist.
