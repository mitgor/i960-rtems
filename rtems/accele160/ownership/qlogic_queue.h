/* Profile 16: fixed RAM reads only. Never follow captured pointers or access
 * chip registers. Sequential observations do not prove hardware exclusion. */
static const unsigned int at_qr_addresses[14]={
 0xc0600d28u,0xc0600d2cu,0xc0600d30u,0xc0600d34u,0xc0600d38u,
 0xc0600d3cu,0xc0600d40u,0xc0600d44u,0xc0600d48u,
 0xc0600d4cu,0xc0600d50u,0xc0498280u,0xc0498284u,0xc049828cu
};
static void at_qlogic_queue(volatile unsigned int *r,unsigned int nonce,
 unsigned int seq,unsigned int phase){unsigned int i;
 for(i=352;i<384;i++)r[i]=0;
 r[352]=0x314d5251u;r[353]=1;r[354]=nonce;r[355]=seq;r[356]=phase;
 r[357]=1;
 if(QR_READ(0xc0384e78u)!=0x10161077u||QR_READ(0xc0384ba0u)!=16u||
    QR_READ(0xc0384b8cu)!=0x8bf00000u)return;
 r[358]=QR_READ(0xc03e5bc8u);
 if(r[358]!=0xc0600d00u){r[357]=2;return;}
 for(i=0;i<14;i++){r[360+i]=QR_READ(at_qr_addresses[i]);r[359]=i+1;}
 r[357]=0;
}
