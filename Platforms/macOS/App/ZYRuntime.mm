#import "ZYRuntime.h"
#import <AppKit/AppKit.h>
#include "ZYConversion.h"
#include "ZYComposer.h"
#include "ZYLearning.h"
#include <limits.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>

static ZYEngine gEngine;
static ZYConversion gConversion;
static ZYLearning gLearning;
static ZYComposerWorkspace gComposerWorkspace;
static BOOL gReady=NO;
static char gLearningBase[PATH_MAX];

enum {
    ZY_COMPOSITION_LEARN_FREQUENCY_CAP = 124000,
    ZY_COMPOSITION_LEARN_RECENCY_CAP = 120000,
    ZY_COMPOSITION_LEARN_QUERY_CAP = 40000,
    ZY_COMPOSITION_LEARN_PREFERENCE_CAP = 120000,
    ZY_COMPOSITION_COMPLETE_QUALITY_WINDOW = 8000,
    ZY_COMPOSITION_PARTIAL_QUALITY_WINDOW = 60000,
    ZY_COMPOSITION_MAX_ADMITTED = 8
};
static const int64_t ZY_COMPOSITION_BASE_SCORE = 2200000LL;
static int64_t cap_i64(int64_t value,int64_t cap){return value>cap?cap:value;}

static uint64_t now_seconds(void){return (uint64_t)time(NULL);}
static uint32_t ZYRuntimeQueryHashBytes(const unsigned char *p,size_t n){
    uint32_t h=2166136261u;if(!p)return 0;
    for(size_t i=0;i<n;){
        // U+02C9 MODIFIER LETTER MACRON is the optional explicit first-tone
        // marker. Dictionary first tone is stored unmarked, so both spellings
        // must share the same query-learning identity. UTF-8: CB 89.
        if(i+1<n&&p[i]==0xCB&&p[i+1]==0x89){i+=2;continue;}
        h^=p[i++];h*=16777619u;
    }
    return h?h:1;
}
uint32_t ZYRuntimeQueryHash(const char *s){
    if(!s)return 0;
    return ZYRuntimeQueryHashBytes((const unsigned char*)s,strlen(s));
}
static size_t ZYRuntimeUTF8CharLength(unsigned char c){
    if(c<0x80)return 1;if((c&0xE0)==0xC0)return 2;if((c&0xF0)==0xE0)return 3;if((c&0xF8)==0xF0)return 4;return 1;
}
static size_t ZYRuntimeQueryCodepointOffsets(const char *s,size_t *offsets,size_t cap){
    if(!s||!offsets||cap<2)return 0;
    size_t len=strlen(s),pos=0,n=0;offsets[0]=0;
    while(pos<len&&n+1<cap){size_t k=ZYRuntimeUTF8CharLength((unsigned char)s[pos]);if(pos+k>len)break;pos+=k;offsets[++n]=pos;}
    return (pos==len)?n:0;
}
static uint32_t ZYRuntimeQueryHashCodepointRange(const char *query,const size_t *offsets,size_t cpCount,size_t start,size_t count){
    if(!query||!offsets||start>cpCount||count>cpCount-start)return 0;
    size_t a=offsets[start],b=offsets[start+count];
    return ZYRuntimeQueryHashBytes((const unsigned char*)query+a,b-a);
}

BOOL ZYRuntimeInitialize(void){
    if(gReady)return YES;
    NSBundle *b=[NSBundle mainBundle];
    NSString *dict=[b pathForResource:@"dictionary" ofType:@"bin"];
    NSString *t2s=[b pathForResource:@"t2s" ofType:@"bin"];
    if(!dict||!t2s)return NO;
    if(zy_engine_open(&gEngine,dict.fileSystemRepresentation)!=0)return NO;
    if(zy_conversion_open(&gConversion,t2s.fileSystemRepresentation)!=0){zy_engine_close(&gEngine);return NO;}
    if(zy_composer_workspace_init(&gComposerWorkspace)!=0){zy_conversion_close(&gConversion);zy_engine_close(&gEngine);return NO;}
    NSArray<NSString*> *dirs=NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory,NSUserDomainMask,YES);
    NSString *root=[[dirs firstObject] stringByAppendingPathComponent:@"逐音輸入法"];
    [[NSFileManager defaultManager] createDirectoryAtPath:root withIntermediateDirectories:YES attributes:nil error:nil];
    NSString *base=[root stringByAppendingPathComponent:@"learning"];
    strlcpy(gLearningBase,base.fileSystemRepresentation,sizeof(gLearningBase));
    zy_learning_init(&gLearning,now_seconds());
    if(zy_learning_load(&gLearning,gLearningBase)==0)gLearning.last_flush_seconds=now_seconds();
    gReady=YES;return YES;
}

size_t ZYRuntimeLookup(const char *query,ZYCandidate *out,size_t cap){
    if(!gReady||!query||!out||!cap)return 0;
    @autoreleasepool {
    ZYCandidate raw[256];size_t rn=zy_engine_lookup(&gEngine,query,raw,256);uint32_t qh=ZYRuntimeQueryHash(query);
    for(size_t i=0;i<rn;i++)if(!raw[i].literal&&raw[i].id<gEngine.dict.h->word_count){
        uint8_t learned_preference=zy_learning_query_preference_rank(&gLearning,qh,raw[i].id);
        if(learned_preference>raw[i].preference_rank)raw[i].preference_rank=learned_preference;
        uint32_t learned_count=zy_learning_word_count(&gLearning,raw[i].id);
        raw[i].learned=(uint8_t)(learned_count>0);
        // A previously selected multi-syllable word that fully matches the
        // current query (possibly through initial abbreviations) gets a soft
        // recall preference. Exact same-query preference remains rank 2.
        if(raw[i].preference_rank<1 && learned_count>0 &&
           (raw[i].dictionary_exact || raw[i].final_syllable_partial))
            raw[i].preference_rank=1;
        raw[i].score+=(int32_t)(zy_learning_word_frequency_bonus(&gLearning,raw[i].id)+
                                zy_learning_word_recency_bonus(&gLearning,raw[i].id)+
                                zy_learning_query_bonus(&gLearning,qh,raw[i].id));
    }
    qsort(raw,rn,sizeof(raw[0]),zy_candidate_rank_compare);
    ZYCandidate tmp[192];size_t n=rn<128?rn:128;
    if(n)memcpy(tmp,raw,n*sizeof(tmp[0]));

    // Continuous composition is intentionally separate from the dictionary lookup:
    // the composer finds legal word boundaries; runtime then applies the same
    // adaptive learning signals to each constituent segment.
    ZYCandidate composed[32];size_t cn=zy_composer_lookup_with_workspace(&gEngine,query,composed,32,&gComposerWorkspace);
    size_t queryOffsets[ZY_COMPOSER_MAX_QUERY_CODEPOINTS+1];
    size_t queryCodepoints=ZYRuntimeQueryCodepointOffsets(query,queryOffsets,ZY_COMPOSER_MAX_QUERY_CODEPOINTS+1);
    int64_t best_composed_score=cn?(int64_t)composed[0].score:INT64_MIN;
    size_t composed_admitted=0;
    for(size_t i=0;i<cn&&n<192;i++){
        ZYCandidate c=composed[i];
        // Quality is decided from the language/dictionary path before personal
        // learning.  A learned full phrase is still available through the
        // dedicated phrase-learning path below.
        int64_t quality_window=c.word_complete?ZY_COMPOSITION_COMPLETE_QUALITY_WINDOW:ZY_COMPOSITION_PARTIAL_QUALITY_WINDOW;
        if(best_composed_score-(int64_t)c.score>quality_window)continue;
        if(composed_admitted>=ZY_COMPOSITION_MAX_ADMITTED)break;

        int64_t frequency=0,recency=0,query_bonus=0,preference=0;size_t qpos=0;
        for(uint8_t j=0;j<c.segment_count;j++){
            uint32_t sid=c.segment_ids[j];uint8_t consume=c.segment_consume_codepoints[j];
            if(sid<gEngine.dict.h->word_count){
                frequency+=zy_learning_word_frequency_bonus(&gLearning,sid);
                recency+=zy_learning_word_recency_bonus(&gLearning,sid);
                if(queryCodepoints&&qpos+consume<=queryCodepoints){
                    uint32_t sh=ZYRuntimeQueryHashCodepointRange(query,queryOffsets,queryCodepoints,qpos,consume);
                    query_bonus+=zy_learning_query_bonus(&gLearning,sh,sid);
                    uint8_t pr=zy_learning_query_preference_rank(&gLearning,sh,sid);
                    if(pr==2)preference+=120000;else if(pr==1)preference+=60000;
                }
            }
            qpos+=consume;
        }
        // Caps are composition-wide, not per segment.  Splitting a phrase into
        // more pieces therefore cannot create more learning score by itself.
        frequency=cap_i64(frequency,ZY_COMPOSITION_LEARN_FREQUENCY_CAP);
        recency=cap_i64(recency,ZY_COMPOSITION_LEARN_RECENCY_CAP);
        query_bonus=cap_i64(query_bonus,ZY_COMPOSITION_LEARN_QUERY_CAP);
        preference=cap_i64(preference,ZY_COMPOSITION_LEARN_PREFERENCE_CAP);
        int64_t learned=frequency+recency+query_bonus+preference;

        // Preserve the composer's quality distance instead of flattening it by
        // /20.  This keeps natural paths above phonetic-but-unnatural paths.
        int64_t ranked=ZY_COMPOSITION_BASE_SCORE+(int64_t)c.score+learned;
        if(ranked>INT_MAX)ranked=INT_MAX;if(ranked<INT_MIN)ranked=INT_MIN;c.score=(int32_t)ranked;
        tmp[n++]=c;composed_admitted++;
    }

    for(size_t i=0;i<ZY_LEARN_PHRASE_CAP&&n<192;i++){
        const ZYLearnPhrase *p=&gLearning.p.phrases[i];if(!p->used)continue;uint8_t mc=0,matched=0;int exact=0;int ok=p->pron[0]?zy_engine_match_pron_key(query,p->pron,&mc,&matched,&exact):(strcmp(query,p->query)==0);
        if(!ok)continue;ZYCandidate c={0};c.id=0x80000000u|(uint32_t)i;c.user_phrase=1;c.learned=1;c.match_class=mc?mc:5;c.matched_chars=matched;c.dictionary_exact=exact?1:0;c.preference_rank=1;c.score=7600000+(int32_t)zy_learning_phrase_frequency_bonus(p)+(int32_t)zy_learning_phrase_recency_bonus(&gLearning,p)+(exact?1200000:0);strlcpy(c.word,p->word,sizeof(c.word));tmp[n++]=c;
    }
    qsort(tmp,n,sizeof(tmp[0]),zy_candidate_rank_compare);
    ZYCandidate deduped[192];size_t dn=0;
    for(size_t i=0;i<n;i++){
        BOOL dup=NO;
        for(size_t j=0;j<dn;j++)if(strcmp(deduped[j].word,tmp[i].word)==0){
            dup=YES;
            if(!deduped[j].learned&&tmp[i].learned)deduped[j]=tmp[i];
            break;
        }
        if(!dup&&dn<192)deduped[dn++]=tmp[i];
    }
    return zy_candidate_apply_length_policy(deduped,dn,out,cap);
    }
}

void ZYRuntimeBeginLearningEvent(void){if(gReady)zy_learning_begin_event(&gLearning);}
void ZYRuntimeLearnWord(uint32_t cid,const char *query){if(!gReady||cid>=gEngine.dict.h->word_count)return;zy_learning_record_word(&gLearning,cid,ZYRuntimeQueryHash(query));ZYRuntimeMaybeFlush();}
BOOL ZYRuntimeRemoveCandidateLearning(uint32_t cid,const char *query){if(!gReady)return NO;BOOL ok=NO;if((cid&0x80000000u)&&cid!=UINT32_MAX)ok=zy_learning_remove_phrase_slot(&gLearning,cid&0x7fffffffu);else if(cid<gEngine.dict.h->word_count)ok=zy_learning_remove_word(&gLearning,cid,ZYRuntimeQueryHash(query));if(ok)ZYRuntimeMaybeFlush();return ok;}
BOOL ZYRuntimeCandidateHasLearning(uint32_t cid){if(!gReady)return NO;if((cid&0x80000000u)&&cid!=UINT32_MAX){uint32_t i=cid&0x7fffffffu;return i<ZY_LEARN_PHRASE_CAP&&gLearning.p.phrases[i].used;}return cid<gEngine.dict.h->word_count&&zy_learning_word_count(&gLearning,cid)>0;}
void ZYRuntimeLearnPhrase(const char *word,const char *query,const char *pron){if(!gReady)return;zy_learning_record_phrase(&gLearning,word,query,pron);ZYRuntimeMaybeFlush();}
int ZYRuntimeCandidatePron(uint32_t cid,char *out,size_t cap){if(!gReady||!out||!cap)return-1;if((cid&0x80000000u)&&cid!=UINT32_MAX){uint32_t i=cid&0x7fffffffu;if(i>=ZY_LEARN_PHRASE_CAP||!gLearning.p.phrases[i].used)return-1;strlcpy(out,gLearning.p.phrases[i].pron,cap);return out[0]?0:-1;}return zy_engine_pronunciation_key(&gEngine,cid,out,cap);}
int ZYRuntimeCandidateWord(uint32_t cid,char *out,size_t cap){
    if(!gReady||!out||!cap)return-1;
    if((cid&0x80000000u)&&cid!=UINT32_MAX){uint32_t i=cid&0x7fffffffu;if(i>=ZY_LEARN_PHRASE_CAP||!gLearning.p.phrases[i].used)return-1;strlcpy(out,gLearning.p.phrases[i].word,cap);return out[0]?0:-1;}
    if(cid>=gEngine.dict.h->word_count)return-1;const char *p=NULL;size_t n=0;if(zy_dict_word(&gEngine.dict,cid,&p,&n)!=0)return-1;if(n>=cap)n=cap-1;memcpy(out,p,n);out[n]=0;return 0;
}
NSString *ZYRuntimeOutputString(NSString *traditional,BOOL simplified){if(!simplified||!traditional)return traditional;const char *in=traditional.UTF8String;size_t cap=strlen(in)*4+32;char *buf=(char*)malloc(cap);if(!buf)return traditional;if(zy_conversion_t2s(&gConversion,in,buf,cap)!=0){free(buf);return traditional;}NSString *s=[[NSString alloc] initWithUTF8String:buf];free(buf);return s?:traditional;}

BOOL ZYRuntimeClearLearning(void){
    if(!gReady)return NO;
    NSFileManager *fm=[NSFileManager defaultManager];
    NSString *base=[fm stringWithFileSystemRepresentation:gLearningBase length:strlen(gLearningBase)];
    if(!base)return NO;
    // The persistent learning snapshots are learning_A.dat and learning_B.dat.
    NSArray<NSString*> *paths=@[[base stringByAppendingString:@"_A.dat"],[base stringByAppendingString:@"_B.dat"]];
    BOOL ok=YES;
    for(NSString *path in paths){
        if(![fm fileExistsAtPath:path])continue;
        NSError *error=nil;
        if(![fm removeItemAtPath:path error:&error]){ok=NO;break;}
    }
    if(!ok)return NO;
    zy_learning_reset(&gLearning,now_seconds());
    return YES;
}

void ZYRuntimeMaybeFlush(void){if(gReady&&zy_learning_should_flush(&gLearning,now_seconds()))zy_learning_save(&gLearning,gLearningBase,now_seconds(),0);}
void ZYRuntimeShutdown(void){if(!gReady)return;if(gLearning.dirty_mutations)zy_learning_save(&gLearning,gLearningBase,now_seconds(),1);zy_composer_workspace_dispose(&gComposerWorkspace);zy_conversion_close(&gConversion);zy_engine_close(&gEngine);gReady=NO;}
