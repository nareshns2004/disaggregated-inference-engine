// M2 microbenchmark: strategies (a)-(d) × message size × QP count × rails.
// Output: CSV into bench/results/<run_id>/transport/. Every row is later joined with the
// perftest ceiling for the same (NIC, size, QPs, memory kind) — see /ceiling-check.
#include <cstdio>

int main() {
  std::puts("bench_strategies: TODO(M2)");
  return 0;
}
