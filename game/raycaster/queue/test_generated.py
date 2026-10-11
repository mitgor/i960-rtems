"""Exercise generated capture lifecycle and read_pair, not a hand-written copy."""
import re,subprocess
from pathlib import Path

def balanced(s,start):
 begin=s.index('{',start);depth=1;end=begin+1
 while depth:
  depth+=(s[end]=='{')-(s[end]=='}');end+=1
 return s[start:end]

def check(out,work):
 s=(out/'dac960rtems.c').read_text()
 assert 'i < 54' not in s
 pos=s.index('d->capture[i].blob.size = (i == 1')
 alloc=balanced(s,s.rfind('for (',0,pos))
 free=balanced(s,s.index('static void free_captures'))
 publish=balanced(s,s.rfind('for (',0,s.index('const char *name = names[i]')))
 pair=balanced(s,s.index('static int read_pair'))
 copy=re.search(r'if \(slot < ARRAY_SIZE\(d->capture\)\)\s*memcpy\([^;]+;',s).group()
 defines='\n'.join(re.findall(r'^#define (?:SCRATCH_REGION_SIZE|SCRATCH_WRITE_SIZE|DRAM_HOOK_SIZE|EXEC_REGION_SIZE|EXEC_RAM_SIZE|EXEC_FLASH_SIZE) .+$','\n'.join(p.read_text() for p in out.glob('*.h')),re.M))
 code=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include "queue.h"
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define GFP_KERNEL 0
#define STAGING_BASE 0xc0f2c000u
typedef uint32_t u32;typedef uint16_t u16;
struct blob {size_t size;void *data;};
struct capture {unsigned char *data;struct blob blob;};
struct experiment {struct capture capture[60],stage[8];void *directory;unsigned char dma_buf[61440];u32 audit_address;u16 audit_length;};
static int allocations,freed,fail_at,published,issued;
static int pointer_check=0,flash_map_check=0,length=512;
static const char *names[60];
static void *kzalloc(size_t size,int flags){(void)flags;if(allocations++==fail_at)return NULL;return calloc(1,size);}
static void kfree(void *p){if(p)freed++;free(p);}
#define kvfree free
static void debugfs_create_blob(const char *name,int mode,void *dir,struct blob *b){(void)name;(void)mode;(void)dir;assert(b->data && b->size);published++;}
'''+defines+'\n'+free+'\n'+r'''
static int allocate(struct experiment *d){unsigned int i;int rc=0;
'''+alloc+r'''
return 0;free_dma:free_captures(d);return rc;}
static void publish(struct experiment *d){unsigned int i;
'''+publish+r'''
}
static int issue(struct experiment *d,int op,u16 count,u32 addr,int fill,unsigned int slot){
(void)op;(void)count;(void)addr;(void)fill;issued++;
'''+copy+r'''
return 0;}
'''+pair+r'''
int main(void){
 struct experiment d;
 for(fail_at=0;fail_at<=60;fail_at++){
  memset(&d,0,sizeof(d));allocations=freed=published=issued=0;
  int rc=allocate(&d);
  if(fail_at<60){assert(rc==-ENOMEM && freed==fail_at);continue;}
  assert(rc==0 && allocations==60);publish(&d);assert(published==60);
  memset(d.dma_buf,0x37,sizeof(d.dma_buf));
  for(unsigned i=0;i<60;i++){assert(d.capture[i].data);if(i>=54)assert(d.capture[i].blob.size==(i<56?64:5120));issue(&d,0,0,0,0,i);for(size_t j=0;j<d.capture[i].blob.size;j++)assert(d.capture[i].data[j]==0x37);}
  for(unsigned i=54;i<60;i+=2)assert(read_pair(&d,STAGING_BASE,(u16)d.capture[i].blob.size,i)==0);
  int n=issued;assert(read_pair(&d,STAGING_BASE,64,59)==-EINVAL);assert(read_pair(&d,STAGING_BASE,65,54)==-EINVAL);assert(read_pair(&d,STAGING_BASE,0,54)==-EINVAL);assert(read_pair(&d,STAGING_BASE,64,~0u)==-EINVAL);
  unsigned char *save=d.capture[54].data;d.capture[54].data=NULL;assert(read_pair(&d,STAGING_BASE,64,54)==-EINVAL);d.capture[54].data=save;assert(issued==n);
  free_captures(&d);assert(freed==60);
 }
 puts("PASS: generated allocation/publication/copy/free for all 60 captures, every allocation failure, read_pair rejects invalid storage before DMA");
}
'''
 source=work/'generated.c';source.write_text(code)
 subprocess.run(['cc','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(out),str(source),'-o',str(work/'generated')],check=True)
 subprocess.run([str(work/'generated')],check=True)
