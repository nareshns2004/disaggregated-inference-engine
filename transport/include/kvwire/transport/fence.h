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

enum class FenceMechanism : std::uint8_t {
  kMemoryWindow,        // per-transfer type-2 MW, invalidated before block reuse
  kQpResetWithHorizon,  // QP -> ERR on abort; reuse only after flush or lease >= horizon
  // Epoch tags are *detection* only and are always on; never a mechanism by themselves.
};

// Upper bound on how long a sender's WRITE can still be retransmitted after the fact:
//   per-attempt timeout = 4.096 us * 2^timeout, times (retry_cnt + 1) attempts.
// Pure arithmetic, unit-tested. Note it bounds the *requester's* retries only; see
// docs/REVIEW_NOTES.md for why the responder-side fence is still the one to rely on.
std::chrono::nanoseconds RetransmitHorizon(std::uint8_t timeout_exp, std::uint8_t retry_cnt);

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
