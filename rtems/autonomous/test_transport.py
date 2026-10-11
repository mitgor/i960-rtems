#!/usr/bin/env python3
"""Fault-inject the generated stop-before-restore transport, offline only."""
import re,subprocess,tempfile,sys
from pathlib import Path
from build_transport import build,ROOT,wire
for network in (False,True):
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp);payload=t/'code.bin';payload.write_bytes(b'\0'*4);build(t/'module',payload,network=network)
  image=wire.prepare(payload.read_bytes());(t/'prepared.bin').write_bytes(image)
  helper=(t/'module/stage_rehearsal.h').read_text();helper=helper[helper.index('static int load_chunks'):]
  # The existing command simulator uses FNV as its digest stub. Adapt only the
  # pinned digest value to that same stub; production generation uses SHA256.
  h=2166136261
  for x in image:h=((h^x)*16777619)&0xffffffff
  digest=h.to_bytes(4,'little')*8
  helper=re.sub(r'static const u8 allowed\[32\]=\{[^}]*\}', 'static const u8 allowed[32]={'+','.join(str(x) for x in digest)+'}',helper)
  (t/'module/transaction_under_test.h').write_text(helper)
  baseline=(ROOT/'host/loadrun/test_transaction.c').read_text().split('static int one(')[0]
  baseline=baseline.replace('    struct firmware *payload;','    bool ready,runner_uncertain,output_valid,irq_may_run;u32 sequence,steps,output_length;\n    struct firmware *payload;')
  baseline=baseline.replace('static bool buffer_io;','static bool buffer_io=true;')
  baseline=baseline.replace('#define payload buffer_payload','#define GFP_KERNEL 0\n#define kzalloc(n,f) calloc(1,n)\n#define kfree free\nstatic int irq_running,bad_stop;\n#define payload buffer_payload')
  baseline=baseline.replace('        assert(d->upload_data);','        assert(d->upload_data);\n        if(irq_running)assert((off>=BIO_OFFSET&&off+count<=BIO_IMAGE_SIZE)||off==EXEC_TABLE_OFFSET||off==LOAD_RESULT_OFFSET);')
  baseline=baseline.replace('b=address(off,count);memcpy', 'if(irq_running)card[0x20100]++;\n        b=address(off,count);memcpy')
  (t/'buffer_demo.c').write_text('''unsigned int payload(unsigned long address){unsigned char*b=(unsigned char*)address,*o=b+BIO_OUTPUT;unsigned int op=bio_word(b+BIO_INPUT+4);if(op==1)irq_running=1;if((op==2||op==6)&&!bad_stop)irq_running=0;memset(o,0,64);bio_put(o,0x31415452);bio_put(o+28,0x10c7);bio_put(o+32,0x80000);bio_put(o+36,0xaaaaaaaa);bio_put(o+40,0xaaaaaaaa);bio_put(o+60,irq_running);bio_put(b+20,0);bio_put(b+24,64);bio_put(b+28,bio_word(b+8));return 0;}''')
  main=r'''
 static u8 prepared[BIO_IMAGE_SIZE];
 static int one(int fail,int timeout){
  struct experiment d={0};struct firmware fw={BIO_IMAGE_SIZE,prepared};unsigned int i;int rc,n,boundary;
  u8*b=calloc(1,BIO_SIZE);memcpy(b,prepared+BIO_OFFSET,BIO_SIZE);
  put(b+8,42);put(b+12,16);put(b+BIO_INPUT,0x31415452);put(b+BIO_INPUT+4,1);
  memcpy(card,original,IMAGE_WINDOW);memset(card+IMAGE_WINDOW,0,sizeof(card)-IMAGE_WINDOW);put(table,0xfefe001c);
  calls=executions=irq_running=0;fail_at=fail;timeout_mode=timeout;payload_argument=BIO_BASE;
  d.payload=&fw;d.runtime_verified=true;
  for(i=0;i<54;i++)d.capture[i].data=calloc(1,128);
  for(i=0;i<8;i++)d.stage[i].data=calloc(1,IMAGE_WINDOW);
  rc=session_open(&d);if(!rc)rc=session_step(&d,b);if(rc)d.ready=false;boundary=calls;
  if(d.pending||d.runner_uncertain){assert(session_close(&d)==-EBUSY&&calls==boundary);}
  else {int close_rc=session_close(&d);if(!rc)rc=close_rc;}
  n=calls;
  if(!fail&&!bad_stop){assert(!rc&&!irq_running&&!d.irq_may_run&&!d.exec_dirty&&!d.stage_dirty&&executions==2);assert(!memcmp(card,original,IMAGE_WINDOW));}
  if(fail)assert(rc&&calls>=fail);if(bad_stop)assert(rc&&irq_running&&d.irq_may_run&&d.stage_dirty);
  if(irq_running)assert(d.stage_dirty); /* Never restore/release live handler RAM. */
  if(d.pending)assert(calls==fail);
  for(i=0;i<54;i++)free(d.capture[i].data);
  for(i=0;i<8;i++)free(d.stage[i].data);
  free(b);return n;
 }
 int main(int argc,char**argv){FILE*f;int n,i;assert(argc==3);f=fopen(argv[1],"rb");assert(f&&fread(original,1,IMAGE_WINDOW,f)==IMAGE_WINDOW);fclose(f);f=fopen(argv[2],"rb");assert(f&&fread(prepared,1,sizeof(prepared),f)==sizeof(prepared));fclose(f);n=one(0,0);for(i=1;i<=n;i++){one(i,0);one(i,1);}bad_stop=1;one(0,0);printf("autonomous: %d command-failure/timeout boundaries; changing private state; stop-before-restore passed\n",n*2);return 0;}
 '''
  (t/'test.c').write_text(baseline+main)
  subprocess.run(['cc','-Wall','-Wextra','-Wno-unused-function','-fsanitize=address,undefined','-g','-I'+str(t/'module'),'-I'+str(t),str(t/'test.c'),'-o',str(t/'test')],check=True)
  subprocess.run([str(t/'test'),str(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin'),str(t/'prepared.bin')],check=True)
