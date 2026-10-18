#!/usr/bin/env python3
"""Installer integrity and command routing without touching a card or service."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import install
import launcher

here=Path(__file__).resolve().parent
wheel=here.parents[4]/'artifacts/current/doom-stream-20261018/dependencies/websockets-15.0.1-py3-none-any.whl'
with tempfile.TemporaryDirectory() as name:
    root=Path(name);source=root/'source';source.mkdir()
    for file in here.iterdir():
        if file.is_file():shutil.copyfile(file,source/file.name)
    wrapper=root/'doom-flat';wrapper.write_text('#!/bin/sh\necho original-owner "$@"\n')
    original=wrapper.read_bytes()
    args=['install','--root',str(root),'--wrapper',str(wrapper),'--wheel',str(wheel)]
    with patch.object(sys,'argv',args):install.main()
    assert (root/'owner-launcher').read_bytes()==original
    with patch.object(sys,'argv',args):install.main()
    assert (root/'owner-launcher').read_bytes()==original
    for action in ('stop','shutdown','status'):
        argv=['launcher','--gateway-root',str(root),'--owner-launcher',str(root/'owner-launcher'),action]
        with patch.object(sys,'argv',argv),patch('subprocess.run',return_value=SimpleNamespace(returncode=0)) as run:
            assert launcher.main()==0
            commands=[x.args[0] for x in run.call_args_list]
            assert [str(root/'owner-launcher'),action] in commands
            stream_stop=['sudo','-n','systemctl','stop','i960-doom-stream.service']
            assert (stream_stop in commands)==(action=='shutdown')
            assert not any('rmmod' in command or 'insmod' in command for command in commands)
    (source/'gateway.py').write_text('tampered')
    with patch.object(sys,'argv',argv),patch('subprocess.run') as run:
        try:launcher.main();raise AssertionError('tampered gateway accepted')
        except RuntimeError as error:assert 'gateway identity' in str(error)
        run.assert_not_called()
print('PASS repeatable install, original-owner preservation, soft STOP routing, terminal shutdown routing and source tamper rejection')
