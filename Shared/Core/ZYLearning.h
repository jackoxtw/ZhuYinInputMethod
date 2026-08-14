#ifndef ZY_LEARNING_H
#define ZY_LEARNING_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ZY_LEARN_WORD_CAP 256
#define ZY_LEARN_QUERY_CAP 128
#define ZY_LEARN_PHRASE_CAP 128
#define ZY_LEARN_WORD_BYTES 96
#define ZY_LEARN_QUERY_BYTES 192
#define ZY_LEARN_PRON_BYTES 256
#define ZY_LEARN_FLUSH_MUTATIONS 32
#define ZY_LEARN_FLUSH_SECONDS 900ULL

#define ZY_LEARN_WORD_FREQ_CAP 31
#define ZY_LEARN_QUERY_FREQ_CAP 8
#define ZY_LEARN_PHRASE_FREQ_CAP 16
#define ZY_LEARN_WORD_RECENCY_EVENTS 30
#define ZY_LEARN_QUERY_PREFERRED_EVENTS 64
#define ZY_LEARN_PHRASE_RECENCY_EVENTS 32
#define ZY_LEARN_WORD_FREQ_STEP 4000u
#define ZY_LEARN_QUERY_FREQ_STEP 5000u
#define ZY_LEARN_PHRASE_FREQ_STEP 8000u
#define ZY_LEARN_WORD_RECENCY_STEP 4000u
#define ZY_LEARN_PHRASE_RECENCY_STEP 5000u

typedef struct { uint32_t id; uint32_t last; uint8_t count; uint8_t used; uint16_t reserved; } ZYLearnWord;
typedef struct { uint32_t hash,id,last; uint8_t count,used; uint16_t reserved; } ZYLearnQuery;
typedef struct {
    uint32_t last; uint8_t count,used; uint16_t reserved;
    char word[ZY_LEARN_WORD_BYTES]; char query[ZY_LEARN_QUERY_BYTES]; char pron[ZY_LEARN_PRON_BYTES];
} ZYLearnPhrase;

typedef struct {
    uint32_t clock;
    ZYLearnWord words[ZY_LEARN_WORD_CAP];
    ZYLearnQuery queries[ZY_LEARN_QUERY_CAP];
    ZYLearnPhrase phrases[ZY_LEARN_PHRASE_CAP];
} ZYLearningPersistent;

typedef struct {
    uint32_t generation;
    uint32_t dirty_mutations;
    uint64_t last_flush_seconds;
    ZYLearningPersistent p;
} ZYLearning;

void zy_learning_init(ZYLearning *l,uint64_t now_seconds);
void zy_learning_reset(ZYLearning *l,uint64_t now_seconds);
void zy_learning_begin_event(ZYLearning *l);
void zy_learning_record_word(ZYLearning *l,uint32_t word_id,uint32_t query_hash);
int zy_learning_remove_word(ZYLearning *l,uint32_t word_id,uint32_t query_hash);
int zy_learning_remove_phrase_slot(ZYLearning *l,uint32_t slot);
uint32_t zy_learning_word_count(const ZYLearning *l,uint32_t word_id);
uint32_t zy_learning_word_frequency_bonus(const ZYLearning *l,uint32_t word_id);
uint32_t zy_learning_word_recency_bonus(const ZYLearning *l,uint32_t word_id);
uint32_t zy_learning_query_bonus(const ZYLearning *l,uint32_t query_hash,uint32_t word_id);
uint8_t zy_learning_query_preference_rank(const ZYLearning *l,uint32_t query_hash,uint32_t word_id);
uint32_t zy_learning_phrase_frequency_bonus(const ZYLearnPhrase *phrase);
uint32_t zy_learning_phrase_recency_bonus(const ZYLearning *l,const ZYLearnPhrase *phrase);
int zy_learning_record_phrase(ZYLearning *l,const char *word,const char *query,const char *pron);
int zy_learning_should_flush(const ZYLearning *l,uint64_t now_seconds);
int zy_learning_save(ZYLearning *l,const char *base_path,uint64_t now_seconds,int force_sync);
int zy_learning_load(ZYLearning *l,const char *base_path);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
