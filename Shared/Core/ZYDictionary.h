#ifndef ZY_DICTIONARY_H
#define ZY_DICTIONARY_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif


typedef struct {
    char magic[8];
    uint32_t version, header_size, word_count, indexed_word_count, syllable_count, bucket_count;
    uint64_t file_size;
    uint64_t word_pool_off, word_pool_size;
    uint64_t word_offsets_off, pron_offsets_off;
    uint64_t syllable_ids_off, syllable_ids_count;
    uint64_t weights_off;
    uint64_t syllable_pool_off, syllable_pool_size;
    uint64_t syllable_offsets_off;
    uint64_t bucket_symbols_off, bucket_offsets_off, bucket_word_ids_off, bucket_word_ids_count;
} ZYDictHeader;

typedef struct {
    int fd;
    size_t size;
    const uint8_t *map;
    const ZYDictHeader *h;
    const uint8_t *word_pool;
    const uint32_t *word_offsets;
    const uint32_t *pron_offsets;
    const uint16_t *syllable_ids;
    const uint8_t *weights;
    const uint8_t *syllable_pool;
    const uint32_t *syllable_offsets;
    const uint32_t *bucket_symbols;
    const uint32_t *bucket_offsets;
    const uint32_t *bucket_word_ids;
} ZYDictionary;

int zy_dict_open(ZYDictionary *d, const char *path);
void zy_dict_close(ZYDictionary *d);
int zy_dict_word(const ZYDictionary *d, uint32_t word_id, const char **ptr, size_t *len);
int zy_dict_syllable(const ZYDictionary *d, uint16_t sid, const char **ptr, size_t *len);
int zy_dict_bucket(const ZYDictionary *d, uint32_t cp, uint32_t *start, uint32_t *end);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
