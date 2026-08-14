#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "ZYLearning.h"

static int exists(const char *p){struct stat st;return stat(p,&st)==0;}

int main(int argc,char **argv){
    assert(argc==2); const char *base=argv[1];
    char a[512],b[512];snprintf(a,sizeof(a),"%s_A.dat",base);snprintf(b,sizeof(b),"%s_B.dat",base);unlink(a);unlink(b);

    ZYLearning l; zy_learning_init(&l,1000);

    /* One final commit is exactly one learning event, even if it records
       multiple dictionary candidates and a learned phrase. */
    zy_learning_begin_event(&l);
    assert(l.p.clock==1);
    zy_learning_record_word(&l,42,1234);
    zy_learning_record_word(&l,77,999);
    assert(zy_learning_record_phrase(&l,"沒有成功","ㄇㄟˊㄧㄡˇㄔㄥˊㄍㄨㄥ","")==0);
    assert(l.p.clock==1);

    /* Frequency is persisted beyond the scoring cap for compatibility, but
       the effective long-term score is bounded. */
    for(int i=0;i<39;i++){
        zy_learning_begin_event(&l);
        zy_learning_record_word(&l,42,1234);
    }
    assert(zy_learning_word_count(&l,42)==40);
    assert(zy_learning_word_frequency_bonus(&l,42)==124000u); /* 31 * 4000 */
    assert(zy_learning_query_bonus(&l,1234,42)==40000u);      /* 8 * 5000 */

    /* A just-used word gets recency, but it naturally decays to zero. */
    assert(zy_learning_word_recency_bonus(&l,42)==120000u);
    for(int i=0;i<29;i++) zy_learning_begin_event(&l);
    assert(zy_learning_word_recency_bonus(&l,42)==4000u);
    zy_learning_begin_event(&l);
    assert(zy_learning_word_recency_bonus(&l,42)==0u);

    /* Exact-query preference is strong but temporary: it survives through
       age 64, then returns to ordinary score competition. */
    assert(zy_learning_query_preference_rank(&l,1234,42)==2u);
    while((uint32_t)(l.p.clock-l.p.queries[0].last)<64u) zy_learning_begin_event(&l);
    assert(zy_learning_query_preference_rank(&l,1234,42)==2u);
    zy_learning_begin_event(&l);
    assert(zy_learning_query_preference_rank(&l,1234,42)==0u);

    /* Re-selecting a different candidate for the same query immediately
       replaces the old preferred candidate. */
    zy_learning_begin_event(&l);
    zy_learning_record_word(&l,77,1234);
    assert(zy_learning_query_preference_rank(&l,1234,77)==2u);
    assert(zy_learning_query_preference_rank(&l,1234,42)==0u);

    /* Phrase learning has its own bounded frequency + recency model. */
    ZYLearnPhrase *p=NULL;
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++) if(l.p.phrases[i].used&&strcmp(l.p.phrases[i].word,"沒有成功")==0){p=&l.p.phrases[i];break;}
    assert(p);
    p->count=200; p->last=l.p.clock;
    assert(zy_learning_phrase_frequency_bonus(p)==128000u); /* 16 * 8000 */
    assert(zy_learning_phrase_recency_bonus(&l,p)==160000u);
    for(int i=0;i<32;i++) zy_learning_begin_event(&l);
    assert(zy_learning_phrase_recency_bonus(&l,p)==0u);

    assert(zy_learning_should_flush(&l,1101));
    assert(zy_learning_save(&l,base,1101,0)==0);
    assert(exists(a)||exists(b)); assert(l.dirty_mutations==0); assert(l.generation==1);

    ZYLearning r; zy_learning_init(&r,2002); assert(zy_learning_load(&r,base)==0); assert(r.generation==1);
    assert(zy_learning_word_count(&r,42)==40);
    assert(zy_learning_word_frequency_bonus(&r,42)==124000u);
    assert(zy_learning_word_count(&r,77)>=2);

    /* Reset must clear all in-memory learning state immediately without
       requiring a process restart. */
    ZYLearning z; zy_learning_init(&z,3000);
    zy_learning_begin_event(&z);
    zy_learning_record_word(&z,42,1234);
    assert(zy_learning_record_phrase(&z,"資料庫","ㄗㄌㄎㄨˋ","ㄗㄌㄧㄠˋㄎㄨˋ")==0);
    z.generation=9;
    assert(zy_learning_word_count(&z,42)==1);
    assert(z.p.clock==1);
    zy_learning_reset(&z,4000);
    assert(z.p.clock==0);
    assert(zy_learning_word_count(&z,42)==0);
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++) assert(!z.p.queries[i].used);
    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP;i++) assert(!z.p.phrases[i].used);
    assert(z.generation==0);
    assert(z.dirty_mutations==0);
    assert(z.last_flush_seconds==4000);

    puts("test_learning: OK");
    return 0;
}
