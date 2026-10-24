#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "ZYLearning.h"

static int valid_utf8(const unsigned char *s){
    while(*s){
        if(*s<0x80){s++;continue;}
        size_t n=0;
        if((*s&0xE0)==0xC0)n=2;
        else if((*s&0xF0)==0xE0)n=3;
        else if((*s&0xF8)==0xF0)n=4;
        else return 0;
        for(size_t i=1;i<n;i++) if((s[i]&0xC0)!=0x80) return 0;
        s+=n;
    }
    return 1;
}

static void clean_base(const char *base){
    char p[1024];
    for(const char *suffixes[]={"_A.dat","_B.dat",".lock",NULL}, **s=suffixes; *s; ++s){
        snprintf(p,sizeof(p),"%s%s",base,*s); unlink(p);
    }
}

int main(int argc,char **argv){
    assert(argc==2); const char *base=argv[1]; clean_base(base);

    /* Same query must retain history for more than one candidate. */
    ZYLearning *q=calloc(1,sizeof(*q)); assert(q); zy_learning_init(q,1000);
    zy_learning_begin_event(q); zy_learning_record_word(q,42,1234);
    zy_learning_begin_event(q); zy_learning_record_word(q,77,1234);
    assert(zy_learning_query_bonus(q,1234,42)>0);
    assert(zy_learning_query_bonus(q,1234,77)>0); free(q);

    /* Learning more than the legacy 256-word capacity must not evict ordinary
       historical words immediately. */
    ZYLearning *many=calloc(1,sizeof(*many)); assert(many); zy_learning_init(many,1000);
    for(uint32_t id=1; id<=300; ++id){zy_learning_begin_event(many); zy_learning_record_word(many,id,100000u+id);}
    assert(zy_learning_word_count(many,1)==1);
    assert(zy_learning_word_count(many,300)==1); free(many);

    /* Lifetime counts are not allowed to saturate at uint8_t/255. */
    ZYLearning *counts=calloc(1,sizeof(*counts)); assert(counts); zy_learning_init(counts,1000);
    for(int i=0;i<300;i++){zy_learning_begin_event(counts); zy_learning_record_word(counts,9,999);}
    assert(zy_learning_word_count(counts,9)==300); free(counts);

    /* Truncating a long UTF-8 learned phrase must stop at a character boundary. */
    ZYLearning *utf=calloc(1,sizeof(*utf)); assert(utf); zy_learning_init(utf,1000); zy_learning_begin_event(utf);
    const char *long_word="測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試測試";
    assert(zy_learning_record_phrase(utf,long_word,"ㄘㄜˋㄕˋ","ㄘㄜˋㄕˋ")==0);
    const ZYLearnPhrase *stored=NULL;
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++) if(utf->p.phrases[i].used){stored=&utf->p.phrases[i];break;}
    assert(stored && valid_utf8((const unsigned char*)stored->word)); assert(memchr(stored->key,0,sizeof(stored->key))); free(utf);

    /* Two stale processes must merge distinct learning instead of last-writer-wins. */
    ZYLearning *seed=calloc(1,sizeof(*seed)), *a=calloc(1,sizeof(*a)), *b=calloc(1,sizeof(*b)), *merged=calloc(1,sizeof(*merged)); assert(seed&&a&&b&&merged);
    zy_learning_init(seed,1000); zy_learning_begin_event(seed); zy_learning_record_word(seed,1,1); assert(zy_learning_save(seed,base,1001,1)==0);
    char first_slot[1024];snprintf(first_slot,sizeof(first_slot),"%s_A.dat",base);struct stat compact_st;assert(stat(first_slot,&compact_st)==0);assert(compact_st.st_size<65536);
    zy_learning_init(a,1002); zy_learning_init(b,1002);
    assert(zy_learning_load(a,base)==0); assert(zy_learning_load(b,base)==0);
    zy_learning_begin_event(a); zy_learning_record_word(a,1001,1111); assert(zy_learning_save(a,base,1003,1)==0);
    zy_learning_begin_event(b); zy_learning_record_word(b,2002,2222); assert(zy_learning_save(b,base,1004,1)==0);
    zy_learning_init(merged,1005); assert(zy_learning_load(merged,base)==0);
    assert(zy_learning_word_count(merged,1001)>0);
    assert(zy_learning_word_count(merged,2002)>0); free(seed);free(a);free(b);free(merged);

    /* A legacy ID-only record and its v2 stable-key form are the same word.
       Concurrent migration must merge them rather than create duplicate rows. */
    clean_base(base);
    ZYLearning *legacy=calloc(1,sizeof(*legacy)), *migrator=calloc(1,sizeof(*migrator)), *stale=calloc(1,sizeof(*stale)), *identity=calloc(1,sizeof(*identity));
    assert(legacy&&migrator&&stale&&identity);
    zy_learning_init(legacy,1100); zy_learning_begin_event(legacy); zy_learning_record_word(legacy,42,4242); assert(zy_learning_save(legacy,base,1101,1)==0);
    zy_learning_init(migrator,1102); zy_learning_init(stale,1102); assert(zy_learning_load(migrator,base)==0); assert(zy_learning_load(stale,base)==0);
    zy_learning_bind_word_identity(migrator,42,0x123456789abcdef0ULL); assert(zy_learning_save(migrator,base,1103,1)==0);
    zy_learning_begin_event(stale); zy_learning_record_word(stale,42,4242); assert(zy_learning_save(stale,base,1104,1)==0);
    zy_learning_init(identity,1105); assert(zy_learning_load(identity,base)==0);
    size_t word_rows=0, query_rows=0;
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++) if(identity->p.words[i].used&&identity->p.words[i].id==42) word_rows++;
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++) if(identity->p.queries[i].used&&identity->p.queries[i].id==42&&identity->p.queries[i].hash==4242) query_rows++;
    assert(word_rows==1); assert(query_rows==1);
    free(legacy);free(migrator);free(stale);free(identity);

    /* Two stale processes incrementing the SAME word must add both deltas.
       v2's max(count) merge lost one of these +1 operations. */
    clean_base(base);
    ZYLearning *same_seed=calloc(1,sizeof(*same_seed)), *same_a=calloc(1,sizeof(*same_a)), *same_b=calloc(1,sizeof(*same_b)), *same_out=calloc(1,sizeof(*same_out));
    assert(same_seed&&same_a&&same_b&&same_out);
    zy_learning_init(same_seed,1200);zy_learning_begin_event(same_seed);zy_learning_record_word_stable(same_seed,42,0x424242ULL,4242);assert(zy_learning_save(same_seed,base,1201,1)==0);
    zy_learning_init(same_a,1202);zy_learning_init(same_b,1202);assert(zy_learning_load(same_a,base)==0);assert(zy_learning_load(same_b,base)==0);
    zy_learning_begin_event(same_a);zy_learning_record_word_stable(same_a,42,0x424242ULL,4242);assert(zy_learning_save(same_a,base,1203,1)==0);
    zy_learning_begin_event(same_b);zy_learning_record_word_stable(same_b,42,0x424242ULL,4242);assert(zy_learning_save(same_b,base,1204,1)==0);
    zy_learning_init(same_out,1205);assert(zy_learning_load(same_out,base)==0);assert(zy_learning_word_count(same_out,42)==3);
    free(same_seed);free(same_a);free(same_b);free(same_out);

    /* A stale process saving unrelated learning must not resurrect a record
       that another process deleted after the stale process loaded. */
    clean_base(base);
    ZYLearning *del_seed=calloc(1,sizeof(*del_seed)), *deleter=calloc(1,sizeof(*deleter)), *stale_writer=calloc(1,sizeof(*stale_writer)), *del_out=calloc(1,sizeof(*del_out));
    assert(del_seed&&deleter&&stale_writer&&del_out);
    zy_learning_init(del_seed,1300);zy_learning_begin_event(del_seed);zy_learning_record_word_stable(del_seed,42,0x424242ULL,4242);assert(zy_learning_save(del_seed,base,1301,1)==0);
    zy_learning_init(deleter,1302);zy_learning_init(stale_writer,1302);assert(zy_learning_load(deleter,base)==0);assert(zy_learning_load(stale_writer,base)==0);
    assert(zy_learning_remove_word(deleter,42,4242)==1);assert(zy_learning_save(deleter,base,1303,1)==0);
    zy_learning_begin_event(stale_writer);zy_learning_record_word_stable(stale_writer,99,0x999999ULL,9999);assert(zy_learning_save(stale_writer,base,1304,1)==0);
    zy_learning_init(del_out,1305);assert(zy_learning_load(del_out,base)==0);assert(zy_learning_word_count(del_out,42)==0);assert(zy_learning_word_count(del_out,99)==1);
    free(del_seed);free(deleter);free(stale_writer);free(del_out);

    clean_base(base);
    puts("test_learning_v2_regressions: OK");
    return 0;
}
