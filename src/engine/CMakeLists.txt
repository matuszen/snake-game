add_library(snake_engine STATIC
    Game.cpp
)
target_include_directories(snake_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(snake_engine PUBLIC snake_core snake_network)
