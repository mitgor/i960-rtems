/* This image can use only the qualified board and existing staging allocation.
 * Identity is admission evidence, never a grant to reclaim cache/SCSI memory. */
static unsigned int resident_board_admit(const unsigned int*w){
 if(w[0]!=6)return 1;
 if(w[1]!=0xc0110780u)return 2;
 if(w[2]!=0xc000d540u)return 3;
 if(w[3]!=0xc004fc40u)return 4;
 if(w[4]!=0x01000000u)return 5;
 if(w[5]!=0xc0f2c000u)return 6;
 if(w[6]!=0x80000u)return 7;
 return 0;
}
