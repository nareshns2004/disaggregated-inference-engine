# kvwire transport. The core library always builds (TCP backend + interfaces), so the tree
# compiles on a laptop with no RDMA stack. The verbs backend is added when libibverbs exists.

add_library(kvwire_transport
  src/status.cc
  src/horizon.cc
  src/tcp_transport.cc
)
target_include_directories(kvwire_transport PUBLIC include)

if(KVWIRE_WITH_VERBS)
  find_library(IBVERBS_LIB ibverbs)
  find_path(IBVERBS_INC infiniband/verbs.h)
  if(IBVERBS_LIB AND IBVERBS_INC)
    message(STATUS "kvwire: verbs backend ON (${IBVERBS_LIB})")
    target_sources(kvwire_transport PRIVATE
      src/device.cc src/mr.cc src/qp.cc src/fence.cc src/rdma_transport.cc)
    target_include_directories(kvwire_transport PRIVATE ${IBVERBS_INC})
    target_link_libraries(kvwire_transport PUBLIC ${IBVERBS_LIB})
    target_compile_definitions(kvwire_transport PUBLIC KVWIRE_HAVE_VERBS=1)
  else()
    message(STATUS "kvwire: libibverbs not found, verbs backend OFF (TCP only)")
  endif()
endif()

if(KVWIRE_WITH_CUDA)
  find_package(CUDAToolkit REQUIRED)
  target_link_libraries(kvwire_transport PUBLIC CUDA::cuda_driver)
  target_compile_definitions(kvwire_transport PUBLIC KVWIRE_HAVE_CUDA=1)
endif()

# ---- tests (plain executables; no framework download needed) ----
add_executable(test_status tests/test_status.cc)
target_link_libraries(test_status kvwire_transport)
add_test(NAME status COMMAND test_status)
set_tests_properties(status PROPERTIES LABELS unit)

add_executable(test_retransmit_horizon tests/test_retransmit_horizon.cc)
target_link_libraries(test_retransmit_horizon kvwire_transport)
add_test(NAME retransmit_horizon COMMAND test_retransmit_horizon)
set_tests_properties(retransmit_horizon PROPERTIES LABELS unit)

# ---- microbenchmarks (compared against perftest ceilings, never reported alone) ----
if(TARGET kvwire_transport AND IBVERBS_LIB)
  add_executable(kvwire_bench_strategies bench/bench_strategies.cc)
  target_link_libraries(kvwire_bench_strategies kvwire_transport)
endif()

if(KVWIRE_WITH_PYTHON)
  find_package(pybind11 CONFIG REQUIRED)
  pybind11_add_module(_transport python/bindings.cc)
  target_link_libraries(_transport PRIVATE kvwire_transport)
endif()
