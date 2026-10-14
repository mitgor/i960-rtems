#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exclusive_builder',HERE.parent/'exclusive/build_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def protect_upload_header(s,engine=False):
 return m.replace(s,'if(i>=0x20010u && i<0x6fff0u) continue;',
                  'if(i>=0x20010u && i<'+('0x60000u' if engine else '0x68000u')+') continue;')
def build(out,payload):
 m.build(out,payload)
 p=out/'dac960auto.c';s=p.read_text();s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'host.h').read_text()+'\nstatic const struct file_operations session_fops=');s=m.replace(s,'.unlocked_ioctl=monitor_ioctl,','.unlocked_ioctl=resident_ioctl,')
 metadata=payload.parent/'build.json'
 flags=json.loads(metadata.read_text())['flags'] if metadata.exists() else []
 if any(f.startswith('-DI960_OWNED_MIB=') for f in flags):
  s='#define I960_LARGE_CONTROL 1\n'+s
 if '-DI960_HEAP_SHARED' in flags:
  s=m.replace(s,'else{token=0x90000000u;reply=0x95000000u;}', 'else{token=w[2]?0x96000000u:0x90000000u;reply=w[2]?0x97000000u:0x95000000u;}')
  s=m.replace(s,'epoch=w[1];mutex_lock(&d->session_lock);', 'if(w[0]==7&&w[2]>1)return -EINVAL;epoch=w[1];mutex_lock(&d->session_lock);')
 if any(f.startswith('-DI960_OWNED_MIB=') for f in flags):
  s=m.replace(s,'if(w[0]==7&&w[2]>1)', 'if(w[0]==7&&w[2]>2)')
  s=m.replace(s,'else{token=w[2]?0x96000000u:0x90000000u;reply=w[2]?0x97000000u:0x95000000u;}', 'else{token=w[2]==2?0x98000000u:w[2]?0x96000000u:0x90000000u;reply=w[2]==2?0x99000000u:w[2]?0x97000000u:0x95000000u;}')
 if '-DI960_DOOM_PLAY' in flags:s='#define I960_DOOM_PLAY 1\n'+s
 if '-DI960_DOOM_ENGINE' in flags:s='#define I960_DOOM_ENGINE 1\n'+s
 if '-DI960_DOOM_RUNTIME' in flags:s='#define I960_DOOM_RUNTIME 1\n'+s
 if '-DI960_DOOM_CHECKPOINT_BARRIERS' in flags:s='#define I960_DOOM_CHECKPOINT_BARRIERS 1\n'+s
 if '-DI960_DOOM_CHECKPOINTS' in flags:s='#define I960_DOOM_CHECKPOINTS 1\n'+s
 if '-DI960_DOOM_OWNED' in flags:s='#define I960_DOOM_OWNED 1\n'+s
 if '-DI960_RESIDENT_UPLOAD' in flags:
  header=out/'buffer_io.h';header.write_text(protect_upload_header(header.read_text(),'-DI960_DOOM_ENGINE' in flags))
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'upload_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=resident_ioctl,','.unlocked_ioctl=upload_ioctl,')
 if '-DI960_DOOM_DMA' in flags:
  s='#define I960_DOOM_DMA 1\n'+s
  s=m.replace(s,'void *dma_buf;', 'void *dma_buf;void *frame_dma_buf;dma_addr_t frame_dma_bus;struct debugfs_blob_wrapper frame_dma_blob;unsigned frame_dma_gen,frame_dma_no_crc;bool frame_dma_pending,frame_dma_valid;unsigned frame_dma_fault[100];struct debugfs_blob_wrapper frame_dma_fault_blob;')
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE.parent/'dma/frame_diag_host.h').read_text()+'\n'+(HERE.parent/'dma/frame_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=upload_ioctl,','.unlocked_ioctl=frame_dma_ioctl,')
  s=m.replace(s,'void *dma_buf;', 'void *dma_buf;void *wad_dma_buf;dma_addr_t wad_dma_bus;unsigned wad_dma_gen,wad_dma_geometry[3];bool wad_dma_pending;')
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE.parent/'dma/wad_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=frame_dma_ioctl,','.unlocked_ioctl=wad_dma_ioctl,')
  # Only an activated bulk-WAD mapping opts into the existing bounded spin.
  # Legacy WAD/control/frame operations retain their previous polling policy.
  begin=s.index('static int packet_exchange(');end=s.index('static long resident_ioctl(',begin)
  exchange=s[begin:end]
  exchange=m.replace(exchange,'  usleep_range(50,100);','  if(d->wad_dma_gen && ((token>>24)==0x75u || (token>>24)==0x76u || ((token>>24)==0x77u && ((token>>16)&255u))) && i<16)cpu_relax();else usleep_range(50,100);')
  s=s[:begin]+exchange+s[end:]
  s=m.replace(s,'    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);','    if(d->wad_dma_buf)dma_free_coherent(&pdev->dev,12288,d->wad_dma_buf,d->wad_dma_bus);\n    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);')
  s=m.replace(s,'    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);','    if(d->frame_dma_buf)dma_free_coherent(&pdev->dev,73728,d->frame_dma_buf,d->frame_dma_bus);\n    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);')
 if '-DI960_DMA_PROOF' in flags:
  s=m.replace(s,'void *dma_buf;', 'void *dma_buf; void *proof_buf; struct debugfs_blob_wrapper proof_blob; dma_addr_t proof_dma; unsigned proof_seq; bool proof_valid,proof_pending,proof_cancelled;unsigned proof_n,proof_offset,proof_seed;')
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE.parent/'dma/host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=resident_ioctl,','.unlocked_ioctl=dma_proof_ioctl,')
  s=m.replace(s,'    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);', '    if(d->proof_buf)dma_free_coherent(&pdev->dev,73728,d->proof_buf,d->proof_dma);\n    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);')
 if '-DI960_FAULT_TEST=3' in flags:
  s=m.replace(s,'mu_resident;', 'mu_resident,mu_nmi_injected;')
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'nmi_test_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=resident_ioctl,','.unlocked_ioctl=nmi_test_ioctl,')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)
