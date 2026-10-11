import unittest
from host import Native,request,decode
class Tests(unittest.TestCase):
 def test_bounded_equivalence(self):
  a,b=Native(),Native();a.step(request(op=0,columns=0));b.step(request(op=0,columns=0))
  for i in range(100):
   keys=i%16
   full=a.step(request(keys=keys))
   for part in range(8):partial=b.step(request(columns=10,keys=keys))
   self.assertEqual(full,partial)
   self.assertLessEqual(decode(full)['dda_steps'],80*32)
 def test_cardinal_geometry(self):
  a=Native();a.step(request(op=0,columns=0));data=a.step(request());d=decode(data)
  # Center rays from (2.5,2.5), east, hit border x=11, perpendicular distance 8.5.
  # Wall projection floor(60/8.5)=7, top floor((60-7)/2)=26.
  for x in (39,40):
   col=[data[64+y*80+x] for y in range(60)]
   self.assertEqual(col[:26],[0]*26);self.assertEqual(col[26:33],[2]*7);self.assertEqual(col[33:],[1]*27)
  self.assertEqual(d['frame_id'],1)
 def test_snapshot_and_collision(self):
  a=Native();a.step(request(op=0,columns=0))
  for i in range(200):data=a.step(request(keys=1))
  self.assertLessEqual(decode(data)['x'],11*1024-128)
  snapshot=a.step(request(op=2,columns=0));self.assertEqual(snapshot,data)
 def test_geometry_against_slab_intersections(self):
  import math
  grid=['111111111111','100000000001','100000000001','100022000001','100020000001','100020000001','100000003001','100000003001','100440000001','100000000001','100000000001','111111111111']
  a=Native();a.step(request(op=0,columns=0))
  for turn in range(64):
   data=a.step(request(keys=8));state=decode(data);angle=state['angle']
   # Independent geometric ray/slab intersection against every occupied square.
   dx=round(math.cos(2*math.pi*angle/256)*1024);dy=round(math.sin(2*math.pi*angle/256)*1024)
   for col in range(0,80,7):
    camera=((col*2+1)*1024//80)-1024
    rx=(dx-int(dy*camera*169/262144))/1024;ry=(dy+int(dx*camera*169/262144))/1024
    nearest=1000.0
    for y,row in enumerate(grid):
     for x,cell in enumerate(row):
      if cell=='0':continue
      low,high=-1e30,1e30
      for origin,direction,edge in [(2.5,rx,x),(2.5,ry,y)]:
       if not direction:
        if not edge<=origin<=edge+1:high=-1e30
       else:
        lo,hi=sorted(((edge-origin)/direction,(edge+1-origin)/direction));low=max(low,lo);high=min(high,hi)
      if 0<=low<=high:nearest=min(nearest,low)
    expected=min(240,int(60/nearest));observed=sum(data[64+y*80+col]>=2 for y in range(60))
    self.assertLessEqual(abs(observed-min(60,expected)),1)
 def test_http_controls(self):
  import http.client,json,threading
  from server import FailClosedServer,Game,handler
  server=FailClosedServer(('127.0.0.1',0),handler(Game(Native(),'native test')))
  thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   client=http.client.HTTPConnection(*server.server_address,timeout=2)
   for keys,code in [(0,200),(8,200),(16,400),(-1,400)]:
    client.request('POST','/step',json.dumps(dict(keys=keys)),{'Content-Type':'application/json'})
    reply=client.getresponse();self.assertEqual(reply.status,code);reply.read()
   client.close()
  finally:server.shutdown();server.server_close();thread.join()
 def test_repeat_benchmarks(self):
  a,b=Native(),Native()
  for k in range(9):
   req=request(op=3,columns=0,pixels=0,kind=k,reps=64)
   self.assertEqual(a.step(req),b.step(req))
if __name__=='__main__':unittest.main()
