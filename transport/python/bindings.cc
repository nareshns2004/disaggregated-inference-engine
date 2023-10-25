// pybind11 module `kvwire._transport`. Status codes are returned, never thrown (CLAUDE.md).
#include <pybind11/pybind11.h>

#include "kvwire/transport/status.h"

namespace py = pybind11;
using namespace kvwire::transport;

PYBIND11_MODULE(_transport, m) {
  m.doc() = "kvwire native transport";
  py::enum_<StatusCode>(m, "StatusCode")
      .value("OK", StatusCode::kOk)
      .value("UNIMPLEMENTED", StatusCode::kUnimplemented)
      .value("QP_ERROR", StatusCode::kQpError)
      .value("REMOTE_ACCESS_ERROR", StatusCode::kRemoteAccessError)
      .value("STALE_EPOCH", StatusCode::kStaleEpoch)
      .value("FENCED", StatusCode::kFenced);
  // TODO(M2): Transport bindings; release the GIL around blocking calls.
}
