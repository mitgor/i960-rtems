/* Profile 17: only 12 fixed 16-bit chip reads after physical PCI and RAM
 * identity checks. No chip writes, bank switches, acknowledgements or retries.
 * Fixed count cannot bound a stalled bus transaction; faults retain resources. */
static const unsigned int at_qc_offsets[6]={0x0a,0x0c,0x78,0x7a,0x0a,0x0c};
static void at_qlogic_chip(volatile unsigned int *r,unsigned int nonce,
 unsigned int seq,unsigned int phase){unsigned int i;
 for(i=384;i<416;i++)r[i]=0;
 r[384]=0x31504351u;r[385]=1;r[386]=nonce;r[387]=seq;r[388]=phase;
 r[389]=1;
 if(r[325]||r[328]!=5||r[330]!=0x10161077u||
    (r[331]&2u)!=2u||r[334]!=0xfff00000u||
    r[357]||r[359]!=14||r[358]!=0xc0600d00u||r[360]!=0x8bf00000u)return;
 for(i=0;i<12;i++){
  r[392+i]=QC_READ16(0x8bf00000u+at_qc_offsets[i%6]);r[390]=i+1;
 }
 r[389]=0;
}
