#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "ZYEngine.h"

int main(void) {
    ZYCandidate rows[3] = {0};

    strcpy(rows[0].word, "沒有成功");
    rows[0].score = 7608000;
    rows[0].preference_rank = 0;

    strcpy(rows[1].word, "沒有成功跟隨");
    rows[1].score = 7616000;
    rows[1].preference_rank = 1; /* exact learned phrase */

    strcpy(rows[2].word, "沒有");
    rows[2].score = 4964000;
    rows[2].preference_rank = 2; /* most recently explicit query choice */

    qsort(rows, 3, sizeof(rows[0]), zy_candidate_rank_compare);
    assert(strcmp(rows[0].word, "沒有") == 0);
    assert(rows[0].preference_rank == 2);
    assert(strcmp(rows[1].word, "沒有成功跟隨") == 0);
    assert(rows[1].preference_rank == 1);

    /* Recent use can beat an older high-frequency candidate when neither has
       an explicit preference rank. */
    ZYCandidate adaptive[2] = {0};
    strcpy(adaptive[0].word,"歷史高頻"); adaptive[0].score=5000000+124000;
    strcpy(adaptive[1].word,"最近常用"); adaptive[1].score=5000000+40000+120000;
    qsort(adaptive,2,sizeof(adaptive[0]),zy_candidate_rank_compare);
    assert(strcmp(adaptive[0].word,"最近常用")==0);

    /* A previously selected multi-syllable exact abbreviation match uses the
       soft preference tier (rank 1), so it can be recalled ahead of raw
       single-character fallbacks even when its language score is lower. */
    ZYCandidate recall[2] = {0};
    strcpy(recall[0].word,"自"); recall[0].score=3255000; recall[0].preference_rank=0;
    strcpy(recall[1].word,"資料庫"); recall[1].score=2966000; recall[1].preference_rank=1;
    qsort(recall,2,sizeof(recall[0]),zy_candidate_rank_compare);
    assert(strcmp(recall[0].word,"資料庫")==0);

    puts("test_candidate_learning_ranking: OK");
    return 0;
}
