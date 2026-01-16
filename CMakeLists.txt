cmake_minimum_required(VERSION 3.20)
project(snake-game VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -flto=auto")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native")

if(POLICY CMP0148)
  cmake_policy(SET CMP0148 NEW)
endif()

find_package(pybind11 REQUIRED)

add_subdirectory(src/core)
add_subdirectory(src/network)
add_subdirectory(src/engine)
add_subdirectory(src/bindings)
add_subdirectory(src/app)
