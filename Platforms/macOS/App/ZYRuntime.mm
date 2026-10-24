#import "ZYRuntime.h"
#import <AppKit/AppKit.h>
#include "ZYConversion.h"
#include "ZYComposer.h"
#include "ZYLearning.h"
#include <limits.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <dispatch/dispatch.h>

@interface ZYRuntimeLockToken : NSObject
@end
@implementation ZYRuntimeLockToken
@end

#define ZY_RUNTIME_SYNCHRONIZED @synchronized([ZYRuntimeLockToken class])

static ZYEngine gEngine;
static ZYConversion gConversion;
static ZYLearning gLearning;
static ZYComposerWorkspace gComposerWorkspace;
static BOOL gReady=NO;
static char gLearningBase[PATH_MAX];
static uint64_t gFlushTicket=0;

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

static uint64_t fnv64_bytes(uint64_t h,const void *data,size_t n){
    const unsigned char *p=(const unsigned char*)data;
    for(size_t i=0;i<n;i++){h^=p[i];h*=1099511628211ULL;}
    return h;
}
static uint64_t ZYRuntimeDictionaryFingerprint(void){
    if(!gEngine.dict.map||!gEngine.dict.size)return 0;
    uint64_t h=1469598103934665603ULL;
    h=fnv64_bytes(h,gEngine.dict.map,gEngine.dict.size);
    return h?h:1;
}
static uint64_t ZYRuntimeStableKeyForWordID(uint32_t cid){
    if(!gEngine.dict.h||cid>=gEngine.dict.h->word_count)return 0;
    const char *word=NULL;size_t wordLen=0;
    if(zy_dict_word(&gEngine.dict,cid,&word,&wordLen)!=0)return 0;
    char pron[512]={0};if(zy_engine_pronunciation_key(&gEngine,cid,pron,sizeof(pron))!=0)return 0;
    uint64_t h=1469598103934665603ULL;
    h=fnv64_bytes(h,word,wordLen);const unsigned char sep=0xff;h=fnv64_bytes(h,&sep,1);h=fnv64_bytes(h,pron,strlen(pron));
    return h?h:1;
}
typedef struct { uint64_t key; uint32_t id; } ZYStableMapEntry;
static int ZYStableMapCompare(const void *aa,const void *bb){
    const ZYStableMapEntry *a=(const ZYStableMapEntry*)aa,*b=(const ZYStableMapEntry*)bb;
    if(a->key<b->key)return -1;if(a->key>b->key)return 1;return a->id<b->id?-1:(a->id>b->id?1:0);
}
static uint32_t ZYStableMapLookup(const ZYStableMapEntry *map,size_t n,uint64_t key){
    size_t lo=0,hi=n;while(lo<hi){size_t mid=lo+(hi-lo)/2;if(map[mid].key<key)lo=mid+1;else hi=mid;}
    return lo<n&&map[lo].key==key?map[lo].id:ZY_LEARN_INVALID_WORD_ID;
}
static BOOL ZYRuntimeReconcileLearningIdentity(void){
    if(!gEngine.dict.h)return NO;
    uint64_t current=ZYRuntimeDictionaryFingerprint();
    BOOL changed=NO;
    BOOL canAdoptFingerprint=YES;
    /* v1 had only dictionary IDs. Bind those IDs once before writing v2. */
    for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord *r=&gLearning.p.words[i];if(!r->used||r->stable_key||r->id>=gEngine.dict.h->word_count)continue;uint64_t key=ZYRuntimeStableKeyForWordID(r->id);if(key){zy_learning_bind_word_identity(&gLearning,r->id,key);changed=YES;}}
    for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery *q=&gLearning.p.queries[i];if(!q->used||q->stable_key||q->id>=gEngine.dict.h->word_count)continue;uint64_t key=ZYRuntimeStableKeyForWordID(q->id);if(key){zy_learning_bind_word_identity(&gLearning,q->id,key);changed=YES;}}
    if(gLearning.p.dictionary_fingerprint&&gLearning.p.dictionary_fingerprint!=current){
        size_t n=gEngine.dict.h->word_count;ZYStableMapEntry *map=(ZYStableMapEntry*)calloc(n,sizeof(*map));
        if(!map)canAdoptFingerprint=NO;
        else {
            size_t used=0;for(uint32_t id=0;id<gEngine.dict.h->word_count;id++){uint64_t key=ZYRuntimeStableKeyForWordID(id);if(key){map[used].key=key;map[used].id=id;used++;}}
            qsort(map,used,sizeof(*map),ZYStableMapCompare);
            for(size_t i=0;i<ZY_LEARN_WORD_CAP;i++){ZYLearnWord *r=&gLearning.p.words[i];if(!r->used||!r->stable_key)continue;uint32_t id=ZYStableMapLookup(map,used,r->stable_key);if(r->id!=id){r->id=id;changed=YES;}}
            for(size_t i=0;i<ZY_LEARN_QUERY_CAP;i++){ZYLearnQuery *q=&gLearning.p.queries[i];if(!q->used||!q->stable_key)continue;uint32_t id=ZYStableMapLookup(map,used,q->stable_key);if(q->id!=id){q->id=id;changed=YES;}}
            free(map);
        }
    }
    if(canAdoptFingerprint&&gLearning.p.dictionary_fingerprint!=current){zy_learning_set_dictionary_fingerprint(&gLearning,current);changed=YES;}
    if(changed&&gLearning.dirty_mutations==0)gLearning.dirty_mutations=1;
    return changed;
}
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
    ZY_RUNTIME_SYNCHRONIZED {
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
    ZYRuntimeReconcileLearningIdentity();
    gReady=YES;
    if(gLearning.loaded_legacy_v1||gLearning.dirty_mutations)ZYRuntimeMaybeFlush();
    return YES;
    }
}

size_t ZYRuntimeLookup(const char *query,ZYCandidate *out,size_t cap){
    ZY_RUNTIME_SYNCHRONIZED {
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
        const ZYLearnPhrase *p=&gLearning.p.phrases[i];if(!p->used)continue;uint8_t mc=0,matched=0;int exact=0;int ok=p->key_kind==ZY_LEARN_PHRASE_KEY_PRON?zy_engine_match_pron_key(query,p->key,&mc,&matched,&exact):(strcmp(query,p->key)==0);
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
}

void ZYRuntimeBeginLearningEvent(void){ZY_RUNTIME_SYNCHRONIZED {if(gReady)zy_learning_begin_event(&gLearning);}}
void ZYRuntimeLearnWord(uint32_t cid,const char *query){ZY_RUNTIME_SYNCHRONIZED {if(!gReady||cid>=gEngine.dict.h->word_count)return;uint64_t stable=ZYRuntimeStableKeyForWordID(cid);zy_learning_record_word_stable(&gLearning,cid,stable,ZYRuntimeQueryHash(query));ZYRuntimeMaybeFlush();}}
BOOL ZYRuntimeRemoveCandidateLearning(uint32_t cid,const char *query){ZY_RUNTIME_SYNCHRONIZED {if(!gReady)return NO;BOOL ok=NO;if((cid&0x80000000u)&&cid!=UINT32_MAX)ok=zy_learning_remove_phrase_slot(&gLearning,cid&0x7fffffffu);else if(cid<gEngine.dict.h->word_count)ok=zy_learning_remove_word(&gLearning,cid,ZYRuntimeQueryHash(query));if(ok)ZYRuntimeMaybeFlush();return ok;}}
BOOL ZYRuntimeCandidateHasLearning(uint32_t cid){ZY_RUNTIME_SYNCHRONIZED {if(!gReady)return NO;if((cid&0x80000000u)&&cid!=UINT32_MAX){uint32_t i=cid&0x7fffffffu;return i<ZY_LEARN_PHRASE_CAP&&gLearning.p.phrases[i].used;}return cid<gEngine.dict.h->word_count&&zy_learning_word_count(&gLearning,cid)>0;}}
void ZYRuntimeLearnPhrase(const char *word,const char *query,const char *pron){ZY_RUNTIME_SYNCHRONIZED {if(!gReady)return;zy_learning_record_phrase(&gLearning,word,query,pron);ZYRuntimeMaybeFlush();}}
int ZYRuntimeCandidatePron(uint32_t cid,char *out,size_t cap){ZY_RUNTIME_SYNCHRONIZED {if(!gReady||!out||!cap)return-1;if((cid&0x80000000u)&&cid!=UINT32_MAX){uint32_t i=cid&0x7fffffffu;if(i>=ZY_LEARN_PHRASE_CAP||!gLearning.p.phrases[i].used)return-1;if(gLearning.p.phrases[i].key_kind!=ZY_LEARN_PHRASE_KEY_PRON)return-1;strlcpy(out,gLearning.p.phrases[i].key,cap);return out[0]?0:-1;}return zy_engine_pronunciation_key(&gEngine,cid,out,cap);}}
int ZYRuntimeCandidateWord(uint32_t cid,char *out,size_t cap){
    ZY_RUNTIME_SYNCHRONIZED {
    if(!gReady||!out||!cap)return-1;
    if((cid&0x80000000u)&&cid!=UINT32_MAX){uint32_t i=cid&0x7fffffffu;if(i>=ZY_LEARN_PHRASE_CAP||!gLearning.p.phrases[i].used)return-1;strlcpy(out,gLearning.p.phrases[i].word,cap);return out[0]?0:-1;}
    if(cid>=gEngine.dict.h->word_count)return-1;const char *p=NULL;size_t n=0;if(zy_dict_word(&gEngine.dict,cid,&p,&n)!=0)return-1;if(n>=cap)n=cap-1;memcpy(out,p,n);out[n]=0;return 0;
    }
}
NSString *ZYRuntimeOutputString(NSString *traditional,BOOL simplified){ZY_RUNTIME_SYNCHRONIZED {if(!simplified||!traditional)return traditional;const char *in=traditional.UTF8String;size_t cap=strlen(in)*4+32;char *buf=(char*)malloc(cap);if(!buf)return traditional;if(zy_conversion_t2s(&gConversion,in,buf,cap)!=0){free(buf);return traditional;}NSString *s=[[NSString alloc] initWithUTF8String:buf];free(buf);return s?:traditional;}}

BOOL ZYRuntimeClearLearning(void){
    ZY_RUNTIME_SYNCHRONIZED {
    if(!gReady)return NO;
    gFlushTicket++;
    return zy_learning_clear_persistent(&gLearning,gLearningBase,now_seconds())==0;
    }
}

void ZYRuntimeMaybeFlush(void){
    ZY_RUNTIME_SYNCHRONIZED {
    if(!gReady||(!gLearning.dirty_mutations&&!gLearning.loaded_legacy_v1))return;
    uint64_t now=now_seconds();
    if(zy_learning_should_flush(&gLearning,now)){(void)zy_learning_save(&gLearning,gLearningBase,now,0);return;}
    uint64_t ticket=++gFlushTicket;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)NSEC_PER_SEC),dispatch_get_main_queue(),^{
        ZY_RUNTIME_SYNCHRONIZED {
        if(!gReady||ticket!=gFlushTicket)return;
        if(gLearning.dirty_mutations||gLearning.loaded_legacy_v1)(void)zy_learning_save(&gLearning,gLearningBase,now_seconds(),0);
        }
    });
    }
}
void ZYRuntimeForceFlush(void){
    ZY_RUNTIME_SYNCHRONIZED {
    if(!gReady)return;gFlushTicket++;
    if(gLearning.dirty_mutations||gLearning.loaded_legacy_v1)(void)zy_learning_save(&gLearning,gLearningBase,now_seconds(),1);
    }
}
void ZYRuntimeShutdown(void){ZY_RUNTIME_SYNCHRONIZED {if(!gReady)return;ZYRuntimeForceFlush();zy_composer_workspace_dispose(&gComposerWorkspace);zy_conversion_close(&gConversion);zy_engine_close(&gEngine);gReady=NO;}}
