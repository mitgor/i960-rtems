/* Destructive fixed-range experiment. This does NOT grant RAM to any allocator.
 * Caller must have exclusive exception ownership, stopped SCSI and idle DMA.
 * Macros allow tests of the exact target algorithm with aliased/failing memory. */
#ifndef RESIDENT_RAM_PROBE_H
#define RESIDENT_RAM_PROBE_H
#define RAM_PROBE_LO 0xc0200000u
#define RAM_PROBE_WORDS 65536u
struct ram_probe_report {unsigned int passes,checked,error,address,expected,observed;};
static unsigned int ram_probe_pattern(unsigned int index,unsigned int pass){
 unsigned int v=0x9e3779b9u*index;
 return pass==0?index^0xa5a5a5a5u:pass==1?index^0x5a5a5a5au:pass==2?v:~v;
}
static unsigned int ram_probe_run(struct ram_probe_report*r,unsigned int admitted){
 unsigned int pass,i,v; r->passes=r->checked=r->error=r->address=r->expected=r->observed=0;
 if(admitted!=1){r->error=1;return 1;}
 for(pass=0;pass<4;pass++){
  for(i=0;i<RAM_PROBE_WORDS;i++)RP_WRITE(RAM_PROBE_LO+4*i,ram_probe_pattern(i,pass));
  RP_SYNC();
  for(i=0;i<RAM_PROBE_WORDS;i++){
   v=RP_READ(RAM_PROBE_LO+4*i);r->checked++;
   if(v!=ram_probe_pattern(i,pass)){r->error=2;r->address=RAM_PROBE_LO+4*i;r->expected=ram_probe_pattern(i,pass);r->observed=v;return 2;}
  }
  if(!RP_BOUNDARY()){r->error=3;return 3;}
  r->passes++;
 }
 return 0;
}
#endif
