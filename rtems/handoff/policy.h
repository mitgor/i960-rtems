/* Evidence bits are target-owned proof, never host claims or idle snapshots. */
#define TRANSFER_REQUIRED 0x7fu
#define TRANSFER_DENIED 1u
#define TRANSFER_BUSY 2u
static unsigned int transfer_check(unsigned int proof,unsigned int busy,unsigned int drift){
 /* Keep explicit stores: the historical i960 compiler miscompiles the
  * combined early return / boolean ternary by clobbering condition codes. */
 volatile unsigned int result=TRANSFER_DENIED;
 if(busy||drift)result=TRANSFER_BUSY;
 else if((proof&TRANSFER_REQUIRED)==TRANSFER_REQUIRED)result=0;
 return result;
}
