---
description: Interview drill on the component just finished; grade answers against the artifacts
argument-hint: [component, e.g. "retransmit horizon"; default = the last thing changed]
---

Run a defence drill on **$ARGUMENTS** (if empty, use the component touched by the most
recent commits: `git log -5 --stat`).

1. Read the component's code, tests and the docs that justify it: TRANSPORT /
   ARCHITECTURE sections, its ADRs ("Options considered"), EVALUATION for any metric it
   feeds, and `docs/prior_art.md` (Mooncake, NIXL, DistServe, vLLM connectors).
2. Ask **5 questions, one at a time**, as a skeptical senior interviewer would:
   - mechanism (down to the verb, QP state, MR/MW, PCIe path or CUDA call),
   - a rejected alternative (why not the option the ADR rejected),
   - failure (what a late write, RNR, QP error or rail loss does to it),
   - measurement (which ceiling, which denominator, how many repetitions),
   - prior art (what Mooncake / NIXL / the vLLM reference connector already do).
3. Grade each answer **against the repo**: correct / partial / wrong, cite file:line or
   the doc section, and give the one-sentence answer the repo supports. If the repo cannot
   answer, that is a documentation gap: say where it should be written.
4. End with a score out of 5 and the gaps. Do not edit files unless asked.
