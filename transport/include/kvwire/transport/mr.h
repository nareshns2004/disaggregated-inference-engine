// Whole-pool memory registration, once per GPU at startup (TRANSPORT.md §3).
// Registration path is ADR-0002: dmabuf (ibv_reg_dmabuf_mr) vs nvidia-peermem vs host staging.
// [OWNER-CORE] implementation.
#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>

#include "kvwire/transport/device.h"

struct ibv_mr;

namespace kvwire::transport {

enum class MemoryKind : std::uint8_t { kHost, kGpuDmabuf, kGpuPeermem };

class MemoryRegion {
 public:
  // `dmabuf_fd` is used only for kGpuDmabuf. Access flags must include MW_BIND if ADR-0005
  // selects memory windows.
  static Status Register(Device& dev, void* addr, std::size_t len, MemoryKind kind,
                         int dmabuf_fd, std::unique_ptr<MemoryRegion>* out);
  ~MemoryRegion();

  std::uint32_t lkey() const;
  std::uint32_t rkey() const;
  MemoryKind kind() const { return kind_; }

 private:
  MemoryRegion() = default;
  ibv_mr* mr_ = nullptr;
  MemoryKind kind_ = MemoryKind::kHost;
};

}  // namespace kvwire::transport
