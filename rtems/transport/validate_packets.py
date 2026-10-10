#!/usr/bin/env python3
"""Independently verify IPv4/IPv6/ICMP/UDP/TCP checksums and reassemble captured streams."""
import argparse,collections,hashlib,json,socket,struct
from pathlib import Path

def checksum(b):
 if len(b)%2:b+=b'\0'
 n=sum(struct.unpack('!%dH'%(len(b)//2),b))
 while n>>16:n=(n&65535)+(n>>16)
 return (~n)&65535

def validate(path):
 b=path.read_bytes();assert len(b)>=24 and struct.unpack_from('<I',b)[0]==0xa1b2c3d4
 assert struct.unpack_from('<I',b,20)[0]==101
 offset=24;counts=collections.Counter();streams=collections.defaultdict(list);dns=[];retransmissions=0;opened=set();resets=set()
 while offset<len(b):
  sec,usec,n,original=struct.unpack_from('<4I',b,offset);offset+=16;p=b[offset:offset+n];offset+=n
  assert len(p)==n==original and n>=20
  version=p[0]>>4
  if version==6:
   assert len(p)>=40 and struct.unpack_from('!H',p,4)[0]+40==len(p)
   src=socket.inet_ntop(socket.AF_INET6,p[8:24]);dst=socket.inet_ntop(socket.AF_INET6,p[24:40]);proto=p[6];ihl=40
   # Host MLD traffic may include the IPv6 hop-by-hop Router Alert option.
   while proto in (0,43,60):
    assert ihl+2<=len(p);next_proto=p[ihl];extension=(p[ihl+1]+1)*8;assert ihl+extension<=len(p);ihl+=extension;proto=next_proto
   assert proto!=44,'fragmented captures require a reassembly validator'
   data=p[ihl:];pseudo=p[8:40]+struct.pack('!I3xB',len(data),proto);counts['ipv6_'+str(proto)]+=1
   if proto==58:assert checksum(pseudo+data)==0
  else:
   assert version==4
   ihl=(p[0]&15)*4;assert 20<=ihl<=len(p)
   length=struct.unpack_from('!H',p,2)[0];assert length==len(p) and checksum(p[:ihl])==0
   fragment=struct.unpack_from('!H',p,6)[0];assert fragment&0x3fff==0
   src=socket.inet_ntoa(p[12:16]);dst=socket.inet_ntoa(p[16:20]);proto=p[9];data=p[ihl:];counts[str(proto)]+=1
   pseudo=p[12:20]+struct.pack('!BBH',0,proto,len(data))
   if proto==1:assert checksum(data)==0
  if proto in (6,17):
   assert len(data)>=(20 if proto==6 else 8)
   if proto==17 and version==6:assert data[6:8]!=b'\0\0','IPv6 UDP checksum required'
   if proto==6 or version==6 or data[6:8]!=b'\0\0':assert checksum(pseudo+data)==0,(src,dst,proto)
   sport,dport=struct.unpack_from('!HH',data)
   if proto==17:
    assert struct.unpack_from('!H',data,4)[0]==len(data)
    if sport==53 or dport==53:dns.append(dict(src=src,dst=dst,source_port=sport,dest_port=dport,payload_hex=data[8:].hex()))
   else:
    hlen=(data[12]>>4)*4;assert 20<=hlen<=len(data)
    key=(src,sport,dst,dport)
    if data[13]&2 and not data[13]&16:opened.add(key)
    if data[13]&4:resets.add(key)
    seq=struct.unpack_from('!I',data,4)[0];body=data[hlen:]
    if body:streams[(src,sport,dst,dport)].append((seq,body))
 result=[]
 for key,segments in streams.items():
  segments.sort(key=lambda x:x[0]);start=segments[0][0];payload=bytearray()
  for seq,data in segments:
   pos=seq-start
   assert pos<=len(payload),'gap in TCP stream'
   overlap=min(len(data),len(payload)-pos)
   if overlap:
    assert payload[pos:pos+overlap]==data[:overlap],'conflicting retransmission';retransmissions+=1
   payload+=data[overlap:]
  result.append(dict(src=key[0],sport=key[1],dst=key[2],dport=key[3],bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),prefix=bytes(payload[:100]).decode('ascii',errors='replace')))
 echoes=[r for r in result if r['sport']==9600 or r['dport']==9600]
 stale=[]
 for flow in echoes:
  key=(flow['src'],flow['sport'],flow['dst'],flow['dport']);reverse_key=(flow['dst'],flow['dport'],flow['src'],flow['sport'])
  if key not in opened and reverse_key not in opened:
   assert reverse_key in resets,'uncaptured echo connection without a reset response'
   stale.append(dict(src=flow['src'],sport=flow['sport'],dst=flow['dst'],dport=flow['dport'],bytes=flow['bytes'],reset=True));continue
  reverse=[r for r in echoes if (r['src'],r['sport'],r['dst'],r['dport'])==(flow['dst'],flow['dport'],flow['src'],flow['sport'])]
  assert len(reverse)==1,'missing reverse echo stream'
  assert flow['bytes']>0 and (flow['sha256'],flow['bytes'])==(reverse[0]['sha256'],reverse[0]['bytes']),'echo stream mismatch'
 return dict(valid=True,packets=sum(counts.values()),protocols=dict(counts),streams=result,dns=dns,retransmitted_segments=retransmissions,preexisting_echo_streams_reset=stale)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pcap',type=Path);a=p.parse_args();print(json.dumps(validate(a.pcap),indent=2))
