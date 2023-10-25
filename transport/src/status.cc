#include "kvwire/transport/status.h"

namespace kvwire::transport {

std::string_view ToString(StatusCode code) {
  switch (code) {
    case StatusCode::kOk: return "OK";
    case StatusCode::kUnimplemented: return "UNIMPLEMENTED";
    case StatusCode::kInvalidArgument: return "INVALID_ARGUMENT";
    case StatusCode::kResourceExhausted: return "RESOURCE_EXHAUSTED";
    case StatusCode::kTimeout: return "TIMEOUT";
    case StatusCode::kQpError: return "QP_ERROR";
    case StatusCode::kRemoteAccessError: return "REMOTE_ACCESS_ERROR";
    case StatusCode::kPortDown: return "PORT_DOWN";
    case StatusCode::kStaleEpoch: return "STALE_EPOCH";
    case StatusCode::kFenced: return "FENCED";
    case StatusCode::kInternal: return "INTERNAL";
  }
  return "UNKNOWN";
}

}  // namespace kvwire::transport
