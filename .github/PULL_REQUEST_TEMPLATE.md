## What and why

<!-- One logical change. Say *why*. Link the issue / ADR / open question. -->

## Checklist

- [ ] `make check` passes (ruff, mypy --strict, CPU tests); `make transport && make test-transport` if C++ changed.
- [ ] **No number without a run.** Any perf figure links to `bench/results/<run_id>/` and sits
      next to its ceiling or baseline; calculations and literature values are labelled.
- [ ] **Correctness gate.** No change to greedy outputs beyond the documented tolerance.
- [ ] **Fencing invariant.** No path returns KV blocks to an allocator before the transfer's
      epoch is fenced (ADR-0005).
- [ ] **Hot path.** No per-WR allocation, locking or logging in `transport/`.
- [ ] **Provenance.** New faults or fixtures are labelled `real` / `induced` / `synthetic`.
- [ ] **Docs move with code.** ARCHITECTURE / TRANSPORT / EVALUATION / ADR updated as needed.
- [ ] Commits are signed off (`git commit -s`, DCO).
