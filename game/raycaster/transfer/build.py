#!/usr/bin/env python3
"""Fine command profiling of the existing guarded RIO transport."""
import argparse,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'host/loadrun'))
from build import replace

def build(out,fast=False,command_profile=True):
 import subprocess
 subprocess.run([sys.executable,str(HERE.parent/'build_transport.py'),'--out',str(out)],check=True)
 p=out/'dac960rtems.c';s=p.read_text()
 if command_profile:
  s=replace(s,'static int issue(struct experiment *d, u8 opcode, u16 count, u32 offset,\n                 u8 pattern, unsigned int slot)',
  '''static int issue_inner(struct experiment *d, u8 opcode, u16 count, u32 offset,
                  u8 pattern, unsigned int slot, u64 *t)''')
  for old,new in [
   ('    rc = readl_poll_timeout(d->bar + IDB,','    t[1]=ktime_get_ns();\n    rc = readl_poll_timeout(d->bar + IDB,'),
   ('    d->tag++;','    t[2]=ktime_get_ns();\n    d->tag++;'),
   ('    record(d, "submit op=', '    t[3]=ktime_get_ns();\n    record(d, "submit op='),
   ('    writel(words[0], d->bar + MBOX);','    t[4]=ktime_get_ns();\n    writel(words[0], d->bar + MBOX);'),
   ('    rc = readl_poll_timeout(d->bar + ODB,','    t[5]=ktime_get_ns();\n    rc = readl_poll_timeout(d->bar + ODB,'),
   ('    returned = readw(d->bar + STATUS_ID);','    t[6]=ktime_get_ns();\n    returned = readw(d->bar + STATUS_ID);'),
   ('    changes = changed(d->dma_buf,','    t[7]=ktime_get_ns();\n    changes = changed(d->dma_buf,'),
   ('    record(d, "complete op=', '    t[8]=ktime_get_ns();\n    record(d, "complete op='),
   ('    if (guard) return -EOVERFLOW;', '    t[9]=ktime_get_ns();\n    if (guard) return -EOVERFLOW;')]:s=replace(s,old,new)
  wrapper='''static int issue(struct experiment *d,u8 op,u16 count,u32 off,u8 pattern,unsigned int slot)
 {
     u64 t[11]={0};int rc;
     t[0]=ktime_get_ns();rc=issue_inner(d,op,count,off,pattern,slot,t);t[10]=ktime_get_ns();
     if(!rc) record(d,"CMDPROFILE op=%02x count=%u offset=%08x gate=%llu input=%llu prepare=%llu submit_log=%llu submit=%llu wait=%llu consume=%llu scan=%llu complete_log=%llu tail=%llu total=%llu\\n",
       op,count,off,(unsigned long long)(t[1]-t[0]),(unsigned long long)(t[2]-t[1]),
       (unsigned long long)(t[3]-t[2]),(unsigned long long)(t[4]-t[3]),
       (unsigned long long)(t[5]-t[4]),(unsigned long long)(t[6]-t[5]),
       (unsigned long long)(t[7]-t[6]),(unsigned long long)(t[8]-t[7]),
       (unsigned long long)(t[9]-t[8]),(unsigned long long)(t[10]-t[9]),
       (unsigned long long)(t[10]-t[0]));
     else record(d,"CMDFAIL op=%02x count=%u offset=%08x rc=%d total=%llu\\n",op,count,off,rc,(unsigned long long)(t[10]-t[0]));
     return rc;
 }

 '''
  s=replace(s,'static int run_pointer(struct experiment *d)',wrapper+'static int run_pointer(struct experiment *d)')
 if fast:
  begin=s.index('static unsigned int changed(');end=s.index('static int issue',begin)
  s=s[:begin]+(HERE/'count.h').read_text()+'\n'+s[end:]
  # Exact immutable intervals replace byte-by-byte classification, not coverage.
  p2=out/'buffer_io.h';v=p2.read_text();a=v.index('static inline int bio_response_valid(')
  v=v[:a]+(HERE/'validate.h').read_text()+'\n#endif\n';p2.write_text(v)
 p.write_text(s)
 (out/'transfer-build.json').write_text(json.dumps(dict(command_profile=command_profile,fast_validation=fast),indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--fast',action='store_true');p.add_argument('--coarse',action='store_true',help='omit detailed command logging; retain phase timing');a=p.parse_args();build(a.out,a.fast,not a.coarse)
