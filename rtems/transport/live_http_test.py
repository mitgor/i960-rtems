#!/usr/bin/env python3
"""Test an already-running card HTTP server; does not change host routing."""
import argparse,hashlib,json,socket

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--address',default='fd96:196:960::2');p.add_argument('--port',type=int,default=80);a=p.parse_args();results=[]
 def query(chunks):
  with socket.socket(socket.AF_INET6,socket.SOCK_STREAM) as s:
   s.settimeout(10);s.connect((a.address,a.port))
   for chunk in chunks:s.sendall(chunk)
   data=b''
   while True:
    part=s.recv(4096)
    if not part:return data
    data+=part
    assert len(data)<8192
 tests=[('get',[b'GET / HTTP/1.0\r\n\r\n'],b'200'),('fragmented',[b'GET / HT',b'TP/1.0\r\nHost: card\r',b'\n\r\n'],b'200'),('invalid',[b'POST / HTTP/1.0\r\n\r\n'],b'400'),('oversize',[b'GET / HTTP/1.0\r\nX: '+b'x'*600+b'\r\n\r\n'],b'431')]
 for name,chunks,status in tests:
  data=query(chunks);assert data.split(b' ')[1]==status,(name,data);results.append(dict(test=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
 for _ in range(20):assert query([b'GET / HTTP/1.0\r\n\r\n']).startswith(b'HTTP/1.0 200')
 print(json.dumps(dict(passed=True,requests=24,results=results),indent=2))
if __name__=='__main__':main()
