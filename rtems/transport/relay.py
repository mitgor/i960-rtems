#!/usr/bin/env python3
"""Route actual card IP packets through a project-owned Linux TUN interface."""
import argparse,traceback,concurrent.futures,fcntl,ipaddress,json,os,select,socket,struct,subprocess,time,hashlib,signal
from pathlib import Path
from run import Board
from ipv6_gateway import IPv6Gateway, CARD6
IFACE='i960rt0';CARD='10.196.0.2';HOST='10.196.0.1';NET=ipaddress.ip_network('10.196.0.0/30')

def command(*args):return subprocess.check_output(args,text=True)
class Gateway:
 def __init__(self,out,internet=False,ipv6=False,internet6=False):
  self.fd=None;self.undo=[];self.forward=None;self.out=out;self.v6=None
  self.journal()
  routes=json.loads(command('ip','-j','route'));(out/'routes-before.json').write_text(json.dumps(routes,indent=2))
  firewall=command('iptables-save');(out/'iptables-before.txt').write_text(firewall)
  if IFACE in firewall:raise RuntimeError('stale project firewall rules; use saved gateway journal to clean up')
  for route in routes:
   dst=route.get('dst','default')
   if dst!='default' and ipaddress.ip_network(dst,strict=False).overlaps(NET):raise RuntimeError('test subnet overlaps existing route')
  if Path('/sys/class/net',IFACE).exists():raise RuntimeError('test interface already exists')
  self.fd=os.open('/dev/net/tun',os.O_RDWR|os.O_NONBLOCK)
  fcntl.ioctl(self.fd,0x400454ca,struct.pack('16sH',IFACE.encode(),0x0001|0x1000))
  try:
   enable6=ipv6 or internet6
   ipv6=Path('/proc/sys/net/ipv6/conf')/IFACE/'disable_ipv6'
   if ipv6.exists():ipv6.write_text('0\n' if enable6 else '1\n')
   command('ip','addr','add',HOST+'/30','dev',IFACE)
   if enable6:self.v6=IPv6Gateway(out,internet6)
   command('ip','link','set',IFACE,'up')
   if internet:
    uplinks=[r['dev'] for r in routes if r['dst']=='default'];assert len(uplinks)==1
    uplink=uplinks[0]
    def rule(table,chain,*args):
     command('iptables','-t',table,'-I',chain,*args);self.undo.append(['iptables','-t',table,'-D',chain,*args]);self.journal()
    # Only this TUN and address are affected. Unsolicited traffic toward card drops.
    rule('filter','FORWARD','-o',IFACE,'-j','DROP')
    rule('filter','FORWARD','-o',IFACE,'-d',CARD,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT')
    rule('filter','FORWARD','-i',IFACE,'-s',CARD,'-o',uplink,'-j','ACCEPT')
    rule('nat','POSTROUTING','-s',CARD+'/32','-o',uplink,'-j','MASQUERADE')
    self.forward=Path('/proc/sys/net/ipv4/ip_forward').read_text();self.journal();Path('/proc/sys/net/ipv4/ip_forward').write_text('1\n')
  except BaseException:self.close();raise
 def journal(self):
  (self.out/'gateway-journal.json').write_text(json.dumps(dict(undo=self.undo,original_forwarding=self.forward),indent=2))
 def close(self):
  (self.out/'iptables-active.txt').write_text(command('iptables-save','-c'))
  errors=[]
  if self.v6:
   try:self.v6.close()
   except Exception as e:errors.append(str(e))
  for args in reversed(self.undo):
   try:command(*args)
   except Exception as e:errors.append(str(e))
  self.undo=[]
  if self.forward is not None:Path('/proc/sys/net/ipv4/ip_forward').write_text(self.forward)
  if self.fd is not None:os.close(self.fd);self.fd=None
  (self.out/'iptables-after.txt').write_text(command('iptables-save'))
  (self.out/'routes-after.json').write_text(command('ip','-j','route'))
  if self.v6:(self.out/'ipv6-routes-after.json').write_text(command('ip','-6','-j','route'))
  (self.out/'cleanup.json').write_text(json.dumps(dict(errors=errors,interface_present=Path('/sys/class/net',IFACE).exists(),ip_forward=Path('/proc/sys/net/ipv4/ip_forward').read_text().strip()),indent=2))
  if errors:raise RuntimeError(errors)

class Relay:
 def __init__(self,board,gateway,drop_data=False):
  self.drop_data={4,6} if drop_data else set();self.dropped=[]
  self.board=board;self.gateway=gateway;self.last=time.monotonic();self.stats=None;self.host_packets=0;self.card_packets=0
  self.pcap=(board.out/'packets.pcap').open('wb');self.pcap.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,101))
 def packet(self,p):
  now=time.time_ns();self.pcap.write(struct.pack('<IIII',now//10**9,(now%10**9)//1000,len(p),len(p))+p);self.pcap.flush()
 def step(self,op=None,payload=b''):
  if op is None:
   op=0
   ready,_,_=select.select([self.gateway.fd],[],[],0)
   if ready:payload=os.read(self.gateway.fd,4096);op=1;self.host_packets+=1;self.packet(payload)
  now=time.monotonic();ms=int((now-self.last)*1000);self.last+=ms/1000
  # Bound catch-up per callback; time debt is serviced on later calls.
  if ms>1000:self.last-= (ms-1000)/1000;ms=1000
  reply=self.board.step(struct.pack('<4I',0x31415452 if self.board.autonomous else 0x314d5452,op,ms,len(payload))+payload)
  assert len(reply)>=48;fields=struct.unpack_from('<12I',reply)
  magic,steps,workers,ticks,n,rx,tx,drops,state,total,hashvalue,bytes_count=fields
  assert magic==(0x31415452 if self.board.autonomous else 0x314d5452) and steps==workers==self.board.sequence and n==24
  self.stats=dict(steps=steps,ticks=ticks,rx=rx,tx=tx,drops=drops,fetch_state=state,fetch_bytes=total,fetch_hash=hashvalue)
  if bytes_count&0x80000000:
   assert op==4 and len(reply)==48+(bytes_count&0x7fffffff);return reply[48:]
  assert len(reply)==48+bytes_count
  offset=48
  while offset<len(reply):
   length=struct.unpack_from('<I',reply,offset)[0];offset+=4;packet=reply[offset:offset+length];offset+=length
   assert 20<=length<=1500 and len(packet)==length
   self.packet(packet)
   version=packet[0]>>4;proto=packet[9] if version==4 else packet[6]
   if version in self.drop_data and proto==6:
    iplen=(packet[0]&15)*4 if version==4 else 40;tcplen=(packet[iplen+12]>>4)*4
    if len(packet)>iplen+tcplen and struct.unpack_from('!H',packet,iplen)[0]==9600:
     self.drop_data.remove(version);self.dropped.append(dict(step=steps,ip_version=version,packet_hex=packet.hex()));(self.board.out/'deliberate-loss.json').write_text(json.dumps(self.dropped,indent=2));continue
   assert os.write(self.gateway.fd,packet)==length;self.card_packets+=1
  return b''
 def pump(self,future,timeout):
  deadline=time.monotonic()+timeout
  while not future.done():
   if time.monotonic()>deadline:raise TimeoutError('network test timeout')
   self.step()
  return future.result()

def echo_tests(slow=False,ipv6=False):
 family=socket.AF_INET6 if ipv6 else socket.AF_INET;address=CARD6 if ipv6 else CARD
 report={}
 report['ping']=command('ping','-6' if ipv6 else '-4','-n','-c','4','-W','3',address)
 with socket.socket(family,socket.SOCK_DGRAM) as s:
  s.settimeout(5)
  for n in [1,31,500,1400]:
   payload=bytes(i%251 for i in range(n));s.sendto(payload,(address,9601));reply,addr=s.recvfrom(4096);assert reply==payload and addr[:2]==(address,9601)
 report['udp_sizes']=[1,31,500,1400]
 data=bytes((i*7)%251 for i in range(16000))
 with socket.socket(family,socket.SOCK_STREAM) as s:
  s.settimeout(20)
  if slow:s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1024)
  s.connect((address,9600));s.sendall(data)
  if slow:time.sleep(2)
  reply=bytearray()
  while len(reply)<len(data):
   chunk=s.recv(4096);assert chunk;reply+=chunk
  assert reply==data
 report['tcp_bytes']=len(data);report['tcp_sha256']=hashlib.sha256(data).hexdigest();return report

def stress_test(duration,ipv6=False):
 address=CARD6 if ipv6 else CARD
 start=time.monotonic();iterations=0;total=0;digest=hashlib.sha256()
 with socket.create_connection((address,9600),timeout=10) as s:
  s.settimeout(15)
  while time.monotonic()-start<duration:
   size=[1,31,1200,4096,16000][iterations%5];data=bytes((i+iterations)%251 for i in range(size));s.sendall(data);reply=bytearray()
   while len(reply)<size:
    b=s.recv(size-len(reply));assert b;reply+=b
   assert reply==data;digest.update(reply);iterations+=1;total+=size
 return dict(elapsed_s=time.monotonic()-start,iterations=iterations,bytes=total,sha256=digest.hexdigest())

def main():
 p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--internet',action='store_true');p.add_argument('--ipv6',action='store_true',help='test static IPv6 alongside IPv4');p.add_argument('--internet6',action='store_true',help='enable IPv6 tests and scoped NAT66 with AAAA/HTTP fetch');p.add_argument('--fetch',default='example.com');p.add_argument('--faults',action='store_true');p.add_argument('--duration',type=float,default=0);p.add_argument('--serve',type=float,nargs='?',const=0,help='keep services active for this many seconds, or until Ctrl-C when omitted');p.add_argument('--autonomous',action='store_true',help='use the pinned background-IRQ net image and dac960auto');p.add_argument('--publish-http6',metavar='GLOBAL_IPV6',help='forward host TCP port to card HTTP (requires --internet6)');p.add_argument('--http-port',type=int,default=8080);a=p.parse_args()
 if a.publish_http6 and not a.internet6:p.error("--publish-http6 requires --internet6")
 if a.duration<0 or (a.serve is not None and a.serve<0):p.error('durations must be nonnegative')
 def interrupted(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
 board=Board(a.payload,a.module,a.output,autonomous=a.autonomous);gateway=None;relay=None
 try:
  gateway=Gateway(a.output,a.internet or a.internet6,a.ipv6,a.internet6);relay=Relay(board,gateway,a.faults);relay.step(0)
  if a.publish_http6:gateway.v6.publish_http(a.publish_http6,a.http_port)
  with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:report=relay.pump(pool.submit(echo_tests,a.faults),90)
  (a.output/'local-network.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
  if a.ipv6 or a.internet6:
   with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:report6=relay.pump(pool.submit(echo_tests,a.faults,True),90)
   (a.output/'local-network6.json').write_text(json.dumps(report6,indent=2)+'\n');print(json.dumps(report6),flush=True)
  if a.duration:
   with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    report=relay.pump(pool.submit(stress_test,a.duration,a.ipv6 or a.internet6),a.duration+30)
   (a.output/'stress-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
  if a.internet or a.internet6:
   relay.step(5 if a.internet6 else 2,struct.pack('<H',80)+a.fetch.encode());deadline=time.monotonic()+60
   while relay.stats['fetch_state'] not in (4,) and relay.stats['fetch_state']<0x80000000:
    if time.monotonic()>deadline:raise TimeoutError(relay.stats)
    relay.step()
   assert relay.stats['fetch_state']==4,relay.stats
   response=relay.step(4,struct.pack('<I',0))+relay.step(4,struct.pack('<I',4096))
   assert len(response)==relay.stats['fetch_bytes'];h=2166136261
   for b in response:h=((h^b)*16777619)&0xffffffff
   assert h==relay.stats['fetch_hash'];assert response.startswith(b'HTTP/1.'),response[:100]
   (a.output/'http-response.bin').write_bytes(response)
   (a.output/'http-result.json').write_text(json.dumps(dict(host=a.fetch,ip_version=6 if a.internet6 else 4,bytes=len(response),sha256=hashlib.sha256(response).hexdigest(),fnv1a=h),indent=2))
  if a.serve is not None:
   started=time.monotonic();last_report=started
   (a.output/'serve-start.json').write_text(json.dumps(dict(pid=os.getpid(),card=CARD,card6=CARD6 if a.ipv6 or a.internet6 else None,tcp_port=9600,udp_port=9601,seconds=a.serve),indent=2)+'\n')
   print('RTEMS services active: '+CARD+(' and '+CARD6 if a.ipv6 or a.internet6 else '')+' TCP 9600, UDP 9601; Ctrl-C to stop',flush=True)
   while a.serve==0 or time.monotonic()-started<a.serve:
    relay.step()
    if time.monotonic()-last_report>=60:print(json.dumps(relay.stats),flush=True);last_report=time.monotonic()
   (a.output/'serve-result.json').write_text(json.dumps(dict(elapsed_s=time.monotonic()-started,stats=relay.stats),indent=2)+'\n')
  for _ in range(12):relay.step()
  (a.output/'network-summary.json').write_text(json.dumps(relay.stats,indent=2)+'\n')
 except BaseException as exc:
  (a.output/'error.json').write_text(json.dumps(dict(error=repr(exc),traceback=traceback.format_exc(),last_stats=relay.stats if relay else None),indent=2)+'\n');raise
 finally:
  try:
   if relay:relay.pcap.close()
   if gateway:gateway.close()
  finally:print(json.dumps(board.close()),flush=True)
if __name__=='__main__':main()
