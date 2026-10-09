#include "../game/io.h"
void __main(void){}
#define BW 10
#define BH 20
static unsigned char board[BH][BW];
void *memcpy(void *d,const void*s,unsigned n){unsigned char*p=d;const unsigned char*q=s;while(n--)*p++=*q++;return d;}
void *memset(void *d,int c,unsigned n){unsigned char*p=d;while(n--)*p++=(unsigned char)c;return d;}
int main(void){
    int r,c,full,yy,score=0;
    memset(board,0,sizeof board);
    /* fill bottom two rows completely, and row 17 partially (col 0 empty) */
    for(c=0;c<BW;c++){ board[19][c]='X'; board[18][c]='X'; }
    for(c=1;c<BW;c++) board[17][c]='X';
    board[17][0]=0;                  /* leave a gap so row 17 is NOT full */
    board[16][5]='X';                /* a stray block that must fall      */
    /* --- exact clear loop copied from tetris.c lock_piece --- */
    for(r=BH-1;r>=0;r--){
        full=1; for(c=0;c<BW;c++) if(!board[r][c]) full=0;
        if(full){ for(yy=r;yy>0;yy--) memcpy(board[yy],board[yy-1],BW);
                  memset(board[0],0,BW); score+=100; r++; }
    }
    /* encode: score, and where the stray/partial ended up */
    IO->frame = score*1000 + (board[19][5]?1:0)*100 + (board[19][0]?0:10) + (board[18][0]?1:0);
    IO->halt = 1; return 0;
}
