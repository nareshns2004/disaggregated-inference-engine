// RAII owners for verbs objects: device context, PD, CQ, completion channel.
// [OWNER-CORE] implementation. Interfaces proposed; change them via TRANSPORT.md in the same PR.
#pragma once

#include <memory>
#include <string>

#include "kvwire/transport/status.h"

struct ibv_context;
struct ibv_pd;
struct ibv_cq;

namespace kvwire::transport {

class Device {
 public:
  // Opens the named HCA (e.g. "mlx5_0"). Selection by GPU affinity happens in kvwire/topology.
  static Status Open(const std::string& name, std::unique_ptr<Device>* out);
  ~Device();
  Device(const Device&) = delete;
  Device& operator=(const Device&) = delete;

  ibv_context* ctx() const { return ctx_; }
  ibv_pd* pd() const { return pd_; }

  // Starts a thread reading ibv_get_async_event: port down/up, QP fatal (TRANSPORT.md §6).
  Status StartAsyncEventThread();

 private:
  Device() = default;
  ibv_context* ctx_ = nullptr;
  ibv_pd* pd_ = nullptr;
};

class CompletionQueue {
 public:
  static Status Create(Device& dev, int depth, std::unique_ptr<CompletionQueue>* out);
  ~CompletionQueue();
  ibv_cq* cq() const { return cq_; }

 private:
  CompletionQueue() = default;
  ibv_cq* cq_ = nullptr;
};

}  // namespace kvwire::transport
