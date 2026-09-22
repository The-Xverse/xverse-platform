include_guard(GLOBAL)

#[=======================================================================[.rst:
XComOfflineDependencies
-----------------------

Admits the exact externally retained dependency set. Both input locations are
explicit environment inputs; no package registry, network fetch, or ambient
latest-version resolution is permitted.
#]=======================================================================]

function(_xverse_xcom_import_library target location include_directory)
  if(NOT TARGET "${target}")
    add_library("${target}" UNKNOWN IMPORTED GLOBAL)
    set_target_properties(
      "${target}"
      PROPERTIES
        IMPORTED_LOCATION "${location}"
        INTERFACE_INCLUDE_DIRECTORIES "${include_directory}"
    )
  endif()
endfunction()

function(_xverse_xcom_import_executable target location)
  if(NOT TARGET "${target}")
    add_executable("${target}" IMPORTED GLOBAL)
    set_target_properties("${target}" PROPERTIES IMPORTED_LOCATION "${location}")
  endif()
endfunction()

function(xverse_xcom_admit_offline_dependencies)
  foreach(input_name IN ITEMS XVERSE_XCOM_TOOLCHAIN XVERSE_XCOM_PACKAGE_MANIFEST)
    if(NOT DEFINED ENV{${input_name}} OR "$ENV{${input_name}}" STREQUAL "")
      message(FATAL_ERROR "Required explicit input ${input_name} is unset")
    endif()
  endforeach()

  set(xcom_prefix "$ENV{XVERSE_XCOM_TOOLCHAIN}")
  set(xcom_manifest "$ENV{XVERSE_XCOM_PACKAGE_MANIFEST}")
  cmake_path(ABSOLUTE_PATH xcom_prefix NORMALIZE)
  cmake_path(ABSOLUTE_PATH xcom_manifest NORMALIZE)
  if(NOT IS_DIRECTORY "${xcom_prefix}")
    message(FATAL_ERROR "XVERSE_XCOM_TOOLCHAIN does not name a directory")
  endif()
  if(NOT EXISTS "${xcom_manifest}" OR IS_DIRECTORY "${xcom_manifest}")
    message(FATAL_ERROR "XVERSE_XCOM_PACKAGE_MANIFEST does not name a file")
  endif()

  find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
  execute_process(
    COMMAND
      "${Python3_EXECUTABLE}"
      "${PROJECT_SOURCE_DIR}/scripts/xcom_dependency_preflight.py"
      --cmake-dependency-check
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    RESULT_VARIABLE xcom_preflight_result
    OUTPUT_VARIABLE xcom_preflight_output
    ERROR_VARIABLE xcom_preflight_error
    TIMEOUT 120
  )
  if(NOT xcom_preflight_result EQUAL 0)
    string(STRIP "${xcom_preflight_output}\n${xcom_preflight_error}" xcom_preflight_detail)
    message(FATAL_ERROR "X-COM dependency admission failed: ${xcom_preflight_detail}")
  endif()

  # Prevent later capability slices from resolving an ambient or newer package.
  set(CMAKE_FIND_USE_PACKAGE_REGISTRY FALSE CACHE BOOL "Ignore user package registry" FORCE)
  set(
    CMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY
    FALSE
    CACHE BOOL
    "Ignore system package registry"
    FORCE
  )
  set(CMAKE_FIND_PACKAGE_NO_PACKAGE_REGISTRY ON CACHE BOOL "No user package registry" FORCE)
  set(
    CMAKE_FIND_PACKAGE_NO_SYSTEM_PACKAGE_REGISTRY
    ON
    CACHE BOOL
    "No system package registry"
    FORCE
  )
  set(FETCHCONTENT_FULLY_DISCONNECTED ON CACHE BOOL "No network dependency resolution" FORCE)
  set(XVERSE_XCOM_TOOLCHAIN "${xcom_prefix}" CACHE PATH "Admitted offline prefix" FORCE)
  set(XVERSE_XCOM_PACKAGE_MANIFEST "${xcom_manifest}" CACHE FILEPATH "Admitted manifest" FORCE)

  set(xcom_include "${xcom_prefix}/usr/include")
  set(xcom_lib "${xcom_prefix}/usr/lib/x86_64-linux-gnu")
  add_library(nlohmann_json::nlohmann_json INTERFACE IMPORTED GLOBAL)
  set_target_properties(
    nlohmann_json::nlohmann_json
    PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "${xcom_include}"
  )
  _xverse_xcom_import_library(
    protobuf::libprotobuf
    "${xcom_lib}/libprotobuf.a"
    "${xcom_include}"
  )
  _xverse_xcom_import_executable(
    protobuf::protoc
    "${xcom_prefix}/usr/bin/protoc"
  )
  _xverse_xcom_import_library(
    gRPC::grpc
    "${xcom_lib}/libgrpc.so"
    "${xcom_include}"
  )
  _xverse_xcom_import_library(
    gRPC::grpc++
    "${xcom_lib}/libgrpc++.so"
    "${xcom_include}"
  )
  set_property(TARGET gRPC::grpc++ APPEND PROPERTY INTERFACE_LINK_LIBRARIES gRPC::grpc)
  _xverse_xcom_import_executable(
    gRPC::grpc_cpp_plugin
    "${xcom_prefix}/usr/bin/grpc_cpp_plugin"
  )
endfunction()
