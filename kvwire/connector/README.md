# connector/

- Pin the vLLM version in ADR-0001 and record it in every env manifest.
- Everything that touches vLLM internals lives here; nothing else in `kvwire/` imports vLLM.
- Open questions for M3: does the pinned API expose a per-layer readiness point without patches?
  How is a request's block list obtained on the scheduler side? What frees blocks on abort?
