#include "check.h"
#include <chrono>
#include <cstdio>

#include "kvwire/transport/fence.h"

using namespace kvwire::transport;
using std::chrono::nanoseconds;

int main() {
  // timeout=0 is infinite per the IB spec: a lease-only fence is impossible.
  CHECK(RetransmitHorizon(0, 7) == nanoseconds::max());
  // timeout=14, retry_cnt=7: 4096ns * 2^14 * 8 attempts (calculation; ~0.54 s).
  CHECK(RetransmitHorizon(14, 7) == nanoseconds(4096LL * (1LL << 14) * 8));
  // Monotone in both arguments.
  CHECK(RetransmitHorizon(15, 7) > RetransmitHorizon(14, 7));
  CHECK(RetransmitHorizon(14, 7) > RetransmitHorizon(14, 3));
  std::puts("test_retransmit_horizon: ok");
  return 0;
}
