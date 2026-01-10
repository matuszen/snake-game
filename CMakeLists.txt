cmake_minimum_required(VERSION 3.20)
project(SnakeGame VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(pybind11 REQUIRED)

set(SOURCES
    src/main.cpp
    src/Game.cpp
    src/Snake.cpp
    src/Board.cpp
    src/Input.cpp
    src/SharedMemoryManager.cpp
    src/CommandSocket.cpp
)

set(HEADERS
    include/Game.hpp
    include/Snake.hpp
    include/Board.hpp
    include/Input.hpp
    include/Types.hpp
    include/SharedMemoryManager.hpp
    include/CommandSocket.hpp
)

add_executable(snake ${SOURCES} ${HEADERS})

target_include_directories(snake PRIVATE include)

find_package(PkgConfig REQUIRED)
pkg_check_modules(NOTCURSES REQUIRED notcurses)
target_link_libraries(snake PRIVATE ${NOTCURSES_LIBRARIES} pthread rt)
target_include_directories(snake PRIVATE ${NOTCURSES_INCLUDE_DIRS})
target_compile_options(snake PRIVATE ${NOTCURSES_CFLAGS_OTHER})

# Python module
set(PYTHON_MODULE_SOURCES
    src/Training.cpp
    src/Snake.cpp
    src/Board.cpp
    src/Input.cpp
    src/SharedMemoryManager.cpp
    src/CommandSocket.cpp
    src/bindings.cpp
)

pybind11_add_module(snake_game ${PYTHON_MODULE_SOURCES})
target_include_directories(snake_game PRIVATE include)
target_link_libraries(snake_game PRIVATE ${NOTCURSES_LIBRARIES} pthread rt)
target_include_directories(snake_game PRIVATE ${NOTCURSES_INCLUDE_DIRS})
target_compile_options(snake_game PRIVATE ${NOTCURSES_CFLAGS_OTHER})
add_custom_command(TARGET snake_game POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    $<TARGET_FILE:snake_game>
    ${CMAKE_SOURCE_DIR}/py/training/
    COMMENT "Copying snake_game module to py/training/"
)
