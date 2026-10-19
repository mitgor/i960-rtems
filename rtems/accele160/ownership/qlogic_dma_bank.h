/* Profile 19. Called once ONLY after confirmed RISC pause by qlogic_pause.h.
 * Physical offsets use ISP1080 DMA window +0x60, not the ISP1040 layout.
 * No FIFO data, DMA control, count, address, or SXP register accesses.
 * Restore CONF1 unconditionally (including saved zero), verify before HCCR.
 * Failed selection/restoration/paused-state verification forbids release. */
static unsigned int at_qlogic_dma_bank(volatile unsigned int *r){
 static const unsigned int offsets[6]={0x80,0x84,0x86,0xc0,0xc4,0xc6};
 unsigned int i,saved=r[424];
 for(i=464;i<512;i++)r[i]=0;
 r[464]=0x31424451u;r[465]=1;r[466]=r[418];r[467]=r[423];
 r[468]=1;r[469]=saved;r[470]=saved|0x300u;
 r[474]=1;QP_WRITE16(0x8bf00006u,r[470]);
 r[471]=QP_READ16(0x8bf00006u);
 if(r[471]==r[470]){
  for(i=0;i<12;i++)r[480+i]=QP_READ16(0x8bf00000u+offsets[i%6]);
  r[475]=12;
 }
 r[474]=2;QP_WRITE16(0x8bf00006u,saved);
 r[472]=QP_READ16(0x8bf00006u);
 r[468]=2;if(r[472]!=saved)return 0; /* HCCR still potentially aliases DMA. */
 r[473]=QP_READ16(0x8bf000c0u);
 r[468]=3;if(r[473]!=r[427])return 0;
 r[468]=4;if(r[471]!=r[470]||r[475]!=12)return 0;
 r[468]=0;return 1;
}
