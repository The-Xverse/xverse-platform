# X-COM core-types target: standard-library-only immutable values and diagnostics.

add_library(
  xverse_xcom_core_types
  STATIC
    src/contract.cpp
    src/diagnostic.cpp
    src/item.cpp
    src/value.cpp
)
add_library(xverse::xcom_core_types ALIAS xverse_xcom_core_types)

target_include_directories(
  xverse_xcom_core_types
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_compile_features(xverse_xcom_core_types PUBLIC cxx_std_20)
xverse_xcom_apply_warnings(xverse_xcom_core_types)
set_target_properties(
  xverse_xcom_core_types
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

add_library(
  xverse_xcom_endpoint_route_lifecycle
  STATIC
    src/endpoint_route_lifecycle.cpp
)
add_library(
  xverse::xcom_endpoint_route_lifecycle
  ALIAS xverse_xcom_endpoint_route_lifecycle
)
target_include_directories(
  xverse_xcom_endpoint_route_lifecycle
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(
  xverse_xcom_endpoint_route_lifecycle
  PUBLIC xverse::xcom_core_types
)
target_compile_features(xverse_xcom_endpoint_route_lifecycle PUBLIC cxx_std_20)
xverse_xcom_apply_warnings(xverse_xcom_endpoint_route_lifecycle)
set_target_properties(
  xverse_xcom_endpoint_route_lifecycle
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

if(BUILD_TESTING)
  find_package(Threads REQUIRED)

  add_executable(
    xverse_xcom_core_types_unit_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/core_types/unit_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_core_types_unit_tests
    PRIVATE xverse::xcom_core_types Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_core_types_unit_tests)

  add_executable(
    xverse_xcom_core_types_negative_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/core_types/negative_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_core_types_negative_tests
    PRIVATE xverse::xcom_core_types
  )
  xverse_xcom_apply_warnings(xverse_xcom_core_types_negative_tests)

  add_executable(
    xverse_xcom_core_types_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/core_types/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_core_types_consumer
    PRIVATE xverse::xcom_core_types
  )
  xverse_xcom_apply_warnings(xverse_xcom_core_types_consumer)

  add_test(NAME xcom_core_types_unit COMMAND xverse_xcom_core_types_unit_tests)
  add_test(NAME xcom_core_types_negative COMMAND xverse_xcom_core_types_negative_tests)
  add_test(NAME xcom_core_types_external_consumer COMMAND xverse_xcom_core_types_consumer)

  add_executable(
    xverse_xcom_lifecycle_unit_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/endpoint_route_lifecycle/unit_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_lifecycle_unit_tests
    PRIVATE xverse::xcom_endpoint_route_lifecycle Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_lifecycle_unit_tests)

  add_executable(
    xverse_xcom_lifecycle_negative_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/endpoint_route_lifecycle/negative_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_lifecycle_negative_tests
    PRIVATE xverse::xcom_endpoint_route_lifecycle
  )
  xverse_xcom_apply_warnings(xverse_xcom_lifecycle_negative_tests)

  add_executable(
    xverse_xcom_lifecycle_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/endpoint_route_lifecycle/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_lifecycle_consumer
    PRIVATE xverse::xcom_endpoint_route_lifecycle
  )
  xverse_xcom_apply_warnings(xverse_xcom_lifecycle_consumer)

  add_test(NAME xcom_lifecycle_unit COMMAND xverse_xcom_lifecycle_unit_tests)
  add_test(NAME xcom_lifecycle_negative COMMAND xverse_xcom_lifecycle_negative_tests)
  add_test(NAME xcom_lifecycle_external_consumer COMMAND xverse_xcom_lifecycle_consumer)
endif()
