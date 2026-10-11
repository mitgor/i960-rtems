/* Same pinned instance across callbacks. Quiescence is not terminal disposal. */
static int pirq_valid(const unsigned int*w,unsigned int seq,unsigned int op){unsigned int i,j,q=w[33]==4;
 if(w[0]!=0x31515250||w[1]!=1||w[2]>5||w[3]!=op||op>6||w[4]!=seq||!w[5]||w[6]<1||w[6]>3||w[7]>1||w[31]!=seq||w[319]!=seq)return 0;
 if(w[17]||w[18]!=q||w[19]||w[20]||w[21]||w[22]||w[23]!=0x10c7||w[24]!=0x80000||w[25]!=w[26]||w[27]||w[28]||w[29]||(w[30]&0x2000))return 0;
 if(w[32]!=w[5]||w[33]!=(q?4:3)||w[36]>1||w[37]!=w[5]||w[38]!=w[5]||w[39]!=w[293]||w[41]!=w[293]||w[42]||w[49]!=7||w[91]!=6||w[292]!=15)return 0;
 if(!w[288]||!w[289]||!w[290]||w[290]!=w[291]||w[318]!=0x514f4b31||w[294]<w[5]||w[294]!=w[5]+w[295])return 0;
 for(i=0;i<4;i++){if(!w[60+i]||!w[72+i]||!w[68+i])return 0;for(j=i+1;j<4;j++)if(w[60+i]==w[60+j]||w[72+i]==w[72+j])return 0;}
 if(w[68]!=w[5]||w[69]!=w[5]||w[70]!=w[5]||w[71]!=w[294])return 0;
 if(q){
  if(w[6]!=2&&w[6]!=3)return 0;
  if(w[50]||w[51]!=1||w[52]||w[53]!=1||w[54]!=2||w[55]||w[56]!=2||w[57]!=0x402||w[58]!=0x402||w[59]!=2)return 0;
  if(w[64]!=1||w[65]!=1||w[66]||w[67]||w[76]!=w[60]||w[77]!=w[61]||w[78]!=1||w[79]!=1||w[46]||w[47]||w[293]+1!=w[5])return 0;
  for(i=0;i<4;i++)if(!w[80+i]||w[80+i]!=w[84+i])return 0;
 }else{
  if(w[6]!=1&&w[6]!=3)return 0;
  if(w[50]!=4||w[51]!=4||w[36]||w[34]!=w[35]||w[46]!=1||w[47]!=1||!w[48]||w[293]!=w[5])return 0;
  for(i=0;i<4;i++)if(w[52+i]||w[56+i]!=2||w[64+i])return 0;
  for(i=76;i<80;i++)if(w[i])return 0;
  if(w[34]!=(0x22000000u|w[5])||w[43]!=(0x44000000u|w[5])||w[45]!=(0x33000000u|w[5]))return 0;
 }
 if(w[280]!=23||w[281]!=23||w[282]!=4||w[283]!=5||w[284]!=1||w[285]!=1)return 0;
 for(i=0;i<2;i++){const unsigned int*s=w+96+i*82,*r=s+12;unsigned int live=!i&&q;
  if(!s[0]||s[2]-s[1]!=8192||s[3]<s[1]+16||s[3]>s[2]-64||(s[3]&15)||s[6]!=0xf2||s[7]!=live||s[8]!=s[9]+live||s[8]<2||s[11]<s[10]+192||s[11]>=s[10]+8128)return 0;
  for(j=0;j<15;j++)if(r[j]!=0x19600000u+i*0x10000000u+j)return 0;
  if(r[68]||!r[69]||r[69]>1000000)return 0;
  if(!live){for(j=0;j<16;j++)if(r[j]!=r[j+16])return 0;for(j=0;j<16;j++)if(j!=2&&j!=3&&j!=5&&r[32+j]!=r[48+j])return 0;if(r[64]!=r[65]||r[66]!=r[67])return 0;}
 }
 if(w[96]==w[178]||w[106]==w[188])return 0;
 if(op>=1&&op<=3){const unsigned int*c=w+260;
  if(w[2]||w[11]<=w[9]||w[12]<w[11]||w[16]<w[12]||w[8]!=w[16]||w[90]!=1000)return 0;
  if(op!=3&&w[317]){if(c[1]<w[9]+16||c[2]!=c[1]+12||c[3]!=c[2]+12||c[4]<c[3]||c[5]!=2||c[6]!=1||c[7]!=1||c[8]||c[9]!=c[10]||c[11]!=c[3]||c[12]||c[13]!=12||c[14]!=12||c[15]||c[17]!=(w[317]==2?2:1)||w[12]!=c[3])return 0;}
  if(op==1&&(q||w[13]<=w[12]||w[14]<w[13]||w[286]!=1))return 0;
  if(op==2&&(!q||!w[36]||w[15]!=w[12]+4))return 0;
  if(op==3&&!q)return 0;
 }
 if(w[7]){if(op!=5||w[2]||w[36]||w[6]!=3)return 0;}else if(w[6]==3)return 0;
 for(i=299;i<316;i++)if(w[i])return 0;
 return 1;
}
