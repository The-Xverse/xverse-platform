cmake_minimum_required(VERSION 3.22)

project(
  XVersePlatform
  VERSION 0.1.0
  DESCRIPTION "X-Verse domain-neutral platform"
  LANGUAGES CXX
)

if(NOT CMAKE_GENERATOR MATCHES "^Ninja")
  message(FATAL_ERROR "X-COM requires a Ninja generator; selected: ${CMAKE_GENERATOR}")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(CTest)
if(NOT BUILD_TESTING)
  message(FATAL_ERROR "X-COM requires BUILD_TESTING=ON")
endif()

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(XComWarnings)
include(XComOfflineDependencies)

xverse_xcom_configure_warnings()
xverse_xcom_admit_offline_dependencies()

# This target is deliberately compile-only. It proves that CMake's selected
# compiler accepts the required language and warning policy while compiling
# headers from the admitted prefix; it introduces no runtime behavior.
set(xcom_policy_probe_source "${CMAKE_CURRENT_BINARY_DIR}/xcom_policy_probe.cpp")
file(
  GENERATE
  OUTPUT "${xcom_policy_probe_source}"
  CONTENT [=[
#include <concepts>
#include <google/protobuf/message.h>
#include <grpcpp/grpcpp.h>
#include <nlohmann/json.hpp>

static_assert(std::same_as<int, int>);

namespace xverse::xcom::build_policy {
[[maybe_unused]] constexpr int probe() noexcept { return 0; }
}  // namespace xverse::xcom::build_policy
]=]
)

add_library(xverse_xcom_policy_probe OBJECT "${xcom_policy_probe_source}")
target_link_libraries(
  xverse_xcom_policy_probe
  PRIVATE
    nlohmann_json::nlohmann_json
    protobuf::libprotobuf
    gRPC::grpc++
)
xverse_xcom_apply_warnings(xverse_xcom_policy_probe)
set_target_properties(
  xverse_xcom_policy_probe
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# This compile-only fixture must never build successfully. The preflight asks
# CMake to build it and admits the warning policy only when the intentional
# warning is promoted to an error by the target's effective compiler options.
set(
  xcom_warning_rejection_probe_source
  "${CMAKE_CURRENT_BINARY_DIR}/xcom_warning_rejection_probe.cpp"
)
file(
  GENERATE
  OUTPUT "${xcom_warning_rejection_probe_source}"
  CONTENT [=[
namespace xverse::xcom::build_policy {
int intentional_return_type_warning() noexcept {}
}  // namespace xverse::xcom::build_policy
]=]
)
add_library(
  xverse_xcom_warning_rejection_probe
  OBJECT
  EXCLUDE_FROM_ALL
  "${xcom_warning_rejection_probe_source}"
)
xverse_xcom_apply_warnings(xverse_xcom_warning_rejection_probe)
set_target_properties(
  xverse_xcom_warning_rejection_probe
  PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

get_target_property(
  xcom_policy_warning_options
  xverse_xcom_warnings
  INTERFACE_COMPILE_OPTIONS
)
if(NOT xcom_policy_warning_options)
  message(FATAL_ERROR "X-COM warning policy did not publish compile options")
endif()

function(_xverse_xcom_json_string output value)
  string(REPLACE "\\" "\\\\" escaped "${value}")
  string(REPLACE "\"" "\\\"" escaped "${escaped}")
  set(${output} "\"${escaped}\"" PARENT_SCOPE)
endfunction()

set(xcom_policy_warning_json "")
foreach(option IN LISTS xcom_policy_warning_options)
  _xverse_xcom_json_string(quoted_option "${option}")
  if(xcom_policy_warning_json)
    string(APPEND xcom_policy_warning_json ", ")
  endif()
  string(APPEND xcom_policy_warning_json "${quoted_option}")
endforeach()
_xverse_xcom_json_string(quoted_compiler "${CMAKE_CXX_COMPILER}")
_xverse_xcom_json_string(quoted_compiler_id "${CMAKE_CXX_COMPILER_ID}")
_xverse_xcom_json_string(quoted_compiler_version "${CMAKE_CXX_COMPILER_VERSION}")
_xverse_xcom_json_string(quoted_generator "${CMAKE_GENERATOR}")
_xverse_xcom_json_string(quoted_manifest "${XVERSE_XCOM_PACKAGE_MANIFEST}")
_xverse_xcom_json_string(quoted_prefix "${XVERSE_XCOM_TOOLCHAIN}")

set(
  XVERSE_XCOM_POLICY_EVIDENCE
  "${CMAKE_CURRENT_BINARY_DIR}/xcom-build-policy.json"
  CACHE INTERNAL
  "Machine-readable evidence for the X-COM build policy"
)
string(
  CONCAT
  xcom_policy_evidence_content
  "{\n"
  "  \"schema_version\": 1,\n"
  "  \"probe_target\": \"xverse_xcom_policy_probe\",\n"
  "  \"compiler\": ${quoted_compiler},\n"
  "  \"compiler_id\": ${quoted_compiler_id},\n"
  "  \"compiler_version\": ${quoted_compiler_version},\n"
  "  \"generator\": ${quoted_generator},\n"
  "  \"cxx_standard\": 20,\n"
  "  \"cxx_standard_required\": true,\n"
  "  \"cxx_extensions\": false,\n"
  "  \"build_testing\": true,\n"
  "  \"warnings_as_errors\": true,\n"
  "  \"warning_options\": [${xcom_policy_warning_json}],\n"
  "  \"toolchain_prefix\": ${quoted_prefix},\n"
  "  \"package_manifest\": ${quoted_manifest}\n"
  "}\n"
)
file(
  GENERATE
  OUTPUT "${XVERSE_XCOM_POLICY_EVIDENCE}"
  CONTENT "${xcom_policy_evidence_content}"
)

# Capability 007 runtime sources are intentionally absent from this foundation
# slice. A later accepted slice may add this subtree without changing the root
# build contract.
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/xverse/xcom/CMakeLists.txt")
  add_subdirectory(src/xverse/xcom)
endif()
