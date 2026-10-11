"""Deliberately withhold TX consumption to exercise bounded queue pressure."""
import errno,json,socket,struct,time

def checksum(b):
 if len(b)&1:b+=b'\0'
 n=sum(struct.unpack('!%dH'%(len(b)//2),b))
 while n>>16:n=(n&65535)+(n>>16)
 return (~n)&65535

def datagram(index):
 data=struct.pack('<I',index)+bytes([index])*60
 src=socket.inet_aton('10.196.0.1');dst=socket.inet_aton('10.196.0.2')
 udp=struct.pack('!4H',44000,9601,8+len(data),0)+data
 check=checksum(src+dst+struct.pack('!BBH',0,17,len(udp))+udp) or 65535
 udp=udp[:6]+struct.pack('!H',check)+udp[8:]
 ip=struct.pack('!BBHHHBBH4s4s',0x45,0,20+len(udp),index,0,64,17,0,src,dst)
 return ip[:10]+struct.pack('!H',checksum(ip))+ip[12:]+udp

def burst(packet,snapshot,out):
 busy=0
 capacity={0x32544e52:64,0x33544e52:72,0x34544e52:68,0x35544e52:128}[snapshot()[57]]
 submitted=max(96,capacity+32) if capacity>72 else 96
 for i in range(submitted):
  frame=datagram(i);deadline=time.monotonic()+5
  while True:
   try:packet(1,frame);break
   except OSError as exc:
    if exc.errno!=errno.EAGAIN:raise
    busy+=1
    if time.monotonic()>=deadline:raise TimeoutError('RX busy did not clear')
 time.sleep(.2);full=snapshot();capacity={0x32544e52:64,0x33544e52:72,0x34544e52:68,0x35544e52:128}[full[57]];assert full[59]==capacity and full[58]>0
 seen=[];other=[];empty=0;deadline=time.monotonic()+15
 while time.monotonic()<deadline and empty<20:
  blob=packet(2);offset=0
  if not blob:empty+=1;time.sleep(.01);continue
  empty=0
  while offset<len(blob):
   n=struct.unpack_from('<I',blob,offset)[0];offset+=4;frame=blob[offset:offset+n];offset+=n;assert len(frame)==n
   if frame[0]>>4==4 and frame[9]==17 and struct.unpack_from('!2H',frame,20)==(9601,44000):
    index=struct.unpack_from('<I',frame,28)[0];assert 0<=index<submitted and frame[28:]==datagram(index)[28:] and index not in seen;seen.append(index)
   else:other.append(frame.hex())
  assert offset==len(blob)
 assert empty==20 and capacity-4<=len(seen)<submitted
 result=dict(submitted=submitted,echoed=len(seen),indices=seen,busy_retries=busy,drops=full[58],queue_highwater=full[59],other_frames=other)
 (out/'burst-results.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
