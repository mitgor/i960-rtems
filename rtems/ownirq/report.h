/* Exact pinned one-shot target. QUIESCED alone never authorizes reclamation. */
static int ownirq_evidence_valid(const unsigned int*w,unsigned int epoch,unsigned int mode){unsigned int i,j;const unsigned int*c=w+60;
 if(w[0]!=0x3149524f||w[1]!=1||w[2]||w[3]!=mode||mode<1||mode>5||w[4]!=epoch||!epoch||epoch>65535)return 0;
 if(w[5]<20||w[5]>100||w[6]<2||w[7]<4||!w[8]||w[9]<w[8]||w[10]!=w[9]||w[16]!=10000)return 0;
 if(w[17]||w[18]!=0x10c7||w[19]!=0x80000||w[20]!=w[21]||w[22]||w[23]||w[24]||(w[25]&0x2000)||w[26]||w[27]||w[31])return 0;
 if(w[32]!=2||w[34]!=2||w[35]!=1||w[40]!=epoch||w[45]!=1||w[46]!=1||w[50]||w[51]!=1||w[53]!=1||w[54]!=23)return 0;
 if(!w[14]||!w[15]||w[15]>=w[14]||w[14]>1000000||!w[244]||!w[245]||!w[246]||w[244]==w[245]||w[244]==w[246]||w[245]==w[246])return 0;
 if(!w[247]||w[247]!=w[248]||w[250]!=1||w[252]||!w[253]||w[254]!=0x4d554f4b||w[255]!=0x514f4b31)return 0;
 if(mode<=2){
  if(w[11]<=w[10]||w[12]<w[11]||w[13]||w[28]||w[29]||w[30]||w[33]!=2||w[36]!=1||w[37]!=0x10203040||w[38]!=1||!w[39])return 0;
  if(w[41]!=3||w[42]!=0x55667788||w[43]!=w[42]||w[44]||w[47]!=1||w[48]!=3||w[49]!=1||w[52]!=1||w[249]||w[251]!=1)return 0;
 }else{
  if(w[12]||w[13]!=w[9]+4||w[28]!=w[244]||w[29]!=1||w[30]!=1||w[33]!=0x402||w[36]||w[37]||w[38]||w[39])return 0;
  if(w[41]!=4||w[42]!=0x10203040||w[43]!=0xdeadbeef||w[44]!=(mode==5)||w[47]||w[48]!=(mode==5?4:5)||w[49]||w[249]!=1||w[251])return 0;
  if(mode==5){if(w[11]||w[52])return 0;}else if(w[11]!=w[13]||w[52]!=1)return 0;
  if(!w[55]||w[55]>1000000||!w[56]||w[56]!=w[57]||!w[58]||w[58]!=w[59]||!c[18]||c[18]!=c[19])return 0;
 }
 if(mode<=2||mode==4){
  if(c[0]!=mode||c[1]<16||c[2]!=c[1]+12||c[3]!=c[2]+12||c[4]<c[3]||c[5]!=2||c[6]!=1||c[7]!=1||c[8]||c[9]!=c[10]||c[11]!=c[3]||c[12]||c[13]!=12||c[14]!=12||c[15]||c[16]<20||c[17]!=(mode==2?2:1)||w[9]!=c[3])return 0;
  if(mode==2){if(w[8]<c[2]+1||w[8]>=c[3])return 0;}else if(w[8]<c[1]+1||w[8]>=c[2])return 0;
 }else if(w[8]<16||w[9]!=w[8])return 0;
 for(i=0;i<2;i++){const unsigned int*s=w+80+i*82,*r=s+12;unsigned int live=(i==1||mode>=3);
  if(!s[0]||s[2]-s[1]!=8192||s[3]<s[1]+16||s[3]>s[2]-64||(s[3]&15)||s[6]!=0xf2||s[7]!=live||s[8]!=s[9]+live||s[8]<2||s[11]<s[10]+192||s[11]>=s[10]+8128)return 0;
  for(j=0;j<15;j++)if(r[j]!=0x19600000u+i*0x10000000u+j)return 0;
  if(r[68]||!r[69]||r[69]>1000000)return 0;
  if(!live){for(j=0;j<16;j++)if(r[j]!=r[j+16])return 0;
   for(j=0;j<16;j++)if(j!=2&&j!=3&&j!=5&&r[32+j]!=r[48+j])return 0;
   if(r[64]!=r[65]||r[66]!=r[67])return 0;}
 }
 if(w[80]==w[162]||w[90]==w[172]||(mode>=3&&w[161]!=w[55])||w[243]!=w[15])return 0;
 return 1;
}
static int ownirq_report_valid(const unsigned int*w,unsigned int epoch,unsigned int mode){return ownirq_evidence_valid(w,epoch,mode)&&!w[44];}
