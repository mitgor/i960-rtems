#!/usr/bin/env python3
import argparse,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--sources',type=Path,required=True);a=p.parse_args()
subprocess.run([sys.executable,str(HERE.parent/'build_target.py'),'--work',str(a.work),'--sources',str(a.sources),'--request-words','--render-fast','--frame-queue'],check=True)
