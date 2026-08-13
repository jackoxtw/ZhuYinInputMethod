#ifndef ZY_ENGINE_H
#define ZY_ENGINE_H
#include <stddef.h>
#include <stdint.h>
#include "ZYDictionary.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ZY_CANDIDATE_WORD_BYTES 128
#define ZY_CANDIDATE_MAX_SEGMENTS 8

typedef struct {
    uint32_t id;
    int32_t score;
    uint8_t match_class;
    uint8_t matched_chars;
    uint8_t dictionary_exact;
    uint8_t literal;
    uint8_t user_phrase;
    uint8_t preference_rank;
    uint8_t consume_codepoints;
    uint8_t word_complete;
    uint8_t final_syllable_partial;
    uint8_t segment_count;
    uint32_t segment_ids[ZY_CANDIDATE_MAX_SEGMENTS];
    uint8_t segment_consume_codepoints[ZY_CANDIDATE_MAX_SEGMENTS];
    char word[ZY_CANDIDATE_WORD_BYTES];
} ZYCandidate;

typedef struct { ZYDictionary dict; } ZYEngine;
int zy_engine_open(ZYEngine *e,const char *dictionary_path);
void zy_engine_close(ZYEngine *e);
size_t zy_engine_lookup(ZYEngine *e,const char *query,ZYCandidate *out,size_t cap);
size_t zy_engine_lookup_prefix(ZYEngine *e,const char *query,ZYCandidate *out,size_t cap);
int zy_candidate_rank_compare(const void *aa,const void *bb);
int zy_engine_pronunciation_key(ZYEngine *e,uint32_t word_id,char *out,size_t cap);
int zy_engine_match_pron_key(const char *query,const char *pron_key,uint8_t *match_class,uint8_t *matched_chars,int *exact);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
