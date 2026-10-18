#!/usr/bin/env python3
"""Four F6 trials from the browser computer; no token is printed or archived.

The browser page provides its normal control token. Requires a running game
and no simultaneous keyboard user. An even number of toggles restores mode.
"""
import json
import re
import statistics
import time
import urllib.request

base = 'http://192.168.2.75:8087'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
with opener.open(base + '/', timeout=5) as response:
    token = re.search(r"const token='([^']+)'", response.read().decode())[1]

def status():
    with opener.open(base + '/status', timeout=5) as response:
        return json.load(response)

def key(run_id, down):
    request = urllib.request.Request(base + '/key',
        json.dumps(dict(run_id=run_id, key=192, down=down)).encode(),
        headers={'Content-Type': 'application/json', 'X-Session-Token': token})
    with opener.open(request, timeout=5) as response:
        assert response.status == 200

rows = []
initial = status()
assert initial['state'] == 'running'
for i in range(4):
    before = status()
    assert before['run_id'] == initial['run_id'] and before['state'] == 'running'
    start = time.monotonic_ns()
    try:
        key(before['run_id'], 1)
        accepted = time.monotonic_ns()
    finally:
        key(before['run_id'], 0)
    deadline = time.monotonic() + 10
    while True:
        confirmed = status()
        assert confirmed['run_id'] == before['run_id']
        if confirmed['flat_switches'] == before['flat_switches'] + 1:
            assert confirmed['flat_planes'] == 1 - before['flat_planes']
            break
        assert time.monotonic() < deadline
        time.sleep(.01)
    rows.append(dict(trial=i+1, before=before, confirmed=confirmed,
        http_down_ms=(accepted-start)/1e6,
        request_to_observed_confirmation_ms=(time.monotonic_ns()-start)/1e6))
    time.sleep(.3)
assert status()['flat_planes'] == initial['flat_planes']
values = [r['request_to_observed_confirmation_ms'] for r in rows]
print(json.dumps(dict(method='Mac HTTP F6; sequential down/up/status, no canvas paint measurement',
    median_ms=statistics.median(values), min_ms=min(values), max_ms=max(values), trials=rows), indent=2))
