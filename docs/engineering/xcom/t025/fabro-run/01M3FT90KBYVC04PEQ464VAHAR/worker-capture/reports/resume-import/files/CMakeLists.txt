cmake_minimum_required(VERSION 3.20)

project(xverse_xcom_t025_validation LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

find_package(Threads REQUIRED)

add_library(xverse_validation STATIC
  src/xverse/xcom/src/validation_session.cpp
)
target_include_directories(xverse_validation PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src/xverse/xcom/include
)
target_compile_features(xverse_validation PUBLIC cxx_std_20)
target_compile_options(xverse_validation PRIVATE
  -Wall
  -Wextra
  -Wpedantic
  -Werror
)
target_link_libraries(xverse_validation PUBLIC Threads::Threads)

enable_testing()
include(/opt/xcom-input/FabroGoogleTest.cmake)

# Label `unit`: every unit specification case ID appears as a discovered test name.
fabro_add_unit_test(validation_session_unit_tests
  SOURCES tests/validation_session_tests.cpp
  LIBRARIES xverse_validation
)
target_compile_options(validation_session_unit_tests PRIVATE
  -Wall
  -Wextra
  -Wpedantic
  -Werror
)

# Label `integration`: cross-component consumption and lifecycle flows.
add_executable(validation_session_integration_tests
  tests/validation_session_integration_tests.cpp
)
target_link_libraries(validation_session_integration_tests PRIVATE
  xverse_validation
  GTest::gtest_main
  GTest::gmock
)
target_compile_features(validation_session_integration_tests PRIVATE cxx_std_20)
target_compile_options(validation_session_integration_tests PRIVATE
  -Wall
  -Wextra
  -Wpedantic
  -Werror
)
gtest_discover_tests(validation_session_integration_tests PROPERTIES LABELS integration)

# Label `validation`: intended-use scenarios and zero-emission checks.
add_executable(validation_session_validation_tests
  tests/validation_session_validation_tests.cpp
)
target_link_libraries(validation_session_validation_tests PRIVATE
  xverse_validation
  GTest::gtest_main
  GTest::gmock
)
target_compile_features(validation_session_validation_tests PRIVATE cxx_std_20)
target_compile_options(validation_session_validation_tests PRIVATE
  -Wall
  -Wextra
  -Wpedantic
  -Werror
)
gtest_discover_tests(validation_session_validation_tests PROPERTIES LABELS validation)
