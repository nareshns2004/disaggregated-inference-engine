# ADR-0006: Meaning of the real / induced / synthetic fault labels

- Status: Accepted
- Date: 2026-11-12
- Deciders: maintainers

## Context
`docs/FAULT_MATRIX.md` labelled K01–K05 and K09–K11 as **R** (real), yet every one is
triggered on purpose by faultlab (SIGKILL, port disable, competing traffic). The schema
(`FaultLabel.INDUCED = "real mechanism, triggered on purpose"`) and the matrix's own legend
define exactly that as **induced**. Scenario files inherited the mislabel
(`must_mixed_2h.yaml` marked K01 `real`). The sibling project goodput resolved the same
contradiction in its ADR-0006, and ADR-0004 says the ledger design is shared.

## Options considered
1. **Keep R for "real mechanism".** Matches the old matrix, but "real" then means both
   "scheduled by us" and "happened on its own", which makes it impossible to separate
   harvested failures from experiments in results.
2. **R only for faults that happen on their own; anything faultlab schedules is I or S.**
   One meaning per label; matches the schema and goodput.

## Decision
Option 2.

- `real`: a fault that occurred without being scheduled (harvested during a run, recorded
  with its evidence).
- `induced`: a real mechanism deliberately triggered by faultlab or a transport test hook.
- `synthetic`: fabricated values or events (no real mechanism).

Every injectable row in `docs/FAULT_MATRIX.md` is therefore **I** (K12 is a test property,
not an injection). Scenario files use `induced`.

## Consequences
- Fault-run reports can state precisely which results come from experiments and which from
  failures that happened on their own, and never present induced results as field rates.
- No code change: `FaultLabel` already encoded this meaning.
- Keeps the two sibling projects' ledgers comparable (ADR-0004).
