cmake_minimum_required(VERSION 3.16)
project(echo_continuum LANGUAGES CXX)

add_library(continuum src/continuum.cpp src/util.cpp)
target_include_directories(continuum PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(continuum PUBLIC echo_idmem)

