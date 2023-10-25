cmake_minimum_required(VERSION 3.22)
project(kvwire LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(KVWIRE_WITH_VERBS   "Build the RDMA (libibverbs) backend if available" ON)
option(KVWIRE_WITH_CUDA    "Enable GPUDirect registration paths (dmabuf/peermem)" OFF)
option(KVWIRE_WITH_PYTHON  "Build pybind11 module kvwire._transport" OFF)
set(KVWIRE_SANITIZER "none" CACHE STRING "none|address|undefined|thread")

add_compile_options(-Wall -Wextra -Werror -Wpedantic)
if(NOT KVWIRE_SANITIZER STREQUAL "none")
  add_compile_options(-fsanitize=${KVWIRE_SANITIZER} -fno-omit-frame-pointer)
  add_link_options(-fsanitize=${KVWIRE_SANITIZER})
endif()

enable_testing()
add_subdirectory(transport)
