add_library(snake_network STATIC
    CommandSocket.cpp
    SharedMemoryManager.cpp
)
target_include_directories(snake_network PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(snake_network PRIVATE snake_core)
