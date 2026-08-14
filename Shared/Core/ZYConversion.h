#ifndef ZY_CONVERSION_H
#define ZY_CONVERSION_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int fd; size_t size; const uint8_t *map;
    uint32_t char_count, phrase_count;
    const uint32_t *trad_chars,*simp_chars;
    const uint8_t *phrase_records,*pool; size_t pool_size;
} ZYConversion;
int zy_conversion_open(ZYConversion *c,const char *path);
void zy_conversion_close(ZYConversion *c);
int zy_conversion_t2s(const ZYConversion *c,const char *input,char *out,size_t out_cap);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
