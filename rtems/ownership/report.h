/* Decoded 64-word report. Pinned target owns the meaning of private states. */
static int ownership_report_valid(const unsigned int*w,unsigned int seq,unsigned int op){unsigned int i;
 if(w[0]!=0x314e574f||w[1]!=1||w[2]!=seq||w[3]!=op||op>12||w[5]>1||!w[6]||w[7]>4||w[10]>1||w[17]!=seq)return 0;
 if(w[4]>5&&!(op==7&&w[4]==23))return 0;
 if(!w[18]||!w[19]||!w[20]||w[18]==w[19]||w[18]==w[20]||w[19]==w[20]||w[28]||w[35]||w[36]||w[37]||(w[40]&0x1f0000)!=0x1f0000||w[45]!=5||w[46])return 0;
 if(w[29]<w[30]||w[29]-w[30]>1||w[34]!=w[6])return 0;
 if(w[7]==1||w[7]==2||w[7]==4){if(w[21]!=w[18]||w[22]!=1||w[27]!=1)return 0;}
 else if(w[21]||w[22]||w[27]||w[8]!=w[9]||w[10])return 0;
 if(w[29]!=w[30]&&!(w[24]&0x400))return 0;
 if(w[7]==4){if((w[48]&3)!=3||!w[38]||!w[39])return 0;}
 if(w[5]){
  if(op!=11||w[4]||w[10]||w[48]!=7||(w[7]!=0&&w[7]!=3&&w[7]!=4))return 0;
  for(i=23;i<26;i++)if(!(w[i]&2))return 0;
 }
 for(i=49;i<64;i++)if(w[i])return 0;
 return 1;
}
