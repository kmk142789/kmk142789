cmake_minimum_required(VERSION 3.16)
project(echo_continuum LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(echo_idmem src/identity.cpp src/memory.cpp)
target_include_directories(echo_idmem PUBLIC ${CMAKE_SOURCE_DIR}/include)

add_library(continuum src/continuum.cpp src/util.cpp src/resonance.cpp src/mosaic.cpp)
target_include_directories(continuum PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(continuum PUBLIC echo_idmem)

