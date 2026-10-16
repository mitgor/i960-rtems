#!/usr/bin/env python3
import json,subprocess
from pathlib import Path
w=Path(__file__).resolve().parent;p=w/'probe'
for i in range(32):
 subprocess.run(['sudo','python3',str(w/'project/host/loadrun/loadrun.py'),str(p/'probe.bin'),'--module',str(p/'module/dac960loadrun.ko'),'--output',str(p/f'case-{i}'),'--argument',str(i),'--expect','32'],check=True)
 print('PASS batch',i,flush=True)
