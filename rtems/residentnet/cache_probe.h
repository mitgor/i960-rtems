/* Reads only firmware-evidenced addresses. Distinguish bus-data echo from a
 * register value; this is never an idle/completion or RAM-ownership predicate. */
static volatile unsigned int probe_seed __attribute__((aligned(16)));
static unsigned int cache_probe_read(unsigned int address,unsigned int seed,unsigned int half){
 unsigned int result,primed;probe_seed=seed;
 if(half)__asm__ volatile("ld (%2),%1;ldos (%3),%0":"=&r"(result),"=&r"(primed):"r"(&probe_seed),"r"(address):"memory");
 else __asm__ volatile("ld (%2),%1;ld (%3),%0":"=&r"(result),"=&r"(primed):"r"(&probe_seed),"r"(address):"memory");
 return result;
}
static void cache_probe(unsigned int*w){unsigned int i,cache_status,scratch;const unsigned int addresses[3]={0x40800000,0x40800008,0x4080000a};
 __asm__ volatile("dcctl 4,0,%0":"=r"(cache_status)::"memory");
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 w[0]=0x31484343;
 for(i=0;i<3;i++){w[1+i*2]=cache_probe_read(addresses[i],0xa5a5a5a5,i!=0);w[2+i*2]=cache_probe_read(addresses[i],0x5a5a5a5a,i!=0);}
 w[7]=*(volatile unsigned int*)0x1700; /* NMISR, read only */
 w[8]=*(volatile unsigned int*)0x1288; /* ATU direct-address decode control */
 w[9]=cache_status; /* observed before temporary D-cache disable */
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 if(cache_status&1)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
}

/* Fixed read-only decode pages. No host-selected address or register writes. */
static void cache_decode_probe(unsigned int*w,unsigned int page){
 static const unsigned int addresses[3][8]={
  {0xff008600,0xff008608,0xff008610,0xff008618,0xff008630,0xff008638,0xff0086fc,0x1288},
  {0x1500,0x1504,0x1508,0x150c,0x1510,0x1514,0x1518,0x1700},
  {0x151c,0x1520,0x1524,0x1528,0x152c,0x1530,0x40800000,0x40800008}};
 unsigned int i,status,scratch;
 if(!page||page>31){cache_probe(w);return;}
 __asm__ volatile("dcctl 4,0,%0":"=r"(status)::"memory");
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 w[0]=0x32484343;w[1]=page;
 if(page>=8){unsigned int table=*(volatile unsigned int*)0xc011e22c,base=0;
  static const unsigned int globals[8]={0xc009c3f4,0xc009c3f8,0xc0112a70,0xc00bee54,0xc00bee50,0xc00a8750,0xc00a8754,0xc00aed64};
  if(page<=10&&table>=0xc0010000u&&table<=0xc013fe00u&&!(table&3))base=table+(page==8?0x100:page==9?0x120:0);
  if(page==11)base=0xc00600e0;
  if(page==12)base=0xc00a8700;
  if(page==15)base=0xc0060110; /* debug counters, including four named SCSI queues */
  if(page==14){base=*(volatile unsigned int*)0xc00bee54;if(base<0xc0010000u||base>0xc013ffe0u||(base&3))base=0;}
  for(i=0;i<8;i++)w[i+2]=page==13?*(volatile unsigned int*)globals[i]:base?*(volatile unsigned int*)(base+i*4):0xffffffffu;
 }

 if(page==16){unsigned int table=*(volatile unsigned int*)0xc011e22c;
  w[2]=*(volatile unsigned int*)0xc0060000;w[3]=table;
  for(i=0;i<3;i++)w[4+i]=table==0xc0110780u?*(volatile unsigned int*)(table+(i==0?0x58:i==1?0x4c:0x50)):0xffffffffu;
  w[7]=*(volatile unsigned int*)0x1018;w[8]=*(volatile unsigned int*)0x12a8;w[9]=*(volatile unsigned int*)0x1288;
 }
 if(page>=17&&page<=28){unsigned int channel=(page-17)/2,base=0xc0083000u+channel*0x170;
  unsigned int count=*(volatile unsigned int*)0xc0060000;
  for(i=0;i<8;i++)w[i+2]=channel<count&&count<=6?*(volatile unsigned int*)(base+((page-17)&1?0xf0:0x2c)+i*4):0xffffffffu;
 }
 if(page==29){unsigned int saved=*(volatile unsigned int*)0x12a8;
  static const unsigned int offsets[5]={0,4,8,0x14,0x18};
  for(i=0;i<8;i++)w[i+2]=0xffffffffu;
  /* Corroborate one identified private device; no enumeration or config writes. */
  if(*(volatile unsigned int*)0xc0060000==1&&*(volatile unsigned int*)0xc0083104==0x000c1000u&&*(volatile unsigned int*)0xc0083040==0x10&&(*(volatile unsigned short*)0x1298&6)==6){
   for(i=0;i<5;i++){*(volatile unsigned int*)0x12a8=0x10000u|offsets[i];w[i+2]=*(volatile unsigned int*)0x12b0;}
   *(volatile unsigned int*)0x12a8=saved;w[7]=saved;w[8]=*(volatile unsigned int*)0x12a8;w[9]=*(volatile unsigned short*)0x1298;
  }
 }
 if(page>=30){unsigned int prcb=*(volatile unsigned int*)0xff008700,ft=0;
  if(prcb>=0xc0000000u&&prcb<=0xc013ffc0u&&!(prcb&3))ft=*(volatile unsigned int*)prcb;
  if(page==30){w[2]=cache_probe_read(0,0xa5a5a5a5,0);w[3]=prcb;w[4]=ft;w[5]=*(volatile unsigned int*)0xff008704;w[6]=*(volatile unsigned int*)0xff008708;w[7]=*(volatile unsigned int*)0x1700;w[8]=*(volatile unsigned int*)0xff008500;w[9]=*(volatile unsigned int*)0xff008504;}
  else for(i=0;i<8;i++)w[i+2]=ft==0xc0000800u?*(volatile unsigned int*)(ft+4*i):0xffffffffu;
 }
 if(page<=3)for(i=0;i<8;i++)w[i+2]=cache_probe_read(addresses[page-1][i],0x5a5a5a5a,0);
 else if(page==4) {
  w[2]=cache_probe_read((unsigned int)&probe_seed,0xa5a5a5a5,0);
  w[3]=cache_probe_read((unsigned int)&probe_seed,0x5a5a5a5a,0);
  w[4]=cache_probe_read((unsigned int)&probe_seed,0xa5a5a5a5,1);
  w[5]=cache_probe_read((unsigned int)&probe_seed,0x5a5a5a5a,1);
  w[6]=cache_probe_read(0x1288,0xa5a5a5a5,0);
  w[7]=cache_probe_read(0x1288,0x5a5a5a5a,0);w[8]=status;w[9]=*(volatile unsigned int*)0x1700;
 }
 if(page==5){
  w[2]=*(volatile unsigned int*)0xc011e22c;w[3]=*(volatile unsigned int*)0xc011e230;
  for(i=0;i<6;i++)w[i+4]=0;
 }
 if(page==7){unsigned int table=*(volatile unsigned int*)0xc011e22c;
  const unsigned int offsets[6]={0xc0,0x168,0x164,0x1b4,0x14c,0x154};
  w[2]=*(volatile unsigned char*)0xe0400000;w[6]=*(volatile unsigned int*)0xc00a8718;
  for(i=0;i<6;i++)w[i<3?i+3:i+4]=0xffffffffu;
  if(table>=0xc0010000u&&table<=0xc013fe00u&&!(table&3))
   for(i=0;i<6;i++)w[i<3?i+3:i+4]=*(volatile unsigned int*)(table+offsets[i]);
 }
 if(page==6){unsigned int table=*(volatile unsigned int*)0xc011e22c;
  /* Firmware-data pointers may be read only inside the established low RAM map. */
  for(i=0;i<8;i++)w[i+2]=0xffffffffu;
  if(table>=0xc0010000u&&table<=0xc013fe00u&&!(table&3))
   for(i=0;i<8;i++)w[i+2]=*(volatile unsigned int*)(table+0x170+i*4);
 }
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 if(status&1)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
}
