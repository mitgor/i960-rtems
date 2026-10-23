"""Generate an isolated CHIP-8 profile from audited resident transport sources.

Only workload-specific admission/file/frame formats change. IRQ, cache, arena,
STOP, lifetime, DMA marker/ownership, rearm and private worker code remain shared.
Every edit must find its exact reviewed source context; no fuzzy patching.
"""
from pathlib import Path
import hashlib,json


def profile(project):
    root=Path(project);src=root/'rtems/accele160/doom_dma';edits=[]
    def change(name,fn):
        p=root/name;old=p.read_text();new=fn(old)
        edits.append(dict(path=name,before=hashlib.sha256(old.encode()).hexdigest(),after=hashlib.sha256(new.encode()).hexdigest()))
        p.write_text(new)
    def once(s,old,new):
        if s.count(old)!=1:raise ValueError('source context changed: '+repr(old[:90]))
        return s.replace(old,new)
    def block(s,start,end,new):
        if s.count(start)!=1:raise ValueError('block context changed: '+start)
        a=s.index(start);b=s.index(end,a);return s[:a]+new+s[b:]
    def kernel(s):
        s=once(s,'static unsigned int engine_first_frame(unsigned int *value){', '#include "../../../game/chip8/accele160/entry.h"\nstatic unsigned int engine_first_frame(unsigned int *value){')
        s=once(s,'ret=((unsigned int(*)(const struct doom_runtime_owned *))\n      (image_base+ENGINE_ENTRY))(&doom_api.base);','ret=chip8_entry(&doom_api.base);')
        start=s.index('static unsigned int engine_first_frame(');end=s.index('static unsigned int reusable_audit(',start)
        part=s[start:end].replace('0x454e4702u','0x43384702u').replace('0x454e4750u','0x31453843u').replace('r[1]==2u','r[1]==1u').replace('r[1]!=2u','r[1]!=1u').replace('r[2]==ZONE_BYTES','r[2]==0u').replace('r[2]!=ZONE_BYTES','r[2]!=0u')
        s=s[:start]+part+s[end:]
        s=once(s,'admitted=1u;','admitted=1u;wad_ready=1u;frame_ready=1u;frame_base=image_base+ENGINE_PLAY_OFFSET; /* No file channel. */')
        s=once(s,'engine_invoked=1u;first_frame_seen=0u;frame_ready=0u;','engine_invoked=1u;first_frame_seen=0u;frame_ready=1u;')
        s=once(s,'#define WAD_FILE_BYTES 28795076u','#define WAD_FILE_BYTES 0u')
        s=once(s,'a->file_id=1u;a->file_bytes=WAD_FILE_BYTES;','a->file_id=0u;a->file_bytes=0u;')
        s=once(s,'for(i=0;i<8u;i++)a->sha256[i]=wad_sha[i];','for(i=0;i<8u;i++)a->sha256[i]=0u;')
        # A STOP while waiting for a destination must not count an unpublished
        # source as delivered. Keep the original strict host equality audit.
        committed=' if(first_frame_seen<DOOM_FPS_FRAMES)frame_ticks[first_frame_seen]=ticks;\n first_frame_seen=z;engine_report[5]=z;\n'
        s=once(s,committed,'')
        s=once(s,' generation=frame_origin+z;\n',committed+' generation=frame_origin+z;\n')
        s=once(s,'hash=dma_cfg[7]?0u:byte_fnv((const void*)x,FRAME_BYTES);','hash=dma_cfg[7]?0u:byte_fnv((const void*)x,512u);')
        return s
    change('rtems/accele160/doom_dma/app.c',kernel)
    def dma(s):
        s=once(s,'dma_cfg[4]!=FRAME_BYTES','dma_cfg[4]!=512u')
        s=s.replace('dma_bus[0]+73728u','dma_bus[0]+8192u').replace('dma_bus[1]+73728u','dma_bus[1]+8192u')
        s=once(s,'d[4]=FRAME_BYTES;','d[4]=512u;')
        s=once(s,'dma_bus[slot]+FRAME_BYTES','dma_bus[slot]+512u')
        s=once(s,'dma_marker[4]=FRAME_BYTES;','dma_marker[4]=512u;')
        return s
    change('rtems/accele160/doom_dma/frame_dma.h',dma)
    change('rtems/accele160/doom_dma/test_dma.c',lambda s:s.replace('cfg[4]=65536','cfg[4]=512').replace('desc[4]==65536','desc[4]==512').replace('cfg[2]+65536','cfg[2]+512'))
    def build(s):
        marker='"$tools_bin/i960-elf-ld" -T'
        s=once(s,marker,'for item in chip8 stream/player; do\n  name=$(basename "$item")\n  "$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding -c "$repo/game/chip8/$item.c" -o "$out/$name.o"\ndone\n'+marker)
        return once(s,'"$out/start.o" "$out/app.o"','"$out/start.o" "$out/app.o" "$out/chip8.o" "$out/player.o"')
    change('rtems/accele160/doom_dma/build.sh',build)
    def browser(s):
        a=s.index('ALLOWED=');b=s.index('\n',a);s=s[:a]+'ALLOWED=set(range(16))'+s[b:]
        s=s.replace('assert len(payload)==65536','assert len(payload)==512').replace('0x31424644,1,self.epoch,generation,320,200,65536,0','0x31424643,1,self.epoch,generation,64,32,512,0')
        return s.replace('Doom','CHIP-8')
    change('rtems/accele160/doom_dma/browser.py',browser)
    (src/'index.html').write_text("<!doctype html><title>CHIP-8 card owner</title><p>Audited CHIP-8 owner. Open the <a href='http://192.168.2.80:8096/'>streaming game</a>.</p><script>const token='__TOKEN__';</script>")
    def bridge(s):
        s=once(s,'from presentation_profile import decode as decode_profile',"sys.path.insert(0,str(ROOT/'game/chip8/stream'))\nfrom codec import validate_payload\nfrom oracle import Oracle\ndef decode_profile(raw,g,options=None):return validate_payload(raw,g)")
        s=s.replace("'relocations','wad','out'","'relocations','out'")
        s=once(s,'a.fps_manifest is not None and a.startup_oracle is not None','a.fps_manifest is not None and a.startup_oracle is None')
        s=block(s,'        oracle_data=a.startup_oracle.read_bytes()','    else:', '        startup_oracle=None\n        need(engine_manifest.get("application")=="chip8","CHIP-8 application identity")\n')
        s=s.replace("pin['bytes']=='65536' and pin['total']=='77824'","pin['bytes']=='512' and pin['total']=='12288'").replace('>=77824', '>=12288').replace('*buses,65536,','*buses,512,')
        s=once(s,'        wad=a.wad.read_bytes()','        wad=b""')
        s=block(s,"        need(sha(wad)=='7323bcc",'        admission=', '')
        s=block(s,'        invalid=bytearray(wad[:512])','        game_run=1;', '        frame=bytes(65536);request_seq=0;wad_receipts=[]\n')
        s=once(s,'if req[0]==request_seq+1 and req[9]==0x444e4550:', 'if req[0]==request_seq+1 and req[9]==0x444e4550:')
        # A CHIP-8 payload may never publish a file request. Keep the explicit
        # fail-closed check rather than accepting arbitrary guest file accesses.
        s=block(s,'                if req[0]==request_seq+1 and req[9]==0x444e4550:', '                if words[8]==engine_seq', '                need(req[0]==0 and req[9]!=0x444e4550,"unexpected CHIP-8 file request")\n')
        s=s.replace('slot,65536,source,','slot,512,source,').replace('os.pread(fd,77824,0)','os.pread(fd,12288,0)')
        s=s.replace("len(capture)==77824", "len(capture)==12288").replace('capture[69664:]', 'capture[4640:]').replace('(77824-69664)', '(12288-4640)').replace('capture[69632:69664]', 'capture[4608:4640]').replace('capture[4096:69632]','capture[4096:4608]')
        s=once(s,"need(pio==image,'complete paired DMA/PIO frame')", "need(pio[:512]==image and not any(pio[512:]),'complete paired compact DMA/full PIO frame')")
        s=s.replace('(31 if a.persistent else 0),0x454e4702','(31 if a.persistent else 0),0x43384702').replace('(0x454e4702,frame_count)','(0x43384702,frame_count)').replace('(0x454e4750,2,6291456)','(0x31453843,1,0)')
        s=s.replace('len(set(game_frame[:64000]))>32','not any(game_frame[512:])').replace("sha(game_frame)==live_receipts[-1]['sha256']","sha(game_frame[:512])==live_receipts[-1]['sha256']")
        s=once(s,'            keyboard_mode=a.keyboard_mode\n','            oracle=Oracle(template[16:16+engine_manifest[\"rom_bytes\"]],hz=engine_manifest[\"cpu_hz\"])\n            keyboard_mode=a.keyboard_mode\n')
        s=once(s,'                        key_batches+=1;','                        oracle.submit(keys)\n                        key_batches+=1;')
        s=once(s,'                    profile=decode_profile(image,local_frame,options=engine_manifest)','                    oracle.check(image)\n                    profile=decode_profile(image,local_frame,options=engine_manifest)')
        s=once(s,'            transact(2,0,wad[:512])\n','')
        s=once(s,"        wad_query(0x56789,512,'stop')","        write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))")
        s=once(s,"need(final_bridge[18:20]==(38+total_reads,4),", "need(final_bridge[18:20]==(0,0),")
        return s.replace('i960-doom','i960-chip8').replace('Doom','CHIP-8')
    change('rtems/accele160/doom_dma/run_bridge.py',bridge)
    def launch(s):
        s=s.replace("'--startup-oracle',str(bundle/'inputs/native-requests.bin'),",'')
        s=s.replace("'--wad',str(bundle/'inputs/freedoom1.wad'),",'')
        s=once(s,"if cfg['schema']!=1 or cfg['card_profile']!='accele160':", "if cfg['schema']!=1 or cfg['card_profile']!='accele160' or cfg.get('application')!='chip8':")
        return s.replace('i960-doom','i960-chip8').replace('default=8087','default=8095').replace('Doom','CHIP-8')
    change('game/doom/play/accele160/launch.py',launch)
    return edits
