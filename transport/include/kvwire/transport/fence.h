// Stale-write fencing (TRANSPORT.md §5, FAULT_MATRIX K07, ADR-0005). THE centrepiece.
// Invariant: no block is readable by decode unless every write of the current epoch completed,
// and no write from an older epoch can land in it afterwards.
// [OWNER-CORE] design and implementation.
#pragma once

#include <chrono>
#include <cstdint>

#include "kvwire/transport/status.h"
#include "kvwire/transport/types.h"

namespace kvwire::transport {

// Primary fences are responder-side: the side that owns the memory must be able to fence
// alone, because in K01/K03 the sender may be dead or partitioned (ADR-0005).
enum class FenceMechanism : std::uint8_t {
  kMemoryWindow,      // ADR-0005 option 1: per-transfer type-2 MW, invalidated before reuse
  kReceiverQpReset,   // ADR-0005 option 2: receiver moves its own QP to ERR/RESET on abort
  // Not primary mechanisms:
  //  - sender-side QP ERR + lease >= RetransmitHorizon (option 3) is belt-and-braces only;
  //  - epoch tags (option 4) are detection, always on, never sufficient alone.
};

// Upper bound on how long a sender's WRITE can still be retransmitted after the fact:
//   per-attempt timeout = 4.096 us * 2^timeout, times (retry_cnt + 1) attempts.
// Pure arithmetic, unit-tested. Note it bounds the *requester's* retries only; see
// docs/TRANSPORT.md §5 for why the responder-side fence is still the one to rely on.
std::chrono::nanoseconds RetransmitHorizon(std::uint8_t timeout_exp, std::uint8_t retry_cnt);

// RNR budget for the commit WRITE_WITH_IMM landing on an empty receive queue (ADR-0007):
//   rnr_retry * RNR NAK timer, where the timer is the responder's min_rnr_timer code
//   (IBV_QP_MIN_RNR_TIMER, 5-bit IB-spec encoding; code 0 = 655.36 ms, 1 = 0.01 ms, ...,
//   31 = 491.52 ms). rnr_retry == 7 means infinite and returns nanoseconds::max(); codes
//   above 31 or rnr_retry above 7 are invalid and also return max (fail safe).
std::chrono::nanoseconds RnrHorizon(std::uint8_t rnr_retry, std::uint8_t min_rnr_timer_code);

// Conservative bound used by the lease backstop: transport retries plus RNR retries,
// saturating at nanoseconds::max(). A WR can hit both, so the bound is their sum.
std::chrono::nanoseconds FenceHorizon(std::uint8_t timeout_exp, std::uint8_t retry_cnt,
                                      std::uint8_t rnr_retry, std::uint8_t min_rnr_timer_code);

class Fence {
 public:
  virtual ~Fence() = default;
  // Receive side: create the grant a sender may write through (MW bind or pool rkey + epoch).
  virtual Status Grant(TransferId id, Epoch epoch, const Region* regions, std::size_t n,
                       RemoteGrant* out) = 0;
  // Receive side: after this returns kOk, no write under (id, epoch) can land. Only then may
  // the blocks be returned to the allocator.
  virtual Status Revoke(TransferId id, Epoch epoch) = 0;
};

}  // namespace kvwire::transport
