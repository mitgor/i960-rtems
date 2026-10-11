#!/usr/bin/env python3
"""Exercise the real generated quiet transaction, policies and failure cleanup."""
import importlib.util,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('upload_builder',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for detail in [True,False]:
 with tempfile.TemporaryDirectory(prefix='i960-upload-test-') as tmp:
  d=Path(tmp);m.build(d/'module',True,detail);root=m.ROOT
  source=(root/'host/loadrun/test_transaction.c').read_text().split('static int one(')[0]
  source=source.replace('    struct firmware *payload;','    bool ready,runner_uncertain,output_valid,quiet_armed,quiet_dirty;u32 sequence,steps,output_length;\n    struct firmware *payload;')
  source=source.replace('card[BIO_IMAGE_SIZE+4]^=1','card[BIO_IMAGE_SIZE+4]=original[BIO_IMAGE_SIZE+4]^1')
  source=source.replace('static bool buffer_io;','static bool buffer_io=true;')
  source=source.replace('static u8 *address(','''#include "quiet_policy.h"
#include "quiet_data.h"
static u8 quiet_memory[80],printf_memory[256],uart_memory[104];
static u32 cached_dispatch;
static u8 board_pointer[]={0x80,0x07,0x11,0xc0};
static u8 board_methods[]={0x90,0xce,0x04,0xc0,0xd0,0xce,0x04,0xc0};
static u8 *address(''')
  source=source.replace('    if(off==EXEC_TABLE_OFFSET)', '''    if(off==QUIET_OFFSET) {assert(size==4 || size==80);return quiet_memory;}
    if(off==0xc011e22cu-STAGING_BASE){assert(size==4);return board_pointer;}
    if(off==0xc0110860u-STAGING_BASE){assert(size==8);return board_methods;}
    if(off==0xc000a2a0u-STAGING_BASE){assert(size==256);return printf_memory;}
    if(off==0xc000a120u-STAGING_BASE){assert(size==104);return uart_memory;}
    if(off==EXEC_TABLE_OFFSET)''')
  source=source.replace('assert(load_upload_allowed(', 'assert(quiet_write_allowed(count,off,d->runtime_verified,d->quiet_armed)||load_upload_allowed(')
  # Model the observed hazard: UART traffic can evict a cached table word;
  # PING leaves it cached, while the cache callback and runner invalidate it.
  source=source.replace('        memcpy(address(off,count),d->upload_data,count);', '        if(quiet_memory[0])cached_dispatch=0;\n        memcpy(address(off,count),d->upload_data,count);')
  source=source.replace('        if(sp_word(table)==0xfefe001c)', '        if(!cached_dispatch)cached_dispatch=sp_word(table);\n        if(cached_dispatch==0xfefe001c)')
  source=source.replace('else if(sp_word(table)==EXEC_RAM_ADDRESS) status=0x17d;', 'else if(cached_dispatch==EXEC_RAM_ADDRESS) {status=0x17d;cached_dispatch=0;}')
  source=source.replace('assert(sp_word(table)==EXEC_FLASH_ADDRESS);', 'assert(cached_dispatch==EXEC_FLASH_ADDRESS);cached_dispatch=0;')
  main=(root/'host/session/test_session_main.c').read_text()
  main=main.replace('    calls=executions=0;', '''    memcpy(quiet_memory,quiet_original,80);memcpy(printf_memory,quiet_printf,256);memcpy(uart_memory,quiet_uart,104);
    cached_dispatch=0;calls=executions=0;''')
  main=main.replace('    n=calls;', '    n=calls;\n    if(!d.quiet_dirty) assert(!memcmp(quiet_memory,quiet_original,80));')
  main=main.replace('!d.exec_dirty && !d.stage_dirty);','!d.exec_dirty && !d.stage_dirty && !d.quiet_dirty);')
  # Directly reject every bad original byte and every active-region corruption.
  extra='''static void preimage_tests(void) {
    struct experiment d={0};unsigned int i;int boundary;
    d.runtime_verified=true;d.quiet_armed=true;
    for(i=0;i<80;i++) {
        memcpy(quiet_memory,quiet_original,80);quiet_memory[i]^=1;
        assert(quiet_pair(&d,QUIET_ADDRESS,quiet_original,80)==-ENODATA);
    }
    d.quiet_dirty=true;
    for(i=0;i<80;i++) {
        memcpy(quiet_memory,quiet_original,80);quiet_memory[0]=0;quiet_memory[i]^=1;
        assert(quiet_check(&d)==-ENODATA);
        boundary=calls;assert(quiet_end(&d)==-ENODATA && calls==boundary+2 && d.quiet_dirty);
    }
    for(i=0;i<256;i++) {
        memcpy(printf_memory,quiet_printf,256);printf_memory[i]^=1;
        assert(quiet_pair(&d,0xc000a2a0,quiet_printf,256)==-ENODATA);
    }
    for(i=0;i<104;i++) {
        memcpy(uart_memory,quiet_uart,104);uart_memory[i]^=1;
        assert(quiet_pair(&d,0xc000a120,quiet_uart,104)==-ENODATA);
    }
    for(i=0;i<260;i++) {
        assert(quiet_write_allowed(i,QUIET_OFFSET,1,1)==(i==4));
        assert(quiet_read_allowed(i,QUIET_OFFSET,1,1)==(i==80));
    }
    assert(!quiet_write_allowed(4,QUIET_OFFSET+4,1,1));
    assert(!quiet_write_allowed(4,QUIET_OFFSET,0,1));
    assert(!quiet_write_allowed(4,QUIET_OFFSET,1,0));
    assert(!quiet_read_allowed(80,QUIET_OFFSET,0,1));
    assert(!quiet_read_allowed(80,QUIET_OFFSET,1,0));
    /* A completed table upload/readback alone cannot prove CPU dispatch visibility. */
    cached_dispatch=0xfefe001c;put(table,EXEC_RAM_ADDRESS);d.exec_expected_status=0x17d;
    assert(issue(&d,0x6f,0,0,0xa5,34)==-EIO && d.exec_last_status==0x17e);
    cached_dispatch=0;
    d.pending=true;boundary=calls;assert(quiet_end(&d)==-EBUSY && calls==boundary);
    d.pending=false;d.runner_uncertain=true;assert(quiet_end(&d)==-EBUSY && calls==boundary);
    puts("quiet: 520 byte corruptions, fixed read/write policy and pending/uncertain restoration refusal passed");
}
'''
  main=main.replace('int main(',extra+'int main(').replace('    n=one(0,0);','    preimage_tests();n=one(0,0);')
  (d/'buffer_demo.c').write_text((root/'loader/runtime/buffer_demo.c').read_text())
  (d/'test.c').write_text(source+main)
  helpers=(d/'module/stage_rehearsal.h').read_text();(d/'module/transaction_under_test.h').write_text(helpers[helpers.index('static int load_chunks'):])
  subprocess.run(['cc','-O2','-Wall','-Wextra','-Wno-unused-function','-fsanitize=address,undefined','-g','-I'+str(d/'module'),'-I'+str(d),str(d/'test.c'),'-o',str(d/'test')],check=True)
  subprocess.run([str(d/'test'),str(root/'artifacts/romhook-20261010/candidate-full-rom.bin')],check=True)
  driver=(d/'module/dac960rtems.c').read_text()
  assert driver.count('d->pending || d->exec_dirty || d->stage_dirty || d->quiet_dirty')==2
  assert 'd->pending || d->exec_dirty || d->stage_dirty)' not in driver
