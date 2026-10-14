#!/usr/bin/env python3
"""Execute actual failure/STOP branches; a failed network future cannot strand audits."""
import tempfile,textwrap,threading
from pathlib import Path
from types import SimpleNamespace
here=Path(__file__).resolve().parent
s=(here/'live.py').read_text();a=s.index('     traffic_active=False\n     if future.exception()');b=s.index('\n    pump_packets()',a)
error=TimeoutError('network test');abort=threading.Event()
with tempfile.TemporaryDirectory() as d:
 ns=dict(future=SimpleNamespace(exception=lambda:error),abort_upload=abort,b=SimpleNamespace(out=Path(d)),traffic_active=True)
 exec(textwrap.dedent(s[a:b]),ns);assert abort.is_set() and not ns['traffic_active'] and 'network test' in (Path(d)/'network-error.txt').read_text()
s=(here/'play_client.py').read_text();a=s.index('    if abort is not None');b=s.index('    # Never race',a)
requests=[];ns=dict(abort=abort,stop=threading.Event(),stop_sent=False,seen=1,server=SimpleNamespace(records=[]),request_base=0,control=SimpleNamespace(query=lambda:[0,42,1],request=requests.append))
exec(textwrap.dedent(s[a:b]),ns);assert ns['stop_sent'] and requests==[42]
exec(textwrap.dedent(s[a:b]),ns);assert requests==[42]
print('PASS network failure keeps control loop alive, records error, requests owned STOP exactly once')
