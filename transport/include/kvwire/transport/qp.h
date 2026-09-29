// RC queue pair with an explicit state machine and reset path (TRANSPORT.md §6).
// [OWNER-CORE] implementation: state transitions, error handling, WR batching/signaling.
#pragma once

#include <cstdint>
#include <memory>

#include "kvwire/transport/device.h"
#include "kvwire/transport/strategy.h"
#include "kvwire/transport/types.h"

struct ibv_qp;

namespace kvwire::transport {

enum class QpState : std::uint8_t { kReset, kInit, kRtr, kRts, kError };

struct QpParams {
  std::uint8_t port = 1;
  std::uint8_t gid_index = 0;      // RoCE: pick per ENVIRONMENT.md
  std::uint8_t timeout = 14;       // local ACK timeout exponent: 4.096us * 2^timeout
  std::uint8_t retry_cnt = 7;       // max 7 (finite)
  // NOT 7: rnr_retry=7 means *infinite* RNR retries, which makes the fence horizon unbounded
  // (WRITE_WITH_IMM consumes a posted recv; an empty RQ triggers RNR). See docs/REVIEW_NOTES.md.
  std::uint8_t rnr_retry = 6;
  std::uint32_t sq_depth = 1024;
  std::uint32_t mtu = 4096;
};

// Connection info exchanged over the control plane (never over RDMA).
struct QpEndpoint {
  std::uint32_t qpn;
  std::uint32_t psn;
  std::uint16_t lid;
  std::uint8_t gid[16];
};

class QueuePair {
 public:
  static Status Create(Device& dev, CompletionQueue& send_cq, CompletionQueue& recv_cq,
                       const QpParams& params, std::unique_ptr<QueuePair>* out);
  ~QueuePair();

  QpEndpoint local() const;
  Status Connect(const QpEndpoint& remote);  // RESET -> INIT -> RTR -> RTS

  // Hot path: no allocation, locking, or logging per WR.
  Status PostLayer(const LayerBatch& batch, const RemoteGrant& grant, std::uint32_t lkey,
                   const StrategyConfig& cfg);

  // Error recovery: drain flush completions, then RESET and reconnect (or re-create).
  Status Reset();
  QpState state() const { return state_; }

 private:
  QueuePair() = default;
  ibv_qp* qp_ = nullptr;
  QpState state_ = QpState::kReset;
  QpParams params_{};
};

}  // namespace kvwire::transport
