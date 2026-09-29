// Retransmit-horizon arithmetic (FAULT_MATRIX "Gotchas"). Kept verbs-free so it is unit-testable
// everywhere. Caveats to verify on real hardware (record in TRANSPORT.md):
//  - timeout exponent 0 means "infinite" in the IB spec: the horizon is unbounded.
//  - the HCA may clamp the effective timeout to at least its local_ca_ack_delay
//    (ibv_query_device), so the effective exponent can exceed the requested one.
//  - RNR retries (WRITE_WITH_IMM into an empty RQ) are a separate budget: rnr_retry * RNR timer,
//    and rnr_retry=7 is infinite. Add that term once the commit mechanism is fixed (ADR-0005).
//  - it bounds requester retransmission only, not packets already queued in the fabric.
#include <chrono>
#include <cstdint>
#include <limits>

#include "kvwire/transport/fence.h"

namespace kvwire::transport {

std::chrono::nanoseconds RetransmitHorizon(std::uint8_t timeout_exp, std::uint8_t retry_cnt) {
  using std::chrono::nanoseconds;
  if (timeout_exp == 0 || timeout_exp > 31) return nanoseconds::max();
  // 4.096 us = 4096 ns.
  const std::uint64_t per_attempt_ns = std::uint64_t{4096} << timeout_exp;
  const std::uint64_t attempts = std::uint64_t{retry_cnt} + 1;
  return nanoseconds(static_cast<std::int64_t>(per_attempt_ns * attempts));
}

}  // namespace kvwire::transport
