#include "owned_probe_bytes.h"
static unsigned owned_last[8];
static unsigned run_owned(unsigned *value){unsigned i,j,k,base=(unsigned)(unsigned long)image.base,ok;void*entry;const struct doom_runtime_owned*a=doom_runtime_owned_api();const struct segment*s=image.manifest.segment;
 if(!a||image.state!=SEG_READY||image.manifest.count!=3||image.manifest.entry!=OWNED_ENTRY)return 1;
 for(i=0;i<3;i++)if(s[i].offset!=owned_geometry[i][0]||s[i].file_bytes!=owned_geometry[i][1]||s[i].memory_bytes!=owned_geometry[i][2]||s[i].flags!=owned_geometry[i][3])return 1;
 for(i=0;i<3;i++)for(j=0;j<s[i].memory_bytes;j++)if(image.base[s[i].offset+j]!=(j<s[i].file_bytes?owned_probe_bytes[s[i].offset+j]:0))return 2;
 if(!doom_shared_enter((void*)1))return 3;entry=seg_start(&image);UNLOCK();if(!entry)return 4;
 if(!doom_runtime_owned_begin()){seg_uncertain(&image);exclusive_abort();return 5;}
 for(i=0;i<sizeof(owned_probe_sites)/sizeof(*owned_probe_sites);i++){j=owned_probe_sites[i];reloc_store(j,reloc_word(j)+base);}
 if(!sync_code(image.base,owned_geometry[0][1])){seg_uncertain(&image);exclusive_abort();return 6;}
#ifndef UPLOAD_NATIVE
 *value=((unsigned(*)(const struct doom_runtime_owned*))entry)(a);
 for(i=0;i<8;i++)owned_last[i]=reloc_word(OWNED_RESULT+4*i);
#else
 *value=owned_entry(a);for(i=0;i<8;i++){owned_last[i]=owned_result[i];owned_result[i]=0;}
#endif
 if((owned_last[6]!=37&&owned_last[6]!=53)||*value!=(DOOM_OWNED_MAGIC^0x49393630u^owned_last[6])||owned_last[0]!=(0x49393630u^7)||owned_last[1]!=3||owned_last[2]!=2||owned_last[7]||owned_last[5]!=(owned_last[6]==53)){seg_uncertain(&image);exclusive_abort();return 7;}
 for(i=0;i<3;i++)for(j=0;j<s[i].file_bytes;j++){unsigned off=s[i].offset+j,v=owned_probe_bytes[off];
  for(k=0;k<sizeof(owned_probe_sites)/sizeof(*owned_probe_sites);k++)if(off>=owned_probe_sites[k]&&off<owned_probe_sites[k]+4){unsigned q=owned_probe_sites[k],l,w=0;for(l=0;l<4;l++)w|=(unsigned)owned_probe_bytes[q+l]<<(8*l);v=((w+base)>>(8*(off-q)))&255;break;}
  if(image.base[off]!=v){seg_uncertain(&image);exclusive_abort();return 8;}
 }
 if(!doom_runtime_owned_end()){seg_uncertain(&image);exclusive_abort();return 9;}
 for(i=0;i<3;i++)for(j=0;j<s[i].memory_bytes;j++)image.base[s[i].offset+j]=j<s[i].file_bytes?owned_probe_bytes[s[i].offset+j]:0;
 if(!sync_code(image.base,owned_geometry[0][1])){seg_uncertain(&image);exclusive_abort();return 10;}
 if(!doom_shared_enter((void*)1)){exclusive_abort();return 11;}ok=seg_complete(&image);UNLOCK();return ok?0:12;
}
