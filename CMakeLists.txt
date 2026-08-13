cmake_minimum_required(VERSION 3.24)
project(ZhuYinInputMethod LANGUAGES C CXX OBJC OBJCXX)
set(CMAKE_OSX_DEPLOYMENT_TARGET "12.0" CACHE STRING "" FORCE)
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)
add_executable(ZhuYinInputMethod MACOSX_BUNDLE
  App/main.m App/ZYRuntime.mm App/ZYCandidatePanel.mm App/ZYAccessibilityCaret.mm App/ZYInputController.mm
  Core/ZYDictionary.c Core/ZYEngine.c Core/ZYComposer.c Core/ZYLearning.c Core/ZYConversion.c
  Resources/dictionary.bin Resources/t2s.bin)
target_include_directories(ZhuYinInputMethod PRIVATE Core App)
target_compile_options(ZhuYinInputMethod PRIVATE -Os)
target_link_options(ZhuYinInputMethod PRIVATE -Wl,-dead_strip)
target_link_libraries(ZhuYinInputMethod PRIVATE "-framework Cocoa" "-framework InputMethodKit" "-framework Carbon" "-framework ApplicationServices" "-framework CoreFoundation")
set_source_files_properties(Resources/dictionary.bin Resources/t2s.bin PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
set_target_properties(ZhuYinInputMethod PROPERTIES
  OUTPUT_NAME "逐音輸入法"
  MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/App/Info.plist"
  XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "tw.zhuyin.inputmethod"
  XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "-"
  XCODE_ATTRIBUTE_CLANG_ENABLE_OBJC_ARC YES)
