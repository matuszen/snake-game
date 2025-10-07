cmake_minimum_required(VERSION 3.20)
project(SnakeGame VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(SOURCES
    src/main.cpp
    src/Game.cpp
    src/Snake.cpp
    src/Board.cpp
    src/Input.cpp
)

set(HEADERS
    include/Game.hpp
    include/Snake.hpp
    include/Board.hpp
    include/Input.hpp
    include/Types.hpp
)

add_executable(snake ${SOURCES} ${HEADERS})

target_include_directories(snake PRIVATE include)

find_package(PkgConfig REQUIRED)
pkg_check_modules(NOTCURSES REQUIRED notcurses)
target_link_libraries(snake PRIVATE ${NOTCURSES_LIBRARIES})
target_include_directories(snake PRIVATE ${NOTCURSES_INCLUDE_DIRS})
target_compile_options(snake PRIVATE ${NOTCURSES_CFLAGS_OTHER})
