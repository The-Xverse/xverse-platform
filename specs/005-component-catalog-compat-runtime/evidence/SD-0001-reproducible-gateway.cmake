function(xverse_finalize_gateway)
  if(NOT TARGET gateway)
    message(FATAL_ERROR "gateway target was not defined")
  endif()

  set_property(
    TARGET gateway
    PROPERTY BUILD_RPATH
      "$ORIGIN/../third_party/zenoh/lib;$ORIGIN/../third_party/vsomeip/lib"
  )
  set_property(
    TARGET gateway
    PROPERTY INSTALL_RPATH
      "$ORIGIN/../third_party/zenoh/lib;$ORIGIN/../third_party/vsomeip/lib"
  )
  set_property(TARGET gateway PROPERTY INSTALL_RPATH_USE_LINK_PATH FALSE)
  set_property(TARGET gateway PROPERTY SKIP_BUILD_RPATH TRUE)
  set_property(TARGET gateway PROPERTY BUILD_WITH_INSTALL_RPATH TRUE)
  target_link_options(gateway PRIVATE "-Wl,--build-id=none")
endfunction()

cmake_language(DEFER DIRECTORY "${CMAKE_SOURCE_DIR}" CALL xverse_finalize_gateway)
