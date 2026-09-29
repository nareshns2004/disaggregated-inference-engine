// Status codes returned across every transport boundary. No exceptions cross the C ABI or the
// pybind11 boundary (CLAUDE.md, code conventions).
#pragma once

#include <cstdint>
#include <string_view>

namespace kvwire::transport {

enum class StatusCode : std::uint8_t {
  kOk = 0,
  kUnimplemented,
  kInvalidArgument,
  kResourceExhausted,   // SQ/CQ full, MR limit, block pool exhausted
  kTimeout,
  kQpError,             // QP moved to ERR; caller must fence affected transfers
  kRemoteAccessError,   // e.g. late write rejected by an invalidated MW (the *desired* K07 outcome)
  kPortDown,
  kStaleEpoch,          // commit/event for an epoch that is no longer current (ignored, idempotent)
  kFenced,              // transfer was aborted and fenced
  kInternal,
};

struct [[nodiscard]] Status {
  StatusCode code = StatusCode::kOk;
  int sys_errno = 0;  // errno / ibv_wc_status when relevant

  static constexpr Status Ok() { return {}; }
  constexpr bool ok() const { return code == StatusCode::kOk; }
};

std::string_view ToString(StatusCode code);

}  // namespace kvwire::transport
