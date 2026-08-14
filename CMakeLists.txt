cmake_minimum_required(VERSION 3.24)
project(ZhuYinInputMethod LANGUAGES C CXX OBJC OBJCXX)
set(CMAKE_OSX_DEPLOYMENT_TARGET "12.0" CACHE STRING "" FORCE)
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)
add_executable(ZhuYinInputMethod MACOSX_BUNDLE
  Platforms/macOS/App/main.m Platforms/macOS/App/ZYRuntime.mm Platforms/macOS/App/ZYCandidatePanel.mm Platforms/macOS/App/ZYAccessibilityCaret.mm Platforms/macOS/App/ZYInputController.mm
  Shared/Core/ZYDictionary.c Shared/Core/ZYEngine.c Shared/Core/ZYComposer.c Shared/Core/ZYLearning.c Shared/Core/ZYConversion.c
  Shared/Resources/dictionary.bin Shared/Resources/t2s.bin)
target_include_directories(ZhuYinInputMethod PRIVATE Shared/Core Platforms/macOS/App)
target_compile_options(ZhuYinInputMethod PRIVATE -Os)
target_link_options(ZhuYinInputMethod PRIVATE -Wl,-dead_strip)
target_link_libraries(ZhuYinInputMethod PRIVATE "-framework Cocoa" "-framework InputMethodKit" "-framework Carbon" "-framework ApplicationServices" "-framework CoreFoundation")
set_source_files_properties(Shared/Resources/dictionary.bin Shared/Resources/t2s.bin PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
set_target_properties(ZhuYinInputMethod PROPERTIES
  OUTPUT_NAME "逐音輸入法"
  MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Platforms/macOS/App/Info.plist"
  XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "tw.zhuyin.inputmethod"
  XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "-"
  XCODE_ATTRIBUTE_CLANG_ENABLE_OBJC_ARC YES)
