#include "ZYEngine.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>


int zy_candidate_rank_compare(const void *aa,const void *bb){
    const ZYCandidate *a=(const ZYCandidate*)aa,*b=(const ZYCandidate*)bb;
    if(a->literal!=b->literal)return a->literal?1:-1;
    if(a->preference_rank!=b->preference_rank)return a->preference_rank>b->preference_rank?-1:1;
    if(a->score!=b->score)return a->score>b->score?-1:1;
    return strcmp(a->word,b->word);
}

static size_t utf8_char_len(unsigned char c){if(c<0x80)return 1;if((c&0xE0)==0xC0)return 2;if((c&0xF0)==0xE0)return 3;if((c&0xF8)==0xF0)return 4;return 1;}
static uint32_t utf8_cp(const char *s,size_t n){
    const unsigned char *p=(const unsigned char*)s; if(!n)return 0;
    if(p[0]<0x80)return p[0]; if(n>=2&&(p[0]&0xE0)==0xC0)return ((p[0]&31)<<6)|(p[1]&63);
    if(n>=3&&(p[0]&0xF0)==0xE0)return ((p[0]&15)<<12)|((p[1]&63)<<6)|(p[2]&63);
    if(n>=4&&(p[0]&0xF8)==0xF0)return ((p[0]&7)<<18)|((p[1]&63)<<12)|((p[2]&63)<<6)|(p[3]&63); return 0;
}
static size_t codepoints(const char *s,size_t n){size_t c=0,i=0;while(i<n){size_t k=utf8_char_len((unsigned char)s[i]);if(i+k>n)break;i+=k;c++;}return c;}

static int learned_continuation_compare(const ZYCandidate *a,const ZYCandidate *b){
    size_t al=codepoints(a->word,strlen(a->word)),bl=codepoints(b->word,strlen(b->word));
    if(al!=bl)return al<bl?-1:1;
    return zy_candidate_rank_compare(a,b);
}
static int candidate_word_already_output(const ZYCandidate *out,size_t count,const char *word){
    for(size_t i=0;i<count;i++)if(strcmp(out[i].word,word)==0)return 1;
    return 0;
}

size_t zy_candidate_apply_length_policy(const ZYCandidate *in,size_t count,ZYCandidate *out,size_t cap){
    if(!in||!out||!cap)return 0;
    size_t en=0,ln=0;
    for(size_t i=0;i<count;i++){
        const ZYCandidate *c=&in[i];size_t wl=codepoints(c->word,strlen(c->word));
        if(c->matched_chars>0&&wl==c->matched_chars)en++;
        else if(c->learned&&c->matched_chars>0&&wl>c->matched_chars)ln++;
    }
    if(!en){size_t n=count<cap?count:cap;if(n)memcpy(out,in,n*sizeof(out[0]));return n;}
    if(!ln){
        size_t n=0;for(size_t i=0;i<count&&n<cap;i++){
            size_t wl=codepoints(in[i].word,strlen(in[i].word));
            if(in[i].matched_chars>0&&wl==in[i].matched_chars)out[n++]=in[i];
        }
        return n;
    }
    size_t reserve=(cap+2)/3;if(reserve<1)reserve=1;if(reserve>ln)reserve=ln;
    size_t exact_cap=cap>reserve?cap-reserve:1;if(exact_cap>20)exact_cap=20;if(exact_cap>en)exact_cap=en;
    size_t n=0;
    for(size_t i=0;i<count&&n<exact_cap;i++){
        size_t wl=codepoints(in[i].word,strlen(in[i].word));
        if(in[i].matched_chars>0&&wl==in[i].matched_chars)out[n++]=in[i];
    }
    while(n<cap){
        const ZYCandidate *best=NULL;
        for(size_t i=0;i<count;i++){
            const ZYCandidate *c=&in[i];size_t wl=codepoints(c->word,strlen(c->word));
            if(!c->learned||!c->matched_chars||wl<=c->matched_chars)continue;
            if(candidate_word_already_output(out,n,c->word))continue;
            if(!best||learned_continuation_compare(c,best)<0)best=c;
        }
        if(!best)break;
        out[n++]=*best;
    }
    return n;
}

static int is_tone_cp(uint32_t cp){return cp==0x02C9||cp==0x02CA||cp==0x02C7||cp==0x02CB||cp==0x02D9;}
static size_t explicit_first_tone_len(const char *q,size_t qn,size_t pos){
    if(pos>=qn)return 0;size_t k=utf8_char_len((unsigned char)q[pos]);if(pos+k>qn)return 0;
    return utf8_cp(q+pos,k)==0x02C9?k:0;
}
static size_t syllable_bare_len(const char *s,size_t n){
    if(!n)return 0; size_t last=0,i=0; while(i<n){last=i;i+=utf8_char_len((unsigned char)s[i]);} uint32_t cp=utf8_cp(s+last,n-last); return is_tone_cp(cp)?last:n;
}
static int prefix(const char *q,size_t qn,size_t pos,const char *r,size_t rn){return pos+rn<=qn && memcmp(q+pos,r,rn)==0;}

typedef struct {int valid,exact,remaining,matched,initials,full,toned,quality,word_complete;size_t consumed;} MR;
static int klass(MR m){if(!m.matched)return 0;if(m.initials==m.matched)return 1;if(m.initials>0)return 2;if(m.toned>0)return 4;return 3;}
static int better(MR a,MR b){if(!a.valid)return 0;if(!b.valid)return 1;int ka=klass(a),kb=klass(b);if(ka!=kb)return ka>kb;if(a.word_complete!=b.word_complete)return a.word_complete>b.word_complete;return a.quality>b.quality;}

static MR match_rec_mode(const ZYDictionary *d,uint32_t si,uint32_t end,const char *q,size_t qn,size_t pos,int allow_suffix){
    if(si==end){
        if(pos==qn||allow_suffix){MR r={1,pos==qn,0,0,0,0,0,0,1,pos};return r;}
        MR z={0};return z;
    }
    if(pos==qn){MR r={1,0,(int)(end-si),0,0,0,0,0,0,pos};return r;}
    uint16_t sid=d->syllable_ids[si]; const char *s=NULL; size_t sn=0; if(zy_dict_syllable(d,sid,&s,&sn)!=0){MR z={0};return z;}
    size_t bare=syllable_bare_len(s,sn), onset=utf8_char_len((unsigned char)s[0]); MR best={0};
    // If the remaining query is a proper prefix of the current syllable, the
    // user is still typing that syllable.  Treat it as a high-quality partial
    // syllable rather than an initial-only abbreviation.
    size_t tail=qn-pos;
    if(tail>0 && tail<bare && memcmp(s,q+pos,tail)==0){
        MR t={1,0,(int)(end-si-1),1,0,1,0,2,0,qn};
        if(better(t,best))best=t;
    }
    struct Opt{size_t len;int kind;} opts[4];int no=0;
    if(sn==bare && bare && prefix(q,qn,pos,s,bare)){size_t ft=explicit_first_tone_len(q,qn,pos+bare);if(ft)opts[no++]=(struct Opt){bare+ft,4};}
    if(sn!=bare && prefix(q,qn,pos,s,sn)) opts[no++]=(struct Opt){sn,4};
    if(bare && prefix(q,qn,pos,s,bare)) opts[no++]=(struct Opt){bare,3};
    if(onset && onset!=bare && prefix(q,qn,pos,s,onset)) opts[no++]=(struct Opt){onset,1};
    for(int i=0;i<no;i++){
        MR t=match_rec_mode(d,si+1,end,q,qn,pos+opts[i].len,allow_suffix); if(!t.valid)continue;
        t.matched++;t.quality+=opts[i].kind;if(opts[i].kind==1)t.initials++;else{t.full++;if(opts[i].kind==4)t.toned++;}
        if(better(t,best))best=t;
    }
    return best;
}
static MR match_word_mode(const ZYDictionary *d,uint32_t wid,const char *q,size_t qn,int allow_suffix){uint32_t a=d->pron_offsets[wid],b=d->pron_offsets[wid+1];if(a==b){MR z={0};return z;}return match_rec_mode(d,a,b,q,qn,0,allow_suffix);}
static MR match_word(const ZYDictionary *d,uint32_t wid,const char *q,size_t qn){return match_word_mode(d,wid,q,qn,0);}

static void copy_word(const ZYDictionary *d,uint32_t wid,char out[ZY_CANDIDATE_WORD_BYTES]){const char *p;size_t n;if(zy_dict_word(d,wid,&p,&n)!=0){out[0]=0;return;}if(n>=ZY_CANDIDATE_WORD_BYTES)n=ZY_CANDIDATE_WORD_BYTES-1;memcpy(out,p,n);out[n]=0;}
static int same_word(const ZYCandidate *a,const char *w){return strcmp(a->word,w)==0;}
static void insert_top(ZYCandidate *out,size_t *n,size_t cap,ZYCandidate c){
    for(size_t i=0;i<*n;i++)if(same_word(&out[i],c.word)){if(c.score>out[i].score)out[i]=c;return;}
    size_t pos=0;while(pos<*n && out[pos].score>=c.score)pos++;
    if(pos>=cap)return; if(*n<cap)(*n)++; for(size_t i=*n-1;i>pos;i--)out[i]=out[i-1];out[pos]=c;
}
static int single_prefix_match(const ZYDictionary *d,uint32_t wid,const char *q,size_t qn,size_t *consumed,int *kind){
    uint32_t a=d->pron_offsets[wid],b=d->pron_offsets[wid+1];if(b-a!=1)return 0;const char *s;size_t sn;if(zy_dict_syllable(d,d->syllable_ids[a],&s,&sn)!=0)return 0;
    size_t bare=syllable_bare_len(s,sn),onset=utf8_char_len((unsigned char)s[0]);size_t best=0;int k=0;
    if(sn==bare&&bare&&prefix(q,qn,0,s,bare)){size_t ft=explicit_first_tone_len(q,qn,bare);if(ft){best=bare+ft;k=4;}}
    if(sn!=bare&&prefix(q,qn,0,s,sn)){best=sn;k=4;} if(bare&&prefix(q,qn,0,s,bare)&&bare>best){best=bare;k=3;} if(onset!=bare&&prefix(q,qn,0,s,onset)&&onset>best){best=onset;k=1;}
    if(!best)return 0;*consumed=best;*kind=k;return 1;
}

int zy_engine_open(ZYEngine *e,const char *path){memset(e,0,sizeof(*e));return zy_dict_open(&e->dict,path);}void zy_engine_close(ZYEngine *e){zy_dict_close(&e->dict);}
size_t zy_engine_lookup(ZYEngine *e,const char *query,ZYCandidate *out,size_t cap){
    if(!e||!query||!out||!cap)return 0;size_t qn=strlen(query);if(!qn)return 0;uint32_t first=utf8_cp(query,qn),a=0,b=0;if(zy_dict_bucket(&e->dict,first,&a,&b)!=0)return 0;size_t n=0;
    for(uint32_t bi=a;bi<b;bi++){
        uint32_t wid=e->dict.bucket_word_ids[bi];MR m=match_word(&e->dict,wid,query,qn);if(!m.valid)continue;
        int rem=m.remaining;long sc=(long)klass(m)*1000000L+(m.exact?600000L:0)-((rem*15000L)>200000L?200000L:rem*15000L)+(long)e->dict.weights[wid]*1000L;
        ZYCandidate c={0};c.id=wid;c.score=(int32_t)sc;c.match_class=(uint8_t)klass(m);c.matched_chars=(uint8_t)m.matched;c.dictionary_exact=(uint8_t)m.exact;c.word_complete=(uint8_t)m.word_complete;c.final_syllable_partial=(uint8_t)(!m.exact&&!m.word_complete&&m.remaining==0&&m.matched>0);copy_word(&e->dict,wid,c.word);
        // A long mixed abbreviation that has already reached every syllable is
        // specific enough for a soft recall priority.  Requiring 5+ syllables
        // prevents short input from surfacing unrelated long dictionary words.
        if(m.initials>0&&m.matched>=5&&m.remaining==0&&codepoints(c.word,strlen(c.word))>=5)c.preference_rank=1;
        insert_top(out,&n,cap,c);
    }
    // Single-character fallback for the first input syllable.
    for(uint32_t bi=a;bi<b;bi++){
        uint32_t wid=e->dict.bucket_word_ids[bi];size_t consumed=0;int k=0;if(!single_prefix_match(&e->dict,wid,query,qn,&consumed,&k))continue;
        const char *wp;size_t wn;if(zy_dict_word(&e->dict,wid,&wp,&wn)!=0||codepoints(wp,wn)!=1)continue;
        ZYCandidate c={0};c.id=wid;c.score=k*1000000+(int)e->dict.weights[wid]*1000-100000;c.match_class=(uint8_t)k;c.matched_chars=1;c.consume_codepoints=(uint8_t)codepoints(query,consumed);copy_word(&e->dict,wid,c.word);insert_top(out,&n,cap,c);
    }
    // Raw Bopomofo literal candidate is intentionally lowest-priority and never learned as a Chinese word.
    ZYCandidate lit={0};lit.id=UINT32_MAX;lit.score=INT_MIN/2;lit.literal=1;size_t copy=qn<ZY_CANDIDATE_WORD_BYTES-1?qn:ZY_CANDIDATE_WORD_BYTES-1;memcpy(lit.word,query,copy);lit.word[copy]=0;
    if(n<cap){out[n++]=lit;}else{out[cap-1]=lit;}
    qsort(out,n,sizeof(out[0]),zy_candidate_rank_compare);
    return n;
}


size_t zy_engine_lookup_prefix(ZYEngine *e,const char *query,ZYCandidate *out,size_t cap){
    if(!e||!query||!out||!cap)return 0;size_t qn=strlen(query);if(!qn)return 0;uint32_t first=utf8_cp(query,qn),a=0,b=0;if(zy_dict_bucket(&e->dict,first,&a,&b)!=0)return 0;size_t n=0;
    // Reserve a small fraction of prefix edges for longer (3+ syllable)
    // matches. This prevents one-character fallbacks from consuming all
    // composer edge slots before a real long word such as 資料庫 can be considered,
    // while avoiding noisy two-syllable abbreviation ambiguities.
    enum { ZY_PREFIX_MULTI_RESERVE_MAX = 4 };
    ZYCandidate multi[ZY_PREFIX_MULTI_RESERVE_MAX];size_t mn=0;
    size_t multi_reserve=cap>=6?cap/3:1;if(multi_reserve>ZY_PREFIX_MULTI_RESERVE_MAX)multi_reserve=ZY_PREFIX_MULTI_RESERVE_MAX;if(multi_reserve>cap)multi_reserve=cap;
    for(uint32_t bi=a;bi<b;bi++){
        uint32_t wid=e->dict.bucket_word_ids[bi];MR m=match_word_mode(&e->dict,wid,query,qn,1);if(!m.valid||!m.consumed)continue;
        int rem=m.remaining;long sc=(long)klass(m)*1000000L+(m.exact?600000L:0)-((rem*15000L)>200000L?200000L:rem*15000L)+(long)e->dict.weights[wid]*1000L;
        ZYCandidate c={0};c.id=wid;c.score=(int32_t)sc;c.match_class=(uint8_t)klass(m);c.matched_chars=(uint8_t)m.matched;c.dictionary_exact=(uint8_t)m.exact;c.word_complete=(uint8_t)m.word_complete;c.final_syllable_partial=(uint8_t)(!m.exact&&!m.word_complete&&m.remaining==0&&m.matched>0);c.consume_codepoints=(uint8_t)codepoints(query,m.consumed);copy_word(&e->dict,wid,c.word);insert_top(out,&n,cap,c);
        if(codepoints(c.word,strlen(c.word))>1 && c.matched_chars>=3)
            insert_top(multi,&mn,multi_reserve,c);
    }
    for(size_t mi=0;mi<mn;mi++){
        int present=0;for(size_t oi=0;oi<n;oi++)if(strcmp(out[oi].word,multi[mi].word)==0){present=1;break;}
        if(present)continue;
        size_t victim=n;for(size_t oi=n;oi>0;oi--){size_t j=oi-1;if(codepoints(out[j].word,strlen(out[j].word))==1){victim=j;break;}}
        if(victim<n)out[victim]=multi[mi];else if(n<cap)out[n++]=multi[mi];
    }
    qsort(out,n,sizeof(out[0]),zy_candidate_rank_compare);
    return n;
}

int zy_engine_pronunciation_key(ZYEngine *e,uint32_t word_id,char *out,size_t cap){
    if(!e||!out||cap==0||word_id>=e->dict.h->word_count)return -1;
    uint32_t a=e->dict.pron_offsets[word_id],b=e->dict.pron_offsets[word_id+1];size_t pos=0;
    for(uint32_t i=a;i<b;i++){
        const char *s;size_t n;if(zy_dict_syllable(&e->dict,e->dict.syllable_ids[i],&s,&n)!=0)return -2;
        if(i>a){if(pos+1>=cap)return -3;out[pos++]=0x1f;}
        if(pos+n>=cap)return -3;memcpy(out+pos,s,n);pos+=n;
    }
    out[pos]=0;return 0;
}

typedef struct {const char *p;size_t n;} ZYSlice;
static MR match_slice_rec(const ZYSlice *seq,size_t count,size_t si,const char*q,size_t qn,size_t pos){
    if(pos==qn){MR r={1,si==count,(int)(count-si),0,0,0,0,0};return r;}
    if(si==count){MR z={0};return z;}
    const char*s=seq[si].p;size_t sn=seq[si].n,bare=syllable_bare_len(s,sn),onset=utf8_char_len((unsigned char)s[0]);MR best={0};
    size_t tail=qn-pos;
    if(tail>0 && tail<bare && memcmp(s,q+pos,tail)==0){
        MR t={1,0,(int)(count-si-1),1,0,1,0,2};
        if(better(t,best))best=t;
    }
    struct Opt{size_t len;int kind;}opts[4];int no=0;
    if(sn==bare&&bare&&prefix(q,qn,pos,s,bare)){size_t ft=explicit_first_tone_len(q,qn,pos+bare);if(ft)opts[no++]=(struct Opt){bare+ft,4};}
    if(sn!=bare&&prefix(q,qn,pos,s,sn))opts[no++]=(struct Opt){sn,4};
    if(bare&&prefix(q,qn,pos,s,bare))opts[no++]=(struct Opt){bare,3};
    if(onset&&onset!=bare&&prefix(q,qn,pos,s,onset))opts[no++]=(struct Opt){onset,1};
    for(int i=0;i<no;i++){MR t=match_slice_rec(seq,count,si+1,q,qn,pos+opts[i].len);if(!t.valid)continue;t.matched++;t.quality+=opts[i].kind;if(opts[i].kind==1)t.initials++;else{t.full++;if(opts[i].kind==4)t.toned++;}if(better(t,best))best=t;}
    return best;
}
int zy_engine_match_pron_key(const char *query,const char *pron_key,uint8_t *mc,uint8_t *matched,int *exact){
    if(!query||!*query||!pron_key||!*pron_key)return 0;ZYSlice seq[32];size_t n=0;const char*p=pron_key,*start=p;
    for(;;p++){
        if(*p==0x1f||*p==0){if(p>start&&n<32){seq[n].p=start;seq[n].n=(size_t)(p-start);n++;}if(*p==0)break;start=p+1;}
    }
    if(!n)return 0;MR r=match_slice_rec(seq,n,0,query,strlen(query),0);if(!r.valid)return 0;if(mc)*mc=(uint8_t)klass(r);if(matched)*matched=(uint8_t)r.matched;if(exact)*exact=r.exact;return 1;
}
