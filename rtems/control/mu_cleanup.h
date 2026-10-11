/* Host-only final ack, AFTER validated target STOP and message restoration.
 * The owned marker prevents clearing a pre-existing, unowned pending bit. */
static int mu_cleanup(unsigned int owned,unsigned int used){
 if(!owned)return used?-ENODATA:0;
 if(MU_READ(0x14)||MU_READ(0x1c)||(MU_READ(0x24)&2)||
    MU_READ(0x28)!=0x1fbu||MU_READ(0x34)!=0xffu)return -ENODATA;
 MU_WRITE(0x30,2);
 return (MU_READ(0x30)&2)?-ENODATA:0;
}
