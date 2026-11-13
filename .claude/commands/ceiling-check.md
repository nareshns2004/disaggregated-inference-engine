---
description: Refuse any transport number that lacks a same-config perftest ceiling
argument-hint: [file or diff to check; default = staged and unstaged changes]
---

Check **$ARGUMENTS** (default: `git diff HEAD`) for transport performance numbers
(GB/s, Gb/s, µs latency, % efficiency, message-rate) in docs, README, comments or
commit messages. CLAUDE.md rule 4: every transport number sits next to its ceiling.

For each number:
1. Find the `bench/results/<run_id>/` it cites. No run id → **reject**.
2. Open that run's `manifest.json` and `ceiling/`. Confirm a perftest point exists at the
   **same NIC, message size, QP count and memory mode** (GPU vs host). If the number is an
   efficiency, confirm which denominator it uses (same-size ceiling or large-message peak,
   EVALUATION §1) and that the text says so.
3. Reject `rxe` (SoftRoCE) runs for any performance claim; they are logic-only.
4. Flag any efficiency above 1.0 against the same-size ceiling as a measurement error.

Output a table: number · location · run id · matching ceiling (yes/no, which) · verdict.
Also run `make check-numbers`. Do not edit files; propose the fix for each rejection.
