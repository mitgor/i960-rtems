#include "persist_report.h"
static int lease_valid(const unsigned int*w,unsigned int seq,unsigned int op){
 if(!pirq_valid(w,seq,op))return 0;
 if(w[320]!=0x3145534c||w[321]!=1||w[322]!=3||w[323]<1||w[323]>3||w[327]||w[331])return 0;
 if(w[323]==1&&(!w[324]||w[328]>=512))return 0;
 if(w[323]==2&&w[328]!=512)return 0;
 if(w[323]==3&&w[347]-w[346]!=24000)return 0;
 if(w[325]<w[346]||w[347]<w[325]||w[328]!=w[347]-w[325]||w[329]<w[328]||w[329]>512)return 0;
 if(w[332]!=0x2000||w[333]!=0xf80000||!w[334]||w[334]==w[335]||w[335]!=w[26]||w[336]!=20000||w[337]!=w[338]||w[339]!=0x6000)return 0;
 if(w[340]!=0xc0f2c000||w[341]!=0xc0f9bff0||w[342]!=0x1fb||w[343]!=0xff||w[344]!=24000||w[345]!=512||w[349]!=15||w[350]||w[351])return 0;
 if(op>=1&&op<=3&&(w[330]!=w[8]-w[9]||w[348]!=seq||w[346]!=w[10]||w[347]!=w[11]||w[317]))return 0;
 return 1;
}
