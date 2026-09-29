# Kickoff — kvwire with Claude Code

## One-time setup
1. `mkdir kvwire && cd kvwire && git init`, then copy in `CLAUDE.md`, `docs/`, and
   `.claude/commands/`.
2. Fill the manual section of `docs/ENVIRONMENT.md`: allowlist, NICs, GPUDirect mode,
   and provenance/clearance.
3. Run `claude` in the repo root and switch to plan mode.

## First prompt (paste as-is)

> Read CLAUDE.md, then docs/PROJECT_BRIEF.md, docs/ARCHITECTURE.md, docs/TRANSPORT.md,
> docs/MILESTONES.md and docs/EVALUATION.md. Do not write code.
>
> 1. Summarize in ≤ 15 lines: the problem, the three headline numbers, what kvwire adds
>    beyond NIXL/Mooncake/vLLM connectors, and the stale-write hazard in your own words.
> 2. List ambiguities, contradictions, unrealistic targets, and anything in TRANSPORT.md
>    you believe is technically wrong for current hardware or software. Be blunt.
> 3. Using read-only commands, inspect this machine: GPUs, driver/CUDA, `nvidia-smi topo -m`,
>    RDMA devices and port states (`ibv_devinfo`), whether perftest is built with CUDA,
>    dmabuf/peermem availability, and the vLLM version if installed. Report the gaps for M1.
> 4. Run /plan-milestone M1 and stop.

## Session hygiene
- Start each session with: "Read CLAUDE.md and docs/MILESTONES.md; we're on <task>."
- Run `/ceiling-check` before any number goes into a doc. Run `/drill` after each component.
- Decisions become ADRs before moving on. Use `/clear` between unrelated tasks.
