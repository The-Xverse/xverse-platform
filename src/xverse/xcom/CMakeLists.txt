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
  xverse_xcom_stimulation_journal
  xverse_xcom_stimulation_guard
  xverse_xcom_stimulation_actions
  xverse_xcom_tool_gateway_proto
  xverse_xcom_tool_gateway
  xverse_xcom_tool_gateway_grpc
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

# T026's bounded durable stimulation intent/outcome journal. It links only the standard
# library and the accepted T025 in-process validation-session contract, which it consumes
# read-only; it adds no third-party dependency and no new identity/digest vocabulary.
add_library(xverse_xcom_stimulation_journal STATIC src/stimulation_journal.cpp)
add_library(xverse::xcom_stimulation_journal ALIAS xverse_xcom_stimulation_journal)
target_include_directories(
  xverse_xcom_stimulation_journal PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(xverse_xcom_stimulation_journal PUBLIC xverse::xcom_validation_session)
target_compile_features(xverse_xcom_stimulation_journal PUBLIC cxx_std_20)
xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_journal)
set_target_properties(
  xverse_xcom_stimulation_journal
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# T027's fail-closed pre-emission guard. It links only the standard library plus the accepted
# T025 in-process validation-session contract and the accepted T-CORE interaction vocabulary,
# which it consumes read-only; it adds no third-party dependency and redefines no identity,
# digest, diagnostic, interaction, or direction type.
add_library(xverse_xcom_stimulation_guard STATIC src/stimulation_guard.cpp)
add_library(xverse::xcom_stimulation_guard ALIAS xverse_xcom_stimulation_guard)
target_include_directories(
  xverse_xcom_stimulation_guard PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(
  xverse_xcom_stimulation_guard
  PUBLIC xverse::xcom_validation_session xverse::xcom_core_types
)
target_compile_features(xverse_xcom_stimulation_guard PUBLIC cxx_std_20)
xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_guard)
set_target_properties(
  xverse_xcom_stimulation_guard
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# T028's guarded action path and exclusive generation-bound service-emulation lease. It links
# only the standard library plus the accepted T025 in-process validation-session contract, the
# accepted T026 journal, the accepted T027 guard, and the accepted T-CORE origin vocabulary,
# which it consumes read-only; it adds no third-party dependency and redefines no identity,
# digest, diagnostic, interaction, origin, or action type.
add_library(xverse_xcom_stimulation_actions STATIC src/stimulation_actions.cpp)
add_library(xverse::xcom_stimulation_actions ALIAS xverse_xcom_stimulation_actions)
target_include_directories(
  xverse_xcom_stimulation_actions PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_link_libraries(
  xverse_xcom_stimulation_actions
  PUBLIC
    xverse::xcom_stimulation_guard
    xverse::xcom_stimulation_journal
    xverse::xcom_validation_session
    xverse::xcom_core_types
)
target_compile_features(xverse_xcom_stimulation_actions PUBLIC cxx_std_20)
xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_actions)
set_target_properties(
  xverse_xcom_stimulation_actions
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

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

# T030's single versioned external-tool contract. The committed
# proto/xverse/xcom/v1/tool_gateway.proto is the source of truth; the admitted protoc 3.12.4 and
# grpc_cpp_plugin 1.30.2 generate the Protocol Buffers messages and gRPC stubs. Both are compiled
# by their owning targets. The generation runs offline with the admitted prefix
# library directory on the child library path only; no ambient path or network is discovered. This
# is one declared addition to the T012 runtime-target inventory above.
set(
  xcom_t030_proto_root
  "${PROJECT_SOURCE_DIR}/proto"
)
set(
  xcom_t030_proto_source
  "${xcom_t030_proto_root}/xverse/xcom/v1/tool_gateway.proto"
)
set(
  xcom_t030_generated_dir
  "${CMAKE_CURRENT_BINARY_DIR}/t030-proto-gen"
)
set(
  xcom_t030_pb_header
  "${xcom_t030_generated_dir}/xverse/xcom/v1/tool_gateway.pb.h"
)
set(
  xcom_t030_pb_source
  "${xcom_t030_generated_dir}/xverse/xcom/v1/tool_gateway.pb.cc"
)
set(
  xcom_t030_grpc_header
  "${xcom_t030_generated_dir}/xverse/xcom/v1/tool_gateway.grpc.pb.h"
)
set(
  xcom_t030_grpc_source
  "${xcom_t030_generated_dir}/xverse/xcom/v1/tool_gateway.grpc.pb.cc"
)
set(
  xcom_t030_protobuf_include
  "${XVERSE_XCOM_TOOLCHAIN}/usr/include"
)
set(
  xcom_t030_toolchain_lib
  "${XVERSE_XCOM_TOOLCHAIN}/usr/lib/x86_64-linux-gnu"
)

add_custom_command(
  OUTPUT
    "${xcom_t030_pb_source}"
    "${xcom_t030_pb_header}"
    "${xcom_t030_grpc_source}"
    "${xcom_t030_grpc_header}"
  COMMAND ${CMAKE_COMMAND} -E make_directory "${xcom_t030_generated_dir}"
  COMMAND
    ${CMAKE_COMMAND} -E env "LD_LIBRARY_PATH=${xcom_t030_toolchain_lib}"
    "$<TARGET_FILE:protobuf::protoc>"
    "-I${xcom_t030_proto_root}"
    "--cpp_out=${xcom_t030_generated_dir}"
    "--grpc_out=${xcom_t030_generated_dir}"
    "--plugin=protoc-gen-grpc=$<TARGET_FILE:gRPC::grpc_cpp_plugin>"
    "xverse/xcom/v1/tool_gateway.proto"
  DEPENDS "${xcom_t030_proto_source}"
  COMMENT "T030: generating the versioned tool-gateway Protocol Buffers and gRPC artifacts"
  VERBATIM
)

# The generated Protocol Buffers message code only; the generated gRPC service is compiled by
# xverse_xcom_tool_gateway_grpc below. The admitted protobuf headers
# and the generated headers are system includes: third-party and generated-header warnings are
# suppressed while the X-COM warning-as-error policy still governs every T030-owned source line.
add_library(xverse_xcom_tool_gateway_proto STATIC "${xcom_t030_pb_source}")
add_library(xverse::xcom_tool_gateway_proto ALIAS xverse_xcom_tool_gateway_proto)
target_include_directories(
  xverse_xcom_tool_gateway_proto
  SYSTEM PRIVATE
    "${xcom_t030_generated_dir}"
    "${xcom_t030_protobuf_include}"
)
target_link_libraries(xverse_xcom_tool_gateway_proto PRIVATE protobuf::libprotobuf)
target_compile_features(xverse_xcom_tool_gateway_proto PUBLIC cxx_std_20)
xverse_xcom_apply_runtime_rules(xverse_xcom_tool_gateway_proto)
set_target_properties(
  xverse_xcom_tool_gateway_proto
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)
add_custom_target(
  xverse_xcom_tool_gateway_proto_generated
  DEPENDS
    "${xcom_t030_pb_header}"
    "${xcom_t030_pb_source}"
    "${xcom_t030_grpc_header}"
    "${xcom_t030_grpc_source}"
)

# T031's bounded, host-protected, local-IPC-only tool gateway session. It realizes the accepted
# T030 message and method contract and delegates onto the accepted T021-T029 in-process boundaries.
# This in-process core links no gRPC runtime; its separate adapter below owns that dependency.
# It adds one declared entry to the T012 runtime-target
# inventory above. The generated Protocol Buffers headers are system includes so third-party and
# generated-header warnings are suppressed while the X-COM warning-as-error policy still governs
# every T031-owned source line.
add_library(xverse_xcom_tool_gateway STATIC src/tool_gateway.cpp)
add_library(xverse::xcom_tool_gateway ALIAS xverse_xcom_tool_gateway)
target_include_directories(
  xverse_xcom_tool_gateway
  PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_include_directories(
  xverse_xcom_tool_gateway
  SYSTEM PUBLIC
    "$<BUILD_INTERFACE:${xcom_t030_generated_dir}>"
    "$<BUILD_INTERFACE:${xcom_t030_protobuf_include}>"
)
target_link_libraries(
  xverse_xcom_tool_gateway
  PUBLIC
    xverse::xcom_observation
    xverse::xcom_stimulation_actions
    xverse::xcom_stimulation_guard
    xverse::xcom_stimulation_journal
    xverse::xcom_validation_session
    xverse::xcom_tool_gateway_proto
)
target_compile_features(xverse_xcom_tool_gateway PUBLIC cxx_std_20)
add_dependencies(xverse_xcom_tool_gateway xverse_xcom_tool_gateway_proto_generated)
xverse_xcom_apply_runtime_rules(xverse_xcom_tool_gateway)
set_target_properties(
  xverse_xcom_tool_gateway
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# The accepted external transport uses the generated service and the pinned offline gRPC runtime.
# The existing framed gateway remains a compatibility fixture for earlier accepted tests.
add_library(
  xverse_xcom_tool_gateway_grpc STATIC
  "${xcom_t030_grpc_source}"
  src/tool_gateway_grpc.cpp
)
add_library(xverse::xcom_tool_gateway_grpc ALIAS xverse_xcom_tool_gateway_grpc)
target_include_directories(
  xverse_xcom_tool_gateway_grpc
  PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
)
target_include_directories(
  xverse_xcom_tool_gateway_grpc
  SYSTEM PUBLIC
    "$<BUILD_INTERFACE:${xcom_t030_generated_dir}>"
    "$<BUILD_INTERFACE:${xcom_t030_protobuf_include}>"
)
target_link_libraries(
  xverse_xcom_tool_gateway_grpc PUBLIC
  xverse::xcom_tool_gateway
  gRPC::grpc++
  protobuf::libprotobuf
)
target_compile_features(xverse_xcom_tool_gateway_grpc PUBLIC cxx_std_20)
add_dependencies(xverse_xcom_tool_gateway_grpc xverse_xcom_tool_gateway_proto_generated)
xverse_xcom_apply_runtime_rules(xverse_xcom_tool_gateway_grpc)
set_target_properties(xverse_xcom_tool_gateway_grpc PROPERTIES
  CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)

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

  # Real generated-client proof against the production gRPC adapter in a separate process.
  add_executable(
    xverse_xcom_grpc_generated_client_tests
    "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway/grpc_generated_client_tests.cpp"
  )
  target_include_directories(xverse_xcom_grpc_generated_client_tests PRIVATE
    "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway")
  target_compile_definitions(xverse_xcom_grpc_generated_client_tests PRIVATE
    "XCOM_T031_SCRATCH_DIR=\"${CMAKE_BINARY_DIR}/t031-scratch\"")
  target_link_libraries(xverse_xcom_grpc_generated_client_tests PRIVATE
    xverse::xcom_tool_gateway_grpc GTest::gtest Threads::Threads)
  xverse_xcom_apply_runtime_rules(xverse_xcom_grpc_generated_client_tests)
  gtest_discover_tests(xverse_xcom_grpc_generated_client_tests PROPERTIES
    LABELS "t030-grpc" WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}")

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

  # T026 bounded durable stimulation intent/outcome journal tests. Registration is additive:
  # no existing target, test name, label, command, or expected value changes. Each suite uses
  # one hyphenated `t026-<kind>` label (CMake 3.22 label workaround). The recovery suite
  # receives a bounded test-local scratch directory as a build-time path; it never prints it
  # into public evidence.
  foreach(
    journal_kind
    IN ITEMS
      unit
      negative
      recovery
      failure
      concurrency
  )
    add_executable(
      xverse_xcom_stimulation_journal_${journal_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/stimulation_journal/${journal_kind}_tests.cpp"
    )
    target_link_libraries(
      xverse_xcom_stimulation_journal_${journal_kind}_tests
      PRIVATE
        xverse::xcom_stimulation_journal
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    target_compile_definitions(
      xverse_xcom_stimulation_journal_${journal_kind}_tests
      PRIVATE
        "XCOM_T026_SCRATCH_DIR=\"${CMAKE_CURRENT_BINARY_DIR}/t026-scratch\""
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_journal_${journal_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_stimulation_journal_${journal_kind}_tests
      PROPERTIES LABELS "t026-${journal_kind}"
    )
  endforeach()

  # T027 fail-closed pre-emission guard tests. Registration is additive: no existing target,
  # test name, label, command, or expected value changes. Each suite uses one hyphenated
  # `t027-<kind>` label (CMake 3.22 label workaround). The negative suite receives the committed
  # public guard header as a build-time read-only path for its bounded declaration inspection;
  # it never prints the path into public evidence. The guard performs no file I/O, so no scratch
  # directory is required.
  foreach(
    guard_kind
    IN ITEMS
      unit
      mismatch
      time
      negative
      concurrency
  )
    add_executable(
      xverse_xcom_stimulation_guard_${guard_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/stimulation_guard/${guard_kind}_tests.cpp"
    )
    target_link_libraries(
      xverse_xcom_stimulation_guard_${guard_kind}_tests
      PRIVATE
        xverse::xcom_stimulation_guard
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    target_compile_definitions(
      xverse_xcom_stimulation_guard_${guard_kind}_tests
      PRIVATE
        "XCOM_T027_HEADER_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom/stimulation_guard.hpp\""
        "XCOM_T027_SOURCE_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/src/stimulation_guard.cpp\""
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_guard_${guard_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_stimulation_guard_${guard_kind}_tests
      PROPERTIES LABELS "t027-${guard_kind}"
    )
  endforeach()

  # T028 guarded action-path and exclusive service-emulation lease tests. Registration is
  # additive: no existing target, test name, label, command, or expected value changes. Each
  # suite uses one hyphenated `t028-<kind>` label (CMake 3.22 label workaround). The negative
  # suite receives the committed public header and implementation source as build-time
  # read-only paths for its bounded declaration inspection; it never prints the paths into
  # public evidence. The action path performs no file I/O, so no scratch directory is required.
  foreach(
    action_kind
    IN ITEMS
      action
      lease
      lifecycle
      negative
      concurrency
  )
    add_executable(
      xverse_xcom_stimulation_actions_${action_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/stimulation_actions/${action_kind}_tests.cpp"
    )
    target_link_libraries(
      xverse_xcom_stimulation_actions_${action_kind}_tests
      PRIVATE
        xverse::xcom_stimulation_actions
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    target_compile_definitions(
      xverse_xcom_stimulation_actions_${action_kind}_tests
      PRIVATE
        "XCOM_T028_HEADER_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom/stimulation_actions.hpp\""
        "XCOM_T028_SOURCE_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/src/stimulation_actions.cpp\""
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_actions_${action_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_stimulation_actions_${action_kind}_tests
      PROPERTIES LABELS "t028-${action_kind}"
    )
  endforeach()

  # T029 complete stimulation verification matrix tests. Registration is additive: no existing
  # target, test name, label, command, or expected value changes, and no runtime-target inventory
  # entry is added. Each suite uses one hyphenated `t029-<kind>` label (CMake 3.22 label
  # workaround). The committed T028 and T-OBS/provider headers are supplied as build-time
  # read-only definitions for the bounded declaration inspection; the paths are never printed
  # into public evidence. The matrix is offline and in-test storage only, so no scratch
  # directory is required.
  foreach(
    matrix_kind
    IN ITEMS
      permit_action_matrix
      journal_recovery
      zero_emission
      provenance
      lease_drain
      concurrency
      external_review
  )
    string(REPLACE "_" "-" matrix_label "${matrix_kind}")
    add_executable(
      xverse_xcom_stimulation_matrix_${matrix_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/stimulation_matrix/${matrix_kind}_tests.cpp"
    )
    target_include_directories(
      xverse_xcom_stimulation_matrix_${matrix_kind}_tests
      PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/stimulation_matrix"
    )
    target_compile_definitions(
      xverse_xcom_stimulation_matrix_${matrix_kind}_tests
      PRIVATE
        "XCOM_T029_ACTIONS_HEADER_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom/stimulation_actions.hpp\""
        "XCOM_T029_ACTIONS_SOURCE_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/src/stimulation_actions.cpp\""
        "XCOM_T029_OBSERVATION_HEADER_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom/observation.hpp\""
        "XCOM_T029_PROVIDER_HEADER_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom/provider.hpp\""
    )
    target_link_libraries(
      xverse_xcom_stimulation_matrix_${matrix_kind}_tests
      PRIVATE
        xverse::xcom_stimulation_actions
        xverse::xcom_observation
        xverse::xcom_provider_loopback
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_stimulation_matrix_${matrix_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_stimulation_matrix_${matrix_kind}_tests
      PROPERTIES LABELS "t029-${matrix_label}"
    )
  endforeach()

  # T030 generated-contract tests. Registration is additive: no existing target, test name, label,
  # command, or expected value changes and no existing discovery count is reduced. Each suite uses
  # one hyphenated `t030-<kind>` label (CMake 3.22 label workaround) and links only the generated
  # Protocol Buffers message library, GTest, and the standard threads library. The admitted protobuf
  # and generated headers are system includes; the provenance suite receives the build-tree generated
  # header paths as read-only compile definitions and never prints them into public evidence.
  add_dependencies(
    xverse_xcom_tool_gateway_proto
    xverse_xcom_tool_gateway_proto_generated
  )
  foreach(tool_gateway_kind IN ITEMS contract evolution negative provenance)
    add_executable(
      xverse_xcom_tool_gateway_${tool_gateway_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway/${tool_gateway_kind}_tests.cpp"
    )
    target_include_directories(
      xverse_xcom_tool_gateway_${tool_gateway_kind}_tests
      PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway"
    )
    target_include_directories(
      xverse_xcom_tool_gateway_${tool_gateway_kind}_tests
      SYSTEM PRIVATE
        "${xcom_t030_generated_dir}"
        "${xcom_t030_protobuf_include}"
    )
    target_compile_definitions(
      xverse_xcom_tool_gateway_${tool_gateway_kind}_tests
      PRIVATE
        "XCOM_T030_PB_HEADER_PATH=\"${xcom_t030_pb_header}\""
        "XCOM_T030_GRPC_HEADER_PATH=\"${xcom_t030_grpc_header}\""
    )
    target_link_libraries(
      xverse_xcom_tool_gateway_${tool_gateway_kind}_tests
      PRIVATE
        xverse::xcom_tool_gateway_proto
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_tool_gateway_${tool_gateway_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_tool_gateway_${tool_gateway_kind}_tests
      PROPERTIES LABELS "t030-${tool_gateway_kind}"
    )
  endforeach()

  # T031 bounded local-IPC-only gateway tests. Registration is additive: no existing target, test
  # name, label, command, or expected value changes and no existing discovery count is reduced.
  # Each suite uses one hyphenated `t031-<kind>` label (CMake 3.22 label workaround) and links only
  # the additive gateway runtime library, GTest, and the preserved platform libraries. The negative
  # suite receives the committed T031 header and source as build-time read-only definitions for its
  # bounded forbidden-API scan; the local-IPC suite receives a bounded build-tree scratch directory.
  # Neither path is printed into public evidence.
  foreach(
    gateway_kind
    IN ITEMS
      session
      bounds
      lifecycle
      local_ipc
      negative
      logging
  )
    string(REPLACE "_" "-" gateway_label "${gateway_kind}")
    add_executable(
      xverse_xcom_gateway_${gateway_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway/gateway_${gateway_kind}_tests.cpp"
    )
    target_include_directories(
      xverse_xcom_gateway_${gateway_kind}_tests
      PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway"
    )
    target_include_directories(
      xverse_xcom_gateway_${gateway_kind}_tests
      SYSTEM PRIVATE
        "${xcom_t030_generated_dir}"
        "${xcom_t030_protobuf_include}"
    )
    target_compile_definitions(
      xverse_xcom_gateway_${gateway_kind}_tests
      PRIVATE
        "XCOM_T031_HEADER_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom/tool_gateway.hpp\""
        "XCOM_T031_SOURCE_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/src/tool_gateway.cpp\""
        "XCOM_T031_SCRATCH_DIR=\"t031-scratch\""
        "XCOM_T031_CMAKE_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt\""
    )
    target_link_libraries(
      xverse_xcom_gateway_${gateway_kind}_tests
      PRIVATE
        xverse::xcom_tool_gateway
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_gateway_${gateway_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_gateway_${gateway_kind}_tests
      PROPERTIES
        LABELS "t031-${gateway_label}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    )
  endforeach()

  # T032 separate-process synthetic-client fixture and generated-client contract tests.
  # Registration is additive: one fixture executable (not a runtime library, so
  # XVERSE_XCOM_RUNTIME_TARGETS is unchanged) and five `t032-<kind>` test executables. No existing
  # target, test name, label, command, or expected value changes and no existing discovery count is
  # reduced. The client fixture path, the committed client source path, and the bounded build-tree
  # scratch directory are supplied as build-time definitions only and are never printed into public
  # evidence. Each suite uses one hyphenated `t032-<kind>` label (CMake 3.22 label workaround).
  add_executable(
    xverse_xcom_synthetic_client
    "${PROJECT_SOURCE_DIR}/src/xverse/xcom/fixtures/synthetic_tool.cpp"
  )
  target_include_directories(
    xverse_xcom_synthetic_client
    SYSTEM PRIVATE
      "${xcom_t030_generated_dir}"
      "${xcom_t030_protobuf_include}"
  )
  target_link_libraries(
    xverse_xcom_synthetic_client
    PRIVATE xverse::xcom_tool_gateway
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_synthetic_client)
  add_dependencies(
    xverse_xcom_synthetic_client
    xverse_xcom_tool_gateway_proto_generated
  )

  foreach(
    synthetic_kind
    IN ITEMS
      observation
      stimulation
      contract
      negative
      bounds
  )
    add_executable(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway/synthetic_client_${synthetic_kind}_tests.cpp"
    )
    target_include_directories(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      PRIVATE "${PROJECT_SOURCE_DIR}/tests/xcom/tool_gateway"
    )
    target_include_directories(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      SYSTEM PRIVATE
        "${xcom_t030_generated_dir}"
        "${xcom_t030_protobuf_include}"
    )
    target_compile_definitions(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      PRIVATE
        "XCOM_T032_SYNTHETIC_CLIENT_PATH=\"$<TARGET_FILE:xverse_xcom_synthetic_client>\""
        "XCOM_T032_CLIENT_SOURCE_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/fixtures/synthetic_tool.cpp\""
        "XCOM_T032_SCRATCH_DIR=\"${CMAKE_BINARY_DIR}/t032-scratch\""
    )
    target_link_libraries(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      PRIVATE
        xverse::xcom_tool_gateway
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_synthetic_client_${synthetic_kind}_tests)
    add_dependencies(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      xverse_xcom_synthetic_client
    )
    gtest_discover_tests(
      xverse_xcom_synthetic_client_${synthetic_kind}_tests
      PROPERTIES
        LABELS "t032-${synthetic_kind}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    )
  endforeach()

  # T033 reusable provider/observer/stimulation-tool/gateway contract suites. Registration is
  # additive: four `t033-<kind>` test executables. No existing target, test name, label, command, or
  # expected value changes and no existing discovery count is reduced, and no runtime-target
  # inventory entry is added. Each suite header is implementation-agnostic and is instantiated by its
  # driver against the accepted implementations; the T033 headers and drivers consume the accepted
  # T016/T021-T029/T031 test fixtures and public headers read-only. The committed test fixtures are
  # reached through the `${PROJECT_SOURCE_DIR}/tests/xcom` include root, and the bounded build-tree
  # scratch directory is supplied as a build-time definition only (never printed into public
  # evidence). Each suite uses one hyphenated `t033-<kind>` label (CMake 3.22 label workaround).
  foreach(
    contract_suite_kind
    IN ITEMS
      provider
      observer
      stimulation_tool
      gateway
  )
    string(REPLACE "_" "-" contract_suite_label "${contract_suite_kind}")
    add_executable(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/contract_suites/${contract_suite_kind}_suite_tests.cpp"
    )
    target_include_directories(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      PRIVATE
        "${PROJECT_SOURCE_DIR}/tests/xcom"
        "${PROJECT_SOURCE_DIR}/tests/xcom/contract_suites"
    )
    target_include_directories(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      SYSTEM PRIVATE
        "${xcom_t030_generated_dir}"
        "${xcom_t030_protobuf_include}"
    )
    target_compile_definitions(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      PRIVATE
        "XCOM_T031_SCRATCH_DIR=\"t033-scratch\""
    )
    target_link_libraries(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      PRIVATE
        xverse::xcom_tool_gateway
        xverse::xcom_stimulation_actions
        xverse::xcom_observation
        xverse::xcom_provider_loopback
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_contract_suite_${contract_suite_kind}_tests)
    add_dependencies(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      xverse_xcom_tool_gateway_proto_generated
    )
    gtest_discover_tests(
      xverse_xcom_contract_suite_${contract_suite_kind}_tests
      PROPERTIES
        LABELS "t033-${contract_suite_label}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    )
  endforeach()

  # T034 second minimal synthetic provider and its replaceability, version-rejection, and
  # failure-isolation drivers. Registration is additive: the fixture source
  # `src/xverse/xcom/fixtures/synthetic_provider.cpp` is compiled directly into each `t034-<kind>`
  # test executable (no new runtime library, so XVERSE_XCOM_RUNTIME_TARGETS is unchanged) and no
  # existing target, test name, label, command, or expected value changes. The fixture header is
  # reached through the fixtures include root; the accepted T033 provider contract suite and the
  # accepted T016 core-matrix fixtures are consumed read-only. Each driver uses one hyphenated
  # `t034-<kind>` label (CMake 3.22 label workaround): the `suite` driver is labelled
  # `t034-replaceability`.
  set(xcom_t034_kinds suite version isolation)
  set(xcom_t034_labels replaceability version isolation)
  list(LENGTH xcom_t034_kinds xcom_t034_count)
  math(EXPR xcom_t034_last "${xcom_t034_count} - 1")
  foreach(xcom_t034_index RANGE 0 ${xcom_t034_last})
    list(GET xcom_t034_kinds ${xcom_t034_index} xcom_t034_kind)
    list(GET xcom_t034_labels ${xcom_t034_index} xcom_t034_label)
    add_executable(
      xverse_xcom_t034_${xcom_t034_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/contract_suites/second_provider_${xcom_t034_kind}_tests.cpp"
      "${PROJECT_SOURCE_DIR}/src/xverse/xcom/fixtures/synthetic_provider.cpp"
    )
    target_include_directories(
      xverse_xcom_t034_${xcom_t034_kind}_tests
      PRIVATE
        "${PROJECT_SOURCE_DIR}/tests/xcom"
        "${PROJECT_SOURCE_DIR}/tests/xcom/contract_suites"
        "${CMAKE_CURRENT_SOURCE_DIR}/fixtures"
    )
    target_link_libraries(
      xverse_xcom_t034_${xcom_t034_kind}_tests
      PRIVATE
        xverse::xcom_provider_loopback
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_t034_${xcom_t034_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_t034_${xcom_t034_kind}_tests
      PROPERTIES
        LABELS "t034-${xcom_t034_label}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
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

  # T016 consolidated core unit and negative test matrix under tests/xcom/core_matrix/. Registration
  # is additive: no existing target, test name, label, command, or expected result is changed. Each
  # suite uses gtest_discover_tests so every SC-001 rejection case is individually named and
  # reportable, and each carries one hyphenated `t016-*` label (CMake 3.22 label workaround). The
  # fault-boundary suite receives the committed public-header include directory as a build-time path
  # for its bounded read-only vocabulary scan.
  foreach(
    core_matrix_kind
    IN ITEMS
      unit
      negative
      recovery
      concurrency
      fault_boundary
  )
    string(REPLACE "_" "-" core_matrix_label "${core_matrix_kind}")
    add_executable(
      xverse_xcom_core_matrix_${core_matrix_kind}_tests
      "${PROJECT_SOURCE_DIR}/tests/xcom/core_matrix/${core_matrix_kind}_tests.cpp"
    )
    target_include_directories(
      xverse_xcom_core_matrix_${core_matrix_kind}_tests
      PRIVATE
        "${PROJECT_SOURCE_DIR}/tests/xcom/core_matrix"
        "${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom"
    )
    target_compile_definitions(
      xverse_xcom_core_matrix_${core_matrix_kind}_tests
      PRIVATE
        "XCOM_T016_INCLUDE_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}/include/xverse/xcom\""
    )
    target_link_libraries(
      xverse_xcom_core_matrix_${core_matrix_kind}_tests
      PRIVATE
        xverse::xcom_provider_loopback
        GTest::gtest_main
        GTest::gmock
        Threads::Threads
    )
    xverse_xcom_apply_runtime_rules(xverse_xcom_core_matrix_${core_matrix_kind}_tests)
    gtest_discover_tests(
      xverse_xcom_core_matrix_${core_matrix_kind}_tests
      PROPERTIES LABELS "t016-${core_matrix_label}"
    )
  endforeach()

  add_executable(
    xverse_xcom_core_matrix_consumer
    "${PROJECT_SOURCE_DIR}/tests/xcom/core_matrix/consumer/main.cpp"
  )
  target_link_libraries(
    xverse_xcom_core_matrix_consumer
    PRIVATE xverse::xcom_provider_loopback
  )
  xverse_xcom_apply_runtime_rules(xverse_xcom_core_matrix_consumer)
  add_test(
    NAME xcom_core_matrix_external_consumer
    COMMAND xverse_xcom_core_matrix_consumer
  )
  set_tests_properties(
    xcom_core_matrix_external_consumer
    PROPERTIES LABELS "t016"
  )
endif()
