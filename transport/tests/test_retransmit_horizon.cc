#include "check.h"
#include <chrono>
#include <cstdio>

#include "kvwire/transport/fence.h"

using namespace kvwire::transport;
using std::chrono::nanoseconds;

int main() {
  // --- transport retries ---
  // timeout=0 is infinite per the IB spec: a lease-only fence is impossible.
  CHECK(RetransmitHorizon(0, 7) == nanoseconds::max());
  // timeout=14, retry_cnt=7: 4096ns * 2^14 * 8 attempts (calculation; ~0.54 s).
  CHECK(RetransmitHorizon(14, 7) == nanoseconds(4096LL * (1LL << 14) * 8));
  // Monotone in both arguments.
  CHECK(RetransmitHorizon(15, 7) > RetransmitHorizon(14, 7));
  CHECK(RetransmitHorizon(14, 7) > RetransmitHorizon(14, 3));

  // --- RNR retries (commit WRITE_WITH_IMM into an empty SRQ) ---
  // rnr_retry=7 is infinite in the IB spec.
  CHECK(RnrHorizon(7, 12) == nanoseconds::max());
  // Invalid encodings fail safe (unbounded) rather than silently shrinking the lease.
  CHECK(RnrHorizon(8, 12) == nanoseconds::max());
  CHECK(RnrHorizon(6, 32) == nanoseconds::max());
  // rnr_retry=0: no RNR retries, so no RNR budget.
  CHECK(RnrHorizon(0, 12) == nanoseconds(0));
  // Encoding spot checks: code 1 = 0.01 ms, code 12 = 0.64 ms, code 31 = 491.52 ms,
  // and code 0 is the *largest* timer (655.36 ms), not the smallest.
  CHECK(RnrHorizon(1, 1) == nanoseconds(10'000));
  CHECK(RnrHorizon(6, 12) == nanoseconds(6LL * 640'000));
  CHECK(RnrHorizon(1, 31) == nanoseconds(491'520'000));
  CHECK(RnrHorizon(1, 0) > RnrHorizon(1, 31));

  // --- combined bound ---
  CHECK(FenceHorizon(14, 7, 6, 12) == RetransmitHorizon(14, 7) + RnrHorizon(6, 12));
  CHECK(FenceHorizon(0, 7, 6, 12) == nanoseconds::max());
  CHECK(FenceHorizon(14, 7, 7, 12) == nanoseconds::max());
  CHECK(FenceHorizon(14, 7, 0, 12) == RetransmitHorizon(14, 7));
  // The largest finite settings stay finite (2^51 ns); max() is reserved for "unbounded".
  CHECK(FenceHorizon(31, 255, 6, 0) > RetransmitHorizon(31, 255));
  std::puts("test_retransmit_horizon: ok");
  return 0;
}
