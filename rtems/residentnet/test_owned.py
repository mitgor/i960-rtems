#!/usr/bin/env python3
"""Real native owned runtime/admission/heap with modeled processor priority."""
import argparse,ast,importlib.util,subprocess,tempfile
from pathlib import Path
from runtime_replay import native,service
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--entry',type=Path,required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('owned_native',r/'../../game/doom/runtime/owned/native.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
tree=ast.parse((r/'test_doom_shared.py').read_text());source=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets)).split('int main(void)')[0]
main=r'''
static unsigned cancel,cancel_wad;
static void runtime_service(void){if(cancel_wad&&owned_running&&wad.state==WAD_REQUEST){assert(leases==1);assert(!doom_runtime_owned_control(0x7a,0,owned_generation,1));cancel_wad=0;}if(cancel&&owned_running&&owned_yields>=16){assert(!doom_runtime_owned_control(0x7a,0,owned_generation,1));cancel=0;}}
int main(void){pthread_t task;unsigned i,v;unsigned binding[11]={0x31444157,1,4096};identity=2;doom_shared_init();assert(upload_init());assert(!pthread_create(&task,0,peer,0));assert(!doom_arena_proof(&app_arena));assert(!doom_runtime_bind(binding,11));
 const struct doom_runtime_owned*a=doom_runtime_owned_api();assert(a&&!a->owner());assert(doom_runtime_owned_begin());assert(a->owner());
 assert(a->wait_ms(1001)==-1);assert(doom_shared_enter((void*)1));assert(!a->owner()&&a->wait_ms(1)==-1);doom_shared_leave((void*)1);
 identity=0;assert(!a->owner()&&!a->io.allocate(1)&&a->wait_ms(1)==-1&&a->stopping());identity=2;
 assert(!doom_runtime_owned_control(0x7a,0,owned_generation+1,1)); /* deliberately rejected below */
 return 0;}
'''
# Keep assertions explicit; a rejected generation returns ~0, not zero.
main=main.replace('assert(!doom_runtime_owned_control(0x7a,0,owned_generation+1,1)); /* deliberately rejected below */\n return 0;}', '''assert(doom_runtime_owned_control(0x7a,0,owned_generation+1,1)==~0u);assert(doom_runtime_owned_end());
 assert(!a->owner()&&!a->io.allocate(1)&&a->stopping());
 assert(doom_runtime_owned_begin());cancel=1;v=owned_entry(a);assert(v==(DOOM_OWNED_MAGIC^0x49393630u^53u));assert(owned_result[0]==(0x49393630u^7)&&owned_result[1]==3&&owned_result[2]==2&&owned_result[5]==1&&owned_result[6]==53&&!owned_result[7]);assert(doom_runtime_owned_end());
 for(i=0;i<8;i++)owned_result[i]=0;
 assert(doom_runtime_owned_begin());v=owned_entry(a);assert(v==(DOOM_OWNED_MAGIC^0x49393630u^37u));assert(owned_result[4]>=10000&&!owned_result[5]&&owned_result[2]==2);assert(doom_runtime_owned_end());
 assert(doom_runtime_owned_control(0x7a,0,owned_generation,1)==~0u);
 assert(doom_runtime_owned_begin());unsigned char*buf=a->io.allocate(512);assert(buf);for(i=0;i<512;i++)buf[i]=0x55;cancel_wad=1;
 assert(a->io.read(1,0,buf,12)==-4&&!leases&&wad.state==WAD_IDLE);for(i=0;i<512;i++)assert(buf[i]==0x55);
 a->io.release(buf);assert(doom_runtime_owned_end());
 atomic_store(&halted,1);assert(!pthread_join(task,0));identity=3;doom_shared_quiesce(1);assert(upload_finish());for(i=0;i<ARENA_SLOTS;i++)assert(!app_arena.slot[i].span);
 puts("PASS owned API: scoped owner, lock/ISR/masked refusal, stale invocation refusal, yields, nested return/jump, STOP recovery and complete drain");return 0;}''')
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);source=native(source,t,(a.entry/'runtime-probe.bin').read_bytes(),[])
 # native() appends an unused WAD service; this test supplies cancellation only.
 source=source.replace(service([]),'')
 source='#define I960_DOOM_RELOCATE 1\n'+helper.prefix(source)
 (t/'test.c').write_text(source+main)
 for name,folder in [('relocated_probe_bytes.h','relocate'),('cache_probe_bytes.h','cache'),('owned_probe_bytes.h','owned')]:
  if (a.entry/folder/name).exists():(t/name).write_bytes((a.entry/folder/name).read_bytes())
 (t/'upload_native.h').write_text('''#define R(a) (*(unsigned int*)(unsigned long)(a))
static unsigned upload_stopping(void){return atomic_load(&halted);}
static unsigned upload_time(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (unsigned)(t.tv_sec*100+t.tv_nsec/10000000);}
static void barrier(void){}
static int sync_code(void*p,unsigned n){return 1;}
static void exclusive_abort(void){assert(0);}
unsigned upload_protect_step(void){return 1;}unsigned upload_protect_finish(void){return 1;}
''')
 core=r.parents[1]/'loader/segmented';runtime=r.parents[1]/'game/doom/runtime'
 subprocess.run(['cc','-std=c11','-pthread','-fsanitize=address,undefined','-I'+str(t),'-I'+str(r),str(t/'test.c'),str(core/'arena.c'),str(core/'image.c'),str(runtime/'heap.c'),str(runtime/'libc.c'),str(runtime/'wad.c'),'-o',str(t/'test')],check=True);subprocess.run([str(t/'test')],check=True)
