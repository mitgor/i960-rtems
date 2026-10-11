/* Host-side reclaim gate, shared verbatim with native fault tests.
 * Input is 236 decoded little-endian words, never an unaligned DMA cast. */
static int contain_report_valid(const unsigned int*w,unsigned int epoch){
 const unsigned int*d=w+184,*q=w+204;unsigned int i,j;
 if(w[0]!=0x31575349||w[1]||w[2]<32||w[2]>128||w[3]<6||w[4]<6||
    w[5]||w[6]||w[7]!=1||w[8]!=1||w[9]||w[10]||
    w[11]!=0x10c7||w[12]!=0x80000||w[13]!=w[14]||
    w[15]||w[16]||w[17]||(w[18]&0x2000)||w[19])return 0;
 if(d[0]!=0x31505453||d[1]!=epoch||!epoch||epoch>65535||d[2]!=8||
    d[3]<32||d[3]>124||(d[4]!=w[20]&&d[4]!=w[102])||
    d[5]!=1||d[6]!=1||d[7]!=1||d[8]!=1||d[9]!=w[2]||
    !d[12]||d[13]!=0x4d554f4b)return 0;
 for(i=14;i<20;i++)if(d[i])return 0;
 if(q[0]!=0x314e5443||!q[1]||q[1]==w[20]||q[1]==w[102]||
    q[2]!=d[3]||q[3]!=w[2]||q[3]-q[2]!=4||q[4]!=4||
    q[15]!=q[1]||q[16]!=q[1]||q[17]!=10000||q[26]!=0x514f4b31||q[27]!=1||
    q[28]||q[29]||q[30]||q[31])return 0;
 for(i=0;i<2;i++){
  const unsigned int*s=w+20+i*82,*r=s+12;
  if(!s[0]||s[2]<=s[1]||s[2]-s[1]!=8192||s[3]<s[1]+16||s[3]>s[2]-64||(s[3]&15)||
     s[6]!=0xf2||s[7]!=1||s[8]<6||s[8]!=s[9]+1||d[10+i]!=s[9]||
     s[11]<s[10]+192||s[11]>=s[10]+8128)return 0;
  for(j=0;j<15;j++)if(r[j]!=0x19600000u+i*0x10000000u+j)return 0;
  if(r[68]||r[69]!=q[7+i]||!q[7+i]||q[7+i]>=q[5+i]||q[5+i]>1000000||
     q[9+i]!=q[7+i]||q[11+i]!=2||q[13+i]!=2||
     q[18+i]!=q[20+i]||q[22+i]!=q[24+i])return 0;
 }
 if(w[20]==w[102]||w[30]==w[112]||!(w[22]<=w[103]||w[104]<=w[21]))return 0;
 return 1;
}
