#ifndef ZY_RUNTIME_H
#define ZY_RUNTIME_H
#import <Foundation/Foundation.h>
#include "ZYEngine.h"

#ifdef __cplusplus
extern "C" {
#endif

BOOL ZYRuntimeInitialize(void);
void ZYRuntimeShutdown(void);
size_t ZYRuntimeLookup(const char *query,ZYCandidate *out,size_t cap);
void ZYRuntimeBeginLearningEvent(void);
void ZYRuntimeLearnWord(uint32_t candidateID,const char *query);
void ZYRuntimeLearnPhrase(const char *word,const char *query,const char *pron);
int ZYRuntimeCandidatePron(uint32_t candidateID,char *out,size_t cap);
int ZYRuntimeCandidateWord(uint32_t candidateID,char *out,size_t cap);
NSString *ZYRuntimeOutputString(NSString *traditional,BOOL simplified);
void ZYRuntimeMaybeFlush(void);
BOOL ZYRuntimeClearLearning(void);
uint32_t ZYRuntimeQueryHash(const char *query);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
