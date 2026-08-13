#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ZYEngine.h"
#include "ZYComposer.h"

static int starts_with(const char *s,const char *prefix){return strncmp(s,prefix,strlen(prefix))==0;}

int main(int argc,char **argv){
    assert(argc==2);
    ZYEngine e;assert(zy_engine_open(&e,argv[1])==0);
    ZYCandidate out[40];
    size_t n=zy_composer_lookup(&e,"ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ",out,40);
    assert(n>0);
    assert(strcmp(out[0].word,"今天天氣")==0);
    assert(out[0].segment_count==2);
    assert(out[0].segment_ids[0] < e.dict.h->word_count);
    assert(out[0].segment_ids[1] < e.dict.h->word_count);
    assert(out[0].segment_consume_codepoints[0]==6);
    assert(out[0].segment_consume_codepoints[1]==6);

    // Explicit first-tone marks are legal syllable terminators and consume
    // their own codepoints while producing the same phrase.
    n=zy_composer_lookup(&e,"ㄐㄧㄣˉㄊㄧㄢˉㄊㄧㄢˉㄑㄧˋ",out,40);
    assert(n>0);
    assert(strcmp(out[0].word,"今天天氣")==0);
    assert(out[0].segment_count==2);
    assert(out[0].segment_consume_codepoints[0]==8);
    assert(out[0].segment_consume_codepoints[1]==7);

    n=zy_composer_lookup(&e,"ㄐㄧㄣㄊㄧㄢㄊ",out,40);
    assert(n>0);
    int found=0;
    for(size_t i=0;i<n;i++) if(starts_with(out[i].word,"今天")){found=1;break;}
    assert(found);

    // Natural long-word segmentation must dominate character-by-character
    // phonetic combinations.  ㄒㄧㄢㄗㄞㄧㄡˇ should strongly prefer
    // 現在 + 有 rather than filling the first row with 先/見/線 + 在 + 有.
    n=zy_composer_lookup(&e,"ㄒㄧㄢㄗㄞㄧㄡˇ",out,40);
    assert(n>0);
    assert(strcmp(out[0].word,"現在有")==0);
    size_t quality_window=n<5?n:5;
    for(size_t i=0;i<quality_window;i++){
        assert(starts_with(out[i].word,"現在"));
        assert(out[i].segment_count<=2);
    }

    zy_engine_close(&e);
    puts("test_composer: OK");
    return 0;
}
