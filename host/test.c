#include "../game/io.h"
void __main(void){}
int main(void){
    int s=0,i,j;
    for(i=1;i<=100;i++){ int sq=i*i; s+=sq; }
    for(j=0;j<50;j++) s ^= (s<<1) ^ (s>>3);   /* exercise shifts/xor */
    s = s % 1000003;                           /* remi/divi */
    IO->frame = s;
    IO->halt = 1;
    return 0;
}
