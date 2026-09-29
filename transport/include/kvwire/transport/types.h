// Plain data types shared by all backends. Mirrors kvwire/schemas/transfer.py (keep in sync;
// the schema version constant must match).
#pragma once

#include <cstddef>
#include <cstdint>
#include <span>

namespace kvwire::transport {

inline constexpr std::uint32_t kSchemaVersion = 1;

using TransferId = std::uint64_t;
using Epoch = std::uint32_t;

// One contiguous region of the KV pool (a block's K, V, or K+V for one layer — depends on the
// engine's attention-backend layout; see kvwire/kvcalc).
struct Region {
  std::uint64_t offset;  // byte offset into the registered pool
  std::uint32_t length;
};

// Unit of work: one layer's worth of regions for one transfer (TRANSPORT.md §4).
struct LayerBatch {
  TransferId transfer_id;
  Epoch epoch;
  std::uint32_t layer;
  std::span<const Region> src;
  std::span<const Region> dst;
  bool last_layer;  // carries the commit (WRITE_WITH_IMM or trailing flag write)
};

// What the receive side publishes when reserving blocks (ARCHITECTURE.md §3 step 2).
struct RemoteGrant {
  std::uint64_t base_addr;
  std::uint32_t rkey;        // pool rkey, or a per-transfer memory-window rkey (ADR-0005)
  TransferId transfer_id;
  Epoch epoch;
};

}  // namespace kvwire::transport
