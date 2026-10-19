#!/usr/bin/env python3
"""One host command interface; existing PCI owner and console remain sole owners."""
import argparse,json,socket,struct
from client import Client
MAGIC=0x505041f1
class Service:
 def __init__(self):self.client=Client()
 def console(self,command):
  if '\n' in command or len(command)>128:raise ValueError('one bounded command required')
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
   s.settimeout(5);s.connect('/run/i960-rtems-console.sock');s.sendall((command+'\n').encode());b=b''
   while True:
    x=s.recv(1024)
    if not x:break
    b+=x
    if len(b)>4096:raise ValueError('console response bounds')
  return b.decode()
 def app(self,op,app,generation=0,payload=b'',allow_error=False):
  if len(payload)>256:raise ValueError('application input limited to 256 bytes')
  raw=bytes.fromhex(self.client.call(5,struct.pack('<5I',MAGIC,1,op,app,generation)+payload)['data'])
  if len(raw)<48:raise RuntimeError('short application response')
  w=struct.unpack_from('<12I',raw)
  if w[:2]!=(0x525041f1,1) or w[3]!=app or w[5]>1 or w[11]>256 or len(raw)!=48+w[11]:raise RuntimeError('application reply identity/length')
  if not w[2] and op!=3 and w[4]!=(generation+1 if op==1 else generation):raise RuntimeError('application generation response')
  r=dict(zip(('status','id','generation','running','updates','elapsed_ms','requests','stops','errors','length'),w[2:]));r['text']=raw[48:].decode('utf-8',errors='replace')
  if r['status'] and not allow_error:raise RuntimeError(r)
  return r
 def execute(self,line):
  args=line.split(maxsplit=2)
  if not args:return ''
  if line.strip()=='help':return self.console('help')+'host: net; app list; app start/stop counter/echo; app echo TEXT\n'
  if args[0]=='net':
   r=self.client.call(7);raw=bytes.fromhex(r['data'])
   if len(raw)!=24:raise RuntimeError('network counter response size')
   result=dict(zip(('received','transmitted','dropped','fetch_state','fetch_bytes','fetch_hash'),struct.unpack('<6I',raw)))
   result.update(module_calls=r['calls'],running=bool(r['started']),poisoned=bool(r['poisoned']));return result
  if args[0]=='app':
   if len(args)<2:raise ValueError('app list | start/stop counter/echo | echo TEXT')
   if args[1]=='list':return [self.app(3,i) for i in (1,2)]
   if args[1]=='echo':
    a=self.app(3,2);return self.app(4,2,a['generation'],(args[2] if len(args)>2 else '').encode())
   words=line.split()
   if len(words)!=3 or words[1] not in ('start','stop') or words[2] not in ('counter','echo'):raise ValueError('app start/stop counter/echo')
   i={'counter':1,'echo':2}[words[2]];a=self.app(3,i)
   if bool(a['running'])==(words[1]=='start'):return a
   return self.app(1 if words[1]=='start' else 2,i,a['generation'])
  return self.console(line)
def main():
 p=argparse.ArgumentParser();p.add_argument('command',nargs='*');a=p.parse_args();s=Service()
 def show(line):
  r=s.execute(line);print(r if isinstance(r,str) else json.dumps(r,indent=2),end='\n')
 if a.command:
  try:show(' '.join(a.command))
  except (OSError,RuntimeError,ValueError,AssertionError) as e:raise SystemExit('service: '+str(e))
  return
 print('RTEMS combined prompt: help, net, app list/start/stop/echo; quit disconnects')
 while True:
  try:
   line=input('rtems> ')
   if line.strip() in ('quit','exit'):return
   show(line)
  except EOFError:return
  except (OSError,RuntimeError,ValueError,AssertionError) as e:print('service:',e)
if __name__=='__main__':main()
