#include "ZYLearning.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#include <process.h>
#include <sys/stat.h>
#include <sys/locking.h>
#else
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#endif


#ifdef _WIN32
static int io_open_read(const char *path){return _open(path,_O_RDONLY|_O_BINARY);}
static int io_open_write(const char *path){return _open(path,_O_WRONLY|_O_CREAT|_O_TRUNC|_O_BINARY,_S_IREAD|_S_IWRITE);}
static int64_t io_pread(int fd,void *buf,size_t n,int64_t off){
    if(_lseeki64(fd,off,SEEK_SET)<0)return -1;size_t done=0;
    while(done<n){unsigned chunk=(unsigned)((n-done)>0x7ffff000u?0x7ffff000u:(n-done));int r=_read(fd,(char*)buf+done,chunk);if(r<0)return -1;if(r==0)break;done+=(size_t)r;}return (int64_t)done;
}
static int64_t io_pwrite(int fd,const void *buf,size_t n,int64_t off){
    if(_lseeki64(fd,off,SEEK_SET)<0)return -1;size_t done=0;
    while(done<n){unsigned chunk=(unsigned)((n-done)>0x7ffff000u?0x7ffff000u:(n-done));int r=_write(fd,(const char*)buf+done,chunk);if(r<0)return -1;if(r==0)break;done+=(size_t)r;}return (int64_t)done;
}
static int io_sync(int fd){return _commit(fd);}
static void io_close(int fd){if(fd>=0)_close(fd);}
static int io_unlink(const char *path){return _unlink(path);}
static long io_pid(void){return (long)_getpid();}
static int io_replace(const char *src,const char *dst){(void)remove(dst);return rename(src,dst);}
typedef int ZYLockHandle;
#define ZY_INVALID_LOCK (-1)
#else
static int io_open_read(const char *path){return open(path,O_RDONLY);}
static int io_open_write(const char *path){return open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);}
static int64_t io_pread(int fd,void *buf,size_t n,int64_t off){return (int64_t)pread(fd,buf,n,(off_t)off);}
static int64_t io_pwrite(int fd,const void *buf,size_t n,int64_t off){return (int64_t)pwrite(fd,buf,n,(off_t)off);}
static int io_sync(int fd){return fsync(fd);}
static void io_close(int fd){if(fd>=0)close(fd);}
static int io_unlink(const char *path){return unlink(path);}
static long io_pid(void){return (long)getpid();}
static int io_replace(const char *src,const char *dst){return rename(src,dst);}
typedef int ZYLockHandle;
#define ZY_INVALID_LOCK (-1)
#endif

#define ZY_LEARN_MAGIC_V1 "ZYLEARN1"
#define ZY_LEARN_MAGIC_V2 "ZYLEARN2"
#define ZY_LEARN_MAGIC_V3 "ZYLEARN3"

/* Exact legacy v1 layout. */
#define ZY_V1_WORD_CAP 256
#define ZY_V1_QUERY_CAP 128
#define ZY_V1_PHRASE_CAP 128
#define ZY_V1_WORD_BYTES 96
#define ZY_V1_QUERY_BYTES 192
#define ZY_V1_PRON_BYTES 256

typedef struct { uint32_t id,last; uint8_t count,used; uint16_t reserved; } ZYLearnWordV1;
typedef struct { uint32_t hash,id,last; uint8_t count,used; uint16_t reserved; } ZYLearnQueryV1;
typedef struct {
    uint32_t last; uint8_t count,used; uint16_t reserved;
    char word[ZY_V1_WORD_BYTES]; char query[ZY_V1_QUERY_BYTES]; char pron[ZY_V1_PRON_BYTES];
} ZYLearnPhraseV1;
typedef struct {
    uint32_t clock;
    ZYLearnWordV1 words[ZY_V1_WORD_CAP];
    ZYLearnQueryV1 queries[ZY_V1_QUERY_CAP];
    ZYLearnPhraseV1 phrases[ZY_V1_PHRASE_CAP];
} ZYLearningPersistentV1;
typedef struct { char magic[8]; uint32_t version,generation,payload_bytes,crc32; } ZYSnapshotHeaderV1;

/* Exact Learning v2 serialized rows. Word/query layouts happen to match v3;
   phrase rows do not because v2 stored both query and pronunciation. */
#define ZY_V2_WORD_BYTES 128
#define ZY_V2_QUERY_BYTES 256
#define ZY_V2_PRON_BYTES 512
typedef struct { uint64_t stable_key; uint32_t id,last,count; uint8_t used; uint8_t reserved[3]; } ZYLearnWordV2;
typedef struct { uint64_t stable_key; uint32_t hash,id,last,count; uint8_t used; uint8_t reserved[3]; } ZYLearnQueryV2;
typedef struct {
    uint32_t last,count; uint8_t used; uint8_t reserved[3];
    char word[ZY_V2_WORD_BYTES]; char query[ZY_V2_QUERY_BYTES]; char pron[ZY_V2_PRON_BYTES];
} ZYLearnPhraseV2;

typedef struct {
    char magic[8];
    uint32_t version;
    uint32_t payload_bytes;
    uint64_t generation;
    uint32_t crc32;
    uint32_t reserved;
} ZYSnapshotHeaderV23;
typedef struct {
    uint32_t clock;
    uint32_t reserved;
    uint64_t dictionary_fingerprint;
    uint64_t reset_serial;
    uint32_t word_count;
    uint32_t query_count;
    uint32_t phrase_count;
    uint32_t reserved2;
} ZYPayloadHeaderV23;

typedef struct { uint64_t generation; uint32_t format_version; ZYLearningPersistent p; } ZYDiskSnapshot;

static uint32_t crc32_bytes(const void *data,size_t n){
    const uint8_t *p=(const uint8_t*)data; uint32_t c=0xffffffffu;
    for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(int32_t)(c&1));}
    return ~c;
}
static uint32_t add_sat_u32(uint32_t a,uint32_t b){return UINT32_MAX-a<b?UINT32_MAX:a+b;}

static size_t utf8_prefix_len_n(const char *src,size_t src_len,size_t max_bytes){
    if(!src)return 0;
    size_t i=0,last=0;
    while(i<src_len&&i<max_bytes){
        unsigned char c=(unsigned char)src[i];size_t n=1;
        if(c<0x80)n=1;else if((c&0xE0)==0xC0)n=2;else if((c&0xF0)==0xE0)n=3;else if((c&0xF8)==0xF0)n=4;else break;
        if(i+n>src_len||i+n>max_bytes)break;
        int valid=1;for(size_t j=1;j<n;j++)if(((unsigned char)src[i+j]&0xC0)!=0x80){valid=0;break;}
        if(!valid)break;
        i+=n;
        last=i;
    }
    return last;
}
static void safe_copy_bounded(char *dst,size_t cap,const char *src,size_t src_cap){
    if(!dst||!cap)return;
    dst[0]=0;
    if(!src||!src_cap)return;
    const char *nul=(const char*)memchr(src,0,src_cap);size_t src_len=nul?(size_t)(nul-src):src_cap;
    size_t n=utf8_prefix_len_n(src,src_len,cap-1);if(n)memcpy(dst,src,n);dst[n]=0;
}
static void safe_copy(char *dst,size_t cap,const char *src){if(!dst||!cap)return;if(!src){dst[0]=0;return;}safe_copy_bounded(dst,cap,src,strlen(src));}

static void clear_pending(ZYLearning *l){
    if(!l)return;
    memset(l->word_pending_delta,0,sizeof(l->word_pending_delta));
    memset(l->query_pending_delta,0,sizeof(l->query_pending_delta));
    memset(l->phrase_pending_delta,0,sizeof(l->phrase_pending_delta));
    memset(l->word_pending_flags,0,sizeof(l->word_pending_flags));
    memset(l->query_pending_flags,0,sizeof(l->query_pending_flags));
    memset(l->phrase_pending_flags,0,sizeof(l->phrase_pending_flags));
    l->pending_clock_delta=0;l->dictionary_fingerprint_dirty=0;
}

void zy_learning_init(ZYLearning *l,uint64_t now){if(!l)return;memset(l,0,sizeof(*l));l->last_flush_seconds=now;}
void zy_learning_reset(ZYLearning *l,uint64_t now){if(!l)return;zy_learning_init(l,now);}
void zy_learning_begin_event(ZYLearning *l){if(!l)return;l->p.clock++;l->pending_clock_delta++;l->dirty_mutations++;}
static uint32_t event_age(uint32_t clock,uint32_t last){return clock-last;}
static uint32_t capped_count(uint32_t count,uint32_t cap){return count<cap?count:cap;}
static int word_identity_match_values(const ZYLearnWord *r,uint32_t id,uint64_t stable){
    if(stable&&r->stable_key)return r->stable_key==stable;
    return r->id!=ZY_LEARN_INVALID_WORD_ID&&id!=ZY_LEARN_INVALID_WORD_ID&&r->id==id;
}
static int query_identity_match_values(const ZYLearnQuery *q,uint32_t hash,uint32_t id,uint64_t stable){
    if(q->hash!=hash)return 0;
    if(stable&&q->stable_key)return q->stable_key==stable;
    return q->id!=ZY_LEARN_INVALID_WORD_ID&&id!=ZY_LEARN_INVALID_WORD_ID&&q->id==id;
}
static int word_same_identity(const ZYLearnWord *a,const ZYLearnWord *b){return word_identity_match_values(a,b->id,b->stable_key);}
static int query_same_identity(const ZYLearnQuery *a,const ZYLearnQuery *b){return query_identity_match_values(a,b->hash,b->id,b->stable_key);}

static int find_word_index_any(ZYLearning *l,uint32_t id,uint64_t stable){
    if(!l)return -1;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord *r=&l->p.words[i];if(r->used&&word_identity_match_values(r,id,stable))return (int)i;}
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord *r=&l->p.words[i];if((l->word_pending_flags[i]&ZY_LEARN_PENDING_DELETE)&&word_identity_match_values(r,id,stable))return (int)i;}
    return -1;
}
static uint64_t word_retention_score(const ZYLearning *l,const ZYLearnWord *r){uint32_t age=event_age(l->p.clock,r->last);uint32_t recent=age<512u?512u-age:0u;return (uint64_t)(r->count>100000u?100000u:r->count)*1024u+recent;}
static int word_slot_index(ZYLearning *l){
    int victim=-1;uint64_t best=UINT64_MAX;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(!l->p.words[i].used&&!l->word_pending_flags[i])return (int)i;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){if(l->word_pending_flags[i]&ZY_LEARN_PENDING_DELETE)continue;ZYLearnWord *r=&l->p.words[i];if(!r->used)continue;uint64_t s=word_retention_score(l,r);if(s<best){best=s;victim=(int)i;}}
    return victim;
}
static int find_query_index_any(ZYLearning *l,uint32_t hash,uint32_t id,uint64_t stable){
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery *q=&l->p.queries[i];if(q->used&&query_identity_match_values(q,hash,id,stable))return (int)i;}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery *q=&l->p.queries[i];if((l->query_pending_flags[i]&ZY_LEARN_PENDING_DELETE)&&query_identity_match_values(q,hash,id,stable))return (int)i;}
    return -1;
}
static uint64_t query_retention_score(const ZYLearning *l,const ZYLearnQuery *q){uint32_t age=event_age(l->p.clock,q->last);uint32_t recent=age<512u?512u-age:0u;return (uint64_t)(q->count>100000u?100000u:q->count)*1024u+recent;}
static int query_slot_index(ZYLearning *l){
    int victim=-1;uint64_t best=UINT64_MAX;
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++)if(!l->p.queries[i].used&&!l->query_pending_flags[i])return (int)i;
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){if(l->query_pending_flags[i]&ZY_LEARN_PENDING_DELETE)continue;ZYLearnQuery *q=&l->p.queries[i];if(!q->used)continue;uint64_t s=query_retention_score(l,q);if(s<best){best=s;victim=(int)i;}}
    return victim;
}

void zy_learning_record_word_stable(ZYLearning *l,uint32_t id,uint64_t stable,uint32_t query_hash){
    if(!l)return;
    int wi=find_word_index_any(l,id,stable);
    if(wi<0){wi=word_slot_index(l);if(wi<0)return;memset(&l->p.words[wi],0,sizeof(l->p.words[wi]));l->word_pending_delta[wi]=0;l->word_pending_flags[wi]=ZY_LEARN_PENDING_DIRTY;}
    ZYLearnWord *r=&l->p.words[wi];
    if(l->word_pending_flags[wi]&ZY_LEARN_PENDING_DELETE){l->word_pending_flags[wi]=(uint8_t)(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_REPLACE);l->word_pending_delta[wi]=0;r->count=0;}
    r->used=1;r->id=id;if(stable)r->stable_key=stable;r->count=add_sat_u32(r->count,1);r->last=l->p.clock;
    l->word_pending_delta[wi]=add_sat_u32(l->word_pending_delta[wi],1);l->word_pending_flags[wi]|=ZY_LEARN_PENDING_DIRTY;
    if(query_hash){
        int qi=find_query_index_any(l,query_hash,id,stable);
        if(qi<0){qi=query_slot_index(l);if(qi>=0){memset(&l->p.queries[qi],0,sizeof(l->p.queries[qi]));l->query_pending_delta[qi]=0;l->query_pending_flags[qi]=ZY_LEARN_PENDING_DIRTY;}}
        if(qi>=0){ZYLearnQuery *q=&l->p.queries[qi];if(l->query_pending_flags[qi]&ZY_LEARN_PENDING_DELETE){l->query_pending_flags[qi]=(uint8_t)(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_REPLACE);l->query_pending_delta[qi]=0;q->count=0;}q->used=1;q->hash=query_hash;q->id=id;if(stable)q->stable_key=stable;q->count=add_sat_u32(q->count,1);q->last=l->p.clock;l->query_pending_delta[qi]=add_sat_u32(l->query_pending_delta[qi],1);l->query_pending_flags[qi]|=ZY_LEARN_PENDING_DIRTY;}
    }
    l->dirty_mutations++;
}
void zy_learning_record_word(ZYLearning *l,uint32_t id,uint32_t query_hash){zy_learning_record_word_stable(l,id,0,query_hash);}
void zy_learning_bind_word_identity(ZYLearning *l,uint32_t id,uint64_t stable){
    if(!l||!stable)return;
    int changed=0;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord *r=&l->p.words[i];if(r->used&&r->id==id&&r->stable_key!=stable){r->stable_key=stable;l->word_pending_flags[i]|=(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_META);changed=1;}}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery *q=&l->p.queries[i];if(q->used&&q->id==id&&q->stable_key!=stable){q->stable_key=stable;l->query_pending_flags[i]|=(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_META);changed=1;}}
    if(changed)l->dirty_mutations++;
}
void zy_learning_set_dictionary_fingerprint(ZYLearning *l,uint64_t fingerprint){if(!l||l->p.dictionary_fingerprint==fingerprint)return;l->p.dictionary_fingerprint=fingerprint;l->dictionary_fingerprint_dirty=1;l->dirty_mutations++;}

int zy_learning_remove_word(ZYLearning *l,uint32_t id,uint32_t query_hash){
    if(!l)return 0;
    int removed=0;
    uint64_t stable=0;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord *r=&l->p.words[i];if(r->used&&r->id==id){if(r->stable_key)stable=r->stable_key;r->used=0;l->word_pending_delta[i]=0;l->word_pending_flags[i]=(uint8_t)(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_DELETE);removed=1;}}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery *q=&l->p.queries[i];if(!q->used)continue;if((q->id==id||(stable&&q->stable_key==stable))&&(!query_hash||q->hash==query_hash)){q->used=0;l->query_pending_delta[i]=0;l->query_pending_flags[i]=(uint8_t)(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_DELETE);removed=1;}}
    if(removed)l->dirty_mutations++;
    return removed;
}
int zy_learning_remove_phrase_slot(ZYLearning *l,uint32_t slot){if(!l||slot>=ZY_LEARN_PHRASE_CAP||!l->p.phrases[slot].used)return 0;l->p.phrases[slot].used=0;l->phrase_pending_delta[slot]=0;l->phrase_pending_flags[slot]=(uint8_t)(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_DELETE);l->dirty_mutations++;return 1;}
uint32_t zy_learning_word_count(const ZYLearning *l,uint32_t id){if(!l)return 0;for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(l->p.words[i].used&&l->p.words[i].id==id)return l->p.words[i].count;return 0;}
uint32_t zy_learning_word_frequency_bonus(const ZYLearning *l,uint32_t id){return capped_count(zy_learning_word_count(l,id),ZY_LEARN_WORD_FREQ_CAP)*ZY_LEARN_WORD_FREQ_STEP;}
uint32_t zy_learning_word_recency_bonus(const ZYLearning *l,uint32_t id){if(!l)return 0;for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){const ZYLearnWord *r=&l->p.words[i];if(!r->used||r->id!=id)continue;uint32_t age=event_age(l->p.clock,r->last);return age<ZY_LEARN_WORD_RECENCY_EVENTS?(ZY_LEARN_WORD_RECENCY_EVENTS-age)*ZY_LEARN_WORD_RECENCY_STEP:0;}return 0;}
uint32_t zy_learning_query_bonus(const ZYLearning *l,uint32_t hash,uint32_t id){if(!l||!hash)return 0;for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){const ZYLearnQuery*q=&l->p.queries[i];if(q->used&&q->hash==hash&&q->id==id)return capped_count(q->count,ZY_LEARN_QUERY_FREQ_CAP)*ZY_LEARN_QUERY_FREQ_STEP;}return 0;}
uint8_t zy_learning_query_preference_rank(const ZYLearning *l,uint32_t hash,uint32_t id){
    if(!l||!hash)return 0;
    const ZYLearnQuery *target=NULL;
    uint32_t newest=0;
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){const ZYLearnQuery*q=&l->p.queries[i];if(!q->used||q->hash!=hash)continue;if(!target&&q->id==id)target=q;else if(q->id==id&&q->last>target->last)target=q;if(q->last>newest)newest=q->last;}
    if(target&&target->last==newest&&event_age(l->p.clock,target->last)<=ZY_LEARN_QUERY_PREFERRED_EVENTS)return 2;
    return 0;
}

static uint8_t phrase_key_kind(const char *pron){return (pron&&*pron)?ZY_LEARN_PHRASE_KEY_PRON:ZY_LEARN_PHRASE_KEY_QUERY;}
static const char *phrase_input_key(const char *query,const char *pron){return (pron&&*pron)?pron:(query?query:"");}
static int phrase_same_key(const ZYLearnPhrase *r,const char *word,uint8_t kind,const char *key){return r->used&&r->key_kind==kind&&strcmp(r->word,word)==0&&strcmp(r->key,key)==0;}
static int phrase_same_row(const ZYLearnPhrase *a,const ZYLearnPhrase *b){return a->key_kind==b->key_kind&&strcmp(a->word,b->word)==0&&strcmp(a->key,b->key)==0;}
static int find_phrase_index_any(ZYLearning *l,const char *word,uint8_t kind,const char *key){
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(phrase_same_key(&l->p.phrases[i],word,kind,key))return (int)i;
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){ZYLearnPhrase*r=&l->p.phrases[i];if((l->phrase_pending_flags[i]&ZY_LEARN_PENDING_DELETE)&&r->key_kind==kind&&strcmp(r->word,word)==0&&strcmp(r->key,key)==0)return (int)i;}
    return -1;
}
static uint64_t phrase_retention_score(const ZYLearning *l,const ZYLearnPhrase *r){uint32_t age=event_age(l->p.clock,r->last);uint32_t recent=age<512u?512u-age:0u;return (uint64_t)(r->count>100000u?100000u:r->count)*1024u+recent;}
static int phrase_slot_index(ZYLearning *l){
    int victim=-1;uint64_t best=UINT64_MAX;
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(!l->p.phrases[i].used&&!l->phrase_pending_flags[i])return (int)i;
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){if(l->phrase_pending_flags[i]&ZY_LEARN_PENDING_DELETE)continue;ZYLearnPhrase*r=&l->p.phrases[i];if(!r->used)continue;uint64_t s=phrase_retention_score(l,r);if(s<best){best=s;victim=(int)i;}}
    return victim;
}
int zy_learning_record_phrase(ZYLearning *l,const char *word,const char *query,const char *pron){
    if(!l||!word||!*word||!query||!*query)return -1;
    uint8_t kind=phrase_key_kind(pron);
    const char *key=phrase_input_key(query,pron);
    int pi=find_phrase_index_any(l,word,kind,key);
    if(pi<0){pi=phrase_slot_index(l);if(pi<0)return -2;memset(&l->p.phrases[pi],0,sizeof(l->p.phrases[pi]));l->phrase_pending_delta[pi]=0;l->phrase_pending_flags[pi]=ZY_LEARN_PENDING_DIRTY;safe_copy(l->p.phrases[pi].word,sizeof(l->p.phrases[pi].word),word);safe_copy(l->p.phrases[pi].key,sizeof(l->p.phrases[pi].key),key);l->p.phrases[pi].key_kind=kind;}
    ZYLearnPhrase *r=&l->p.phrases[pi];if(l->phrase_pending_flags[pi]&ZY_LEARN_PENDING_DELETE){l->phrase_pending_flags[pi]=(uint8_t)(ZY_LEARN_PENDING_DIRTY|ZY_LEARN_PENDING_REPLACE);l->phrase_pending_delta[pi]=0;r->count=0;r->used=1;}
    r->used=1;r->count=add_sat_u32(r->count,1);r->last=l->p.clock;l->phrase_pending_delta[pi]=add_sat_u32(l->phrase_pending_delta[pi],1);l->phrase_pending_flags[pi]|=ZY_LEARN_PENDING_DIRTY;l->dirty_mutations++;return 0;
}
uint32_t zy_learning_phrase_frequency_bonus(const ZYLearnPhrase *r){if(!r||!r->used)return 0;return capped_count(r->count,ZY_LEARN_PHRASE_FREQ_CAP)*ZY_LEARN_PHRASE_FREQ_STEP;}
uint32_t zy_learning_phrase_recency_bonus(const ZYLearning *l,const ZYLearnPhrase *r){if(!l||!r||!r->used)return 0;uint32_t age=event_age(l->p.clock,r->last);return age<ZY_LEARN_PHRASE_RECENCY_EVENTS?(ZY_LEARN_PHRASE_RECENCY_EVENTS-age)*ZY_LEARN_PHRASE_RECENCY_STEP:0;}
int zy_learning_should_flush(const ZYLearning *l,uint64_t now){if(!l||(!l->dirty_mutations&&!l->loaded_legacy_v1))return 0;if(l->dirty_mutations>=ZY_LEARN_FLUSH_MUTATIONS)return 1;return now>=l->last_flush_seconds+ZY_LEARN_FLUSH_SECONDS;}

static void slot_path(char *out,size_t cap,const char *base,char slot){snprintf(out,cap,"%s_%c.dat",base,slot);}
static void lock_path(char *out,size_t cap,const char *base){snprintf(out,cap,"%s.lock",base);}
static int write_all_at(int fd,const void *data,size_t n,int64_t off){
    const uint8_t *p=(const uint8_t*)data;size_t done=0;
    while(done<n){int64_t w=io_pwrite(fd,p+done,n-done,off+(int64_t)done);if(w<0){if(errno==EINTR)continue;return -1;}if(w==0)return -1;done+=(size_t)w;}
    return 0;
}
#ifdef _WIN32
static int lock_file(const char *base,ZYLockHandle *fd_out){
    char path[1024];lock_path(path,sizeof(path),base);int fd=_open(path,_O_RDWR|_O_CREAT|_O_BINARY,_S_IREAD|_S_IWRITE);if(fd<0)return -1;
    if(_lseeki64(fd,0,SEEK_SET)<0){_close(fd);return -2;}
    while(_locking(fd,_LK_LOCK,1)!=0){if(errno==EINTR)continue;_close(fd);return -2;}
    *fd_out=fd;return 0;
}
static void unlock_file(ZYLockHandle fd){if(fd<0)return;if(_lseeki64(fd,0,SEEK_SET)>=0)(void)_locking(fd,_LK_UNLCK,1);_close(fd);}
#else
static int lock_file(const char *base,ZYLockHandle *fd_out){
    char path[1024];lock_path(path,sizeof(path),base);int fd=open(path,O_RDWR|O_CREAT,0600);if(fd<0)return -1;
    struct flock fl;memset(&fl,0,sizeof(fl));fl.l_type=F_WRLCK;fl.l_whence=SEEK_SET;
    while(fcntl(fd,F_SETLKW,&fl)!=0){if(errno==EINTR)continue;io_close(fd);return -2;}
    *fd_out=fd;return 0;
}
static void unlock_file(ZYLockHandle fd){if(fd<0)return;struct flock fl;memset(&fl,0,sizeof(fl));fl.l_type=F_UNLCK;fl.l_whence=SEEK_SET;(void)fcntl(fd,F_SETLK,&fl);close(fd);}
#endif

static void migrate_v1(ZYLearningPersistent *out,const ZYLearningPersistentV1 *in){
    memset(out,0,sizeof(*out));out->clock=in->clock;
    for(size_t i=0;i<ZY_V1_WORD_CAP&&i<ZY_LEARN_WORD_CAP;i++)if(in->words[i].used){out->words[i].used=1;out->words[i].id=in->words[i].id;out->words[i].last=in->words[i].last;out->words[i].count=in->words[i].count;}
    for(size_t i=0;i<ZY_V1_QUERY_CAP&&i<ZY_LEARN_QUERY_CAP;i++)if(in->queries[i].used){out->queries[i].used=1;out->queries[i].hash=in->queries[i].hash;out->queries[i].id=in->queries[i].id;out->queries[i].last=in->queries[i].last;out->queries[i].count=in->queries[i].count;}
    for(size_t i=0;i<ZY_V1_PHRASE_CAP&&i<ZY_LEARN_PHRASE_CAP;i++)if(in->phrases[i].used){ZYLearnPhrase *d=&out->phrases[i];d->used=1;d->last=in->phrases[i].last;d->count=in->phrases[i].count;safe_copy_bounded(d->word,sizeof(d->word),in->phrases[i].word,sizeof(in->phrases[i].word));if(memchr(in->phrases[i].pron,0,sizeof(in->phrases[i].pron))&&in->phrases[i].pron[0]){d->key_kind=ZY_LEARN_PHRASE_KEY_PRON;safe_copy_bounded(d->key,sizeof(d->key),in->phrases[i].pron,sizeof(in->phrases[i].pron));}else{d->key_kind=ZY_LEARN_PHRASE_KEY_QUERY;safe_copy_bounded(d->key,sizeof(d->key),in->phrases[i].query,sizeof(in->phrases[i].query));}}
}
static int migrate_v2_payload(ZYLearningPersistent *out,const uint8_t *payload,size_t payload_bytes){
    if(payload_bytes<sizeof(ZYPayloadHeaderV23))return -1;
    ZYPayloadHeaderV23 ph;
    memcpy(&ph,payload,sizeof(ph));
    if(ph.word_count>ZY_LEARN_WORD_CAP||ph.query_count>ZY_LEARN_QUERY_CAP||ph.phrase_count>ZY_LEARN_PHRASE_CAP)return -1;
    size_t expected=sizeof(ph)+(size_t)ph.word_count*sizeof(ZYLearnWordV2)+(size_t)ph.query_count*sizeof(ZYLearnQueryV2)+(size_t)ph.phrase_count*sizeof(ZYLearnPhraseV2);if(expected!=payload_bytes)return -1;
    memset(out,0,sizeof(*out));out->clock=ph.clock;out->dictionary_fingerprint=ph.dictionary_fingerprint;out->reset_serial=ph.reset_serial;const uint8_t *cur=payload+sizeof(ph);
    for(uint32_t i=0;i<ph.word_count;i++){ZYLearnWordV2 s;memcpy(&s,cur,sizeof(s));cur+=sizeof(s);if(!s.used)continue;out->words[i].stable_key=s.stable_key;out->words[i].id=s.id;out->words[i].last=s.last;out->words[i].count=s.count;out->words[i].used=1;}
    for(uint32_t i=0;i<ph.query_count;i++){ZYLearnQueryV2 s;memcpy(&s,cur,sizeof(s));cur+=sizeof(s);if(!s.used)continue;out->queries[i].stable_key=s.stable_key;out->queries[i].hash=s.hash;out->queries[i].id=s.id;out->queries[i].last=s.last;out->queries[i].count=s.count;out->queries[i].used=1;}
    for(uint32_t i=0;i<ph.phrase_count;i++){ZYLearnPhraseV2 s;memcpy(&s,cur,sizeof(s));cur+=sizeof(s);if(!s.used)continue;if(!memchr(s.word,0,sizeof(s.word))||!memchr(s.query,0,sizeof(s.query))||!memchr(s.pron,0,sizeof(s.pron)))return -1;ZYLearnPhrase*d=&out->phrases[i];d->used=1;d->last=s.last;d->count=s.count;safe_copy_bounded(d->word,sizeof(d->word),s.word,sizeof(s.word));if(s.pron[0]){d->key_kind=ZY_LEARN_PHRASE_KEY_PRON;safe_copy_bounded(d->key,sizeof(d->key),s.pron,sizeof(s.pron));}else{d->key_kind=ZY_LEARN_PHRASE_KEY_QUERY;safe_copy_bounded(d->key,sizeof(d->key),s.query,sizeof(s.query));}}
    return 0;
}
static int read_slot_any(const char *path,ZYDiskSnapshot *out){
    int fd=io_open_read(path);if(fd<0)return -1;char magic[8];int64_t m=io_pread(fd,magic,sizeof(magic),0);if(m!=(int64_t)sizeof(magic)){io_close(fd);return -2;}
    if(memcmp(magic,ZY_LEARN_MAGIC_V3,8)==0||memcmp(magic,ZY_LEARN_MAGIC_V2,8)==0){
        int is_v3=memcmp(magic,ZY_LEARN_MAGIC_V3,8)==0;ZYSnapshotHeaderV23 h;int64_t a=io_pread(fd,&h,sizeof(h),0);uint32_t expected_version=is_v3?3u:2u;
        size_t phrase_size=is_v3?sizeof(ZYLearnPhrase):sizeof(ZYLearnPhraseV2);size_t max_payload=sizeof(ZYPayloadHeaderV23)+(size_t)ZY_LEARN_WORD_CAP*sizeof(ZYLearnWordV2)+(size_t)ZY_LEARN_QUERY_CAP*sizeof(ZYLearnQueryV2)+(size_t)ZY_LEARN_PHRASE_CAP*phrase_size;
        if(a!=(int64_t)sizeof(h)||h.version!=expected_version||h.payload_bytes<sizeof(ZYPayloadHeaderV23)||h.payload_bytes>max_payload){io_close(fd);return -2;}
        uint8_t *payload=(uint8_t*)malloc(h.payload_bytes);if(!payload){io_close(fd);return -4;}int64_t b=io_pread(fd,payload,h.payload_bytes,(int64_t)sizeof(h));io_close(fd);if(b!=(int64_t)h.payload_bytes||crc32_bytes(payload,h.payload_bytes)!=h.crc32){free(payload);return -3;}
        if(!is_v3){int rc=migrate_v2_payload(&out->p,payload,h.payload_bytes);free(payload);if(rc!=0)return -2;out->generation=h.generation;out->format_version=2;return 0;}
        ZYPayloadHeaderV23 ph;memcpy(&ph,payload,sizeof(ph));if(ph.word_count>ZY_LEARN_WORD_CAP||ph.query_count>ZY_LEARN_QUERY_CAP||ph.phrase_count>ZY_LEARN_PHRASE_CAP){free(payload);return -2;}
        size_t expected=sizeof(ph)+(size_t)ph.word_count*sizeof(ZYLearnWord)+(size_t)ph.query_count*sizeof(ZYLearnQuery)+(size_t)ph.phrase_count*sizeof(ZYLearnPhrase);if(expected!=h.payload_bytes){free(payload);return -2;}
        memset(&out->p,0,sizeof(out->p));out->p.clock=ph.clock;out->p.dictionary_fingerprint=ph.dictionary_fingerprint;out->p.reset_serial=ph.reset_serial;const uint8_t *cur=payload+sizeof(ph);
        if(ph.word_count){memcpy(out->p.words,cur,(size_t)ph.word_count*sizeof(ZYLearnWord));cur+=(size_t)ph.word_count*sizeof(ZYLearnWord);}if(ph.query_count){memcpy(out->p.queries,cur,(size_t)ph.query_count*sizeof(ZYLearnQuery));cur+=(size_t)ph.query_count*sizeof(ZYLearnQuery);}if(ph.phrase_count){memcpy(out->p.phrases,cur,(size_t)ph.phrase_count*sizeof(ZYLearnPhrase));}
        for(uint32_t i=0;i<ph.phrase_count;i++){ZYLearnPhrase*r=&out->p.phrases[i];if(r->used&&(!memchr(r->word,0,sizeof(r->word))||!memchr(r->key,0,sizeof(r->key))||r->key_kind>ZY_LEARN_PHRASE_KEY_PRON)){free(payload);return -2;}}
        free(payload);out->generation=h.generation;out->format_version=3;return 0;
    }
    if(memcmp(magic,ZY_LEARN_MAGIC_V1,8)==0){ZYSnapshotHeaderV1 h;int64_t a=io_pread(fd,&h,sizeof(h),0);if(a!=(int64_t)sizeof(h)||h.version!=1||h.payload_bytes!=sizeof(ZYLearningPersistentV1)){io_close(fd);return -2;}ZYLearningPersistentV1 *oldp=(ZYLearningPersistentV1*)malloc(sizeof(*oldp));if(!oldp){io_close(fd);return -4;}int64_t b=io_pread(fd,oldp,sizeof(*oldp),(int64_t)sizeof(h));io_close(fd);if(b!=(int64_t)sizeof(*oldp)||crc32_bytes(oldp,sizeof(*oldp))!=h.crc32){free(oldp);return -3;}migrate_v1(&out->p,oldp);free(oldp);out->generation=h.generation;out->format_version=1;return 0;}
    io_close(fd);return -2;
}
static int read_best(const char *base,ZYDiskSnapshot *out){
    if(!base||!out)return -1;
    char a[1024],b[1024];
    slot_path(a,sizeof(a),base,'A');
    slot_path(b,sizeof(b),base,'B');
    ZYDiskSnapshot *sa=(ZYDiskSnapshot*)calloc(1,sizeof(*sa)),*sb=(ZYDiskSnapshot*)calloc(1,sizeof(*sb));
    if(!sa||!sb){free(sa);free(sb);return -4;}
    int ra=read_slot_any(a,sa),rb=read_slot_any(b,sb);
    if(ra&&rb){free(sa);free(sb);return -2;}
    if(!ra&&(rb||sa->generation>=sb->generation))*out=*sa;
    else *out=*sb;
    free(sa);
    free(sb);
    return 0;
}

static ZYLearnWord *merge_find_word(ZYLearningPersistent *p,const ZYLearnWord *src){for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord*d=&p->words[i];if(d->used&&word_same_identity(d,src))return d;}return NULL;}
static ZYLearnWord *merge_word_slot(ZYLearningPersistent *p){for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(!p->words[i].used)return &p->words[i];ZYLearnWord*v=&p->words[0];for(size_t i=1;i<ZY_LEARN_WORD_CAP;i++)if(p->words[i].count<v->count||(p->words[i].count==v->count&&p->words[i].last<v->last))v=&p->words[i];return v;}
static void merge_remove_word(ZYLearningPersistent *p,const ZYLearnWord *src){for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord*d=&p->words[i];if(d->used&&word_same_identity(d,src))memset(d,0,sizeof(*d));}}
static ZYLearnQuery *merge_find_query(ZYLearningPersistent *p,const ZYLearnQuery *src){for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery*d=&p->queries[i];if(d->used&&query_same_identity(d,src))return d;}return NULL;}
static ZYLearnQuery *merge_query_slot(ZYLearningPersistent *p){for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++)if(!p->queries[i].used)return &p->queries[i];ZYLearnQuery*v=&p->queries[0];for(size_t i=1;i<ZY_LEARN_QUERY_CAP;i++)if(p->queries[i].count<v->count||(p->queries[i].count==v->count&&p->queries[i].last<v->last))v=&p->queries[i];return v;}
static void merge_remove_query(ZYLearningPersistent *p,const ZYLearnQuery *src){for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery*d=&p->queries[i];if(d->used&&query_same_identity(d,src))memset(d,0,sizeof(*d));}}
static ZYLearnPhrase *merge_find_phrase(ZYLearningPersistent *p,const ZYLearnPhrase *src){for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){ZYLearnPhrase*d=&p->phrases[i];if(d->used&&phrase_same_row(d,src))return d;}return NULL;}
static ZYLearnPhrase *merge_phrase_slot(ZYLearningPersistent *p){for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(!p->phrases[i].used)return &p->phrases[i];ZYLearnPhrase*v=&p->phrases[0];for(size_t i=1;i<ZY_LEARN_PHRASE_CAP;i++)if(p->phrases[i].count<v->count||(p->phrases[i].count==v->count&&p->phrases[i].last<v->last))v=&p->phrases[i];return v;}
static void merge_remove_phrase(ZYLearningPersistent *p,const ZYLearnPhrase *src){for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){ZYLearnPhrase*d=&p->phrases[i];if(d->used&&phrase_same_row(d,src))memset(d,0,sizeof(*d));}}

static void replay_pending(const ZYLearning *l,ZYLearningPersistent *dst){
    dst->clock=add_sat_u32(dst->clock,l->pending_clock_delta);if(l->dictionary_fingerprint_dirty)dst->dictionary_fingerprint=l->p.dictionary_fingerprint;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){uint8_t f=l->word_pending_flags[i];if(!f)continue;const ZYLearnWord*s=&l->p.words[i];if(f&ZY_LEARN_PENDING_DELETE){merge_remove_word(dst,s);continue;}if(f&ZY_LEARN_PENDING_REPLACE)merge_remove_word(dst,s);ZYLearnWord*d=merge_find_word(dst,s);if(!d){d=merge_word_slot(dst);memset(d,0,sizeof(*d));d->used=1;d->id=s->id;d->stable_key=s->stable_key;}if((f&ZY_LEARN_PENDING_META)&&s->stable_key)d->stable_key=s->stable_key;if(s->id!=ZY_LEARN_INVALID_WORD_ID)d->id=s->id;if(l->word_pending_delta[i])d->count=add_sat_u32(d->count,l->word_pending_delta[i]);d->last=dst->clock;}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){uint8_t f=l->query_pending_flags[i];if(!f)continue;const ZYLearnQuery*s=&l->p.queries[i];if(f&ZY_LEARN_PENDING_DELETE){merge_remove_query(dst,s);continue;}if(f&ZY_LEARN_PENDING_REPLACE)merge_remove_query(dst,s);ZYLearnQuery*d=merge_find_query(dst,s);if(!d){d=merge_query_slot(dst);memset(d,0,sizeof(*d));d->used=1;d->hash=s->hash;d->id=s->id;d->stable_key=s->stable_key;}if((f&ZY_LEARN_PENDING_META)&&s->stable_key)d->stable_key=s->stable_key;if(s->id!=ZY_LEARN_INVALID_WORD_ID)d->id=s->id;if(l->query_pending_delta[i])d->count=add_sat_u32(d->count,l->query_pending_delta[i]);d->last=dst->clock;}
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){uint8_t f=l->phrase_pending_flags[i];if(!f)continue;const ZYLearnPhrase*s=&l->p.phrases[i];if(f&ZY_LEARN_PENDING_DELETE){merge_remove_phrase(dst,s);continue;}if(f&ZY_LEARN_PENDING_REPLACE)merge_remove_phrase(dst,s);ZYLearnPhrase*d=merge_find_phrase(dst,s);if(!d){d=merge_phrase_slot(dst);memset(d,0,sizeof(*d));d->used=1;d->key_kind=s->key_kind;safe_copy(d->word,sizeof(d->word),s->word);safe_copy(d->key,sizeof(d->key),s->key);}if(l->phrase_pending_delta[i])d->count=add_sat_u32(d->count,l->phrase_pending_delta[i]);d->last=dst->clock;}
}

static int write_snapshot_path(const char *path,const ZYLearningPersistent *p,uint64_t generation,int force_sync){
    uint32_t wc=0,qc=0,pc=0;for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(p->words[i].used)wc++;for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++)if(p->queries[i].used)qc++;for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(p->phrases[i].used)pc++;
    size_t payload_size=sizeof(ZYPayloadHeaderV23)+(size_t)wc*sizeof(ZYLearnWord)+(size_t)qc*sizeof(ZYLearnQuery)+(size_t)pc*sizeof(ZYLearnPhrase);if(payload_size>UINT32_MAX)return -6;uint8_t *payload=(uint8_t*)calloc(1,payload_size);if(!payload)return -5;
    ZYPayloadHeaderV23 ph;memset(&ph,0,sizeof(ph));ph.clock=p->clock;ph.dictionary_fingerprint=p->dictionary_fingerprint;ph.reset_serial=p->reset_serial;ph.word_count=wc;ph.query_count=qc;ph.phrase_count=pc;memcpy(payload,&ph,sizeof(ph));uint8_t *cur=payload+sizeof(ph);
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(p->words[i].used){memcpy(cur,&p->words[i],sizeof(ZYLearnWord));cur+=sizeof(ZYLearnWord);}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++)if(p->queries[i].used){memcpy(cur,&p->queries[i],sizeof(ZYLearnQuery));cur+=sizeof(ZYLearnQuery);}
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(p->phrases[i].used){memcpy(cur,&p->phrases[i],sizeof(ZYLearnPhrase));cur+=sizeof(ZYLearnPhrase);}
    char tmp[1200];snprintf(tmp,sizeof(tmp),"%s.tmp.%ld",path,io_pid());int fd=io_open_write(tmp);if(fd<0){free(payload);return -2;}ZYSnapshotHeaderV23 h;memset(&h,0,sizeof(h));memcpy(h.magic,ZY_LEARN_MAGIC_V3,8);h.version=3;h.payload_bytes=(uint32_t)payload_size;h.generation=generation;h.crc32=crc32_bytes(payload,payload_size);int rc=write_all_at(fd,&h,sizeof(h),0);if(rc==0)rc=write_all_at(fd,payload,payload_size,(int64_t)sizeof(h));if(rc==0&&io_sync(fd)!=0)rc=-3;io_close(fd);free(payload);if(rc==0&&io_replace(tmp,path)!=0)rc=-4;if(rc!=0)io_unlink(tmp);if(rc==0&&force_sync){
#ifndef _WIN32
        char dir[1200];snprintf(dir,sizeof(dir),"%s",path);char *slash=strrchr(dir,'/');if(slash){*slash=0;int dfd=open(dir[0]?dir:"/",O_RDONLY);if(dfd>=0){(void)fsync(dfd);close(dfd);}}
#else
        (void)force_sync;
#endif
    }return rc;
}

int zy_learning_save(ZYLearning *l,const char *base,uint64_t now,int force_sync){
    if(!l||!base)return -1;
    if(!l->dirty_mutations&&!l->loaded_legacy_v1)return 0;
    ZYLockHandle lockfd=ZY_INVALID_LOCK;
    if(lock_file(base,&lockfd)!=0)return -2;
    ZYDiskSnapshot *disk=(ZYDiskSnapshot*)calloc(1,sizeof(*disk));ZYLearningPersistent *merged=(ZYLearningPersistent*)calloc(1,sizeof(*merged));if(!disk||!merged){free(disk);free(merged);unlock_file(lockfd);return -5;}
    int have_disk=read_best(base,disk)==0;if(have_disk)*merged=disk->p;else *merged=l->p;
    /* A full clear performed by another process wins over stale pending data.
       On the very first save there is no disk baseline, so l->p already is the
       complete state and must not receive its own deltas a second time. */
    if(have_disk&&disk->p.reset_serial>l->loaded_reset_serial){*merged=disk->p;clear_pending(l);l->dirty_mutations=0;}else if(have_disk)replay_pending(l,merged);
    uint64_t base_generation=have_disk&&disk->generation>l->generation?disk->generation:l->generation;uint64_t next=base_generation+1;char path[1024];slot_path(path,sizeof(path),base,(next&1)?'A':'B');int rc=write_snapshot_path(path,merged,next,force_sync);
    if(rc==0){l->p=*merged;l->generation=next;l->loaded_reset_serial=merged->reset_serial;l->dirty_mutations=0;l->loaded_legacy_v1=0;l->last_flush_seconds=now;clear_pending(l);}free(disk);free(merged);unlock_file(lockfd);return rc;
}
int zy_learning_load(ZYLearning *l,const char *base){
    if(!l||!base)return -1;
    ZYDiskSnapshot *s=(ZYDiskSnapshot*)calloc(1,sizeof(*s));
    if(!s)return -4;
    int rc=read_best(base,s);
    if(rc!=0){free(s);return rc;}
    uint64_t last_flush=l->last_flush_seconds;
    l->p=s->p;
    l->generation=s->generation;
    l->loaded_reset_serial=s->p.reset_serial;
    l->dirty_mutations=0;
    l->loaded_legacy_v1=(uint8_t)(s->format_version<3?1:0);
    clear_pending(l);
    l->last_flush_seconds=last_flush;
    free(s);
    return 0;
}
int zy_learning_clear_persistent(ZYLearning *l,const char *base,uint64_t now){
    if(!l||!base)return -1;
    ZYLockHandle lockfd=ZY_INVALID_LOCK;
    if(lock_file(base,&lockfd)!=0)return -2;
    ZYDiskSnapshot *disk=(ZYDiskSnapshot*)calloc(1,sizeof(*disk));
    ZYLearningPersistent *empty=(ZYLearningPersistent*)calloc(1,sizeof(*empty));
    if(!disk||!empty){free(disk);free(empty);unlock_file(lockfd);return -5;}
    uint64_t generation=l->generation;
    uint64_t reset=l->p.reset_serial;
    if(read_best(base,disk)==0){if(disk->generation>generation)generation=disk->generation;if(disk->p.reset_serial>reset)reset=disk->p.reset_serial;}
    empty->dictionary_fingerprint=l->p.dictionary_fingerprint;
    empty->reset_serial=reset+1;
    char a[1024],b[1024];
    slot_path(a,sizeof(a),base,'A');
    slot_path(b,sizeof(b),base,'B');
    int rc=write_snapshot_path(a,empty,generation+1,1);
    if(rc==0)rc=write_snapshot_path(b,empty,generation+2,1);
    if(rc==0){l->p=*empty;l->generation=generation+2;l->loaded_reset_serial=empty->reset_serial;l->dirty_mutations=0;l->loaded_legacy_v1=0;l->last_flush_seconds=now;clear_pending(l);}
    free(disk);
    free(empty);
    unlock_file(lockfd);
    return rc;
}
