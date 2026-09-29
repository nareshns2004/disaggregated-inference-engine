# Prior art: M1 gate ([OWNER-CORE] gap analysis)

For each system: mechanism · transport · fault/fencing story (published?) · measured numbers
(cited) · gap · what kvwire reuses. Verify everything against primary sources and cite them.

| System | Mechanism | KV transport | Fault / fencing behaviour | Gap vs kvwire | Reuse |
|---|---|---|---|---|---|
| DistServe (OSDI '24) | | | | | goodput-under-SLO metric |
| Splitwise (ISCA '24) | | | | | |
| Mooncake (FAST '25) | | | | | |
| TetriInfer | | | | | |
| Sarathi-Serve | | | | | C0 baseline (chunked prefill) |
| NVIDIA Dynamo / NIXL | | | | | D0 baseline |
| vLLM KV connectors | | | | | integration point (ADR-0001) |
| SGLang PD | | | | | |
| LMCache | | | | | |
| llm-d | | | | | |

## Go / re-scope decision
- [ ] Does any of the above publish stale-write fencing + fault-injection results? → if yes, re-scope.
