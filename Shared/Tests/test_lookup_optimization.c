#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ZYDictionary.h"
#include "ZYEngine.h"
#include "ZYComposer.h"

int main(int argc,char **argv){
    assert(argc==2);
    ZYDictionary d;assert(zy_dict_open(&d,argv[1])==0);
    const uint32_t cps[]={0x3105u,0x3107u,0x3110u,0x3115u,0x3127u,0x3129u};
    for(size_t i=0;i<sizeof(cps)/sizeof(cps[0]);i++){
        uint32_t a=0,b=0;assert(zy_dict_bucket(&d,cps[i],&a,&b)==0);assert(b>a);
    }
    zy_dict_close(&d);
    size_t bytes=zy_composer_workspace_bytes();
    assert(bytes<=300000u);
    printf("test_lookup_optimization: workspace=%zu bytes OK\n",bytes);
    return 0;
}
