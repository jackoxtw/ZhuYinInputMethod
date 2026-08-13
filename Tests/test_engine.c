#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ZYEngine.h"

static int contains(ZYCandidate *c, size_t n, const char *word) {
    for (size_t i=0;i<n;i++) if (strcmp(c[i].word, word)==0) return 1;
    return 0;
}

int main(int argc, char **argv) {
    assert(argc == 2);
    ZYEngine e;
    assert(zy_engine_open(&e, argv[1]) == 0);
    ZYCandidate out[40];
    size_t n = zy_engine_lookup(&e, "ㄋㄏㄇ", out, 40);
    assert(contains(out,n,"你好嗎"));
    n = zy_engine_lookup(&e, "ㄌㄧˇ", out, 40);
    assert(contains(out,n,"李"));
    n = zy_engine_lookup(&e, "ㄓㄨˋㄧㄣ", out, 40);
    assert(contains(out,n,"ㄓㄨˋㄧㄣ"));

    // Official built-in brand term must be available on every fresh install.
    n = zy_engine_lookup(&e, "ㄓㄨˊㄧㄣㄕㄨㄖㄨˋㄈㄚˇ", out, 40);
    assert(n>0);
    assert(strcmp(out[0].word,"逐音輸入法")==0);

    // A five-syllable mixed abbreviation is specific enough to soft-recall a
    // long built-in word, while a short first syllable must not advertise it.
    ZYCandidate brand_wide[256];
    n = zy_engine_lookup(&e, "ㄓㄧㄕㄖㄈ", brand_wide, 256);
    assert(n>0);
    assert(strcmp(brand_wide[0].word,"逐音輸入法")==0);
    n = zy_engine_lookup(&e, "ㄓㄨˊ", out, 40);
    assert(!contains(out,n,"逐音輸入法"));

    // Taiwan readings and polyphones must be reachable through the real engine.
    n = zy_engine_lookup(&e, "ㄑㄧˊ", out, 40);
    assert(contains(out,n,"期"));
    n = zy_engine_lookup(&e, "ㄏㄤˊ", out, 40);
    assert(contains(out,n,"行"));
    n = zy_engine_lookup(&e, "ㄔㄨㄥˊ", out, 40);
    assert(contains(out,n,"重"));
    n = zy_engine_lookup(&e, "ㄔㄤˊ", out, 40);
    assert(contains(out,n,"長"));
    n = zy_engine_lookup(&e, "ㄩㄝˋ", out, 40);
    assert(contains(out,n,"樂"));

    // Explicit first tone U+02C9 is optional but, when present, must behave
    // exactly like the dictionary's unmarked first tone.
    n = zy_engine_lookup(&e, "ㄊㄧㄢˉ", out, 40);
    assert(n>0);
    assert(strcmp(out[0].word,"天")==0);
    assert(out[0].match_class==4);
    assert(out[0].dictionary_exact==1);


    // A complete toneless one-symbol syllable (e.g. ㄧ for ㄧˋ) must not be
    // downgraded to an initial-only abbreviation.  This is the real-world
    // "記憶體" regression: ㄐㄧ ㄧ ㄊㄧˇ should still surface 記憶體.
    n = zy_engine_lookup(&e, "ㄐㄧㄧㄊㄧˇ", out, 40);
    assert(contains(out,n,"記憶體"));
    assert(strcmp(out[0].word,"記憶體")==0);

    // While the final syllable is still being typed, its prefix must count as
    // an in-progress syllable, not an initial-only abbreviation.
    n = zy_engine_lookup(&e, "ㄐㄧㄧㄊ", out, 40);
    assert(contains(out,n,"記憶體"));
    assert(strcmp(out[0].word,"記憶體")==0);

    // Learned abbreviation recall needs a wider raw pool: 資料庫 is a valid
    // exact mixed full/initial match for ㄗㄌㄎㄨˋ even though it is outside
    // the legacy top-40 raw ranking.
    ZYCandidate wide[128];
    n = zy_engine_lookup(&e, "ㄗㄌㄎㄨˋ", wide, 128);
    assert(contains(wide,n,"資料庫"));

    // Composer prefix lookup must reserve room for real multi-syllable words;
    // single-character fallbacks must not consume all 12 edge slots.
    n = zy_engine_lookup_prefix(&e, "ㄗㄌㄎㄨˋ", out, 12);
    assert(contains(out,n,"資料庫"));

    // If the query reaches every syllable of a learned word but the final
    // syllable is still being typed, the engine must expose that state so
    // runtime can recall the learned word without treating an earlier prefix
    // such as ㄗㄌ as equivalent.
    n = zy_engine_lookup(&e, "ㄗㄌㄎ", wide, 128);
    int found_partial_database = 0;
    for (size_t i=0;i<n;i++) {
        if (strcmp(wide[i].word,"資料庫")==0) {
            found_partial_database = 1;
            assert(wide[i].matched_chars==3);
            assert(wide[i].dictionary_exact==0);
            assert(wide[i].word_complete==0);
            assert(wide[i].final_syllable_partial==1);
        }
    }
    assert(found_partial_database);

    n = zy_engine_lookup(&e, "ㄗㄌ", wide, 128);
    for (size_t i=0;i<n;i++) {
        if (strcmp(wide[i].word,"資料庫")==0)
            assert(wide[i].final_syllable_partial==0);
    }

    // Prefix lookup is the primitive used by continuous composition.  A fully
    // matched word may consume only the beginning of a longer query.
    n = zy_engine_lookup_prefix(&e, "ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ", out, 40);
    int found_today_prefix = 0;
    for (size_t i=0;i<n;i++) {
        if (strcmp(out[i].word,"今天")==0) {
            found_today_prefix = 1;
            assert(out[i].word_complete == 1);
            assert(out[i].consume_codepoints == 6);
            assert(out[i].dictionary_exact == 0);
        }
    }
    assert(found_today_prefix);

    char pk[256]; assert(zy_engine_pronunciation_key(&e,0,pk,sizeof(pk))==0);
    uint8_t mc=0,matched=0; int exact=0; assert(zy_engine_match_pron_key("ㄌ", "ㄌㄧˇ\x1fㄎㄤ", &mc,&matched,&exact));
    mc=0; matched=0; exact=0;
    assert(zy_engine_match_pron_key("ㄐㄧㄧㄊㄧˇ", "ㄐㄧˋ\x1fㄧˋ\x1fㄊㄧˇ", &mc,&matched,&exact));
    assert(mc==4 && matched==3 && exact==1);
    mc=0; matched=0; exact=1;
    assert(zy_engine_match_pron_key("ㄐㄧㄧㄊ", "ㄐㄧˋ\x1fㄧˋ\x1fㄊㄧˇ", &mc,&matched,&exact));
    assert(mc>=3 && matched==3 && exact==0);
    mc=0; matched=0; exact=0;
    assert(zy_engine_match_pron_key("ㄊㄧㄢˉ", "ㄊㄧㄢ", &mc,&matched,&exact));
    assert(mc==4 && matched==1 && exact==1);
    // Explicit first tone must not turn another tone into first tone.
    mc=0; matched=0; exact=0;
    assert(!zy_engine_match_pron_key("ㄊㄧㄢˉ", "ㄊㄧㄢˊ", &mc,&matched,&exact));
    zy_engine_close(&e);
    puts("test_engine: OK");
    return 0;
}
