/* Destructive, resident-only adapter. Never called by bounded monitor entry.
 * One private Symbios channel matches byte-checked firmware initialization.
 * Config-address selection is restored; only ID is read, never chip status. */
#define SCSI_STOP_READ16(a) ESHORT(a)
#define SCSI_STOP_READ32(a) EREG(a)
#define SCSI_STOP_WRITE16(a,v) (ESHORT(a)=(v))
#define SCSI_STOP_WRITE32(a,v) (EREG(a)=(v))
#define SCSI_STOP_SNAPSHOT engine_snapshot
#include "scsi_stop.h"
static struct scsi_stop_state scsi_stop;
static unsigned int scsi_target_identity(void){unsigned int saved,id;
 if(EREG(0xc011e22c)!=0xc0110780u)return 0;
 if(EREG(0xc0060000)!=1)return 0;
 if(EREG(0xc01107d8)!=1)return 0; /* table+58 secondary count */
 if(EREG(0xc0083104)!=0x000c1000u)return 0;
 if(ESHORT(0xc0083108)!=2)return 0;
 if(EREG(0xc008302c)!=0x88000000u)return 0;
 if(EREG(0xc0083030)!=0xfff00000u)return 0;
 if(EREG(0xc0083038)!=0x88002000u)return 0;
 if(EREG(0xc008303c)!=0)return 0;
 if(EREG(0xc0083040)!=0x10)return 0;
 if((ESHORT(0x1298)&6)!=6)return 0;
 if(EREG(0x1700))return 0;
 saved=EREG(0x12a8);EREG(0x12a8)=0x10000;id=EREG(0x12b0);
 EREG(0x12a8)=saved;if(EREG(0x12a8)!=saved)return 0;
 if(id!=0x000c1000u||EREG(0x1700))return 0;
 return 1;
}
unsigned int scsi_target_verified(void){unsigned int w[16];
 if(!scsi_stop.verified)return 0;
 engine_snapshot(w);
 if(!scsi_stop_postcheck(w,scsi_stop.before))return 1;
#ifdef I960_DOOM_DMA
 {extern unsigned frame_dma_isolation_snapshot(unsigned*),wad_dma_isolation_snapshot(unsigned*);
  if(wad_dma_isolation_snapshot(w))return !scsi_stop_postcheck(w,scsi_stop.before);
  if(frame_dma_isolation_snapshot(w))return !scsi_stop_postcheck(w,scsi_stop.before);}
#endif
 return 0;
}
