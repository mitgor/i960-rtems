#!/usr/bin/env python3
"""Offline card/workflow admission for shell build pipelines."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from card_profiles import require_workflow

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--card-profile',required=True)
p.add_argument('--workflow',required=True)
a=p.parse_args()
try:
    print(json.dumps(require_workflow(a.card_profile,a.workflow),sort_keys=True))
except ValueError as e:
    p.error(str(e))
