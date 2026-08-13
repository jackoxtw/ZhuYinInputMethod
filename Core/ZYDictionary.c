#include "ZYDictionary.h"
#include <fcntl.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static int range_ok(const ZYDictionary *d, uint64_t off, uint64_t bytes) {
    return off <= d->size && bytes <= d->size - off;
}

int zy_dict_open(ZYDictionary *d, const char *path) {
    memset(d,0,sizeof(*d)); d->fd=-1;
    int fd=open(path,O_RDONLY); if(fd<0) return -1;
    struct stat st; if(fstat(fd,&st)!=0 || st.st_size<(off_t)sizeof(ZYDictHeader)){close(fd);return -2;}
    void *m=mmap(NULL,(size_t)st.st_size,PROT_READ,MAP_PRIVATE,fd,0); if(m==MAP_FAILED){close(fd);return -3;}
    d->fd=fd; d->size=(size_t)st.st_size; d->map=(const uint8_t*)m; d->h=(const ZYDictHeader*)m;
    if(memcmp(d->h->magic,"ZYDICT1",7)!=0 || d->h->version!=1 || d->h->file_size!=d->size){zy_dict_close(d);return -4;}
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
    return 0;
}

void zy_dict_close(ZYDictionary *d){
    if(d->map && d->size) munmap((void*)d->map,d->size);
    if(d->fd>=0) close(d->fd);
    memset(d,0,sizeof(*d)); d->fd=-1;
}

int zy_dict_word(const ZYDictionary *d, uint32_t id, const char **ptr, size_t *len){
    if(!d||!d->h||id>=d->h->word_count) return -1;
    uint32_t a=d->word_offsets[id],b=d->word_offsets[id+1]; if(b<a||b>d->h->word_pool_size)return -2;
    *ptr=(const char*)d->word_pool+a; *len=(size_t)(b-a); return 0;
}
int zy_dict_syllable(const ZYDictionary *d, uint16_t sid, const char **ptr, size_t *len){
    if(!d||!d->h||sid>=d->h->syllable_count)return -1;
    uint32_t a=d->syllable_offsets[sid],b=d->syllable_offsets[sid+1]; if(b<a||b>d->h->syllable_pool_size)return -2;
    *ptr=(const char*)d->syllable_pool+a; *len=(size_t)(b-a); return 0;
}
int zy_dict_bucket(const ZYDictionary *d,uint32_t cp,uint32_t *start,uint32_t *end){
    for(uint32_t i=0;i<d->h->bucket_count;i++) if(d->bucket_symbols[i]==cp){*start=d->bucket_offsets[i];*end=d->bucket_offsets[i+1];return 0;} return -1;
}
