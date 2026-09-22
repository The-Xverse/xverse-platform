include_guard(GLOBAL)

#[=======================================================================[.rst:
XComWarnings
------------

Defines the warning policy shared by future X-COM C++ targets. Unsupported
compilers fail configuration rather than silently weakening the policy.
#]=======================================================================]

function(_xverse_xcom_warning_option_is_negating output option)
  string(TOLOWER "${option}" normalized_option)
  set(is_negating FALSE)
  if(
    normalized_option STREQUAL "-w"
    OR normalized_option STREQUAL "/w"
    OR normalized_option MATCHES "^-wno-"
    OR normalized_option MATCHES "^/w[0-3]$"
    OR normalized_option MATCHES "^/wd[0-9]+$"
    OR normalized_option MATCHES "^/wx[-:]"
    OR normalized_option MATCHES "^@"
  )
    set(is_negating TRUE)
  elseif(normalized_option MATCHES "^-wp,(.+)$")
    set(forwarded_options "${CMAKE_MATCH_1}")
    string(REPLACE "," ";" forwarded_options "${forwarded_options}")
    foreach(forwarded_option IN LISTS forwarded_options)
      _xverse_xcom_warning_option_is_negating(
        forwarded_is_negating
        "${forwarded_option}"
      )
      if(forwarded_is_negating)
        set(is_negating TRUE)
      endif()
    endforeach()
  elseif(normalized_option MATCHES "^-x(clang|compiler|preprocessor)[=,](.+)$")
    set(forwarded_options "${CMAKE_MATCH_2}")
    string(REPLACE "," ";" forwarded_options "${forwarded_options}")
    foreach(forwarded_option IN LISTS forwarded_options)
      _xverse_xcom_warning_option_is_negating(
        forwarded_is_negating
        "${forwarded_option}"
      )
      if(forwarded_is_negating)
        set(is_negating TRUE)
      endif()
    endforeach()
  endif()
  set(${output} "${is_negating}" PARENT_SCOPE)
endfunction()

function(_xverse_xcom_reject_negating_warning_options source value)
  string(REPLACE ";" " " normalized_value "${value}")
  separate_arguments(options NATIVE_COMMAND "${normalized_value}")
  set(forwarder "")
  foreach(option IN LISTS options)
    string(TOLOWER "${option}" normalized_option)
    _xverse_xcom_warning_option_is_negating(is_negating "${option}")
    if(forwarder)
      _xverse_xcom_warning_option_is_negating(
        forwarded_is_negating
        "${option}"
      )
      if(forwarded_is_negating)
        set(is_negating TRUE)
      endif()
      set(forwarder "")
    endif()
    if(is_negating)
      message(
        FATAL_ERROR
        "X-COM warning policy rejects ${option} from ${source}"
      )
    endif()
    if(normalized_option MATCHES "^-x(clang|compiler|preprocessor)$")
      set(forwarder "${option}")
    endif()
  endforeach()
endfunction()

function(xverse_xcom_assert_warning_policy_inputs)
  _xverse_xcom_reject_negating_warning_options("environment CXXFLAGS" "$ENV{CXXFLAGS}")

  get_cmake_property(cache_variables CACHE_VARIABLES)
  foreach(variable IN LISTS cache_variables)
    if(variable MATCHES "^CMAKE_CXX_FLAGS($|_)")
      _xverse_xcom_reject_negating_warning_options(
        "CMake cache entry ${variable}"
        "${${variable}}"
      )
    endif()
  endforeach()
endfunction()

function(xverse_xcom_configure_warnings)
  if(TARGET xverse_xcom_warnings)
    return()
  endif()

  xverse_xcom_assert_warning_policy_inputs()

  add_library(xverse_xcom_warnings INTERFACE)
  add_library(xverse::xcom_warnings ALIAS xverse_xcom_warnings)

  if(CMAKE_CXX_COMPILER_ID MATCHES "^(GNU|Clang|AppleClang)$")
    target_compile_options(
      xverse_xcom_warnings
      INTERFACE -Wall -Wextra -Wpedantic -Werror
    )
  elseif(MSVC)
    target_compile_options(xverse_xcom_warnings INTERFACE /W4 /WX /permissive-)
  else()
    message(
      FATAL_ERROR
      "No accepted X-COM warning policy for compiler ${CMAKE_CXX_COMPILER_ID}"
    )
  endif()
endfunction()

function(xverse_xcom_apply_warnings target_name)
  if(NOT TARGET "${target_name}")
    message(FATAL_ERROR "Cannot apply X-COM warnings to missing target ${target_name}")
  endif()
  target_link_libraries("${target_name}" PRIVATE xverse::xcom_warnings)
endfunction()
