// Small-message strategies compared in the M2 microbenchmark (TRANSPORT.md §4).
#pragma once

#include <cstdint>

namespace kvwire::transport {

enum class Strategy : std::uint8_t {
  kPerBlockWrite,   // (a) one WRITE per region — the naive baseline / ablation D2
  kSgeList,         // (b) many local SGEs -> one contiguous remote region (bounded by max_sge)
  kPackedWrite,     // (c) GPU pack kernel into staging buffer -> one large WRITE per layer
  kChainedWr,       // (d) WR chaining, doorbell coalescing, selective signaling
};

struct StrategyConfig {
  Strategy strategy = Strategy::kChainedWr;
  std::uint32_t signal_every = 16;       // selective signaling interval (d)
  std::uint32_t max_sge = 0;             // 0 = query device attr
  std::uint32_t max_outstanding_wr = 0;  // 0 = derive from SQ/CQ depth; document the choice
};

}  // namespace kvwire::transport
