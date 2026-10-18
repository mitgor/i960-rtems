"""Workload adapter rejects source drift; no Doom-only admission or shutdown."""
from pathlib import Path
import ast,shutil,tempfile,subprocess
from generate import profile
root=Path(__file__).resolve().parents[3]
paths=['rtems/accele160/doom_dma/'+x for x in ('app.c','frame_dma.h','test_dma.c','build.sh','browser.py','run_bridge.py')]+['game/doom/play/accele160/launch.py']
with tempfile.TemporaryDirectory(prefix='chip8-profile-') as directory:
 out=Path(directory)
 for name in paths:
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dest)
 edits=profile(out);assert len(edits)==len(paths)
 kernel=(out/paths[0]).read_text()
 assert kernel.index('while(live[base]!=live[base+3u])')<kernel.index('first_frame_seen=z;engine_report[5]=z;')
 bridge=(out/paths[-2]).read_text();ast.parse(bridge)
 assert 'wad_query(' not in bridge and 'transact(2,' not in bridge
 assert "write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))" in bridge
 assert "oracle.check(image)" in bridge and 'complete paired compact DMA/full PIO frame' in bridge
 for name in (paths[-1],'rtems/accele160/doom_dma/browser.py'):ast.parse((out/name).read_text())
 # Compile the actual generated admission/wait/counter prefix. A pending
 # destination and STOP/timeout must leave the committed frame counter intact.
 a=kernel.index(' slot=(z-1u)&1u;base=slot?6u:2u;')
 b=kernel.index(' generation=frame_origin+z;',a)
 fixture=r"""
#include <assert.h>
#define DOOM_PERSISTENT 1
#define DOOM_FPS_FRAMES 32
#define FRAME_BYTES 65536
#define ENGINE_PLAY_OFFSET 4080
#define STOP 0x504f5453u
#define RTEMS_SUCCESSFUL 0
static unsigned first_frame_seen,engine_report[16],frame_ticks[32],ticks,live[16],control[16],stopped;
static unsigned char image_base[4080+2*65536];
static void dma_drain(void){}
static void lease_invalidate_dcache(void){}
static unsigned engine_stopping(void){return stopped;}
static int rtems_task_wake_after(unsigned n){ticks+=n*100;return 0;}
static void priority0(void){}
static void bounded_fatal(unsigned n){(void)n;assert(0);}
static int probe(unsigned long x,unsigned y,unsigned z){unsigned slot,base,start;
"""+kernel[a:b]+r"""
return 0;}
int main(void){unsigned long source=(unsigned long)(image_base+ENGINE_PLAY_OFFSET);
live[2]=1;live[5]=0;stopped=1;
assert(probe(source,65536,1)==-1 && !first_frame_seen && !engine_report[5]);
stopped=0;ticks=0;
assert(probe(source,65536,1)==-1 && ticks==500 && !first_frame_seen);
live[5]=1;
assert(probe(source,65536,1)==0 && first_frame_seen==1 && engine_report[5]==1);
return 0;}
"""
 # Target uses 32-bit addresses; native unsigned-long comparison preserves the
 # allocation's address while executing the identical control/commit sequence.
 fixture=fixture.replace('x!=(unsigned int)(image_base+', 'x!=(unsigned long)(image_base+')
 c=out/'publish.c';c.write_text(fixture);exe=out/'publish'
 subprocess.run(['cc','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
 try:profile(out)
 except ValueError:pass
 else:raise AssertionError('profile accepted already transformed sources')
print('PASS exact source generation, actual wait/commit ASan STOP/timeout/normal cases, host syntax, replay/paired audits, no Doom WAD admission/shutdown, drift rejection')
