#include "cache_probe_bytes.h"
static unsigned int run_cache_entry(unsigned int *value){unsigned i,j,v,base=(unsigned int)(unsigned long)image.base,ok;void *entry;const struct doom_runtime_v1*a=doom_runtime_api();
 if(!a||image.state!=SEG_READY||image.manifest.count!=1||image.manifest.entry!=CACHE_PROBE_ENTRY||image.manifest.segment[0].offset||image.manifest.segment[0].flags!=SEG_RX||image.manifest.segment[0].file_bytes!=sizeof(cache_probe_bytes)||image.manifest.segment[0].memory_bytes!=sizeof(cache_probe_bytes))return 1;
 for(i=0;i<sizeof(cache_probe_bytes);i++)if(image.base[i]!=cache_probe_bytes[i])return 2;
 if(!doom_shared_enter((void*)1))return 3;entry=seg_start(&image);UNLOCK();if(!entry)return 4;
 for(i=0;i<sizeof(cache_probe_sites)/sizeof(*cache_probe_sites);i++){j=cache_probe_sites[i];reloc_store(j,reloc_word(j)+base);}
 if(!sync_code(image.base,sizeof(cache_probe_bytes))){seg_uncertain(&image);exclusive_abort();return 5;}
#ifndef UPLOAD_NATIVE
 *value=((unsigned int(*)(const struct doom_runtime_v1*))entry)(a);
#else
 *value=cache_entry(a);
#endif
 for(i=0;i<sizeof(cache_probe_bytes);i++){
  unsigned k,expected=cache_probe_bytes[i];
  for(k=0;k<sizeof(cache_probe_sites)/sizeof(*cache_probe_sites);k++)if(i>=cache_probe_sites[k]&&i<cache_probe_sites[k]+4){unsigned q=cache_probe_sites[k],l,w=0;for(l=0;l<4;l++)w|=(unsigned)cache_probe_bytes[q+l]<<(8*l);expected=((w+base)>>(8*(i-q)))&255;break;}
  if(image.base[i]!=expected){seg_uncertain(&image);exclusive_abort();return 6;}
 }
 for(i=0;i<sizeof(cache_probe_bytes);i++)image.base[i]=cache_probe_bytes[i];
 if(!sync_code(image.base,sizeof(cache_probe_bytes))){seg_uncertain(&image);exclusive_abort();return 7;}
 if(!doom_shared_enter((void*)1)){exclusive_abort();return 8;}ok=seg_complete(&image);UNLOCK();return ok?0:9;
}
