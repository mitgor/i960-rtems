#!/usr/bin/env python3
"""Sanitized ownership/admission/zero-fill checks using the actual target core."""
import argparse,ast,subprocess,tempfile
from pathlib import Path
from runtime_replay import native
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--entry',type=Path,required=True);a=p.parse_args()
tree=ast.parse((r/'test_doom_shared.py').read_text())
src=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets)).split('int main(void)')[0]
main=r'''
int main(void){pthread_t task;unsigned int i,v,pad;unsigned long first=0;struct manifest m={0};
 unsigned int binding[11]={0x31444157,1,4096};identity=2;doom_shared_init();assert(upload_init());
 assert(!pthread_create(&task,0,peer,0));assert(!doom_arena_proof(&app_arena));assert(!doom_runtime_bind(binding,11));
 m.abi=1;m.count=3;m.entry=RELOC_ENTRY;
 m.segment[0]=(struct segment){0,RELOC_TEXT,RELOC_TEXT,SEG_RX,seg_crc32(0,relocated_bytes,RELOC_TEXT)};
 m.segment[1]=(struct segment){RELOC_DATA,RELOC_DATA_BYTES,RELOC_DATA_BYTES,SEG_RW,seg_crc32(0,relocated_bytes+RELOC_DATA,RELOC_DATA_BYTES)};
 m.segment[2]=(struct segment){RELOC_BSS,0,128,SEG_RW,0};
 assert(run_relocated(&v)==1);
 for(i=0;i<2;i++){
 assert(doom_shared_enter((void*)1));pad= i?arena_alloc(&app_arena,4096):0;
 assert(seg_begin(&image,&app_arena,&m));doom_shared_leave((void*)1);
 if(!i)first=(unsigned long)image.base;else assert(first!=(unsigned long)image.base);
 assert(run_relocated(&v)==1);
 assert(seg_write(&image,0,0,relocated_bytes,RELOC_TEXT));assert(seg_write(&image,1,0,relocated_bytes+RELOC_DATA,RELOC_DATA_BYTES));
 while((v=seg_prepare(&image,sync_code))==1){}assert(v==2);
 image.manifest.entry+=4;assert(run_relocated(&v)==1);image.manifest.entry-=4;
 image.base[0]^=1;assert(run_relocated(&v)==2);image.base[0]^=1;
 image.base[RELOC_SEED]^=1;assert(run_relocated(&v)==2);image.base[RELOC_SEED]^=1;
 image.base[RELOC_BSS]=1;assert(run_relocated(&v)==3);image.base[RELOC_BSS]=0;
 assert(!run_relocated(&v)&&v==((5*33)^0x49393630u));assert(!run_relocated(&v));
 assert(doom_shared_enter((void*)1));assert(seg_cancel(&image));if(pad)assert(arena_release(&app_arena,pad));doom_shared_leave((void*)1);
 }
 atomic_store(&halted,1);assert(!pthread_join(task,0));identity=3;doom_shared_quiesce(1);assert(upload_finish());
 puts("PASS relocation: two allocation addresses, repeated entries, entry/code/data/BSS/loading refusals, full drain");return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);src=native(src,t,(a.entry/'runtime-probe.bin').read_bytes(),[])
 (t/'test.c').write_text('#define I960_DOOM_RELOCATE 1\n'+src+main)
 (t/'relocated_probe_bytes.h').write_bytes((a.entry/'relocate/relocated_probe_bytes.h').read_bytes())
 (t/'upload_native.h').write_text('''#define R(a) (*(unsigned int*)(unsigned long)(a))
static unsigned int upload_stopping(void){return atomic_load(&halted);}
static unsigned int upload_time(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (unsigned int)(t.tv_sec*100+t.tv_nsec/10000000);}
static void barrier(void){}
static int sync_code(void*p,unsigned int n){return 1;}
static void exclusive_abort(void){assert(0);}
unsigned int upload_protect_step(void){return 1;}
unsigned int upload_protect_finish(void){return 1;}
''')
 core=r.parents[1]/'loader/segmented';runtime=r.parents[1]/'game/doom/runtime'
 subprocess.run(['cc','-std=c11','-pthread','-fsanitize=address,undefined','-I'+str(t),'-I'+str(r),str(t/'test.c'),str(core/'arena.c'),str(core/'image.c'),str(runtime/'heap.c'),str(runtime/'libc.c'),str(runtime/'wad.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test')],check=True)
