#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ZYEngine.h"

static ZYCandidate row(const char *word, int score, unsigned matched, int exact, int learned) {
    ZYCandidate c = {0};
    strncpy(c.word, word, sizeof(c.word)-1);
    c.score = score;
    c.matched_chars = (uint8_t)matched;
    c.dictionary_exact = (uint8_t)exact;
    c.learned = (uint8_t)learned;
    return c;
}

int main(void) {
    ZYCandidate in[32] = {0};
    size_t n = 0;

    /* Current input has two matched syllables. Exact two-character rows stay first. */
    in[n++] = row("你好", 900, 2, 1, 0);
    in[n++] = row("您好", 850, 2, 1, 0);

    /* Generic longer dictionary continuations must not leak back in. */
    in[n++] = row("你好啊", 1200, 2, 0, 0);

    /* Learned continuations are appended by length, then adaptive rank. */
    in[n++] = row("你好世界", 5000, 2, 0, 1);
    in[n++] = row("你好嗎", 1000, 2, 0, 1);
    in[n++] = row("你好呀", 1100, 2, 0, 1);

    ZYCandidate out[16] = {0};
    size_t m = zy_candidate_apply_length_policy(in, n, out, 16);
    assert(m == 5);
    assert(strcmp(out[0].word, "你好") == 0);
    assert(strcmp(out[1].word, "您好") == 0);
    assert(strcmp(out[2].word, "你好呀") == 0); /* same 3-char length, higher score */
    assert(strcmp(out[3].word, "你好嗎") == 0);
    assert(strcmp(out[4].word, "你好世界") == 0);

    for (size_t i=0; i<m; ++i) assert(strcmp(out[i].word, "你好啊") != 0);


    /* Native abbreviation matching can mark ㄋㄏ -> 你好 as non-exact because
       the final onset is also a valid in-progress syllable prefix. Length policy
       must still recognize two matched syllables as a two-character primary row. */
    ZYCandidate abbrev[3] = {
        row("你好", 900, 2, 0, 0),
        row("你好啊", 1200, 2, 0, 0),
        row("你好嗎", 1000, 2, 0, 1)
    };
    m = zy_candidate_apply_length_policy(abbrev, 3, out, 16);
    assert(m == 2);
    assert(strcmp(out[0].word, "你好") == 0);
    assert(strcmp(out[1].word, "你好嗎") == 0);

    /* With many exact rows, learned continuations still get visible room. */
    ZYCandidate crowded[32] = {0};
    for (int i=0; i<25; ++i) {
        crowded[i] = row("詞詞", 2000-i, 2, 1, 0);
    }
    crowded[25] = row("學習延伸三", 1500, 2, 0, 1);
    crowded[26] = row("學習延伸四字", 1400, 2, 0, 1);
    m = zy_candidate_apply_length_policy(crowded, 27, out, 16);
    assert(m == 16);
    int saw_learned = 0;
    for (size_t i=0; i<m; ++i) if (out[i].learned) saw_learned = 1;
    assert(saw_learned);

    /* No exact-length group means keep the legacy fallback behavior. */
    ZYCandidate fallback[3] = {
        row("中華民國", 100, 1, 0, 0),
        row("中文", 90, 1, 0, 0),
        row("ㄓ", -100, 0, 0, 0)
    };
    m = zy_candidate_apply_length_policy(fallback, 3, out, 16);
    assert(m == 3);
    assert(strcmp(out[0].word, "中華民國") == 0);
    assert(strcmp(out[1].word, "中文") == 0);

    puts("test_candidate_length_policy: OK");
    return 0;
}
