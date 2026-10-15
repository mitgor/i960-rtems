"""STOP drain diagnostics. Raw journal equality is enforced by system replay."""
def validate_drain(records,irq_gap_us):
 assert records
 version=records[0][1]
 assert version in (1,2)
 for w in records:
  assert len(w)==64 and all(isinstance(x,int) and 0<=x<=0xffffffff for x in w)
  assert w[:3]==[0x314e5244,version,4166700] and w[13:]==[0]*51
  assert all(n in (0,1) for n in w[11:13])
  for i in range(2):
   if w[11+i]:
    assert w[5+i]>0
    if version==2:
     # Final masked shutdown may have no following IRQ sample. Independently
     # require the drain's tick progress to track its elapsed counter time.
     assert abs(w[9+i]*41667-w[5+i])<2*41667
     if w[5+i]>2*41667:assert w[9+i]>0
 for a,b in zip(records,records[1:]):
  for i in range(2):
   assert b[11+i]>=a[11+i]
   if a[11+i]:assert all(a[k+i]==b[k+i] for k in (3,5,7,9,11))
 w=records[-1];assert w[11:13]==[1,1]
 if version==1:assert w[9:11]==[0,0], 'masked drain unexpectedly advanced ticks'
 else:assert irq_gap_us<20000, 'interruptible drain failed 20 ms full-session IRQ gate'
 return dict(version=version,interruptible=version==2,worker_elapsed_ms=[x/4166.7 for x in w[5:7]],worker_tick_deltas=w[9:11],completed=w[11:13],irq_max_gap_us=irq_gap_us,acceptance_irq_ceiling_us=20000 if version==2 else None)
