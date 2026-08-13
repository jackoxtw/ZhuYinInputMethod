#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ZYEngine.h"
#include "ZYComposer.h"

static void assert_same(const ZYCandidate *a,size_t an,const ZYCandidate *b,size_t bn){
    assert(an==bn);
    for(size_t i=0;i<an;i++){
        assert(a[i].id==b[i].id);
        assert(a[i].score==b[i].score);
        assert(a[i].segment_count==b[i].segment_count);
        assert(strcmp(a[i].word,b[i].word)==0);
    }
}

int main(int argc,char **argv){
    assert(argc==2);
    ZYEngine e;assert(zy_engine_open(&e,argv[1])==0);
    ZYComposerWorkspace ws;
    zy_composer_workspace_init(&ws);

    const char *queries[]={
        "ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ",
        "ㄒㄧㄢㄗㄞㄧㄡˇ",
        "ㄊㄚㄗㄞㄐㄧㄚ",
        "ㄐㄧㄣㄊㄧㄢㄊ"
    };
    for(size_t q=0;q<sizeof(queries)/sizeof(queries[0]);q++){
        ZYCandidate expected[40],actual[40],again[40];
        size_t en=zy_composer_lookup(&e,queries[q],expected,40);
        size_t an=zy_composer_lookup_with_workspace(&e,queries[q],actual,40,&ws);
        size_t rn=zy_composer_lookup_with_workspace(&e,queries[q],again,40,&ws);
        assert_same(expected,en,actual,an);
        assert_same(actual,an,again,rn);
    }

    zy_composer_workspace_dispose(&ws);
    zy_engine_close(&e);
    puts("test_composer_workspace: OK");
    return 0;
}
