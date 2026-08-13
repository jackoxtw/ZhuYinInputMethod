#include "ZYConversion.h"
#include <fcntl.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

typedef struct { char magic[8]; uint32_t version,char_count,phrase_count,header_size; uint64_t file_size,trad_off,simp_off,records_off,pool_off,pool_size; } H;
typedef struct { uint32_t trad_off,trad_len,simp_off,simp_len; } R;
static size_t clen(unsigned char c){if(c<0x80)return 1;if((c&0xe0)==0xc0)return 2;if((c&0xf0)==0xe0)return 3;if((c&0xf8)==0xf0)return 4;return 1;}
static uint32_t cpdec(const char *s,size_t n){const unsigned char*p=(const unsigned char*)s;if(!n)return 0;if(p[0]<128)return p[0];if(n>=2&&(p[0]&0xe0)==0xc0)return((p[0]&31)<<6)|(p[1]&63);if(n>=3&&(p[0]&0xf0)==0xe0)return((p[0]&15)<<12)|((p[1]&63)<<6)|(p[2]&63);if(n>=4&&(p[0]&0xf8)==0xf0)return((p[0]&7)<<18)|((p[1]&63)<<12)|((p[2]&63)<<6)|(p[3]&63);return 0;}
static size_t cpenc(uint32_t cp,char o[4]){if(cp<0x80){o[0]=(char)cp;return 1;}if(cp<0x800){o[0]=(char)(0xc0|(cp>>6));o[1]=(char)(0x80|(cp&63));return 2;}if(cp<0x10000){o[0]=(char)(0xe0|(cp>>12));o[1]=(char)(0x80|((cp>>6)&63));o[2]=(char)(0x80|(cp&63));return 3;}o[0]=(char)(0xf0|(cp>>18));o[1]=(char)(0x80|((cp>>12)&63));o[2]=(char)(0x80|((cp>>6)&63));o[3]=(char)(0x80|(cp&63));return 4;}
int zy_conversion_open(ZYConversion*c,const char*path){memset(c,0,sizeof(*c));c->fd=-1;int fd=open(path,O_RDONLY);if(fd<0)return-1;struct stat st;if(fstat(fd,&st)!=0||(size_t)st.st_size<sizeof(H)){close(fd);return-2;}void*m=mmap(NULL,(size_t)st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(m==MAP_FAILED){close(fd);return-3;}const H*h=(const H*)m;if(memcmp(h->magic,"ZYT2S1",6)||h->version!=1||h->file_size!=(uint64_t)st.st_size){munmap(m,st.st_size);close(fd);return-4;}
#define OK(off,n) ((off)<=h->file_size&&(n)<=h->file_size-(off))
if(!OK(h->trad_off,(uint64_t)h->char_count*4)||!OK(h->simp_off,(uint64_t)h->char_count*4)||!OK(h->records_off,(uint64_t)h->phrase_count*sizeof(R))||!OK(h->pool_off,h->pool_size)){munmap(m,st.st_size);close(fd);return-5;}
c->fd=fd;c->size=(size_t)st.st_size;c->map=m;c->char_count=h->char_count;c->phrase_count=h->phrase_count;c->trad_chars=(const uint32_t*)((const uint8_t*)m+h->trad_off);c->simp_chars=(const uint32_t*)((const uint8_t*)m+h->simp_off);c->phrase_records=(const uint8_t*)m+h->records_off;c->pool=(const uint8_t*)m+h->pool_off;c->pool_size=(size_t)h->pool_size;return 0;
#undef OK
}
void zy_conversion_close(ZYConversion*c){if(c->map&&c->size)munmap((void*)c->map,c->size);if(c->fd>=0)close(c->fd);memset(c,0,sizeof(*c));c->fd=-1;}
static uint32_t mapcp(const ZYConversion*c,uint32_t cp){size_t lo=0,hi=c->char_count;while(lo<hi){size_t m=(lo+hi)/2;uint32_t x=c->trad_chars[m];if(x<cp)lo=m+1;else hi=m;}return(lo<c->char_count&&c->trad_chars[lo]==cp)?c->simp_chars[lo]:cp;}
int zy_conversion_t2s(const ZYConversion*c,const char*in,char*out,size_t cap){if(!c||!in||!out||cap==0)return-1;size_t n=strlen(in),ip=0,op=0;const R*rs=(const R*)c->phrase_records;while(ip<n){const R*best=NULL;for(uint32_t i=0;i<c->phrase_count;i++){const R*r=&rs[i];if(r->trad_len<=n-ip&&r->trad_off+r->trad_len<=c->pool_size&&memcmp(in+ip,c->pool+r->trad_off,r->trad_len)==0){best=r;break;}}if(best){if(op+best->simp_len>=cap)return-2;memcpy(out+op,c->pool+best->simp_off,best->simp_len);op+=best->simp_len;ip+=best->trad_len;continue;}size_t k=clen((unsigned char)in[ip]);if(ip+k>n)k=1;uint32_t cp=mapcp(c,cpdec(in+ip,k));char tmp[4];size_t w=cpenc(cp,tmp);if(op+w>=cap)return-2;memcpy(out+op,tmp,w);op+=w;ip+=k;}out[op]=0;return 0;}
