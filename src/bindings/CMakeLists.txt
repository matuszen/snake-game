find_package(pybind11 REQUIRED)
pybind11_add_module(snake_lib Bindings.cpp)
target_link_libraries(snake_lib PRIVATE snake_engine snake_core)

install(TARGETS snake_lib
        LIBRARY DESTINATION ${CMAKE_SOURCE_DIR}/py
        COMPONENT python)
