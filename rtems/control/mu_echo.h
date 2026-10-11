/* Single tagged echo. Shared by target and native tests through MU_READ/WRITE.
 * Only message-1 data and its W1C status bit are ever written. */
#ifndef MU_READ
#define MU_READ(off) (*(volatile unsigned int*)(0x1300u+(off)))
#define MU_WRITE(off,value) (*(volatile unsigned int*)(0x1300u+(off))=(value))
#endif
static unsigned int mu_owned,mu_enabled,mu_age,mu_count,mu_inmask,mu_outmask;
static unsigned int mu_start(void){
 if(mu_owned)return 1;
 mu_inmask=MU_READ(0x28);mu_outmask=MU_READ(0x34);
 if(!(mu_inmask&2)||!(mu_outmask&2)||MU_READ(0x14)||MU_READ(0x1c)||
    (MU_READ(0x24)&2)||(MU_READ(0x30)&2))return 2;
 mu_owned=mu_enabled=1;mu_age=mu_count=0;return 0;
}
static void mu_poll(void){unsigned int token;
 if(!mu_enabled)return;
 if(++mu_age>200||MU_READ(0x28)!=mu_inmask||MU_READ(0x34)!=mu_outmask){mu_enabled=0;return;}
 token=MU_READ(0x14);
 if((token&0xffff0000u)!=0xc71e0000u||mu_count)return;
 MU_WRITE(0x1c,token^0x5a5a5a5au);(void)MU_READ(0x1c);
 MU_WRITE(0x24,2);(void)MU_READ(0x24);mu_count=1;mu_enabled=0;
}
static unsigned int mu_finish(void){
 mu_enabled=0;if(!mu_owned)return 0;
 if(MU_READ(0x28)!=mu_inmask||MU_READ(0x34)!=mu_outmask)return 1;
 MU_WRITE(0x14,0);(void)MU_READ(0x14);
 MU_WRITE(0x1c,0);(void)MU_READ(0x1c);
 MU_WRITE(0x24,2); /* OISR is read-only locally; host clears it after STOP. */
 if(MU_READ(0x14)||MU_READ(0x1c)||(MU_READ(0x24)&2) )return 2;
 mu_owned=0;return 0;
}
