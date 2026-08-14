cmake_minimum_required(VERSION 3.24)

if(NOT WIN32)
  message(FATAL_ERROR "Platforms/Windows can only be built on Windows.")
endif()

project(ZhuYinWindowsInputMethod LANGUAGES C CXX)
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)

add_library(ZhuyinWindowsCore STATIC
  "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core/ZYDictionary.c"
  "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core/ZYEngine.c"
  "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core/ZYComposer.c"
  "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core/ZYLearning.c"
  "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core/ZYConversion.c")
target_include_directories(ZhuyinWindowsCore PUBLIC "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core")

# The TSF COM adapter is intentionally introduced separately; this target is
# the buildable, non-UI bridge it will call for candidate lookup and learning.
add_library(ZhuyinTextService SHARED Ime/ZhuyinTextService.cpp)
target_link_libraries(ZhuyinTextService PRIVATE ZhuyinWindowsCore ole32 uuid msctf)
target_include_directories(ZhuyinTextService PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../../Shared/Core")
