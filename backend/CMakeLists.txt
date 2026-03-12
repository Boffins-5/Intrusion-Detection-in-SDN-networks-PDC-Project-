cmake_minimum_required(VERSION 3.16)
project(SDN_Detection)

set(CMAKE_CXX_STANDARD 17)

# ── OpenMP ──────────────────────────────
find_package(OpenMP REQUIRED)

# ── MPI ─────────────────────────────────
set(MPI_INCLUDE "C:/Program Files (x86)/Microsoft SDKs/MPI/Include")
set(MPI_LIB     "C:/Program Files (x86)/Microsoft SDKs/MPI/Lib/x64")

# ── OpenCL ──────────────────────────────
set(OCL_INCLUDE "C:/msys64/mingw64/include")

# ── Include directories ──────────────────
include_directories(
    include
    ${MPI_INCLUDE}
    ${OCL_INCLUDE}
)

# ── Common compile flags ─────────────────
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")

# ── Executables ──────────────────────────

# Node Simulator
add_executable(node_simulator
    src/node_simulator.cpp
)

# Traffic Generator
add_executable(traffic_generator
    src/traffic_generator.cpp
)

# Attack Simulator
add_executable(attack_simulator
    src/attack_simulator.cpp
)

# Sequential Detection
add_executable(detection_sequential
    src/detection_sequential.cpp
)

# OpenMP Detection
add_executable(detection_openmp
    src/detection_openmp.cpp
)
target_link_libraries(detection_openmp OpenMP::OpenMP_CXX)

# MPI Detection
add_executable(detection_mpi
    src/detection_mpi.cpp
)
target_link_libraries(detection_mpi
    ${MPI_LIB}/msmpi.lib
)

# OpenCL Detection
add_executable(detection_opencl
    src/detection_opencl.cpp
)
target_link_libraries(detection_opencl OpenCL)

# Performance Analyzer
add_executable(performance_analyzer
    src/performance_analyzer.cpp
)