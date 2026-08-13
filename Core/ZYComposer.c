#include "ZYComposer.h"
#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int64_t score;
    uint16_t offset;
    uint8_t segment_count;
    uint8_t final_complete;
    uint8_t matched_chars;
    uint32_t segment_ids[ZY_COMPOSER_MAX_SEGMENTS];
    uint8_t segment_consume[ZY_COMPOSER_MAX_SEGMENTS];
    char text[ZY_CANDIDATE_WORD_BYTES];
} ZYComposePath;

static size_t utf8_char_len(unsigned char c){if(c<0x80)return 1;if((c&0xE0)==0xC0)return 2;if((c&0xF0)==0xE0)return 3;if((c&0xF8)==0xF0)return 4;return 1;}

static uint32_t utf8_cp(const char *s,size_t n){
    const unsigned char *p=(const unsigned char*)s;if(!n)return 0;
    if(p[0]<0x80)return p[0];if(n>=2&&(p[0]&0xE0)==0xC0)return ((p[0]&31)<<6)|(p[1]&63);
    if(n>=3&&(p[0]&0xF0)==0xE0)return ((p[0]&15)<<12)|((p[1]&63)<<6)|(p[2]&63);
    if(n>=4&&(p[0]&0xF8)==0xF0)return ((p[0]&7)<<18)|((p[1]&63)<<12)|((p[2]&63)<<6)|(p[3]&63);return 0;
}
static int is_initial(uint32_t cp){return cp>=0x3105&&cp<=0x3119;}
static int is_medial(uint32_t cp){return cp>=0x3127&&cp<=0x3129;}
static int is_final(uint32_t cp){return cp>=0x311A&&cp<=0x3126;}
static int is_tone(uint32_t cp){return cp==0x02C9||cp==0x02CA||cp==0x02C7||cp==0x02CB||cp==0x02D9;}

// Continuous Bopomofo has no explicit separators.  Build only phonotactically
// plausible syllable boundaries so the composer cannot split ㄐㄧㄣ as ㄐㄧ｜ㄣ.
static void query_boundaries(const char *q,const size_t *byte_offsets,size_t cp_count,unsigned char *boundary){
    memset(boundary,0,cp_count+1);boundary[0]=1;
    int has_initial=0,has_medial=0,has_final=0;
    for(size_t i=0;i<cp_count;i++){
        size_t a=byte_offsets[i],b=byte_offsets[i+1];uint32_t cp=utf8_cp(q+a,b-a);
        int starts_new=0;
        if(is_initial(cp)){if(has_initial||has_medial||has_final)starts_new=1;}
        else if(is_medial(cp)){if(has_medial||has_final)starts_new=1;}
        else if(is_final(cp)){if(has_final)starts_new=1;}
        else if(is_tone(cp)){}
        else{if(has_initial||has_medial||has_final)starts_new=1;}
        if(starts_new){boundary[i]=1;has_initial=has_medial=has_final=0;}
        if(is_initial(cp))has_initial=1;else if(is_medial(cp))has_medial=1;else if(is_final(cp))has_final=1;
        if(is_tone(cp)){boundary[i+1]=1;has_initial=has_medial=has_final=0;}
    }
    boundary[cp_count]=1;
}

static size_t codepoint_offsets(const char *s,size_t *offsets,size_t cap){
    size_t n=0,pos=0,len=strlen(s);if(!cap)return 0;offsets[0]=0;
    while(pos<len&&n+1<cap){size_t k=utf8_char_len((unsigned char)s[pos]);if(pos+k>len)break;pos+=k;offsets[++n]=pos;}
    return n;
}

static int append_text(char dst[ZY_CANDIDATE_WORD_BYTES],const char *src){
    size_t a=strlen(dst),b=strlen(src);if(a+b>=ZY_CANDIDATE_WORD_BYTES)return 0;memcpy(dst+a,src,b+1);return 1;
}

static int64_t edge_score(const ZYEngine *e,const ZYCandidate *c){
    uint32_t weight=(c->id<e->dict.h->word_count)?e->dict.weights[c->id]:0;
    int64_t s=(int64_t)weight*1000LL+(int64_t)c->matched_chars*100000LL;
    if(c->matched_chars>1)s+=(int64_t)(c->matched_chars-1)*600000LL;
    s+=c->word_complete?250000LL:-100000LL;
    if(c->dictionary_exact)s+=100000LL;
    s+=(int64_t)c->match_class*20000LL;
    return s;
}

static void beam_insert(ZYComposePath *beam,size_t *count,const ZYComposePath *p){
    for(size_t i=0;i<*count;i++){
        if(strcmp(beam[i].text,p->text)==0){
            if(p->score>beam[i].score){beam[i]=*p;while(i>0&&beam[i].score>beam[i-1].score){ZYComposePath t=beam[i-1];beam[i-1]=beam[i];beam[i]=t;i--;}}
            return;
        }
    }
    size_t pos=0;while(pos<*count&&beam[pos].score>=p->score)pos++;
    if(pos>=ZY_COMPOSER_BEAM_WIDTH)return;
    if(*count<ZY_COMPOSER_BEAM_WIDTH)(*count)++;
    for(size_t i=*count-1;i>pos;i--)beam[i]=beam[i-1];
    beam[pos]=*p;
}

static int candidate_compare(const void *aa,const void *bb){
    const ZYCandidate *a=(const ZYCandidate*)aa,*b=(const ZYCandidate*)bb;
    if(a->score!=b->score)return a->score>b->score?-1:1;
    if(a->segment_count!=b->segment_count)return a->segment_count<b->segment_count?-1:1;
    return strcmp(a->word,b->word);
}

int zy_composer_workspace_init(ZYComposerWorkspace *workspace){
    if(!workspace)return -1;
    memset(workspace,0,sizeof(*workspace));
    const size_t slots=ZY_COMPOSER_MAX_QUERY_CODEPOINTS+1;
    workspace->beams=calloc(slots*ZY_COMPOSER_BEAM_WIDTH,sizeof(ZYComposePath));
    workspace->counts=(size_t*)calloc(slots,sizeof(size_t));
    if(!workspace->beams||!workspace->counts){
        zy_composer_workspace_dispose(workspace);
        return -1;
    }
    return 0;
}

void zy_composer_workspace_dispose(ZYComposerWorkspace *workspace){
    if(!workspace)return;
    free(workspace->counts);
    free(workspace->beams);
    memset(workspace,0,sizeof(*workspace));
}

size_t zy_composer_lookup_with_workspace(ZYEngine *e,const char *query,ZYCandidate *out,size_t cap,ZYComposerWorkspace *workspace){
    if(!e||!query||!*query||!out||!cap||!workspace||!workspace->beams||!workspace->counts)return 0;
    size_t byte_offsets[ZY_COMPOSER_MAX_QUERY_CODEPOINTS+1];
    size_t cp_count=codepoint_offsets(query,byte_offsets,ZY_COMPOSER_MAX_QUERY_CODEPOINTS+1);
    if(!cp_count||byte_offsets[cp_count]!=strlen(query))return 0;
    unsigned char boundary[ZY_COMPOSER_MAX_QUERY_CODEPOINTS+1];query_boundaries(query,byte_offsets,cp_count,boundary);

    size_t slots=cp_count+1;
    ZYComposePath *beams=(ZYComposePath*)workspace->beams;
    size_t *counts=workspace->counts;
    memset(beams,0,slots*ZY_COMPOSER_BEAM_WIDTH*sizeof(ZYComposePath));
    memset(counts,0,slots*sizeof(size_t));
    ZYComposePath start={0};start.offset=0;beams[0]=start;counts[0]=1;

    for(size_t off=0;off<cp_count;off++){
        if(!counts[off])continue;
        ZYCandidate edges[ZY_COMPOSER_EDGE_CAP];
        size_t edge_count=zy_engine_lookup_prefix(e,query+byte_offsets[off],edges,ZY_COMPOSER_EDGE_CAP);
        for(size_t pi=0;pi<counts[off];pi++){
            ZYComposePath base=beams[off*ZY_COMPOSER_BEAM_WIDTH+pi];
            if(base.segment_count>=ZY_COMPOSER_MAX_SEGMENTS)continue;
            for(size_t ei=0;ei<edge_count;ei++){
                ZYCandidate *edge=&edges[ei];
                size_t consumed=edge->consume_codepoints;
                if(!consumed||off+consumed>cp_count)continue;
                size_t next=off+consumed;
                if(next<cp_count&&!boundary[next])continue;
                if(next<cp_count&&!edge->word_complete)continue;
                ZYComposePath np=base;
                if(!append_text(np.text,edge->word))continue;
                uint8_t si=np.segment_count++;
                np.segment_ids[si]=edge->id;
                np.segment_consume[si]=(uint8_t)consumed;
                np.offset=(uint16_t)next;
                np.final_complete=edge->word_complete;
                unsigned matched=(unsigned)np.matched_chars+(unsigned)edge->matched_chars;np.matched_chars=(uint8_t)(matched>255?255:matched);
                np.score+=edge_score(e,edge);
                // Prefer a longer complete word at the left edge of a phrase.
                // Without an n-gram model, this longest-prefix prior prevents
                // paths such as 先 + 再有 from clustering with 現在 + 有.
                if(si==0 && edge->word_complete && edge->matched_chars>1)
                    np.score+=(int64_t)(edge->matched_chars-1)*240000LL;
                if(si>0)np.score-=220000LL;
                beam_insert(&beams[next*ZY_COMPOSER_BEAM_WIDTH],&counts[next],&np);
            }
        }
    }

    size_t n=0;ZYComposePath *final=&beams[cp_count*ZY_COMPOSER_BEAM_WIDTH];
    for(size_t i=0;i<counts[cp_count]&&n<cap;i++){
        if(final[i].segment_count<2)continue;
        ZYCandidate c={0};c.id=UINT32_MAX-1u;c.score=(int32_t)(final[i].score>INT_MAX?INT_MAX:(final[i].score<INT_MIN?INT_MIN:final[i].score));
        c.match_class=5;c.matched_chars=final[i].matched_chars;c.dictionary_exact=final[i].final_complete?1:0;c.word_complete=final[i].final_complete;c.consume_codepoints=(uint8_t)cp_count;c.segment_count=final[i].segment_count;
        memcpy(c.segment_ids,final[i].segment_ids,sizeof(c.segment_ids));memcpy(c.segment_consume_codepoints,final[i].segment_consume,sizeof(c.segment_consume_codepoints));
        memcpy(c.word,final[i].text,sizeof(c.word));out[n++]=c;
    }
    qsort(out,n,sizeof(out[0]),candidate_compare);
    return n;
}

size_t zy_composer_lookup(ZYEngine *e,const char *query,ZYCandidate *out,size_t cap){
    ZYComposerWorkspace workspace;
    if(zy_composer_workspace_init(&workspace)!=0)return 0;
    size_t n=zy_composer_lookup_with_workspace(e,query,out,cap,&workspace);
    zy_composer_workspace_dispose(&workspace);
    return n;
}
