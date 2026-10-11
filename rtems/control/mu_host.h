/* Exact bounded host transaction; lock and user-copy handled by ioctl wrapper.
 * MU_READ/WRITE and MU_PAUSE are supplied by kernel or simulator. */
static int mu_exchange(unsigned int *words){unsigned int i,token=words[0];
 if((token&0xffff0000u)!=0xc71e0000u)return -EINVAL;
 words[6]=MU_READ(0x28);words[7]=MU_READ(0x34);
 if(!(words[6]&2)||!(words[7]&2)||MU_READ(0x14)||MU_READ(0x1c)||
    (MU_READ(0x24)&2)||(MU_READ(0x30)&2))return -EBUSY;
 MU_WRITE(0x14,token);(void)MU_READ(0x14);
 for(i=0;i<200;i++){
  if(MU_READ(0x28)!=words[6]||MU_READ(0x34)!=words[7])return -EIO;
  words[1]=MU_READ(0x1c);
  if(words[1]==(token^0x5a5a5a5au)){
   words[4]=MU_READ(0x24);words[5]=MU_READ(0x30);return 0;
  }
  MU_PAUSE();
 }
 return -ETIMEDOUT;
}
