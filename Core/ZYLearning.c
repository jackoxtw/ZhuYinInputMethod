#include "ZYLearning.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define ZY_LEARN_MAGIC "ZYLEARN1"
typedef struct {
    char magic[8]; uint32_t version,generation,payload_bytes,crc32;
} ZYSnapshotHeader;

static uint32_t crc32_bytes(const void *data,size_t n){
    const uint8_t *p=(const uint8_t*)data; uint32_t c=0xffffffffu;
    for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(int32_t)(c&1));}
    return ~c;
}
static void safe_copy(char *dst,size_t cap,const char *src){if(!cap)return;size_t n=src?strlen(src):0;if(n>=cap)n=cap-1;if(n)memcpy(dst,src,n);dst[n]=0;}
void zy_learning_init(ZYLearning *l,uint64_t now){memset(l,0,sizeof(*l));l->last_flush_seconds=now;}
void zy_learning_reset(ZYLearning *l,uint64_t now){if(!l)return;zy_learning_init(l,now);}
void zy_learning_begin_event(ZYLearning *l){if(!l)return;l->p.clock++;l->dirty_mutations++;}
static uint32_t event_age(uint32_t clock,uint32_t last){return clock-last;}
static uint32_t capped_count(uint32_t count,uint32_t cap){return count<cap?count:cap;}

static ZYLearnWord *find_word(ZYLearning *l,uint32_t id){for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(l->p.words[i].used&&l->p.words[i].id==id)return &l->p.words[i];return NULL;}
static ZYLearnWord *word_slot(ZYLearning *l){
    ZYLearnWord *victim=&l->p.words[0];
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){if(!l->p.words[i].used)return &l->p.words[i];if(l->p.words[i].last<victim->last)victim=&l->p.words[i];}
    return victim;
}
static ZYLearnQuery *query_slot(ZYLearning *l,uint32_t hash){
    ZYLearnQuery *victim=&l->p.queries[0];
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){
        ZYLearnQuery *q=&l->p.queries[i];
        if(q->used&&q->hash==hash)return q;
        if(!q->used)return q;
        if(q->last<victim->last)victim=q;
    }
    return victim;
}
void zy_learning_record_word(ZYLearning *l,uint32_t id,uint32_t query_hash){
    if(!l)return;
    ZYLearnWord *r=find_word(l,id);
    if(!r){r=word_slot(l);memset(r,0,sizeof(*r));r->id=id;r->used=1;}
    if(r->count<255)r->count++;r->last=l->p.clock;
    if(query_hash){
        ZYLearnQuery *q=query_slot(l,query_hash);
        if(!q->used||q->hash!=query_hash||q->id!=id){memset(q,0,sizeof(*q));q->used=1;q->hash=query_hash;q->id=id;}
        if(q->count<255)q->count++;q->last=l->p.clock;
    }
    l->dirty_mutations++;
}
int zy_learning_remove_word(ZYLearning *l,uint32_t id,uint32_t query_hash){
    if(!l)return 0;int removed=0;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(l->p.words[i].used&&l->p.words[i].id==id){memset(&l->p.words[i],0,sizeof(l->p.words[i]));removed=1;}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++)if(l->p.queries[i].used&&l->p.queries[i].id==id&&(!query_hash||l->p.queries[i].hash==query_hash)){memset(&l->p.queries[i],0,sizeof(l->p.queries[i]));removed=1;}
    if(removed)l->dirty_mutations++;return removed;
}
int zy_learning_remove_phrase_slot(ZYLearning *l,uint32_t slot){if(!l||slot>=ZY_LEARN_PHRASE_CAP||!l->p.phrases[slot].used)return 0;memset(&l->p.phrases[slot],0,sizeof(l->p.phrases[slot]));l->dirty_mutations++;return 1;}
uint32_t zy_learning_word_count(const ZYLearning *l,uint32_t id){if(!l)return 0;for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++)if(l->p.words[i].used&&l->p.words[i].id==id)return l->p.words[i].count;return 0;}
uint32_t zy_learning_word_frequency_bonus(const ZYLearning *l,uint32_t id){
    return capped_count(zy_learning_word_count(l,id),ZY_LEARN_WORD_FREQ_CAP)*ZY_LEARN_WORD_FREQ_STEP;
}
uint32_t zy_learning_word_recency_bonus(const ZYLearning *l,uint32_t id){
    if(!l)return 0;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){
        const ZYLearnWord *r=&l->p.words[i];if(!r->used||r->id!=id)continue;
        uint32_t age=event_age(l->p.clock,r->last);
        return age<ZY_LEARN_WORD_RECENCY_EVENTS?(ZY_LEARN_WORD_RECENCY_EVENTS-age)*ZY_LEARN_WORD_RECENCY_STEP:0;
    }
    return 0;
}
uint32_t zy_learning_query_bonus(const ZYLearning *l,uint32_t hash,uint32_t id){
    if(!l||!hash)return 0;
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){const ZYLearnQuery*q=&l->p.queries[i];if(q->used&&q->hash==hash&&q->id==id)return capped_count(q->count,ZY_LEARN_QUERY_FREQ_CAP)*ZY_LEARN_QUERY_FREQ_STEP;}
    return 0;
}
uint8_t zy_learning_query_preference_rank(const ZYLearning *l,uint32_t hash,uint32_t id){
    if(!l||!hash)return 0;
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){
        const ZYLearnQuery*q=&l->p.queries[i];
        if(q->used&&q->hash==hash&&q->id==id&&event_age(l->p.clock,q->last)<=ZY_LEARN_QUERY_PREFERRED_EVENTS)return 2;
    }
    return 0;
}

static ZYLearnPhrase *find_phrase(ZYLearning *l,const char *word,const char *pron){for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){ZYLearnPhrase *r=&l->p.phrases[i];if(r->used&&strcmp(r->word,word)==0&&strcmp(r->pron,pron?pron:"")==0)return r;}return NULL;}
static ZYLearnPhrase *phrase_slot(ZYLearning *l){ZYLearnPhrase *v=&l->p.phrases[0];for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++){if(!l->p.phrases[i].used)return &l->p.phrases[i];if(l->p.phrases[i].last<v->last)v=&l->p.phrases[i];}return v;}
int zy_learning_record_phrase(ZYLearning *l,const char *word,const char *query,const char *pron){if(!l||!word||!*word||!query||!*query)return -1;ZYLearnPhrase *r=find_phrase(l,word,pron);if(!r){r=phrase_slot(l);memset(r,0,sizeof(*r));r->used=1;safe_copy(r->word,sizeof(r->word),word);safe_copy(r->query,sizeof(r->query),query);safe_copy(r->pron,sizeof(r->pron),pron?pron:"");}if(r->count<255)r->count++;r->last=l->p.clock;l->dirty_mutations++;return 0;}
uint32_t zy_learning_phrase_frequency_bonus(const ZYLearnPhrase *r){if(!r||!r->used)return 0;return capped_count(r->count,ZY_LEARN_PHRASE_FREQ_CAP)*ZY_LEARN_PHRASE_FREQ_STEP;}
uint32_t zy_learning_phrase_recency_bonus(const ZYLearning *l,const ZYLearnPhrase *r){if(!l||!r||!r->used)return 0;uint32_t age=event_age(l->p.clock,r->last);return age<ZY_LEARN_PHRASE_RECENCY_EVENTS?(ZY_LEARN_PHRASE_RECENCY_EVENTS-age)*ZY_LEARN_PHRASE_RECENCY_STEP:0;}
int zy_learning_should_flush(const ZYLearning *l,uint64_t now){if(!l||!l->dirty_mutations)return 0;if(l->dirty_mutations>=ZY_LEARN_FLUSH_MUTATIONS)return 1;return now>=l->last_flush_seconds+ZY_LEARN_FLUSH_SECONDS;}

static void slot_path(char *out,size_t cap,const char *base,char slot){snprintf(out,cap,"%s_%c.dat",base,slot);}
static int write_all_at(int fd,const void *data,size_t n,off_t off){const uint8_t *p=data;size_t done=0;while(done<n){ssize_t w=pwrite(fd,p+done,n-done,off+(off_t)done);if(w<0){if(errno==EINTR)continue;return -1;}done+=(size_t)w;}return 0;}
int zy_learning_save(ZYLearning *l,const char *base,uint64_t now,int force_sync){
    if(!l||!base)return -1;if(!l->dirty_mutations)return 0;uint32_t next=l->generation+1;char path[1024];slot_path(path,sizeof(path),base,(next&1)?'A':'B');
    int fd=open(path,O_WRONLY|O_CREAT,0600);if(fd<0)return -2;ZYSnapshotHeader h={{0},1,next,(uint32_t)sizeof(l->p),crc32_bytes(&l->p,sizeof(l->p))};memcpy(h.magic,ZY_LEARN_MAGIC,8);
    int rc=write_all_at(fd,&h,sizeof(h),0);if(rc==0)rc=write_all_at(fd,&l->p,sizeof(l->p),(off_t)sizeof(h));if(rc==0&&force_sync&&fsync(fd)!=0)rc=-3;close(fd);if(rc!=0)return rc;l->generation=next;l->dirty_mutations=0;l->last_flush_seconds=now;return 0;
}
static int read_slot(const char *path,uint32_t *gen,ZYLearningPersistent *p){int fd=open(path,O_RDONLY);if(fd<0)return -1;ZYSnapshotHeader h;ssize_t a=pread(fd,&h,sizeof(h),0);if(a!=(ssize_t)sizeof(h)||memcmp(h.magic,ZY_LEARN_MAGIC,8)!=0||h.version!=1||h.payload_bytes!=sizeof(*p)){close(fd);return -2;}ssize_t b=pread(fd,p,sizeof(*p),(off_t)sizeof(h));close(fd);if(b!=(ssize_t)sizeof(*p)||crc32_bytes(p,sizeof(*p))!=h.crc32)return -3;*gen=h.generation;return 0;}
int zy_learning_load(ZYLearning *l,const char *base){if(!l||!base)return -1;char a[1024],b[1024];slot_path(a,sizeof(a),base,'A');slot_path(b,sizeof(b),base,'B');ZYLearningPersistent pa,pb;uint32_t ga=0,gb=0;int ra=read_slot(a,&ga,&pa),rb=read_slot(b,&gb,&pb);if(ra&&rb)return -2;if(!ra&&(rb||ga>=gb)){l->p=pa;l->generation=ga;}else{l->p=pb;l->generation=gb;}l->dirty_mutations=0;return 0;}
