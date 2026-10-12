/* Closed, build-generated relocation proof. Called only by worker 1.
 * The image remains pinned throughout CRC verification, patching, execution,
 * postcondition checks, restoration and cache synchronization. */
#include "relocated_probe_bytes.h"
static unsigned int reloc_word(unsigned int offset){unsigned int i,v=0;for(i=0;i<4;i++)v|=(unsigned int)image.base[offset+i]<<(8*i);return v;}
static void reloc_store(unsigned int offset,unsigned int v){unsigned int i;for(i=0;i<4;i++)image.base[offset+i]=(unsigned char)(v>>(8*i));}
static unsigned int run_relocated(unsigned int *value){
 unsigned int i,j,base=(unsigned int)(unsigned long)image.base,ok=1;void *entry;
 const struct doom_runtime_v1 *a=doom_runtime_api();
 const struct segment *s=image.manifest.segment;
 if(!a||image.state!=SEG_READY||image.manifest.count!=3||image.manifest.entry!=RELOC_ENTRY||
 s[0].offset||s[0].file_bytes!=RELOC_TEXT||s[0].memory_bytes!=RELOC_TEXT||s[0].flags!=SEG_RX||
 s[1].offset!=RELOC_DATA||s[1].file_bytes!=RELOC_DATA_BYTES||s[1].memory_bytes!=RELOC_DATA_BYTES||s[1].flags!=SEG_RW||
 s[2].offset!=RELOC_BSS||s[2].file_bytes||s[2].memory_bytes!=128||s[2].flags!=SEG_RW)return 1;
 for(i=0;i<3;i++)for(j=0;j<s[i].file_bytes;j++)if(image.base[s[i].offset+j]!=relocated_bytes[s[i].offset+j])return 2;
 for(i=0;i<128;i++)if(image.base[RELOC_BSS+i])return 3;
 if(!doom_shared_enter((void*)1))return 4;entry=seg_start(&image);UNLOCK();if(!entry)return 5;
 for(i=0;i<sizeof(relocated_sites)/sizeof(*relocated_sites);i++){j=relocated_sites[i];reloc_store(j,reloc_word(j)+base);}
 if(!sync_code(image.base,RELOC_TEXT)){seg_uncertain(&image);exclusive_abort();return 6;}
#ifndef UPLOAD_NATIVE
 *value=((unsigned int(*)(const struct doom_runtime_v1*))entry)(a);
#else
 /* Native replay models the bounded i960 arithmetic, not its ISA execution. */
 {void *p=a->allocate(512);if(!p)*value=2;else{
 for(i=0;i<32;i++)reloc_store(RELOC_COUNTS+4*i,(i*33)^0x49393630u);
 *value=reloc_word(RELOC_COUNTS+20);a->release(p);}}
#endif
 if(*value!=((5u*33)^0x49393630u))ok=0;
 for(i=0;i<32;i++)if(reloc_word(RELOC_COUNTS+4*i)!=((i*33)^0x49393630u))ok=0;
 /* Every initialized code/data byte must still match the rebased template. */
 for(i=0;i<3;i++)for(j=0;j<s[i].file_bytes;j++){
 unsigned int off=s[i].offset+j,k,v=relocated_bytes[off];
 for(k=0;k<sizeof(relocated_sites)/sizeof(*relocated_sites);k++)if(off>=relocated_sites[k]&&off<relocated_sites[k]+4){
 unsigned int q=relocated_sites[k],w=0,l;for(l=0;l<4;l++)w|=(unsigned int)relocated_bytes[q+l]<<(8*l);v=((w+base)>>(8*(off-q)))&255;break;}
 if(image.base[off]!=v)ok=0;
 }
 if(!ok){seg_uncertain(&image);exclusive_abort();return 7;}
 /* Return to the CRC-verified template so a repeat must pass admission again. */
 for(i=0;i<3;i++)for(j=0;j<s[i].memory_bytes;j++)image.base[s[i].offset+j]=j<s[i].file_bytes?relocated_bytes[s[i].offset+j]:0;
 if(!sync_code(image.base,RELOC_TEXT)){seg_uncertain(&image);exclusive_abort();return 8;}
 if(!doom_shared_enter((void*)1)){exclusive_abort();return 9;}ok=seg_complete(&image);UNLOCK();return ok?0:10;
}
