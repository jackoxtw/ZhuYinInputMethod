#include "ZhuyinTextService.h"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <utility>

namespace {
std::uint64_t nowSeconds() {
    return static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count());
}

std::string resourcePath(const std::string& directory, const char* filename) {
    if (directory.empty()) return filename;
    const char separator = directory.back() == '\\' || directory.back() == '/' ? '\0' : '\\';
    return separator ? directory + separator + filename : directory + filename;
}
}

ZhuyinWindowsCoreBridge::ZhuyinWindowsCoreBridge(std::string resourceDirectory)
    : resourceDirectory_(std::move(resourceDirectory)) {}

ZhuyinWindowsCoreBridge::~ZhuyinWindowsCoreBridge() {
    if (!open_) return;
    zy_conversion_close(&conversion_);
    zy_engine_close(&engine_);
}

bool ZhuyinWindowsCoreBridge::open() {
    if (open_) return true;
    const std::string dictionary = resourcePath(resourceDirectory_, "dictionary.bin");
    const std::string conversion = resourcePath(resourceDirectory_, "t2s.bin");
    if (zy_engine_open(&engine_, dictionary.c_str()) != 0) return false;
    if (zy_conversion_open(&conversion_, conversion.c_str()) != 0) {
        zy_engine_close(&engine_);
        return false;
    }
    zy_learning_init(&learning_, nowSeconds());
    open_ = true;
    return true;
}

bool ZhuyinWindowsCoreBridge::isOpen() const { return open_; }

std::vector<ZYCandidate> ZhuyinWindowsCoreBridge::lookup(const std::string& query, std::size_t limit) {
    if (!open_ || query.empty()) return {};
    limit = std::min<std::size_t>(limit, 256);
    std::vector<ZYCandidate> candidates(limit);
    const std::size_t count = zy_engine_lookup(&engine_, query.c_str(), candidates.data(), candidates.size());
    const std::uint32_t hash = queryHash(query);
    for (std::size_t i = 0; i < count; ++i) {
        ZYCandidate& candidate = candidates[i];
        if (candidate.literal || candidate.id >= engine_.dict.h->word_count) continue;
        candidate.preference_rank = std::max(candidate.preference_rank,
            zy_learning_query_preference_rank(&learning_, hash, candidate.id));
        candidate.score += static_cast<std::int32_t>(
            zy_learning_word_frequency_bonus(&learning_, candidate.id) +
            zy_learning_word_recency_bonus(&learning_, candidate.id) +
            zy_learning_query_bonus(&learning_, hash, candidate.id));
    }
    candidates.resize(count);
    std::qsort(candidates.data(), candidates.size(), sizeof(ZYCandidate), zy_candidate_rank_compare);
    return candidates;
}

void ZhuyinWindowsCoreBridge::commitCandidate(std::uint32_t candidateId, const std::string& query) {
    if (!open_ || candidateId >= engine_.dict.h->word_count) return;
    zy_learning_begin_event(&learning_);
    zy_learning_record_word(&learning_, candidateId, queryHash(query));
}

void ZhuyinWindowsCoreBridge::reset() {
    zy_learning_reset(&learning_, nowSeconds());
}

std::uint32_t ZhuyinWindowsCoreBridge::queryHash(const std::string& query) {
    std::uint32_t hash = 2166136261u;
    for (const unsigned char character : query) {
        hash ^= character;
        hash *= 16777619u;
    }
    return hash ? hash : 1;
}
