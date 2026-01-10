add_library(snake_core STATIC
    Board.cpp
    Snake.cpp
)
target_include_directories(snake_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
