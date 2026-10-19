/* Profile 18: one-shot RISC pause/release qualification, NOT DMA isolation.
 * Prerequisite failures issue no chip writes. After a write, uncertainty stops
 * the transaction with no rollback/retry. The host retains everything for reset.
 * Poll count is bounded, but a stalled bus transaction is not time-bounded. */
#define QP_POLLS 10000u
static unsigned int at_qp_attempted;
static unsigned int at_qp_ready(volatile unsigned int *r){unsigned int i;
 if(r[325]||r[328]!=5||r[330]!=0x10161077u||
    (r[331]&6u)!=6u||r[334]!=0xfff00000u||r[357]||r[359]!=14||
    r[358]!=0xc0600d00u||r[360]!=0x8bf00000u||r[361]||r[362]||
    r[363]!=0xc0600df0u||r[364]!=256u||r[365]!=0xc0604df0u||r[366]!=128u||
    (r[371]&65535u)||r[389]||r[390]!=12u)return 0;
 for(i=0;i<6;i++)if(r[392+i]!=r[398+i])return 0;
 if(r[392]||r[396]||(r[393]&1u)||(r[397]&1u)||r[393]!=r[397])return 0;
 if(r[394]>=256u||r[395]>=128u||r[394]!=(r[369]&65535u)||
    r[395]!=(r[370]&65535u)||r[395]!=(r[370]>>16))return 0;
 return 1;
}
static void at_qlogic_pause(volatile unsigned int *r,unsigned int nonce,
 unsigned int seq,unsigned int phase){unsigned int i,v;
 if(at_qp_attempted){r[419]=seq;r[420]=phase;return;}
 at_qp_attempted=1;
 for(i=416;i<464;i++)r[i]=0;
 r[416]=0x31535051u;r[417]=1;r[418]=nonce;r[419]=seq;r[420]=phase;
 r[421]=1;r[422]=1;r[423]=seq;r[439]=QP_TICKS();
 if(!nonce||!at_qp_ready(r))return;
 r[421]=2;if(seq!=1u||phase)return;
 r[421]=3;
 r[424]=QP_READ16(0x8bf00006u);r[425]=QP_READ16(0x8bf00008u);
 /* HCCR aliases a DMA register if that bank is selected. Never switch banks. */
 if((r[424]&0x300u)||(r[425]&1u))return;
 r[426]=QP_READ16(0x8bf000c0u);
 if(r[426]&0x4e0u)return; /* reset, paused, host interrupt or parity error */
 r[421]=4;r[431]=1;QP_WRITE16(0x8bf000c0u,0x2000u);
 for(i=0;i<QP_POLLS;i++){
  v=QP_READ16(0x8bf000c0u);r[427]=v;r[428]=i+1;
  if(v&0x20u)break;
 }
 if(!(r[427]&0x20u))return;
 if((r[427]&~0x20u)!=r[426]){r[421]=6;return;}
#ifdef QP_PAUSED
 if(!QP_PAUSED(r)){r[421]=6;return;}
#endif
 r[421]=5;r[431]=2;QP_WRITE16(0x8bf000c0u,0x3000u);
 for(i=0;i<QP_POLLS;i++){
  v=QP_READ16(0x8bf000c0u);r[429]=v;r[430]=i+1;
  if(!(v&0x20u))break;
 }
 if(r[429]&0x20u)return;
 r[421]=6;
 r[432]=QP_READ16(0x8bf00006u);r[433]=QP_READ16(0x8bf00008u);
 if((r[432]&0x300u)||(r[433]&1u))return;
 r[434]=QP_READ16(0x8bf000c0u);r[435]=QP_READ16(0x8bf0000au);
 r[436]=QP_READ16(0x8bf0000cu);r[437]=QP_READ16(0x8bf00078u);
 r[438]=QP_READ16(0x8bf0007au);r[440]=QP_TICKS();
 if(r[432]!=r[424]||r[433]!=r[425]||r[429]!=r[426]||r[434]!=r[426]||
    r[435]||r[436]!=r[393]||r[437]!=r[394]||r[438]!=r[395])return;
 r[421]=0;
}
