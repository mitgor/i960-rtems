/* Secondary-bus destructive stop prototype, Intel 272736-002 table 15-35.
 * Opt-in resident adapter requires the qualified live topology.
 * IO macros permit native tests of the exact transaction sequence.
 * Caller must already own the CPU exclusively, phase-2 bus isolation, and must
 * never resume stock firmware after written becomes nonzero, even on failure. */
#ifndef RESIDENT_SCSI_STOP_H
#define RESIDENT_SCSI_STOP_H
struct scsi_stop_state {unsigned int written,verified,error,polls,before,after,secondary;};
static unsigned int scsi_stop_precheck(const unsigned int*w,unsigned int topology){
 unsigned int i;
 if(topology!=0x31504353u)return 1; /* SCP1: local verified topology, not host input */
 for(i=0;i<6;i++)if(w[i])return 2;
 if(w[6]!=2||w[7]&4||w[8]&0x40)return 3;
 if((w[9]&0x13ffc)!=0x13ffc||w[11])return 4;
 return 0;
}
static unsigned int scsi_stop_postcheck(const unsigned int*w,unsigned int before){
 unsigned int i;
 for(i=0;i<6;i++)if(w[i])return 1;
 if(w[6]!=2||w[7]&6)return 2;
 /* Bit 10 is W1C discard status, never acknowledged by the reset write. */
 if((w[8]&~0x400u)!=((before&~0x400u)|0x40u))return 3;
 if((w[9]&0x13ffc)!=0x13ffc||w[11])return 4;
 return 0;
}
#ifdef SCSI_STOP_READ16
static unsigned int scsi_stop_hold(struct scsi_stop_state*s,unsigned int topology){
 unsigned int w[16],i,stable=0;
 if(s->written||s->verified)return 5;
 SCSI_STOP_SNAPSHOT(w);s->error=scsi_stop_precheck(w,topology);if(s->error)return s->error;
 s->before=w[8];s->written=1; /* mark irreversible BEFORE touching hardware */
 SCSI_STOP_WRITE16(0x103e,(w[8]&~0x400u)|0x40u);
 s->after=SCSI_STOP_READ16(0x103e);
 /* Secondary arbitration state can reset too; retain the deny-all policy. */
 SCSI_STOP_WRITE32(0x104c,SCSI_STOP_READ32(0x104c)|0x13ffcu);
 (void)SCSI_STOP_READ32(0x104c);
 for(i=0;i<4096;i++){
  SCSI_STOP_SNAPSHOT(w);s->polls=i+1;s->after=w[8];s->secondary=w[7];
  if(!scsi_stop_postcheck(w,s->before)){if(++stable==3){s->verified=1;s->error=0;return 0;}}
  else stable=0;
 }
 s->error=6;return 6; /* keep reset asserted; retain everything until reboot */
}
#endif
#endif
