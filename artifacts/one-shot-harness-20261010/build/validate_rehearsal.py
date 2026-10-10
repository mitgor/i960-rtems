#!/usr/bin/env python3
"""Validate the live default-mode rehearsal; never executes hardware commands."""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]

def validate():
    base=ROOT/'artifacts/one-shot-harness-20261010'
    spec=importlib.util.spec_from_file_location('cpu_validation',ROOT/'loader/staging-cpu/validate_live.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=module.validate(base)
    text=(base/'captures/result.txt').read_text()
    assert 'program-state=2 rc=0 submitted=0 completed=0 verified=0' in text
    assert 'PROGRAM SUBMITTED' not in text
    assert 'invalid-token-rejected-before-driver-registration' in (base/'token-rejection.txt').read_text()
    report.update(programming_mode='disabled',programming_doorbells=0,
                  invalid_program_token_rejected=True,live_programming_path_tested=False)
    return report

if __name__=='__main__':print(json.dumps(validate(),indent=2))
