#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "ZYDictionary.h"

static unsigned char *read_all(const char *path,size_t *n){
    struct stat st;assert(stat(path,&st)==0);FILE*f=fopen(path,"rb");assert(f);unsigned char*b=malloc((size_t)st.st_size);assert(b);assert(fread(b,1,(size_t)st.st_size,f)==(size_t)st.st_size);fclose(f);*n=(size_t)st.st_size;return b;
}
static void write_all(const char *path,const unsigned char *b,size_t n){FILE*f=fopen(path,"wb");assert(f);assert(fwrite(b,1,n,f)==n);fclose(f);}
static void expect_bad(const char *path,unsigned char *b,size_t n){write_all(path,b,n);ZYDictionary d;assert(zy_dict_open(&d,path)!=0);}

int main(int argc,char **argv){
    assert(argc==3);const char *src=argv[1],*tmp=argv[2];size_t n=0;unsigned char *orig=read_all(src,&n);assert(n>=sizeof(ZYDictHeader));
    const ZYDictHeader *h=(const ZYDictHeader*)orig;assert(memcmp(h->magic,"ZYDICT2",7)==0&&h->version==2);
    ZYDictionary d;assert(zy_dict_open(&d,src)==0);zy_dict_close(&d);

    /* Reader remains backward compatible with the same v1 layout. */
    unsigned char *b=malloc(n);assert(b);memcpy(b,orig,n);memcpy(b,"ZYDICT1\0",8);((ZYDictHeader*)b)->version=1;write_all(tmp,b,n);assert(zy_dict_open(&d,tmp)==0);zy_dict_close(&d);

    /* Word offset sentinel must exactly match the pool size. */
    memcpy(b,orig,n);ZYDictHeader *m=(ZYDictHeader*)b;uint32_t *word_offsets=(uint32_t*)(b+m->word_offsets_off);word_offsets[m->word_count]--;expect_bad(tmp,b,n);

    /* Pronunciation offsets must be monotonic and end at syllable_ids_count. */
    memcpy(b,orig,n);m=(ZYDictHeader*)b;uint32_t *pron_offsets=(uint32_t*)(b+m->pron_offsets_off);if(m->word_count>2)pron_offsets[2]=pron_offsets[1]-1;expect_bad(tmp,b,n);

    /* Every pronunciation ID must address the syllable table. */
    memcpy(b,orig,n);m=(ZYDictHeader*)b;uint16_t *sids=(uint16_t*)(b+m->syllable_ids_off);assert(m->syllable_ids_count>0);sids[0]=(uint16_t)m->syllable_count;expect_bad(tmp,b,n);

    /* Every bucket word ID must address the word table. */
    memcpy(b,orig,n);m=(ZYDictHeader*)b;uint32_t *wids=(uint32_t*)(b+m->bucket_word_ids_off);assert(m->bucket_word_ids_count>0);wids[0]=m->word_count;expect_bad(tmp,b,n);

    /* Bucket sentinel must match bucket_word_ids_count. */
    memcpy(b,orig,n);m=(ZYDictHeader*)b;uint32_t *bo=(uint32_t*)(b+m->bucket_offsets_off);bo[m->bucket_count]--;expect_bad(tmp,b,n);

    unlink(tmp);free(b);free(orig);puts("test_dictionary_v2_validation: OK");return 0;
}
