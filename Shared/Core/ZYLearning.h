#ifndef ZY_LEARNING_H
#define ZY_LEARNING_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Learning v3 keeps the v2 capacities but stores learned phrases with one
   matching key (pronunciation when available, otherwise raw query) instead of
   keeping both query+pronunciation buffers resident. */
#define ZY_LEARN_WORD_CAP 4096
#define ZY_LEARN_QUERY_CAP 8192
#define ZY_LEARN_PHRASE_CAP 1024
#define ZY_LEARN_WORD_BYTES 128
#define ZY_LEARN_KEY_BYTES 512
#define ZY_LEARN_FLUSH_MUTATIONS 32
#define ZY_LEARN_FLUSH_SECONDS 30ULL

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

#define ZY_LEARN_INVALID_WORD_ID UINT32_MAX
#define ZY_LEARN_PHRASE_KEY_QUERY 0u
#define ZY_LEARN_PHRASE_KEY_PRON 1u

/* Runtime pending flags. They are never serialized. */
#define ZY_LEARN_PENDING_DIRTY   0x01u
#define ZY_LEARN_PENDING_DELETE  0x02u
#define ZY_LEARN_PENDING_REPLACE 0x04u
#define ZY_LEARN_PENDING_META    0x08u

typedef struct {
    uint64_t stable_key;
    uint32_t id;
    uint32_t last;
    uint32_t count;
    uint8_t used;
    uint8_t reserved[3];
} ZYLearnWord;

typedef struct {
    uint64_t stable_key;
    uint32_t hash;
    uint32_t id;
    uint32_t last;
    uint32_t count;
    uint8_t used;
    uint8_t reserved[3];
} ZYLearnQuery;

typedef struct {
    uint32_t last;
    uint32_t count;
    uint8_t used;
    uint8_t key_kind;
    uint16_t reserved;
    char word[ZY_LEARN_WORD_BYTES];
    char key[ZY_LEARN_KEY_BYTES];
} ZYLearnPhrase;

typedef struct {
    uint32_t clock;
    uint32_t reserved;
    uint64_t dictionary_fingerprint;
    uint64_t reset_serial;
    ZYLearnWord words[ZY_LEARN_WORD_CAP];
    ZYLearnQuery queries[ZY_LEARN_QUERY_CAP];
    ZYLearnPhrase phrases[ZY_LEARN_PHRASE_CAP];
} ZYLearningPersistent;

typedef struct {
    uint64_t generation;
    uint32_t dirty_mutations;
    /* Kept for source compatibility. In v3 this means "loaded an older format
       and should rewrite it as ZYLEARN3 on the next flush". */
    uint8_t loaded_legacy_v1;
    uint8_t dictionary_fingerprint_dirty;
    uint8_t reserved0[2];
    uint64_t last_flush_seconds;
    uint64_t loaded_reset_serial;
    uint32_t pending_clock_delta;
    uint32_t reserved1;
    ZYLearningPersistent p;
    /* Only unsaved deltas are merged into a newly-read disk snapshot. This is
       what prevents stale processes from losing concurrent +1 operations or
       resurrecting records that another process deleted. */
    uint32_t word_pending_delta[ZY_LEARN_WORD_CAP];
    uint32_t query_pending_delta[ZY_LEARN_QUERY_CAP];
    uint32_t phrase_pending_delta[ZY_LEARN_PHRASE_CAP];
    uint8_t word_pending_flags[ZY_LEARN_WORD_CAP];
    uint8_t query_pending_flags[ZY_LEARN_QUERY_CAP];
    uint8_t phrase_pending_flags[ZY_LEARN_PHRASE_CAP];
} ZYLearning;

void zy_learning_init(ZYLearning *l,uint64_t now_seconds);
void zy_learning_reset(ZYLearning *l,uint64_t now_seconds);
void zy_learning_begin_event(ZYLearning *l);
void zy_learning_record_word(ZYLearning *l,uint32_t word_id,uint32_t query_hash);
void zy_learning_record_word_stable(ZYLearning *l,uint32_t word_id,uint64_t stable_key,uint32_t query_hash);
void zy_learning_bind_word_identity(ZYLearning *l,uint32_t word_id,uint64_t stable_key);
void zy_learning_set_dictionary_fingerprint(ZYLearning *l,uint64_t fingerprint);
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
int zy_learning_clear_persistent(ZYLearning *l,const char *base_path,uint64_t now_seconds);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
