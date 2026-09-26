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
  xverse_xcom_observation
  STATIC
    src/observation.cpp
)
add_library(xverse::xcom_observation ALIAS xverse_xcom_observation)
target_include_directories(
  xverse_xcom_observation
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(
  xverse_xcom_observation
  PUBLIC xverse::xcom_core_types
)
target_compile_features(xverse_xcom_observation PUBLIC cxx_std_20)
xverse_xcom_apply_warnings(xverse_xcom_observation)
set_target_properties(
  xverse_xcom_observation
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
  xverse_xcom_provider_loopback
  STATIC
    src/provider.cpp
    src/loopback_provider.cpp
)
add_library(
  xverse::xcom_provider_loopback
  ALIAS xverse_xcom_provider_loopback
)
target_include_directories(
  xverse_xcom_provider_loopback
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(
  xverse_xcom_provider_loopback
  PUBLIC
    xverse::xcom_endpoint_route_lifecycle
    xverse::xcom_observation
)
target_compile_features(xverse_xcom_provider_loopback PUBLIC cxx_std_20)
xverse_xcom_apply_warnings(xverse_xcom_provider_loopback)
set_target_properties(
  xverse_xcom_provider_loopback
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
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

# T025's bounded local time authority, validation permit, and session lifecycle.
add_library(xverse_xcom_validation_session STATIC src/validation_session.cpp)
add_library(xverse::xcom_validation_session ALIAS xverse_xcom_validation_session)
target_include_directories(
  xverse_xcom_validation_session PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_compile_features(xverse_xcom_validation_session PUBLIC cxx_std_20)
xverse_xcom_apply_warnings(xverse_xcom_validation_session)

if(BUILD_TESTING)
  find_package(Threads REQUIRED)
  if(NOT DEFINED ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN} OR "$ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN}" STREQUAL "")
    message(FATAL_ERROR "T025 tests require the admitted XVERSE_XCOM_T025_TEST_TOOLCHAIN prefix")
  endif()
  find_package(
    GTest CONFIG REQUIRED
    PATHS "$ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN}/usr/lib/x86_64-linux-gnu/cmake/GTest"
    NO_DEFAULT_PATH
  )
  include(GoogleTest)

  foreach(test_kind IN ITEMS unit integration validation)
    add_executable(
      xverse_xcom_validation_${test_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/validation_session/${test_kind}_tests.cpp"
    )
    target_link_libraries(
      xverse_xcom_validation_${test_kind}_tests
      PRIVATE xverse::xcom_validation_session GTest::gtest_main GTest::gmock Threads::Threads
    )
    xverse_xcom_apply_warnings(xverse_xcom_validation_${test_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_validation_${test_kind}_tests
      PROPERTIES LABELS "t025;${test_kind}"
    )
  endforeach()

  # Test-only friend seam for paired comparison with the admitted pre-observation submit path.
  target_compile_definitions(
    xverse_xcom_provider_loopback
    PUBLIC XVERSE_XCOM_ENABLE_DISABLED_OBSERVATION_BENCHMARK=1
  )

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

  add_executable(
    xverse_xcom_observation_unit_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/observation/core/unit_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_observation_unit_tests
    PRIVATE xverse::xcom_observation Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_observation_unit_tests)

  add_test(
    NAME xcom_observation_unit
    COMMAND xverse_xcom_observation_unit_tests
  )

  add_executable(
    xverse_xcom_provider_loopback_unit_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/provider_loopback/unit_tests.cpp"
  )
  target_include_directories(
    xverse_xcom_provider_loopback_unit_tests
    PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/provider_loopback"
  )
  target_link_libraries(
    xverse_xcom_provider_loopback_unit_tests
    PRIVATE xverse::xcom_provider_loopback Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_provider_loopback_unit_tests)

  add_executable(
    xverse_xcom_provider_loopback_negative_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/provider_loopback/negative_tests.cpp"
  )
  target_include_directories(
    xverse_xcom_provider_loopback_negative_tests
    PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/provider_loopback"
  )
  target_link_libraries(
    xverse_xcom_provider_loopback_negative_tests
    PRIVATE xverse::xcom_provider_loopback Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_provider_loopback_negative_tests)

  add_executable(
    xverse_xcom_provider_loopback_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/provider_loopback/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_provider_loopback_consumer
    PRIVATE xverse::xcom_provider_loopback
  )
  xverse_xcom_apply_warnings(xverse_xcom_provider_loopback_consumer)

  add_test(
    NAME xcom_provider_loopback_unit
    COMMAND xverse_xcom_provider_loopback_unit_tests
  )
  add_test(
    NAME xcom_provider_loopback_negative
    COMMAND xverse_xcom_provider_loopback_negative_tests
  )
  add_test(
    NAME xcom_provider_loopback_external_consumer
    COMMAND xverse_xcom_provider_loopback_consumer
  )

  add_executable(
    xverse_xcom_observation_integration_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/observation/integration/integration_tests.cpp"
  )
  target_include_directories(
    xverse_xcom_observation_integration_tests
    PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/observation/integration"
  )
  target_link_libraries(
    xverse_xcom_observation_integration_tests
    PRIVATE xverse::xcom_provider_loopback Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_observation_integration_tests)

  add_executable(
    xverse_xcom_observation_disabled_benchmark
    "${PROJECT_SOURCE_DIR}/tests/xcom/observation/integration/disabled_tap_benchmark.cpp"
  )
  target_include_directories(
    xverse_xcom_observation_disabled_benchmark
    PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/observation/integration"
  )
  target_link_libraries(
    xverse_xcom_observation_disabled_benchmark
    PRIVATE xverse::xcom_provider_loopback Threads::Threads
  )
  xverse_xcom_apply_warnings(xverse_xcom_observation_disabled_benchmark)

  add_test(
    NAME xcom_observation_integration
    COMMAND xverse_xcom_observation_integration_tests
  )
  add_test(
    NAME xcom_observation_disabled_benchmark
    COMMAND xverse_xcom_observation_disabled_benchmark
  )
  set_tests_properties(
    xcom_observation_disabled_benchmark
    PROPERTIES LABELS "performance;observation"
  )
endif()
