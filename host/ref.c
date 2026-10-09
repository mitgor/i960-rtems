#include <stdio.h>
int main(void){ int s=0,i,j; for(i=1;i<=100;i++){int sq=i*i;s+=sq;}
 for(j=0;j<50;j++) s^=(s<<1)^(s>>3); s%=1000003; printf("RESULT=%d\n",s); return 0; }
