# ADR-0001: Integrate with vLLM via the KV connector interface

- Status: Proposed

## Options

1. **vLLM KV connector.** Most widely deployed; an official disaggregation path;
   reference connectors exist for comparison.
2. **SGLang PD disaggregation.** Strong performance; a smaller surface; a different
   transfer-backend abstraction.
3. **A minimal custom engine.** Full control, but it is a non-goal, and interviewers
   would ask why it was rebuilt.

## Leaning

Option 1. Pin the version; keep all version-specific code in `kvwire/connector/`.
Revisit if the connector API cannot expose per-layer readiness without invasive patches.
