"""Independent counters and clock-domain checks for shared heap telemetry."""
def validate_diagnostics(records,final):
 assert len(records)>=2
 for w in records:
  assert len(w)==64 and all(isinstance(x,int) and 0<=x<=0xffffffff for x in w) and w[0]==0x314c5348 and w[1] in (1,2,3,4) and w[2]==4166700
  if w[1]<4:assert w[3:5]==[0xffffffff,1]
  else:assert w[3]<=w[5] and w[4]<=w[5]
  assert w[1]==records[0][1] and w[11]==41667 and w[54]==0 and w[55]==w[63]==1
  assert w[5]>1 and 0<w[10]<=w[6] and w[7]<=w[11]
  assert w[44]>=w[45] and w[44]-w[45]==w[49]<=8 and w[51]<=w[50]<=2*w[49]
  assert w[60]>=w[61] and (w[60]==w[61])==(w[62]==0)
  for op in range(8):
   count,maximum,lo,hi=w[12+op*4:16+op*4]
   assert count and maximum and maximum<=((hi<<32)|lo)<=count*maximum
 for a,b in zip(records,records[1:]):
  for i in (5,6,7,44,45,46,47,48,52,53,56,60,61):assert b[i]>=a[i]
  assert ((b[9]<<32)|b[8])>=((a[9]<<32)|a[8])
  if b[1]>=4:assert b[3]>=a[3] and b[4]>=a[4]
  if b[1]>=2:assert all(b[i]>=a[i] for i in (57,58))
  for op in range(8):
   x=a[12+op*4:16+op*4];y=b[12+op*4:16+op*4]
   assert y[0]>=x[0] and y[1]>=x[1] and ((y[3]<<32)|y[2])>=((x[3]<<32)|x[2])
 w=records[-1];assert w[5]==final[5] and w[44]==w[45]>2 and w[49:52]==[0,0,0]
 assert w[52]>10 and w[53]>=w[52] and w[47]>=w[52] and w[48]>w[52]
 assert w[59]==3 and w[60]==w[61]==final[50] and w[62]==0
 elapsed=(w[9]<<32)|w[8];assert 40000<elapsed/(w[5]-1)<50000
 ops={}
 for op,name in enumerate(('check','malloc','calloc','realloc','free','share','cancel','empty')):
  n,maximum,lo,hi=w[12+4*op:16+4*op];ops[name]=dict(samples=n,max_counter_ticks=maximum,max_us=maximum/4.1667,mean_us=((hi<<32)|lo)/n/4.1667)
 return dict(network_irq_spanning_calls=w[3:5] if w[1]>=4 else None,large_workload_allocation_refusals=w[56] if w[1]>=3 else None,unlocked_copy_preemptions=w[57:59] if w[1]>=2 else None,counter_hz_nominal=4166700,irq_samples=w[5],irq_max_gap_us=w[6]/4.1667,irq_max_entry_phase_us=w[7]/4.1667,irq_mean_period_us=elapsed/(w[5]-1)/4.1667,operations=ops,shared_created=w[44],shared_retired=w[45],completed_cycles=w[52],deferred_acknowledgements=w[47],rejected_operations=w[48],retained_content_checks=w[53])
