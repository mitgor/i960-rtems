#include "tetris.h"
#ifndef TARGET_I960
#include <stdio.h>
#endif
static u32 hash=2166136261u;
static void digest(const u8 *b,unsigned n){while(n--)hash=(hash^*b++)*16777619u;}
static void clear(void *p,unsigned n){u8 *b=p;while(n--)*b++=0;}
#define CHECK(x) do{if(!(x))return __LINE__;}while(0)
static int tests(void)
{
    struct tetris_state s,t;
    u8 packed[TETRIS_STATE_BYTES],request[TETRIS_REQUEST_BYTES],reply[TETRIS_RESPONSE_BYTES+16];
    u8 screen[ROWS*COLS+16];
    unsigned i,j,seed,key;
    CHECK(sizeof(s)==TETRIS_STATE_BYTES);
    tetris_init(&s,0);CHECK(tetris_valid(&s));
    tetris_encode(&s,packed);tetris_decode(&t,packed);CHECK(tetris_valid(&t));
    CHECK(tetris_step(&s,0,21)==1);CHECK(tetris_step(&s,255,1)==1);
    tetris_encode(&s,request);for(i=0;i<TETRIS_STATE_BYTES;i++)CHECK(request[i]==packed[i]);
    s.piece=0;s.rotation=0;s.x=0;s.y=0;
    CHECK(!tetris_step(&s,K_LEFT,0) && s.x==0);
    CHECK(!tetris_step(&s,K_ROT,0) && s.rotation==1);
    CHECK(!tetris_step(&s,K_DROP,0) && s.y==16);
    CHECK(!tetris_step(&s,0,20));CHECK(s.board[19][2]=='I');
    /* Two simultaneous lines through the real production clear loop. */
    tetris_init(&s,1);s.piece=1;s.rotation=0;s.x=3;s.y=18;s.tick=19;
    for(i=18;i<20;i++)for(j=0;j<10;j++)s.board[i][j]=(j==4||j==5)?0:'J';
    s.board[17][0]='L';CHECK(tetris_valid(&s));
    CHECK(!tetris_step(&s,0,1) && s.score==200 && s.board[19][0]=='L');
    /* Spawn collision => game over; terminal state stays stable except quit. */
    tetris_init(&s,1);s.piece=0;s.rotation=0;s.x=3;s.y=18;s.tick=19;
    for(i=0;i<2;i++)for(j=3;j<7;j++)s.board[i][j]='J';
    CHECK(!tetris_step(&s,0,1) && s.phase==1);
    CHECK(!tetris_step(&s,K_QUIT,0) && s.phase==2);
    tetris_init(&s,1);CHECK(s.phase==0 && !s.score);
    /* Malformed states never index shapes/board out of bounds. */
    for(i=0;i<10;i++) {
        tetris_init(&s,1);tetris_encode(&s,packed);
        for(j=0;j<4;j++)packed[i*4+j]=(i==5||i==6)?(j==3?128:0):255;
        tetris_decode(&s,packed);
        if(i!=1)CHECK(!tetris_valid(&s)); /* any nonzero RNG bit pattern is valid */
    }
    tetris_init(&s,1);s.board[19][9]='?';CHECK(!tetris_valid(&s));
    /* Guards and largest score formatting, including terminal render. */
    tetris_init(&s,1);s.score=999999900u;
    for(i=0;i<sizeof(screen);i++)screen[i]=0xa5;
    tetris_render(&s,screen);for(i=ROWS*COLS;i<sizeof(screen);i++)CHECK(screen[i]==0xa5);
    clear(request,sizeof(request));request[0]=1;
    for(i=0;i<sizeof(reply);i++)reply[i]=0xa5;
    CHECK(tetris_request(request,sizeof(request)-1,reply,TETRIS_RESPONSE_BYTES)==1);
    CHECK(tetris_request(request,sizeof(request),reply,TETRIS_RESPONSE_BYTES-1)==2);
    for(i=0;i<sizeof(reply);i++)CHECK(reply[i]==0xa5);
    CHECK(!tetris_request(request,sizeof(request),reply,TETRIS_RESPONSE_BYTES));
    for(i=TETRIS_RESPONSE_BYTES;i<sizeof(reply);i++)CHECK(reply[i]==0xa5);
    request[16]=1;CHECK(tetris_request(request,sizeof(request),reply,TETRIS_RESPONSE_BYTES)==1);
    /* Deterministic seeded traces; hash every state and framebuffer. */
    for(seed=1;seed<=4;seed++) {
        tetris_init(&s,seed);
        for(i=0;i<256;i++) {
            if(s.phase)tetris_init(&s,seed+i);
            key=i%11==0?K_DROP:i%7==0?K_ROT:i%3==0?K_LEFT:i%5==0?K_RIGHT:0;
            CHECK(!tetris_step(&s,key,(i%20)+1));
            CHECK(tetris_valid(&s));
            tetris_encode(&s,packed);tetris_render(&s,screen);
            digest(packed,sizeof(packed));digest(screen,ROWS*COLS);
        }
    }
    return 0;
}
void __main(void){}
int main(void)
{
    int error=tests();i32 result=error?-(i32)error:(i32)(hash&0x7fffffff);
#ifdef TARGET_I960
    IO->frame=result;IO->halt=1;
#else
    printf("RESULT=%d\n",result);
#endif
    return error?1:0;
}
