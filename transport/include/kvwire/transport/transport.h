// Backend-neutral transport interface. RDMA and TCP implement the same contract so the TCP
// variant is a genuine control experiment (TRANSPORT.md §7), not a strawman.
#pragma once

#include <cstdint>
#include <functional>
#include <memory>

#include "kvwire/transport/status.h"
#include "kvwire/transport/strategy.h"
#include "kvwire/transport/types.h"

namespace kvwire::transport {

enum class EventKind : std::uint8_t { kLayerSent, kCommitted, kAborted, kError };

struct TransferEvent {
  TransferId transfer_id;
  Epoch epoch;
  EventKind kind;
  std::uint32_t layer;
  Status status;
  std::uint64_t ts_mono_ns;
};

using EventCallback = std::function<void(const TransferEvent&)>;

struct TransportStats {
  std::uint64_t bytes_posted = 0;
  std::uint64_t wrs_posted = 0;
  std::uint64_t doorbells = 0;
  std::uint64_t cq_polls = 0;
  std::uint64_t errors = 0;
};

class Transport {
 public:
  virtual ~Transport() = default;

  // Send side.
  virtual Status SendLayer(const LayerBatch& batch, const RemoteGrant& grant) = 0;
  virtual Status Abort(TransferId id, Epoch epoch) = 0;

  // Receive side.
  virtual Status Reserve(TransferId id, Epoch epoch, const Region* dst, std::size_t n,
                         RemoteGrant* out) = 0;
  virtual Status Release(TransferId id, Epoch epoch) = 0;  // fences, then frees

  // Completion/progress thread delivers events; callbacks must not block.
  virtual void SetEventCallback(EventCallback cb) = 0;
  virtual TransportStats Stats() const = 0;

  // Test hook for FAULT_MATRIX K06/K07. Compiled into test builds only.
  virtual Status TestForceQpError(std::uint32_t /*qp_index*/) {
    return {StatusCode::kUnimplemented, 0};
  }
};

std::unique_ptr<Transport> MakeTcpTransport(/* TODO(M2): endpoint config */);
#if defined(KVWIRE_HAVE_VERBS)
std::unique_ptr<Transport> MakeRdmaTransport(/* TODO(M2): device, pool, strategy config */);
#endif

}  // namespace kvwire::transport
