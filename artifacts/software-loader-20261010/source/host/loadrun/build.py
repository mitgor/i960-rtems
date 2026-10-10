#!/usr/bin/env python3
"""Generate the runtime loader module. No hardware access or flash operation."""
from pathlib import Path
import argparse,hashlib,re,shutil
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError('base source changed: '+old[:80])
    return s.replace(old,new,1)

def build(out):
    if out.exists(): raise ValueError('output directory must not exist')
    code=(ROOT/'artifacts/software-loader-20261010/target/runner.bin').read_bytes()
    if hashlib.sha256(code).hexdigest()!='0ee14834d8484957836126e6fbe33aeb9928b3398fab023c9c6479f8cd927075':
        raise ValueError('runner build not pinned')
    if len(code)!=104 or code[16:20]!=bytes.fromhex('78563412') or code[24:28]!=bytes.fromhex('00c0f2c0'):
        raise ValueError('wrong runner layout')
    if code[-4:]!=bytes.fromhex('00500484'): raise ValueError('wrong completion tail')
    out.mkdir(parents=True)
    for name in ['dac960dump.c','Makefile','staging_pointer.h','ram_scratch.h','rom_exec.h','stage_data.h','stage_rehearsal.h']:
        shutil.copyfile(ROOT/'host/dump'/name,out/name)
    shutil.copyfile(HERE/'policy.h',out/'load_policy.h')
    p=out/'stage_data.h';s=p.read_text();m=re.search(r'static const unsigned char stage_candidate_sha256\[32\] = \{.*?\};',s,re.S)
    if not m: raise ValueError('installed firmware hash missing')
    p.write_text(m[0]+'\n')
    p=out/'rom_exec.h';s=p.read_text().replace('#define EXEC_REGION_SIZE 64u','#define EXEC_REGION_SIZE 128u').replace('#define EXEC_FLASH_SIZE 36u','#define EXEC_FLASH_SIZE 104u')
    s=s.replace('0x7e,0x01,0x88,0x8c','0x7d,0x01,0x88,0x8c')
    s,n=re.subn(r'static const unsigned char exec_flash_code\[EXEC_FLASH_SIZE\] = \{.*?\};','static const unsigned char exec_flash_code[EXEC_FLASH_SIZE] = {\n'+','.join(f'0x{x:02x}' for x in code)+'\n};',s,flags=re.S)
    if n!=1: raise ValueError('runner array not found')
    s=s.replace('((count == EXEC_TABLE_SIZE && offset == EXEC_TABLE_OFFSET) ||', '((count == 16 && offset == LOAD_RESULT_OFFSET) ||\n         (count == EXEC_TABLE_SIZE && offset == EXEC_TABLE_OFFSET) ||')
    p.write_text(s)
    p=out/'stage_rehearsal.h';s=p.read_text().split('static int stage_upload(',1)[0]+(HERE/'transaction.h').read_text();p.write_text(s)
    p=out/'dac960dump.c';s=p.read_text()
    s=replace(s,'#include "rom_exec.h"','#include <linux/firmware.h>\n#include "load_policy.h"\n#include "rom_exec.h"')
    s=replace(s,'static bool stage_check;','''static char *firmware_name;
static unsigned int payload_argument;
static unsigned int entry_offset;
module_param(firmware_name, charp, 0444);
module_param(payload_argument, uint, 0444);
module_param(entry_offset, uint, 0444);
static bool stage_check;''')
    s=replace(s,'    struct pci_dev *pdev;','''    const struct firmware *payload;
    bool load_armed;
    u8 runner_code[EXEC_FLASH_SIZE];
    struct pci_dev *pdev;''')
    s=replace(s,'!stage_upload_allowed(count,offset,d->runtime_verified,d->stage_armed)',
              '!load_upload_allowed(count,offset,d->payload->size,d->runtime_verified,d->load_armed)')
    s=replace(s,'(status == 0x0104 || status == 0x017e || status == 0x017f)',
              '(status == 0x0104 || status == 0x017d || status == 0x017e || status == 0x017f)')
    s=replace(s,'    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;',
              '    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;\n    if (!stage_check || !firmware_name) return -EINVAL;')
    s=replace(s,'    d->pdev = pdev;','''    d->pdev = pdev;
    rc = request_firmware(&d->payload, firmware_name, &pdev->dev);
    if (rc) goto free_state;
    if (d->payload->size > LOAD_MAX || !load_valid(d->payload->size, entry_offset)) { rc=-EINVAL; goto free_state; }''')
    s=replace(s,'        d->capture[i].data = kzalloc(d->capture[i].blob.size, GFP_KERNEL);',
              '        if (i == 20 || i == 21) d->capture[i].blob.size = 16;\n        d->capture[i].data = kzalloc(d->capture[i].blob.size, GFP_KERNEL);')
    s=s.replace('    kfree(d);','    if (d->payload) release_firmware(d->payload);\n    kfree(d);')
    s=replace(s,'module_pci_driver(dac960dump_driver);','''static int __init load_init(void)
{
    if (!firmware_name || !stage_check || !pointer_check || !runtime_check ||
        scratch_check || rom_exec_check || rom_table_check || dram_hook_check || flash_map_check || attempt)
        return -EINVAL;
    return pci_register_driver(&dac960dump_driver);
}
static void __exit load_exit(void) { pci_unregister_driver(&dac960dump_driver); }
module_init(load_init);
module_exit(load_exit);''')
    # Distinct module/driver/debugfs name; it cannot co-own the PCI device.
    s=s.replace('dac960dump','dac960loadrun')
    (out/'dac960loadrun.c').write_text(s);p.unlink()
    (out/'Makefile').write_text((out/'Makefile').read_text().replace('dac960dump','dac960loadrun'))
    print('Built source for runtime loader; runner SHA256 '+hashlib.sha256(code).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();build(a.out)
