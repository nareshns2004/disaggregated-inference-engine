---
description: Write a plan for a milestone (or one deliverable of it) and stop for approval
argument-hint: <milestone, e.g. M1 or "M2 fencing experiment">
---

Plan **$ARGUMENTS** for kvwire. Do not edit any file except the plan itself.

1. Read `docs/MILESTONES.md` (the section for $ARGUMENTS), then only what it depends on:
   `docs/TRANSPORT.md` for anything under `transport/`, `docs/ARCHITECTURE.md` for
   boundaries, `docs/EVALUATION.md` for anything measured, `docs/FAULT_MATRIX.md` for
   faults, `docs/OPEN_QUESTIONS.md` and `docs/adr/`. Do not re-open an Accepted ADR.
2. Write the plan to `docs/design/<milestone>-<topic>.md` (or `.local/plans/` if it is a
   scratch plan) with:
   - **Scope:** deliverables and exit criteria you will close, quoted from MILESTONES.
   - **Files:** every file to add or change, one line each on why.
   - **Interfaces:** C++ headers, pybind surface, Python mirrors (status-code parity).
   - **`[OWNER-CORE]` split:** what the maintainer implements versus what you write.
   - **Tests:** CPU, `rxe` (labelled non-performance), `gpu`, `multinode`.
   - **Measurement:** each number, its `bench/results/<run_id>/`, its perftest ceiling at
     the same NIC, message size, QP count and memory mode, and the repetitions it needs.
   - **Hardware actions:** every command on real hosts, with its revert.
   - **Open questions:** blockers, each with a proposed answer.
3. Print the plan and **stop**. Wait for the maintainer's approval before writing code.
