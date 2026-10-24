#include "ZYDictionary.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef _WIN32
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

static int range_ok(const ZYDictionary *d, uint64_t off, uint64_t bytes) {
    return off <= d->size && bytes <= d->size - off;
}
static int offsets_ok(const uint32_t *v,uint32_t count,uint64_t limit){
    if(!v)return 0;
    if(v[0]!=0)return 0;
    for(uint32_t i=0;i<count;i++)if(v[i]>v[i+1]||(uint64_t)v[i+1]>limit)return 0;
    return (uint64_t)v[count]==limit;
}
static int validate_dictionary(const ZYDictionary *d){
    if(!d||!d->h)return 0;
    const ZYDictHeader *h=d->h;
    if(h->header_size!=sizeof(ZYDictHeader))return 0;
    if(h->indexed_word_count>h->word_count)return 0;
    if(h->word_count==0||h->syllable_count==0)return 0;
    if(!offsets_ok(d->word_offsets,h->word_count,h->word_pool_size))return 0;
    if(!offsets_ok(d->pron_offsets,h->word_count,h->syllable_ids_count))return 0;
    if(!offsets_ok(d->syllable_offsets,h->syllable_count,h->syllable_pool_size))return 0;
    if(!offsets_ok(d->bucket_offsets,h->bucket_count,h->bucket_word_ids_count))return 0;
    if(h->bucket_word_ids_count<h->indexed_word_count)return 0;
    for(uint64_t i=0;i<h->syllable_ids_count;i++)if(d->syllable_ids[i]>=h->syllable_count)return 0;
    for(uint64_t i=0;i<h->bucket_word_ids_count;i++)if(d->bucket_word_ids[i]>=h->word_count)return 0;
    for(uint32_t i=1;i<h->bucket_count;i++)if(d->bucket_symbols[i-1]>=d->bucket_symbols[i])return 0;
    return 1;
}

int zy_dict_open(ZYDictionary *d, const char *path) {
    if(!d||!path)return -1;
    memset(d,0,sizeof(*d)); d->fd=-1;
#ifdef _WIN32
    FILE *fp=fopen(path,"rb"); if(!fp)return -1;
    if(fseek(fp,0,SEEK_END)!=0){fclose(fp);return -2;}
    long end=ftell(fp); if(end<(long)sizeof(ZYDictHeader)){fclose(fp);return -2;}
    if(fseek(fp,0,SEEK_SET)!=0){fclose(fp);return -2;}
    uint8_t *m=(uint8_t*)malloc((size_t)end); if(!m){fclose(fp);return -3;}
    if(fread(m,1,(size_t)end,fp)!=(size_t)end){free(m);fclose(fp);return -3;}
    fclose(fp);d->fd=-1;d->size=(size_t)end;d->map=m;d->h=(const ZYDictHeader*)m;
#else
    int fd=open(path,O_RDONLY); if(fd<0) return -1;
    struct stat st; if(fstat(fd,&st)!=0 || st.st_size<(off_t)sizeof(ZYDictHeader)){close(fd);return -2;}
    void *m=mmap(NULL,(size_t)st.st_size,PROT_READ,MAP_PRIVATE,fd,0); if(m==MAP_FAILED){close(fd);return -3;}
    d->fd=fd; d->size=(size_t)st.st_size; d->map=(const uint8_t*)m; d->h=(const ZYDictHeader*)m;
#endif
    int is_v1=memcmp(d->h->magic,"ZYDICT1",7)==0&&d->h->version==1;
    int is_v2=memcmp(d->h->magic,"ZYDICT2",7)==0&&d->h->version==2;
    if((!is_v1&&!is_v2)||d->h->file_size!=d->size||d->h->header_size!=sizeof(ZYDictHeader)){zy_dict_close(d);return -4;}
#define SETPTR(field,off,bytes,type) do{ if(!range_ok(d,d->h->off,(bytes))){zy_dict_close(d);return -5;} d->field=(const type*)(d->map+d->h->off); }while(0)
    SETPTR(word_pool,word_pool_off,d->h->word_pool_size,uint8_t);
    SETPTR(word_offsets,word_offsets_off,(uint64_t)(d->h->word_count+1)*4,uint32_t);
    SETPTR(pron_offsets,pron_offsets_off,(uint64_t)(d->h->word_count+1)*4,uint32_t);
    SETPTR(syllable_ids,syllable_ids_off,d->h->syllable_ids_count*2,uint16_t);
    SETPTR(weights,weights_off,d->h->word_count,uint8_t);
    SETPTR(syllable_pool,syllable_pool_off,d->h->syllable_pool_size,uint8_t);
    SETPTR(syllable_offsets,syllable_offsets_off,(uint64_t)(d->h->syllable_count+1)*4,uint32_t);
    SETPTR(bucket_symbols,bucket_symbols_off,(uint64_t)d->h->bucket_count*4,uint32_t);
    SETPTR(bucket_offsets,bucket_offsets_off,(uint64_t)(d->h->bucket_count+1)*4,uint32_t);
    SETPTR(bucket_word_ids,bucket_word_ids_off,d->h->bucket_word_ids_count*4,uint32_t);
#undef SETPTR
    if(!validate_dictionary(d)){zy_dict_close(d);return -6;}
    return 0;
}

void zy_dict_close(ZYDictionary *d){
    if(!d)return;
#ifdef _WIN32
    if(d->map) free((void*)d->map);
#else
    if(d->map && d->size) munmap((void*)d->map,d->size);
    if(d->fd>=0) close(d->fd);
#endif
    memset(d,0,sizeof(*d)); d->fd=-1;
}

int zy_dict_word(const ZYDictionary *d, uint32_t id, const char **ptr, size_t *len){
    if(!d||!d->h||!ptr||!len||id>=d->h->word_count) return -1;
    uint32_t a=d->word_offsets[id],b=d->word_offsets[id+1]; if(b<a||b>d->h->word_pool_size)return -2;
    *ptr=(const char*)d->word_pool+a; *len=(size_t)(b-a); return 0;
}
int zy_dict_syllable(const ZYDictionary *d, uint16_t sid, const char **ptr, size_t *len){
    if(!d||!d->h||!ptr||!len||sid>=d->h->syllable_count)return -1;
    uint32_t a=d->syllable_offsets[sid],b=d->syllable_offsets[sid+1]; if(b<a||b>d->h->syllable_pool_size)return -2;
    *ptr=(const char*)d->syllable_pool+a; *len=(size_t)(b-a); return 0;
}
int zy_dict_bucket(const ZYDictionary *d,uint32_t cp,uint32_t *start,uint32_t *end){
    if(!d||!d->h||!start||!end)return -1;
    /* Current native dictionaries use two tone buckets followed by the
       contiguous Bopomofo block U+3105..U+3129.  Resolve those in O(1) while
       retaining a tiny binary-search fallback for legacy/custom dictionaries. */
    uint32_t i=UINT32_MAX;
    if(cp==0x02C7u)i=0;
    else if(cp==0x02CAu)i=1;
    else if(cp>=0x3105u&&cp<=0x3129u)i=2u+(cp-0x3105u);
    if(i<d->h->bucket_count&&d->bucket_symbols[i]==cp){
        *start=d->bucket_offsets[i];*end=d->bucket_offsets[i+1];return 0;
    }
    uint32_t lo=0,hi=d->h->bucket_count;
    while(lo<hi){
        uint32_t mid=lo+(hi-lo)/2, v=d->bucket_symbols[mid];
        if(v<cp)lo=mid+1;else hi=mid;
    }
    if(lo<d->h->bucket_count&&d->bucket_symbols[lo]==cp){*start=d->bucket_offsets[lo];*end=d->bucket_offsets[lo+1];return 0;}
    return -1;
}
