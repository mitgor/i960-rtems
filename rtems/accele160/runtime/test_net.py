#!/usr/bin/env python3
"""Exercise actual Accele module entry with raw IPv4/IPv6, no host HTTP server."""
import ctypes,ipaddress,struct,sys,json
rpc=sys.argv[1]=='--rpc'
if rpc:
 from client import Client
 client=Client()
 def call(op,data=b'',ms=10):
  if op==0:return b''
  return bytes.fromhex(client.call(7 if op==3 else 5,data)['data'])
else:
 lib=ctypes.CDLL(sys.argv[1]);entry=lib.accele_net_entry
 entry.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint];entry.restype=ctypes.c_uint
 out=ctypes.create_string_buffer(2048)
 def call(op,data=b'',ms=10):
  b=ctypes.create_string_buffer(data);n=entry(op,ms,b,len(data),out,2048)
  assert n<=2048,(op,n)
  return out.raw[:n]
def packets(b):
 result=[]
 while b:
  n=struct.unpack_from('<I',b)[0];assert 0<n<=1500 and len(b)>=4+n
  result.append(b[4:4+n]);b=b[4+n:]
 return result
def checksum(b):
 if len(b)&1:b+=b'\0'
 n=sum(struct.unpack('!%dH'%(len(b)//2),b))
 while n>>16:n=(n&65535)+(n>>16)
 return (~n)&65535
def addresses(v):
 return tuple(ipaddress.ip_address(s).packed for s in (('10.196.0.1','10.196.0.2') if v==4 else ('fd96:196:960::1','fd96:196:960::2')))
def pseudo(v,src,dst,proto,n):return src+dst+(struct.pack('!BBH',0,proto,n) if v==4 else struct.pack('!I3xB',n,proto))
def ip(v,proto,data):
 src,dst=addresses(v)
 if v==4:
  h=struct.pack('!BBHHHBBH4s4s',0x45,0,len(data)+20,1,0,64,proto,0,src,dst)
  h=h[:10]+struct.pack('!H',checksum(h))+h[12:]
 else:h=struct.pack('!IHBB16s16s',0x60000000,len(data),proto,64,src,dst)
 return h+data
def transport(v,proto,data,checkoff):
 src,dst=addresses(v);c=checksum(pseudo(v,src,dst,proto,len(data))+data)
 return ip(v,proto,data[:checkoff]+struct.pack('!H',c or 65535)+data[checkoff+2:])
def split(v,p):
 off=20 if v==4 else 40
 assert p[0]>>4==v
 src,dst=(p[12:16],p[16:20]) if v==4 else (p[8:24],p[24:40])
 proto=p[9] if v==4 else p[6];data=p[off:]
 assert checksum(pseudo(v,src,dst,proto,len(data))+data)==0
 return data
def tcp(v,seq,ack,flags,data=b''):
 return transport(v,6,struct.pack('!HHIIBBHHH',12345,80,seq,ack,5<<4,flags,4800,0,0)+data,16)
call(0,ms=0);results={}
for v in (4,6):
 payload=b'Accele160 raw IP echo'
 udp=transport(v,17,struct.pack('!HHHH',12346,9601,8+len(payload),0)+payload,6)
 reply=packets(call(2,udp));assert len(reply)==1 and split(v,reply[0])[8:]==payload
 syn=packets(call(2,tcp(v,1000,0,2)));assert len(syn)==1
 t=split(v,syn[0]);assert t[13]&0x12==0x12
 ack=struct.unpack_from('!I',t,4)[0]+1
 request=b'GET / HTTP/1.0\r\nHost: accele160\r\n\r\n'
 packets(call(2,tcp(v,1001,ack,16)))
 pending=packets(call(2,tcp(v,1001,ack,24,request)));body=b'';seq=1001+len(request);finished=False
 for _ in range(40):
  for packet in pending:
   t=split(v,packet);n=(t[12]>>4)*4;data=t[n:];server_seq=struct.unpack_from('!I',t,4)[0]
   if data:
    assert server_seq==ack;body+=data;ack+=len(data)
   if t[13]&1:ack+=1;finished=True
  pending=packets(call(2,tcp(v,seq,ack,16),ms=100))
  if finished:break
 assert finished and body.startswith(b'HTTP/1.0 200 OK')
 assert b'AcceleRAID 160' in body and b'Darth Vader' in body and b'192 KiB' in body and b'384 KiB' in body
 assert b'Mylex DAC960' not in body
 results['ipv'+str(v)]=dict(udp_echo=True,http_bytes=len(body),http200=True,card_identity=True,fin=True)
 if not rpc:assert entry(2,0,out,1501,out,2048)==0xffffffff
stats=struct.unpack('<6I',call(3));results['counters']=dict(rx=stats[0],tx=stats[1],drops=stats[2]);print(json.dumps(results,indent=2))
