#!/usr/bin/env python3
"""ASan/UBSan test of the actual lwIP stack and virtual interface on the host."""
import subprocess,tempfile,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp)
 with tarfile.open(ROOT/'artifacts/rtems-20261011/sources/lwip-2.1.3.tar.gz') as t:t.extractall(tmp,filter='data')
 src=tmp/'lwip-STABLE-2_1_3_RELEASE'
 # Same narrow DNS packing fix as target build.
 p=src/'src/core/dns.c';p.write_text(p.read_text().replace('struct dns_answer {','struct __attribute__((packed)) dns_answer {'))
 sources=sorted((src/'src/core').glob('*.c'))+sorted((src/'src/core/ipv4').glob('*.c'))+[HERE/'net/network.c',HERE/'net/test_network.c']
 cmd=['cc','-fno-common','-O1','-g','-fsanitize=address,undefined','-I'+str(HERE/'net'),'-I'+str(HERE/'transport'),'-I'+str(src/'src/include'),*map(str,sources),'-o',str(tmp/'test')]
 subprocess.run(cmd,check=True);subprocess.run([str(tmp/'test')],check=True)
