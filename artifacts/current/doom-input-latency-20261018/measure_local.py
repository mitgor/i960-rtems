#!/usr/bin/env python3
"""Run on the Linux host as root against a live reusable flat-enabled game.

Eight F6 press/release pairs restore the initial mode. No PCI access; the
existing owner keeps all audits. Measures request-to-validated-frame, not paint.
"""
import json
from pathlib import Path
import statistics
import time
import urllib.request

control = json.loads(Path('/run/i960-doom-control.json').read_text())
base = 'http://127.0.0.1:' + str(control['port'])

def status():
    with urllib.request.urlopen(base + '/status', timeout=3) as r:
        return json.load(r)

def post(path, body):
    request = urllib.request.Request(base + path, json.dumps(body).encode(),
        headers={'X-Session-Token': control['token'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=3) as r:
        assert r.status == 200

initial = status()
assert initial['state'] == 'running' and initial['flat_planes'] in (0, 1)
rows = []
for i in range(8):
    before = status()
    assert before['run_id'] == initial['run_id'] and before['state'] == 'running'
    start = time.monotonic_ns()
    post('/key', dict(run_id=before['run_id'], key=192, down=1))
    accepted = time.monotonic_ns()
    post('/key', dict(run_id=before['run_id'], key=192, down=0))
    deadline = time.monotonic() + 5
    while True:
        current = status()
        assert current['run_id'] == before['run_id']
        if current['flat_switches'] == before['flat_switches'] + 1:
            assert current['flat_planes'] == 1 - before['flat_planes']
            break
        assert time.monotonic() < deadline, 'F6 confirmation timeout'
        time.sleep(.01)
    rows.append(dict(trial=i+1, before=before, confirmed=current,
        http_down_ms=(accepted-start)/1e6,
        request_to_validated_frame_ms=(time.monotonic_ns()-start)/1e6))
    time.sleep(.3)  # Allow the acknowledged release before another press.
assert status()['flat_planes'] == initial['flat_planes']
values = [r['request_to_validated_frame_ms'] for r in rows]
print(json.dumps(dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    method='Linux loopback HTTP F6 to mode confirmed in validated card frame; 10 ms observer polling',
    median_ms=statistics.median(values), min_ms=min(values), max_ms=max(values), trials=rows), indent=2))
