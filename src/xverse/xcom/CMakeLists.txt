# ------------------------------------------------------------------------------------------------
# T012 subtree build/test contract. This block declares the X-COM runtime target inventory, fails
# closed when the inherited warning-as-error policy is absent, resolves the opt-in sanitizer
# selection, routes every runtime and test target through one uniform rule helper, and emits the
# effective policy as build-tree evidence verified by the `xcom_build_contract` CTest target.
# See docs/engineering/xcom/t012/ for the governing requirements, architecture, and design.
# ------------------------------------------------------------------------------------------------

# Declared, ordered runtime library inventory (T012-SR-001, INV-12). A task that changes this
# inventory must update this list and the build-contract verifier together.
set(
  XVERSE_XCOM_RUNTIME_TARGETS
  xverse_xcom_core_types
  xverse_xcom_observation
  xverse_xcom_endpoint_route_lifecycle
  xverse_xcom_provider_loopback
  xverse_xcom_validation_session
  xverse_xcom_activation_plan
)

# Fail closed when the inherited warning-as-error policy is absent or not promoted to an error
# (T012-SR-003, INV-02, INV-03).
function(xverse_xcom_assert_runtime_warning_policy)
  if(NOT TARGET xverse::xcom_warnings)
    message(
      FATAL_ERROR
      "X-COM subtree requires the inherited xverse::xcom_warnings target"
    )
  endif()
  get_target_property(
    xcom_runtime_warning_options
    xverse::xcom_warnings
    INTERFACE_COMPILE_OPTIONS
  )
  if(NOT xcom_runtime_warning_options)
    message(FATAL_ERROR "X-COM warning policy publishes no compile options")
  endif()
  set(xcom_runtime_promotes_errors FALSE)
  foreach(xcom_runtime_warning_option IN LISTS xcom_runtime_warning_options)
    if(
      xcom_runtime_warning_option STREQUAL "-Werror"
      OR xcom_runtime_warning_option STREQUAL "/WX"
      OR xcom_runtime_warning_option MATCHES "^-Werror="
    )
      set(xcom_runtime_promotes_errors TRUE)
    endif()
  endforeach()
  if(NOT xcom_runtime_promotes_errors)
    message(FATAL_ERROR "X-COM warning policy does not promote warnings to errors")
  endif()
endfunction()

# Resolve the opt-in sanitizer selection into compile/link flags (T012-SR-004, T012-SR-005).
# The empty default adds no flag; an unknown entry or the address+thread combination fails
# configuration before any target is defined. The selected names are also published so the
# generated evidence can record the selection.
function(xverse_xcom_runtime_sanitizers)
  set(xverse_xcom_sanitize_compile "" PARENT_SCOPE)
  set(xverse_xcom_sanitize_link "" PARENT_SCOPE)
  set(xverse_xcom_sanitizer_names "" PARENT_SCOPE)
  set(xcom_sanitizer_requested "${XVERSE_XCOM_SANITIZERS}")
  if("${xcom_sanitizer_requested}" STREQUAL "")
    return()
  endif()
  string(REPLACE "," ";" xcom_sanitizer_requested "${xcom_sanitizer_requested}")
  set(xcom_sanitizer_seen "")
  foreach(xcom_sanitizer_name IN LISTS xcom_sanitizer_requested)
    if(NOT xcom_sanitizer_name MATCHES "^(address|thread|undefined)$")
      message(
        FATAL_ERROR
        "Unsupported XVERSE_XCOM_SANITIZERS entry '${xcom_sanitizer_name}'"
      )
    endif()
    if(xcom_sanitizer_name IN_LIST xcom_sanitizer_seen)
      continue()
    endif()
    list(APPEND xcom_sanitizer_seen "${xcom_sanitizer_name}")
  endforeach()
  if(
    "address" IN_LIST xcom_sanitizer_seen
    AND "thread" IN_LIST xcom_sanitizer_seen
  )
    message(
      FATAL_ERROR
      "XVERSE_XCOM_SANITIZERS: address and thread are mutually exclusive"
    )
  endif()
  set(xcom_sanitize_compile "")
  set(xcom_sanitize_link "")
  foreach(xcom_sanitizer_name IN LISTS xcom_sanitizer_seen)
    if(xcom_sanitizer_name STREQUAL "address")
      list(
        APPEND xcom_sanitize_compile
        -fsanitize=address
        -fno-omit-frame-pointer
      )
      list(APPEND xcom_sanitize_link -fsanitize=address)
    elseif(xcom_sanitizer_name STREQUAL "thread")
      list(APPEND xcom_sanitize_compile -fsanitize=thread)
      list(APPEND xcom_sanitize_link -fsanitize=thread)
    else()
      list(
        APPEND xcom_sanitize_compile
        -fsanitize=undefined
        -fno-sanitize-recover=undefined
      )
      list(APPEND xcom_sanitize_link -fsanitize=undefined)
    endif()
  endforeach()
  set(xverse_xcom_sanitize_compile "${xcom_sanitize_compile}" PARENT_SCOPE)
  set(xverse_xcom_sanitize_link "${xcom_sanitize_link}" PARENT_SCOPE)
  set(xverse_xcom_sanitizer_names "${xcom_sanitizer_seen}" PARENT_SCOPE)
endfunction()

# Uniform application (T012-SR-002, T012-SR-005, INV-02, INV-04): every runtime and test target is
# routed through this helper so no target escapes the warning or selected-sanitizer rules.
function(xverse_xcom_apply_runtime_rules target)
  if(NOT TARGET "${target}")
    message(FATAL_ERROR "Cannot configure missing X-COM target ${target}")
  endif()
  xverse_xcom_apply_warnings("${target}")
  if(xverse_xcom_sanitize_compile)
    target_compile_options("${target}" PRIVATE ${xverse_xcom_sanitize_compile})
    target_link_options("${target}" PRIVATE ${xverse_xcom_sanitize_link})
  endif()
endfunction()

xverse_xcom_assert_runtime_warning_policy()
xverse_xcom_runtime_sanitizers()

# Effective-policy evidence beneath the build tree (T012-SR-007, INV-10). Consumed only by the
# generated `xcom_build_contract` verifier; never committed. `_xverse_xcom_json_string` is the
# root-contract JSON-escape helper the subtree is permitted to reuse.
get_target_property(
  xcom_contract_warning_options
  xverse::xcom_warnings
  INTERFACE_COMPILE_OPTIONS
)
set(xcom_contract_warning_json "")
foreach(xcom_contract_warning_option IN LISTS xcom_contract_warning_options)
  _xverse_xcom_json_string(
    xcom_contract_quoted_option
    "${xcom_contract_warning_option}"
  )
  if(xcom_contract_warning_json)
    string(APPEND xcom_contract_warning_json ", ")
  endif()
  string(APPEND xcom_contract_warning_json "${xcom_contract_quoted_option}")
endforeach()

set(xcom_contract_target_json "")
foreach(xcom_contract_target IN LISTS XVERSE_XCOM_RUNTIME_TARGETS)
  _xverse_xcom_json_string(xcom_contract_quoted_target "${xcom_contract_target}")
  if(xcom_contract_target_json)
    string(APPEND xcom_contract_target_json ", ")
  endif()
  string(APPEND xcom_contract_target_json "${xcom_contract_quoted_target}")
endforeach()

set(xcom_contract_sanitizer_json "")
foreach(xcom_contract_sanitizer IN LISTS xverse_xcom_sanitizer_names)
  _xverse_xcom_json_string(
    xcom_contract_quoted_sanitizer
    "${xcom_contract_sanitizer}"
  )
  if(xcom_contract_sanitizer_json)
    string(APPEND xcom_contract_sanitizer_json ", ")
  endif()
  string(APPEND xcom_contract_sanitizer_json "${xcom_contract_quoted_sanitizer}")
endforeach()

string(
  CONCAT
  xcom_runtime_contract_content
  "{\n"
  "  \"schema_version\": 1,\n"
  "  \"task_id\": \"T012\",\n"
  "  \"cxx_standard\": ${CMAKE_CXX_STANDARD},\n"
  "  \"cxx_extensions\": \"${CMAKE_CXX_EXTENSIONS}\",\n"
  "  \"warning_options\": [${xcom_contract_warning_json}],\n"
  "  \"sanitizers\": [${xcom_contract_sanitizer_json}],\n"
  "  \"runtime_targets\": [${xcom_contract_target_json}],\n"
  "  \"build_testing\": \"${BUILD_TESTING}\"\n"
  "}\n"
)
file(
  GENERATE
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/xcom-runtime-contract.json"
  CONTENT "${xcom_runtime_contract_content}"
)

# Deterministic, offline verifier for the evidence above (T012-SR-007, T012-SR-008). The bracket
# argument keeps the script's own `${...}` references literal; only the expected inventory
# placeholder is substituted at configure time.
set(
  xcom_runtime_contract_verifier_template
  [==[
# Generated by src/xverse/xcom/CMakeLists.txt (T012). Do not edit; CMake rebuilds it.
cmake_minimum_required(VERSION 3.19)

set(xcom_contract_path "${CMAKE_CURRENT_LIST_DIR}/xcom-runtime-contract.json")
if(NOT EXISTS "${xcom_contract_path}")
  message(FATAL_ERROR "xcom_build_contract: missing ${xcom_contract_path}")
endif()
file(READ "${xcom_contract_path}" xcom_contract_json)

function(xcom_contract_get output path)
  string(JSON value ERROR_VARIABLE xcom_json_error GET "${xcom_contract_json}" ${path})
  if(xcom_json_error)
    message(FATAL_ERROR "xcom_build_contract: cannot read '${path}': ${xcom_json_error}")
  endif()
  set(${output} "${value}" PARENT_SCOPE)
endfunction()

xcom_contract_get(xcom_contract_standard cxx_standard)
if(NOT xcom_contract_standard STREQUAL "20")
  message(FATAL_ERROR "xcom_build_contract: cxx_standard must be 20 but is '${xcom_contract_standard}'")
endif()

xcom_contract_get(xcom_contract_extensions cxx_extensions)
if(NOT xcom_contract_extensions STREQUAL "OFF")
  message(FATAL_ERROR "xcom_build_contract: cxx_extensions must be OFF but is '${xcom_contract_extensions}'")
endif()

xcom_contract_get(xcom_contract_build_testing build_testing)
if(NOT xcom_contract_build_testing STREQUAL "ON")
  message(FATAL_ERROR "xcom_build_contract: build_testing must be ON but is '${xcom_contract_build_testing}'")
endif()

string(
  JSON xcom_contract_warning_count
  ERROR_VARIABLE xcom_json_error
  LENGTH "${xcom_contract_json}" warning_options
)
if(xcom_json_error)
  message(FATAL_ERROR "xcom_build_contract: cannot read warning_options: ${xcom_json_error}")
endif()
set(xcom_contract_warning_options "")
if(xcom_contract_warning_count GREATER 0)
  math(EXPR xcom_contract_warning_last "${xcom_contract_warning_count} - 1")
  foreach(xcom_contract_index RANGE 0 ${xcom_contract_warning_last})
    string(
      JSON xcom_contract_warning
      GET "${xcom_contract_json}" warning_options ${xcom_contract_index}
    )
    list(APPEND xcom_contract_warning_options "${xcom_contract_warning}")
  endforeach()
endif()
foreach(xcom_contract_required -Wall -Wextra -Wpedantic)
  if(NOT xcom_contract_required IN_LIST xcom_contract_warning_options)
    message(FATAL_ERROR "xcom_build_contract: warning option ${xcom_contract_required} is missing")
  endif()
endforeach()
set(xcom_contract_promotes_errors FALSE)
foreach(xcom_contract_warning IN LISTS xcom_contract_warning_options)
  if(
    xcom_contract_warning STREQUAL "-Werror"
    OR xcom_contract_warning STREQUAL "/WX"
    OR xcom_contract_warning MATCHES "^-Werror="
  )
    set(xcom_contract_promotes_errors TRUE)
  endif()
endforeach()
if(NOT xcom_contract_promotes_errors)
  message(FATAL_ERROR "xcom_build_contract: warning options do not promote warnings to errors")
endif()

string(
  JSON xcom_contract_target_count
  ERROR_VARIABLE xcom_json_error
  LENGTH "${xcom_contract_json}" runtime_targets
)
if(xcom_json_error)
  message(FATAL_ERROR "xcom_build_contract: cannot read runtime_targets: ${xcom_json_error}")
endif()
set(xcom_contract_targets "")
if(xcom_contract_target_count GREATER 0)
  math(EXPR xcom_contract_target_last "${xcom_contract_target_count} - 1")
  foreach(xcom_contract_index RANGE 0 ${xcom_contract_target_last})
    string(
      JSON xcom_contract_target
      GET "${xcom_contract_json}" runtime_targets ${xcom_contract_index}
    )
    list(APPEND xcom_contract_targets "${xcom_contract_target}")
  endforeach()
endif()
set(xcom_contract_expected_targets "@XVERSE_XCOM_EXPECTED_TARGETS@")
if(NOT "${xcom_contract_targets}" STREQUAL "${xcom_contract_expected_targets}")
  message(
    FATAL_ERROR
    "xcom_build_contract: runtime target inventory mismatch: expected [${xcom_contract_expected_targets}] but found [${xcom_contract_targets}]"
  )
endif()

string(
  JSON xcom_contract_sanitizer_count
  ERROR_VARIABLE xcom_json_error
  LENGTH "${xcom_contract_json}" sanitizers
)
if(xcom_json_error)
  message(FATAL_ERROR "xcom_build_contract: cannot read sanitizers: ${xcom_json_error}")
endif()
set(xcom_contract_sanitizers "")
if(xcom_contract_sanitizer_count GREATER 0)
  math(EXPR xcom_contract_sanitizer_last "${xcom_contract_sanitizer_count} - 1")
  foreach(xcom_contract_index RANGE 0 ${xcom_contract_sanitizer_last})
    string(
      JSON xcom_contract_sanitizer
      GET "${xcom_contract_json}" sanitizers ${xcom_contract_index}
    )
    if(NOT xcom_contract_sanitizer MATCHES "^(address|thread|undefined)$")
      message(FATAL_ERROR "xcom_build_contract: unsupported sanitizer '${xcom_contract_sanitizer}'")
    endif()
    list(APPEND xcom_contract_sanitizers "${xcom_contract_sanitizer}")
  endforeach()
endif()
if(
  "address" IN_LIST xcom_contract_sanitizers
  AND "thread" IN_LIST xcom_contract_sanitizers
)
  message(FATAL_ERROR "xcom_build_contract: address and thread are mutually exclusive")
endif()

message(STATUS "xcom_build_contract: effective X-COM subtree policy verified")
]==]
)
string(
  REPLACE
  "@XVERSE_XCOM_EXPECTED_TARGETS@"
  "${XVERSE_XCOM_RUNTIME_TARGETS}"
  xcom_runtime_contract_verifier
  "${xcom_runtime_contract_verifier_template}"
)
file(
  GENERATE
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/verify-xcom-runtime-contract.cmake"
  CONTENT "${xcom_runtime_contract_verifier}"
)

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
xverse_xcom_apply_runtime_rules(xverse_xcom_core_types)
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
xverse_xcom_apply_runtime_rules(xverse_xcom_observation)
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
xverse_xcom_apply_runtime_rules(xverse_xcom_provider_loopback)
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
xverse_xcom_apply_runtime_rules(xverse_xcom_endpoint_route_lifecycle)
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
xverse_xcom_apply_runtime_rules(xverse_xcom_validation_session)

# T019's bounded C++ decoder for the canonical activation-plan v1 artifact. It links only the
# standard library and the already-admitted nlohmann/json header; the third-party JSON type is an
# implementation detail and does not appear in the public header.
add_library(xverse_xcom_activation_plan STATIC src/activation_plan.cpp)
add_library(xverse::xcom_activation_plan ALIAS xverse_xcom_activation_plan)
target_include_directories(
  xverse_xcom_activation_plan PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(xverse_xcom_activation_plan PUBLIC nlohmann_json::nlohmann_json)
target_compile_features(xverse_xcom_activation_plan PUBLIC cxx_std_20)
xverse_xcom_apply_runtime_rules(xverse_xcom_activation_plan)
set_target_properties(
  xverse_xcom_activation_plan
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

if(BUILD_TESTING)
  find_package(Threads REQUIRED)
  if(NOT DEFINED ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN} OR "$ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN}" STREQUAL "")
    # Accept an explicit, previously admitted cache value when the environment input is absent;
    # no new mandatory input is introduced and the admitted prefix is still used unmodified.
    if(DEFINED XVERSE_XCOM_T025_TEST_TOOLCHAIN AND NOT "${XVERSE_XCOM_T025_TEST_TOOLCHAIN}" STREQUAL "")
      set(ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN} "${XVERSE_XCOM_T025_TEST_TOOLCHAIN}")
    else()
      message(FATAL_ERROR "T025 tests require the admitted XVERSE_XCOM_T025_TEST_TOOLCHAIN prefix")
    endif()
  endif()
  find_package(
    GTest CONFIG REQUIRED
    PATHS "$ENV{XVERSE_XCOM_T025_TEST_TOOLCHAIN}/usr/lib/x86_64-linux-gnu/cmake/GTest"
    NO_DEFAULT_PATH
  )
  include(GoogleTest)

  # T012 deterministic, offline build-contract check. Exactly one additive test; every baseline test
  # name and label is preserved (T012-SR-006, INV-06).
  add_test(
    NAME xcom_build_contract
    COMMAND
      ${CMAKE_COMMAND} -P
      "${CMAKE_CURRENT_BINARY_DIR}/verify-xcom-runtime-contract.cmake"
  )
  set_tests_properties(xcom_build_contract PROPERTIES LABELS "t012")

  foreach(test_kind IN ITEMS unit integration validation)
    add_executable(
      xverse_xcom_validation_${test_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/validation_session/${test_kind}_tests.cpp"
    )
    target_link_libraries(
      xverse_xcom_validation_${test_kind}_tests
      PRIVATE xverse::xcom_validation_session GTest::gtest_main GTest::gmock Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_validation_${test_kind}_tests)
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
  xverse_xcom_apply_runtime_rules(xverse_xcom_core_types_unit_tests)

  add_executable(
    xverse_xcom_core_types_negative_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/core_types/negative_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_core_types_negative_tests
    PRIVATE xverse::xcom_core_types
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_core_types_negative_tests)

  add_executable(
    xverse_xcom_core_types_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/core_types/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_core_types_consumer
    PRIVATE xverse::xcom_core_types
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_core_types_consumer)

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
  xverse_xcom_apply_runtime_rules(xverse_xcom_lifecycle_unit_tests)

  add_executable(
    xverse_xcom_lifecycle_negative_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/endpoint_route_lifecycle/negative_tests.cpp"
  )
  target_link_libraries(
    xverse_xcom_lifecycle_negative_tests
    PRIVATE xverse::xcom_endpoint_route_lifecycle
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_lifecycle_negative_tests)

  add_executable(
    xverse_xcom_lifecycle_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/endpoint_route_lifecycle/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_lifecycle_consumer
    PRIVATE xverse::xcom_endpoint_route_lifecycle
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_lifecycle_consumer)

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
  xverse_xcom_apply_runtime_rules(xverse_xcom_observation_unit_tests)

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
  xverse_xcom_apply_runtime_rules(xverse_xcom_provider_loopback_unit_tests)

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
  xverse_xcom_apply_runtime_rules(xverse_xcom_provider_loopback_negative_tests)

  add_executable(
    xverse_xcom_provider_loopback_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/provider_loopback/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_provider_loopback_consumer
    PRIVATE xverse::xcom_provider_loopback
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_provider_loopback_consumer)

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
  xverse_xcom_apply_runtime_rules(xverse_xcom_observation_integration_tests)

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
  xverse_xcom_apply_runtime_rules(xverse_xcom_observation_disabled_benchmark)

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

  # T019 bounded activation-plan decoder tests. The fixture directory and the committed plan
  # schema are supplied as build-time paths so the tests read the T017 artifacts read-only.
  foreach(plan_kind IN ITEMS unit negative)
    add_executable(
      xverse_xcom_activation_plan_${plan_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/decoder_${plan_kind}_tests.cpp"
    )
    target_compile_definitions(
      xverse_xcom_activation_plan_${plan_kind}_tests
      PRIVATE
        "XCOM_ACTIVATION_PLAN_FIXTURE_DIR=\"${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/fixtures\""
        "XCOM_ACTIVATION_PLAN_SCHEMA_PATH=\"${PROJECT_SOURCE_DIR}/src/xverse/xcom/contracts/v1/activation-plan.schema.json\""
    )
    target_link_libraries(
      xverse_xcom_activation_plan_${plan_kind}_tests
      PRIVATE
        xverse::xcom_activation_plan
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_activation_plan_${plan_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_activation_plan_${plan_kind}_tests
      PROPERTIES LABELS "t019;${plan_kind}"
    )
  endforeach()

  # T020 ordering-equivalence, malformed-plan, drift, bound-matrix, and regression tests. The
  # fixture, plan-schema, and Profile-schema paths are supplied as build-time compile definitions so
  # the suites read the anchored T017 artifacts read-only. The T019 targets are unchanged and the
  # T020 labels are distinct.
  foreach(
    kind
    IN ITEMS
      ordering_equivalence
      malformed_plan
      drift
      bound_matrix
      regression
  )
    string(REPLACE "_" "-" label "${kind}")
    add_executable(
      xverse_xcom_activation_plan_t020_${kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/t020_${kind}_tests.cpp"
    )
    target_compile_definitions(
      xverse_xcom_activation_plan_t020_${kind}_tests
      PRIVATE
        "XCOM_ACTIVATION_PLAN_FIXTURE_DIR=\"${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/fixtures\""
        "XCOM_ACTIVATION_PLAN_SCHEMA_PATH=\"${PROJECT_SOURCE_DIR}/src/xverse/xcom/contracts/v1/activation-plan.schema.json\""
        "XCOM_T020_PROFILE_SCHEMA_PATH=\"${PROJECT_SOURCE_DIR}/xdl/profiles/xcom-v0.1.schema.json\""
    )
    target_link_libraries(
      xverse_xcom_activation_plan_t020_${kind}_tests
      PRIVATE
        xverse::xcom_activation_plan
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_activation_plan_t020_${kind}_tests)
    # A single hyphenated label is used because CMake 3.22's gtest_discover_tests
    # splits a semicolon-separated LABELS value, registering only its first element.
    # `ctest -L t020` and `ctest -L ${label}` both match this one label by regex.
    gtest_discover_tests(
      xverse_xcom_activation_plan_t020_${kind}_tests
      PROPERTIES LABELS "t020-${label}"
    )
  endforeach()
endif()
