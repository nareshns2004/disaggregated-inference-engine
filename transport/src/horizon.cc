// Retransmit-horizon arithmetic (FAULT_MATRIX "Gotchas"). Kept verbs-free so it is unit-testable
// everywhere. Caveats to verify on real hardware (record in TRANSPORT.md):
//  - timeout exponent 0 means "infinite" in the IB spec: the horizon is unbounded.
//  - the HCA may clamp the effective timeout to at least its local_ca_ack_delay
//    (ibv_query_device), so the effective exponent can exceed the requested one.
//  - RNR retries (WRITE_WITH_IMM into an empty RQ/SRQ) are a separate budget:
//    rnr_retry * RNR timer, and rnr_retry=7 is infinite (RnrHorizon below; ADR-0007 fixes
//    rnr_retry <= 6 for the commit path).
//  - it bounds requester retransmission only, not packets already queued in the fabric.
#include <array>
#include <chrono>
#include <cstdint>
#include <limits>

#include "kvwire/transport/fence.h"

namespace kvwire::transport {
namespace {

using std::chrono::nanoseconds;

// IB-spec RNR NAK timer encoding (also documented in ibv_modify_qp(3)), in nanoseconds.
constexpr std::array<std::int64_t, 32> kRnrTimerNs = {
    655'360'000,  // 0  = 655.36 ms
    10'000,       // 1  = 0.01 ms
    20'000,      30'000,      40'000,      60'000,      80'000,      120'000,
    160'000,     240'000,     320'000,     480'000,     640'000,     960'000,
    1'280'000,   1'920'000,   2'560'000,   3'840'000,   5'120'000,   7'680'000,
    10'240'000,  15'360'000,  20'480'000,  30'720'000,  40'960'000,  61'440'000,
    81'920'000,  122'880'000, 163'840'000, 245'760'000, 327'680'000,
    491'520'000,  // 31 = 491.52 ms
};

nanoseconds SaturatingAdd(nanoseconds a, nanoseconds b) {
  if (a == nanoseconds::max() || b == nanoseconds::max()) return nanoseconds::max();
  if (a.count() > std::numeric_limits<std::int64_t>::max() - b.count()) return nanoseconds::max();
  return a + b;
}

}  // namespace

nanoseconds RetransmitHorizon(std::uint8_t timeout_exp, std::uint8_t retry_cnt) {
  if (timeout_exp == 0 || timeout_exp > 31) return nanoseconds::max();
  // 4.096 us = 4096 ns.
  const std::uint64_t per_attempt_ns = std::uint64_t{4096} << timeout_exp;
  const std::uint64_t attempts = std::uint64_t{retry_cnt} + 1;
  return nanoseconds(static_cast<std::int64_t>(per_attempt_ns * attempts));
}

nanoseconds RnrHorizon(std::uint8_t rnr_retry, std::uint8_t min_rnr_timer_code) {
  if (rnr_retry >= 7 || min_rnr_timer_code >= kRnrTimerNs.size()) return nanoseconds::max();
  return nanoseconds(kRnrTimerNs[min_rnr_timer_code] * rnr_retry);
}

nanoseconds FenceHorizon(std::uint8_t timeout_exp, std::uint8_t retry_cnt, std::uint8_t rnr_retry,
                         std::uint8_t min_rnr_timer_code) {
  return SaturatingAdd(RetransmitHorizon(timeout_exp, retry_cnt),
                       RnrHorizon(rnr_retry, min_rnr_timer_code));
}

}  // namespace kvwire::transport
