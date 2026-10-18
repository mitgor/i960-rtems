#!/usr/bin/env python3
"""Offline-only CHIP-8 resident profile + compact DMA bundle for AcceleRAID 160.

No PCI access, module load, service stop or firmware write. Existing base-bundle
inputs remain immutable; choose a fresh work directory. ROMs are guest bytecode.
"""
import argparse,hashlib,json,os,shutil,struct,subprocess,sys
from pathlib import Path
from generate import profile
ROOT=Path(__file__).resolve().parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--work',type=Path,required=True);p.add_argument('--base-bundle',type=Path,required=True)
 p.add_argument('--rtems-build',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-')
 p.add_argument('--rom',type=Path);p.add_argument('--cpu-hz',type=int,default=500)
 a=p.parse_args();w=a.work.resolve();base=a.base_bundle.resolve()
 if not 1<=a.cpu_hz<=4000:p.error('CPU rate must be 1..4000 instructions/s')
 sys.path.insert(0,str(ROOT/'game/chip8'));from host import demo_rom
 rom=a.rom.read_bytes() if a.rom else demo_rom()
 if not 2<=len(rom)<=3584:p.error('ROM must be 2..3584 bytes')
 cfg=json.loads((base/'bundle.json').read_text())
 if cfg['card_profile']!='accele160' or cfg['bdf']!='0000:37:09.1':raise ValueError('base card profile/BDF')
 for name,digest in cfg['files'].items():
  path=(base/name).resolve()
  if not path.is_relative_to(base) or sha(path.read_bytes())!=digest:raise ValueError('base identity: '+name)
 w.mkdir(parents=True,exist_ok=False);bundle=w/'bundle';bundle.mkdir();project=bundle/'project';project.mkdir()
 for name in ('game','rtems','host','loader','card_profiles'):
  shutil.copytree(ROOT/name,project/name,ignore=shutil.ignore_patterns('build','._*','__pycache__','*.pyc','*.o','*.so','*.ko'))
 edits=profile(project);src=project/'rtems/accele160/doom_dma'
 # Checked guest ROM, result words, then two 64KiB internal source slots.
 # Only each slot's compact 512-byte prefix is transferred over DMA.
 text=struct.pack('<4I',0x314d5243,len(rom),1,a.cpu_hz)+rom
 span=0xff0+2*65536;template=text+bytes(span-len(text));engine=bundle/'engine';engine.mkdir()
 (engine/'template.bin').write_bytes(template);(engine/'relocations.bin').write_bytes(b'')
 m=dict(application='chip8',card_profile='accele160',file_bytes=span,memory_bytes=span,entry=0,result=0xf00,
        metadata_offset=span,metadata_bytes=0,metadata_sha256=sha(b''),template_sha256=sha(template),
        admission_bytes=span,play_offset=0xff0,persistent_play=True,double_buffer=True,direct_frame=True,no_fnv=True,
        runtime_flat=False,frame_profile=False,cpu_profile=False,low_detail=False,rom_sha256=sha(rom),rom_bytes=len(rom),cpu_hz=a.cpu_hz,
        transfer_bytes=512,source_slot_bytes=65536,native_guest_code=False)
 (engine/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 defines=dict(ENTRY=0,FILE=span,SPAN=span,RESULT=0xf00,META=span,SITES=0,TEXT=len(text),PLAY_OFFSET=0xff0)
 h=''.join(f'#define ENGINE_{key} {v}u\n' for key,v in defines.items())
 for name,data in (('image',template),('metadata',b''),('text',text)):
  h+='static const unsigned char engine_'+name+'_sha[32]={'+','.join(str(v) for v in bytes.fromhex(sha(data)))+'};\n'
 h+='static const unsigned engine_geometry[4][4]={{0,0,0,0},{0,0,0,0},{0,0,0,0},{0,0,0,0}};\n'
 h+='#define ENGINE_STARTUP 1\n#define ENGINE_PLAYABLE 1\n#define ENGINE_PLAY_DOUBLE 1\n#define ENGINE_PINGPONG 1\n'
 (src/'engine_identity.h').write_text(h)
 inputs=bundle/'inputs';inputs.mkdir()
 for name in ('candidate.bin','handler.bin','myrsread.ko','rawreader.ko','reserve_command.ko','release_command.ko','copy_command.ko','digest_command.ko','admit_command.ko'):
  shutil.copy2(base/'inputs'/name,inputs/name)
 # The admitted host command must use the proven private queue, not events.
 accepted_private='2886bd370752621fd82013f27c435c76cf6b40a10e928c12a68e928b0d6e1825'
 if sha((inputs/'admit_command.ko').read_bytes())!=accepted_private:raise ValueError('private admission module required')
 dma=w/'dma';dma.mkdir();source=(project/'host/accele160/frame_dma/dma_frames.c').read_text()
 source=source.replace('#define PAYLOAD 65536u','#define PAYLOAD 512u').replace('#define TOTAL (19u*GUARD)','#define TOTAL (3u*GUARD)')
 if '#define PAYLOAD 512u' not in source or '#define TOTAL (3u*GUARD)' not in source:raise ValueError('DMA source context')
 (dma/'dma_frames.c').write_text(source);(dma/'Makefile').write_text('obj-m += dma_frames.o\n')
 def run(cmd,name,env=None):
  with (w/(name+'.log')).open('w') as log:subprocess.run(list(map(str,cmd)),stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
 run(['make','-C',project/'game/chip8','all'],'native-build')
 run(['make','-C',f'/lib/modules/{os.uname().release}/build','M='+str(dma),'modules'],'dma-build')
 shutil.copy2(dma/'dma_frames.ko',inputs/'dma_frames.ko')
 env=dict(os.environ,DOOM_PERSISTENT='1',DOOM_REUSABLE='1',DOOM_FPS_FRAMES='32',DOOM_KEY_FIFO_SUPPORT='1',CARD_PROFILE='accele160')
 run(['bash',src/'build.sh',a.rtems_build,Path(a.cross).parent,bundle/'kernel'],'kernel-build',env)
 run([sys.executable,src/'write_manifest.py',src,bundle/'kernel',engine/'manifest.json',inputs/'dma_frames.ko',inputs/'admit_command.ko'],'manifest')
 # Distinct app identity, service and control file; never adopts Doom's owner.
 cfg.update(application='chip8');cfg['files']={str(f.relative_to(bundle)):sha(f.read_bytes()) for f in sorted(bundle.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
 (bundle/'bundle.json').write_text(json.dumps(cfg,indent=2)+'\n')
 (w/'build.json').write_text(json.dumps(dict(application='chip8',hardware_tested=False,rom_sha256=sha(rom),cpu_hz=a.cpu_hz,patches=edits,kernel_sha256=sha((bundle/'kernel/kernel.bin').read_bytes()),dma_sha256=sha((inputs/'dma_frames.ko').read_bytes())),indent=2)+'\n')
 print(bundle)
if __name__=='__main__':main()
