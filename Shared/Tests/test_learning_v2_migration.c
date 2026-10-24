#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "ZYLearning.h"

#define V1_WORD_CAP 256
#define V1_QUERY_CAP 128
#define V1_PHRASE_CAP 128
#define V1_WORD_BYTES 96
#define V1_QUERY_BYTES 192
#define V1_PRON_BYTES 256

typedef struct { uint32_t id,last; uint8_t count,used; uint16_t reserved; } WordV1;
typedef struct { uint32_t hash,id,last; uint8_t count,used; uint16_t reserved; } QueryV1;
typedef struct { uint32_t last; uint8_t count,used; uint16_t reserved; char word[V1_WORD_BYTES],query[V1_QUERY_BYTES],pron[V1_PRON_BYTES]; } PhraseV1;
typedef struct { uint32_t clock; WordV1 words[V1_WORD_CAP]; QueryV1 queries[V1_QUERY_CAP]; PhraseV1 phrases[V1_PHRASE_CAP]; } PersistV1;
typedef struct { char magic[8]; uint32_t version,generation,payload_bytes,crc32; } HeaderV1;

typedef struct { uint64_t stable_key; uint32_t id,last,count; uint8_t used; uint8_t reserved[3]; } WordV2;
typedef struct { uint64_t stable_key; uint32_t hash,id,last,count; uint8_t used; uint8_t reserved[3]; } QueryV2;
typedef struct { uint32_t last,count; uint8_t used; uint8_t reserved[3]; char word[128],query[256],pron[512]; } PhraseV2;
typedef struct { char magic[8]; uint32_t version,payload_bytes; uint64_t generation; uint32_t crc32,reserved; } HeaderV2;
typedef struct { uint32_t clock,reserved; uint64_t dictionary_fingerprint,reset_serial; uint32_t word_count,query_count,phrase_count,reserved2; } PayloadV2;

static uint32_t crc32_bytes(const void *data,size_t n){
    const uint8_t *p=(const uint8_t*)data; uint32_t c=0xffffffffu;
    for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(int32_t)(c&1));}
    return ~c;
}
static void cleanup(const char *base){char p[1024];for(const char*s[]={"_A.dat","_B.dat",".lock",NULL},**x=s;*x;x++){snprintf(p,sizeof(p),"%s%s",base,*x);unlink(p);}}
static void write_v1(const char *base){
    PersistV1 p;memset(&p,0,sizeof(p));p.clock=44;p.words[0].used=1;p.words[0].id=42;p.words[0].count=19;p.words[0].last=40;
    p.queries[0].used=1;p.queries[0].hash=1234;p.queries[0].id=42;p.queries[0].count=7;p.queries[0].last=40;
    p.phrases[0].used=1;p.phrases[0].count=3;p.phrases[0].last=41;strcpy(p.phrases[0].word,"逐音輸入法");strcpy(p.phrases[0].query,"ㄓㄨˊㄧㄣ");strcpy(p.phrases[0].pron,"ㄓㄨˊ\x1fㄧㄣ");
    HeaderV1 h;memset(&h,0,sizeof(h));memcpy(h.magic,"ZYLEARN1",8);h.version=1;h.generation=7;h.payload_bytes=(uint32_t)sizeof(p);h.crc32=crc32_bytes(&p,sizeof(p));
    char path[1024];snprintf(path,sizeof(path),"%s_A.dat",base);int fd=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);assert(fd>=0);assert(write(fd,&h,sizeof(h))==(ssize_t)sizeof(h));assert(write(fd,&p,sizeof(p))==(ssize_t)sizeof(p));close(fd);
}
static int has_magic(const char *path,const char *magic){char m[8]={0};int fd=open(path,O_RDONLY);if(fd<0)return 0;ssize_t n=read(fd,m,8);close(fd);return n==8&&memcmp(m,magic,8)==0;}
static void write_v1_unterminated(const char *base){
    PersistV1 p;memset(&p,0,sizeof(p));p.clock=50;PhraseV1 *r=&p.phrases[V1_PHRASE_CAP-1];r->used=1;r->count=1;r->last=50;
    memset(r->word,'a',sizeof(r->word));memset(r->query,'b',sizeof(r->query));memset(r->pron,'c',sizeof(r->pron));
    HeaderV1 h;memset(&h,0,sizeof(h));memcpy(h.magic,"ZYLEARN1",8);h.version=1;h.generation=3;h.payload_bytes=(uint32_t)sizeof(p);h.crc32=crc32_bytes(&p,sizeof(p));
    char path[1024];snprintf(path,sizeof(path),"%s_A.dat",base);int fd=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);assert(fd>=0);assert(write(fd,&h,sizeof(h))==(ssize_t)sizeof(h));assert(write(fd,&p,sizeof(p))==(ssize_t)sizeof(p));close(fd);
}

static void write_v2(const char *base){
    PayloadV2 ph;memset(&ph,0,sizeof(ph));ph.clock=88;ph.dictionary_fingerprint=0xabcddcbaULL;ph.word_count=1;ph.query_count=1;ph.phrase_count=2;
    WordV2 w;memset(&w,0,sizeof(w));w.used=1;w.id=42;w.stable_key=0x424242ULL;w.count=11;w.last=80;
    QueryV2 q;memset(&q,0,sizeof(q));q.used=1;q.id=42;q.hash=1234;q.stable_key=0x424242ULL;q.count=5;q.last=81;
    PhraseV2 p[2];memset(p,0,sizeof(p));
    p[0].used=1;p[0].count=3;p[0].last=82;strcpy(p[0].word,"逐音輸入法");strcpy(p[0].query,"ㄓㄨˊㄧㄣ");strcpy(p[0].pron,"ㄓㄨˊ\x1fㄧㄣ");
    p[1].used=1;p[1].count=2;p[1].last=83;strcpy(p[1].word,"測試");strcpy(p[1].query,"ㄘㄕ");p[1].pron[0]=0;
    size_t payload_bytes=sizeof(ph)+sizeof(w)+sizeof(q)+sizeof(p);unsigned char *payload=calloc(1,payload_bytes);assert(payload);unsigned char *cur=payload;memcpy(cur,&ph,sizeof(ph));cur+=sizeof(ph);memcpy(cur,&w,sizeof(w));cur+=sizeof(w);memcpy(cur,&q,sizeof(q));cur+=sizeof(q);memcpy(cur,p,sizeof(p));
    HeaderV2 h;memset(&h,0,sizeof(h));memcpy(h.magic,"ZYLEARN2",8);h.version=2;h.payload_bytes=(uint32_t)payload_bytes;h.generation=9;h.crc32=crc32_bytes(payload,payload_bytes);
    char path[1024];snprintf(path,sizeof(path),"%s_A.dat",base);int fd=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);assert(fd>=0);assert(write(fd,&h,sizeof(h))==(ssize_t)sizeof(h));assert(write(fd,payload,payload_bytes)==(ssize_t)payload_bytes);close(fd);free(payload);
}

int main(int argc,char **argv){
    assert(argc==2);const char *base=argv[1];cleanup(base);write_v1(base);
    ZYLearning *l=(ZYLearning*)calloc(1,sizeof(*l));assert(l);zy_learning_init(l,1000);assert(zy_learning_load(l,base)==0);assert(l->loaded_legacy_v1==1);assert(l->generation==7);assert(zy_learning_word_count(l,42)==19);assert(zy_learning_query_bonus(l,1234,42)>0);
    zy_learning_bind_word_identity(l,42,0x123456789abcdef0ULL);zy_learning_set_dictionary_fingerprint(l,0x5555ULL);assert(zy_learning_save(l,base,1001,1)==0);assert(l->generation==8);assert(l->loaded_legacy_v1==0);
    char a[1024],b[1024];snprintf(a,sizeof(a),"%s_A.dat",base);snprintf(b,sizeof(b),"%s_B.dat",base);assert(has_magic(a,"ZYLEARN1"));assert(has_magic(b,"ZYLEARN3"));
    ZYLearning *r=(ZYLearning*)calloc(1,sizeof(*r));assert(r);zy_learning_init(r,1002);assert(zy_learning_load(r,base)==0);assert(r->generation==8);assert(zy_learning_word_count(r,42)==19);assert(r->p.words[0].stable_key==0x123456789abcdef0ULL);assert(r->p.dictionary_fingerprint==0x5555ULL);
    assert(zy_learning_clear_persistent(r,base,1003)==0);ZYLearning *z=(ZYLearning*)calloc(1,sizeof(*z));assert(z);zy_learning_init(z,1004);assert(zy_learning_load(z,base)==0);assert(zy_learning_word_count(z,42)==0);assert(z->p.reset_serial>0);
    free(l);free(r);free(z);cleanup(base);

    /* Legacy fixed-width strings may be malformed and contain no NUL. Migration
       must stay within the legacy field boundary and still produce terminated v2 strings. */
    write_v1_unterminated(base);ZYLearning *u=(ZYLearning*)calloc(1,sizeof(*u));assert(u);zy_learning_init(u,1005);assert(zy_learning_load(u,base)==0);
    const ZYLearnPhrase *up=NULL;for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(u->p.phrases[i].used){up=&u->p.phrases[i];break;}
    assert(up);assert(memchr(up->word,0,sizeof(up->word)));assert(memchr(up->key,0,sizeof(up->key)));free(u);

    /* A real compact ZYLEARN2 snapshot upgrades without losing stable IDs or
       either learned-phrase matching mode. */
    cleanup(base);write_v2(base);ZYLearning *v2=(ZYLearning*)calloc(1,sizeof(*v2));assert(v2);zy_learning_init(v2,1100);assert(zy_learning_load(v2,base)==0);assert(v2->loaded_legacy_v1==1);assert(v2->generation==9);assert(zy_learning_word_count(v2,42)==11);assert(v2->p.dictionary_fingerprint==0xabcddcbaULL);
    const ZYLearnPhrase *pron_phrase=NULL,*query_phrase=NULL;for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++)if(v2->p.phrases[i].used){if(strcmp(v2->p.phrases[i].word,"逐音輸入法")==0)pron_phrase=&v2->p.phrases[i];if(strcmp(v2->p.phrases[i].word,"測試")==0)query_phrase=&v2->p.phrases[i];}
    assert(pron_phrase&&pron_phrase->key_kind==ZY_LEARN_PHRASE_KEY_PRON&&strcmp(pron_phrase->key,"ㄓㄨˊ\x1fㄧㄣ")==0);assert(query_phrase&&query_phrase->key_kind==ZY_LEARN_PHRASE_KEY_QUERY&&strcmp(query_phrase->key,"ㄘㄕ")==0);
    assert(zy_learning_save(v2,base,1101,1)==0);snprintf(b,sizeof(b),"%s_B.dat",base);assert(has_magic(b,"ZYLEARN3"));free(v2);
    cleanup(base);puts("test_learning_v2_migration: OK");return 0;
}
