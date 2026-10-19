/* Profile 15 only. Single known secondary device; no configuration data writes.
 * Q_READ/Q_WRITE keep single-dword volatile accesses explicit and testable.
 * Fixed operation count is NOT a wall-clock bound on a stalled PCI transaction.
 * Owned worker/ISR execution excludes stock firmware config users. A fault parks
 * with resources retained: selector restoration cannot be promised after fault. */
static void at_qlogic_snapshot(volatile unsigned int *r,unsigned int nonce,
 unsigned int seq,unsigned int phase){
 unsigned int i,saved,id;
 static const unsigned int offsets[5]={0,4,8,0x10,0x14};
 for(i=320;i<340;i++)r[i]=0;
 r[320]=0x31494350u;r[321]=1;r[322]=nonce;r[323]=seq;r[324]=phase;
 r[325]=1; /* refused until metadata is verified */
 if(Q_READ(0xc0384e78u)!=0x10161077u||Q_READ(0xc0384ba0u)!=16u||
    Q_READ(0xc0384b8cu)!=0x8bf00000u||Q_READ(0xc0384b90u)!=0xfff00000u)return;
 saved=Q_READ(0x12a8u);r[326]=saved;r[325]=2; /* in progress */
 Q_WRITE(0x12a8u,0x10000u);
 id=Q_READ(0x12b0u);r[330]=id;r[328]=1;
 if(id==0x10161077u){
  for(i=1;i<5;i++){
   Q_WRITE(0x12a8u,0x10000u|offsets[i]);
   r[330+i]=Q_READ(0x12b0u);r[328]=i+1;
  }
 }
 Q_WRITE(0x12a8u,saved);r[327]=Q_READ(0x12a8u);
 r[325]=(r[327]!=saved)?4u:((id!=0x10161077u)?3u:0u);
}
