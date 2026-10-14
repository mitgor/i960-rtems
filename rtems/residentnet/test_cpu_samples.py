#!/usr/bin/env python3
"""Compile the actual IRQ sampling clause and owned read callback."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
s=(root/'rtems/exclusive/runtime.c').read_text();clause=s.split('void switch_irq_body(void){\n#ifdef I960_DOOM_CPU_PROFILE\n',1)[1].split('\n#endif',1)[0]
code='#include <assert.h>\nstatic unsigned switch_threads[2],_Thread_Executing,doom_cpu_samples;\nvoid sample(void){'+clause+'}\nint main(void){sample();assert(!doom_cpu_samples);switch_threads[0]=1;switch_threads[1]=2;_Thread_Executing=1;sample();assert(!doom_cpu_samples);_Thread_Executing=2;sample();sample();assert(doom_cpu_samples==2);_Thread_Executing=3;sample();assert(doom_cpu_samples==2);return 0;}\n'
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code);subprocess.run(['cc','-Wall','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
# Existing two-slot test with actual callback extension, including stop refusal.
s=(root/'rtems/residentnet/test_double_buffer.py').read_text()
s=s.replace('#define ENGINE_PLAY_DOUBLE 1','#define ENGINE_PLAY_DOUBLE 1\n#define ENGINE_CPU_PROFILE 1\nunsigned doom_profile_samples(void){return 123;}')
s=s.replace('static unsigned owner(void){return 1;}','static unsigned owner_ok=1;static unsigned owner(void){return owner_ok;}')
s=s.replace(' for(g=1;g<=32;g++){' ,' assert(engine_play_mark(102,0,0,0)==123);stop=1;assert(engine_play_mark(102,0,0,0)==-1);stop=0;owner_ok=0;assert(engine_play_mark(102,0,0,0)==-1);owner_ok=1;\n for(g=1;g<=32;g++){')
s=s.replace('root=Path(__file__).resolve().parents[2]','root=Path('+repr(str(root))+')')
exec(compile(s,__file__,'exec'))
print('PASS actual task sampler attribution and owned/stopping callback checks')
