#include "check.h"
#include <cstdio>

#include "kvwire/transport/status.h"
#include "kvwire/transport/transport.h"

using namespace kvwire::transport;

int main() {
  CHECK(Status::Ok().ok());
  CHECK(ToString(StatusCode::kFenced) == "FENCED");
  auto tcp = MakeTcpTransport();
  CHECK(tcp != nullptr);
  CHECK(tcp->Abort(1, 1).code == StatusCode::kUnimplemented);  // flips when M2 lands
  std::puts("test_status: ok");
  return 0;
}
