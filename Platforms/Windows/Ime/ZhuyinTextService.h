#pragma once

#include <cstdint>
#include <string>
#include <vector>

extern "C" {
#include "ZYEngine.h"
#include "ZYLearning.h"
#include "ZYConversion.h"
}

// This class deliberately owns no TSF or window objects.  A future TSF text
// service adapts key events and candidate UI to this shared-core bridge.
class ZhuyinWindowsCoreBridge {
public:
    explicit ZhuyinWindowsCoreBridge(std::string resourceDirectory);
    ~ZhuyinWindowsCoreBridge();

    ZhuyinWindowsCoreBridge(const ZhuyinWindowsCoreBridge&) = delete;
    ZhuyinWindowsCoreBridge& operator=(const ZhuyinWindowsCoreBridge&) = delete;

    bool open();
    bool isOpen() const;
    std::vector<ZYCandidate> lookup(const std::string& query, std::size_t limit = 128);
    void commitCandidate(std::uint32_t candidateId, const std::string& query);
    void reset();

private:
    static std::uint32_t queryHash(const std::string& query);
    std::string resourceDirectory_;
    ZYEngine engine_{};
    ZYConversion conversion_{};
    ZYLearning learning_{};
    bool open_ = false;
};
