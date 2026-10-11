/* Caller owns the session lock and supplies a fresh nonzero transport generation.
 * words[0..15] request, [16..31] response, [32] generation, [33] final halt flag.
 * The ioctl wrapper supplies firmware sequence in [34..35]. */
static int mu_fragment(unsigned int token,unsigned int expected,unsigned int mask,unsigned int *reply){unsigned int i;
 MU_WRITE(0x14,token);(void)MU_READ(0x14);
 for(i=0;i<100;i++){
  if(MU_READ(0x28)!=0x1fb||MU_READ(0x34)!=0xff)return -EIO;
  *reply=MU_READ(0x1c);if((*reply&mask)==expected)return 0;
  MU_PAUSE();
 }
 return -ETIMEDOUT;
}
static int mu_exchange(unsigned int *words){unsigned int i,t,r;int rc;
 if(words[33])return mu_fragment(0xd0000000u,0x2f000000u,0xffffffffu,&words[16]);
 if(!words[32]||words[32]>0xffffff)return -EINVAL;
 t=0xc0000000u|words[32];rc=mu_fragment(t,t^0xff000000u,0xffffffffu,&r);if(rc)return rc;
 for(i=0;i<32;i++){
  t=0xa0000000u|(i<<16)|((words[i/2]>>((i%2)*16))&65535);
  rc=mu_fragment(t,t^0xff000000u,0xffffffffu,&r);if(rc)return rc;
 }
 for(i=0;i<16;i++)words[16+i]=0;
 for(i=0;i<32;i++){
  t=0xb0000000u|(i<<16);
  rc=mu_fragment(t,0x4f000000u|(i<<16),0xffff0000u,&r);if(rc)return rc;
  words[16+i/2]|=(r&65535)<<((i%2)*16);
 }
 return 0;
}
