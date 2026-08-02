cmake_minimum_required(VERSION 3.10)

project(RecSysServer VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3 -march=native)
endif()

find_package(Threads REQUIRED)

add_executable(server 
    src/basefile.cpp 
    src/matrix.cpp 
    src/knn_engine.cpp 
    src/main.cpp
)
target_include_directories(server PRIVATE src)
target_link_libraries(server PRIVATE Threads::Threads)