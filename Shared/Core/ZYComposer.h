#ifndef ZY_COMPOSER_H
#define ZY_COMPOSER_H
#include <stddef.h>
#include "ZYEngine.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ZY_COMPOSER_MAX_SEGMENTS 8
#define ZY_COMPOSER_BEAM_WIDTH 32
#define ZY_COMPOSER_EDGE_CAP 12
#define ZY_COMPOSER_MAX_QUERY_CODEPOINTS 128

typedef struct {
    void *beams;
    size_t *counts;
} ZYComposerWorkspace;

int zy_composer_workspace_init(ZYComposerWorkspace *workspace);
void zy_composer_workspace_dispose(ZYComposerWorkspace *workspace);
size_t zy_composer_lookup_with_workspace(ZYEngine *engine,const char *query,ZYCandidate *out,size_t cap,ZYComposerWorkspace *workspace);
size_t zy_composer_lookup(ZYEngine *engine,const char *query,ZYCandidate *out,size_t cap);

#ifdef __cplusplus
} // extern "C"
#endif
#endif
