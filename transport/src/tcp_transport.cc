// TCP control variant (TRANSPORT.md §7): same interface, same layer-wise streaming.
// Tuning to document when implemented: SO_SNDBUF/RCVBUF, N parallel connections, MSG_ZEROCOPY.
#include <memory>

#include "kvwire/transport/transport.h"

namespace kvwire::transport {

namespace {
constexpr Status kTodo{StatusCode::kUnimplemented, 0};

class TcpTransport final : public Transport {
 public:
  Status SendLayer(const LayerBatch&, const RemoteGrant&) override { return kTodo; }
  Status Abort(TransferId, Epoch) override { return kTodo; }
  Status Reserve(TransferId, Epoch, const Region*, std::size_t, RemoteGrant*) override {
    return kTodo;
  }
  Status Release(TransferId, Epoch) override { return kTodo; }
  void SetEventCallback(EventCallback cb) override { cb_ = std::move(cb); }
  TransportStats Stats() const override { return stats_; }

 private:
  EventCallback cb_;
  TransportStats stats_;
};
}  // namespace

std::unique_ptr<Transport> MakeTcpTransport() { return std::make_unique<TcpTransport>(); }

}  // namespace kvwire::transport
