/* Bounded deterministic game core. No hidden mutable state or hardware I/O. */
#include "tetris.h"
#define BW 10
#define BH 20
static const signed char shapes[7][4][4][2] = {
 /* I */ {{{0,1},{1,1},{2,1},{3,1}},{{2,0},{2,1},{2,2},{2,3}},{{0,2},{1,2},{2,2},{3,2}},{{1,0},{1,1},{1,2},{1,3}}},
 /* O */ {{{1,0},{2,0},{1,1},{2,1}},{{1,0},{2,0},{1,1},{2,1}},{{1,0},{2,0},{1,1},{2,1}},{{1,0},{2,0},{1,1},{2,1}}},
 /* T */ {{{1,0},{0,1},{1,1},{2,1}},{{1,0},{1,1},{2,1},{1,2}},{{0,1},{1,1},{2,1},{1,2}},{{1,0},{0,1},{1,1},{1,2}}},
 /* S */ {{{1,0},{2,0},{0,1},{1,1}},{{1,0},{1,1},{2,1},{2,2}},{{1,1},{2,1},{0,2},{1,2}},{{0,0},{0,1},{1,1},{1,2}}},
 /* Z */ {{{0,0},{1,0},{1,1},{2,1}},{{2,0},{1,1},{2,1},{1,2}},{{0,1},{1,1},{1,2},{2,2}},{{1,0},{0,1},{1,1},{0,2}}},
 /* J */ {{{0,0},{0,1},{1,1},{2,1}},{{1,0},{2,0},{1,1},{1,2}},{{0,1},{1,1},{2,1},{2,2}},{{1,0},{1,1},{0,2},{1,2}}},
 /* L */ {{{2,0},{0,1},{1,1},{2,1}},{{1,0},{1,1},{1,2},{2,2}},{{0,1},{1,1},{2,1},{0,2}},{{0,0},{1,0},{1,1},{1,2}}},
};
static const char piece_ch[7] = {'I','O','T','S','Z','J','L'};


static void zero_bytes(void *p,unsigned n) {u8 *b=p;while(n--) *b++=0;}
static int fits(const struct tetris_state *s,int p,int r,int x,int y)
{
    int i;
    for(i=0;i<4;i++) {
        int xx=x+shapes[p][r][i][0],yy=y+shapes[p][r][i][1];
        if(xx<0 || xx>=BW || yy>=BH) return 0;
        if(yy>=0 && s->board[yy][xx]) return 0;
    }
    return 1;
}
static void spawn(struct tetris_state *s)
{
    s->rng^=s->rng<<13;s->rng^=s->rng>>17;s->rng^=s->rng<<5;
    s->piece=s->rng%7;s->rotation=0;s->x=3;s->y=0;
    if(!fits(s,s->piece,0,3,0))s->phase=1;
}
void tetris_init(struct tetris_state *s,u32 seed)
{
    zero_bytes(s,sizeof(*s));s->version=1;s->rng=seed?seed:0x1234567u;spawn(s);
}
int tetris_valid(const struct tetris_state *s)
{
    unsigned r,c,i;
    if(s->version!=1 || !s->rng || s->score>999999900u || s->score%100 ||
       s->piece>=7 || s->rotation>=4 || s->x< -3 || s->x>9 || s->y< -3 || s->y>19 ||
       s->tick>=20 || s->phase>2 || s->reserved) return 0;
    for(r=0;r<BH;r++) for(c=0;c<BW;c++) {
        if(!s->board[r][c])continue;
        for(i=0;i<7;i++)if(s->board[r][c]==piece_ch[i])break;
        if(i==7)return 0;
    }
    return s->phase || fits(s,s->piece,s->rotation,s->x,s->y);
}
static void lock_piece(struct tetris_state *s)
{
    int i,r,c,yy,full;
    for(i=0;i<4;i++) {
        int x=s->x+shapes[s->piece][s->rotation][i][0];
        int y=s->y+shapes[s->piece][s->rotation][i][1];
        if(y<0) {s->phase=1;return;}
        s->board[y][x]=piece_ch[s->piece];
    }
    for(r=BH-1;r>=0;r--) {
        full=1;for(c=0;c<BW;c++)if(!s->board[r][c])full=0;
        if(full) {
            for(yy=r;yy>0;yy--)for(c=0;c<BW;c++)s->board[yy][c]=s->board[yy-1][c];
            for(c=0;c<BW;c++)s->board[0][c]=0;
            if(s->score<999999900u)s->score+=100;
            r++;
        }
    }
    spawn(s);
}
int tetris_step(struct tetris_state *s,u32 key,u32 ticks)
{
    unsigned i;
    if(!tetris_valid(s) || ticks>TETRIS_MAX_TICKS ||
       (key && key!=K_LEFT && key!=K_RIGHT && key!=K_ROT && key!=K_DROP && key!=K_QUIT))return 1;
    if(key==K_QUIT){s->phase=2;return 0;}
    if(s->phase)return 0;
    if(key==K_LEFT && fits(s,s->piece,s->rotation,s->x-1,s->y))s->x--;
    if(key==K_RIGHT && fits(s,s->piece,s->rotation,s->x+1,s->y))s->x++;
    if(key==K_ROT && fits(s,s->piece,(s->rotation+1)&3,s->x,s->y))s->rotation=(s->rotation+1)&3;
    if(key==K_DROP)for(i=0;i<BH+4 && fits(s,s->piece,s->rotation,s->x,s->y+1);i++)s->y++;
    for(i=0;i<ticks && !s->phase;i++)if(++s->tick==20) {
        s->tick=0;
        if(fits(s,s->piece,s->rotation,s->x,s->y+1))s->y++;
        else lock_piece(s);
    }
    return 0;
}
void tetris_render(const struct tetris_state *s,u8 *f)
{
    unsigned i,r,c,n=0,v=s->score;
    char digits[10];const char *label="SCORE:";
    for(i=0;i<ROWS*COLS;i++)f[i]=' ';
    for(r=0;r<BH;r++) {
        f[(r+1)*COLS]='|';f[(r+1)*COLS+21]='|';
        for(c=0;c<BW;c++) {
            char ch=s->board[r][c]?s->board[r][c]:'.';
            f[(r+1)*COLS+1+c*2]=ch;f[(r+1)*COLS+2+c*2]=ch=='.'?' ':ch;
        }
    }
    for(c=0;c<22;c++){f[c]='-';f[21*COLS+c]='-';}
    for(i=0;i<4;i++) {
        int x=s->x+shapes[s->piece][s->rotation][i][0],y=s->y+shapes[s->piece][s->rotation][i][1];
        if(x>=0 && x<BW && y>=0 && y<BH) {
            f[(y+1)*COLS+1+x*2]=piece_ch[s->piece];f[(y+1)*COLS+2+x*2]=piece_ch[s->piece];
        }
    }
    i=2*COLS+25;while(*label)f[i++]=*label++;
    do{digits[n++]='0'+v%10;v/=10;}while(v);
    while(n)f[i++]=digits[--n];
    if(s->phase) {
        label=s->phase==1?"GAME OVER":"QUIT";i=10*COLS+25;
        while(*label)f[i++]=*label++;
    }
}
static u32 get32(const u8 *b){return (u32)b[0]|(u32)b[1]<<8|(u32)b[2]<<16|(u32)b[3]<<24;}
static void put32(u8 *b,u32 v){b[0]=v;b[1]=v>>8;b[2]=v>>16;b[3]=v>>24;}
static i32 signed32(u32 v){return v<=0x7fffffffu?(i32)v:-1-(i32)(~v);}
void tetris_encode(const struct tetris_state *s,u8 *b)
{
    unsigned i;put32(b,s->version);put32(b+4,s->rng);put32(b+8,s->score);
    put32(b+12,s->piece);put32(b+16,s->rotation);put32(b+20,(u32)s->x);put32(b+24,(u32)s->y);
    put32(b+28,s->tick);put32(b+32,s->phase);put32(b+36,0);
    for(i=0;i<200;i++)b[40+i]=s->board[i/10][i%10];
}
void tetris_decode(struct tetris_state *s,const u8 *b)
{
    unsigned i;s->version=get32(b);s->rng=get32(b+4);s->score=get32(b+8);
    s->piece=get32(b+12);s->rotation=get32(b+16);s->x=signed32(get32(b+20));s->y=signed32(get32(b+24));
    s->tick=get32(b+28);s->phase=get32(b+32);s->reserved=get32(b+36);
    for(i=0;i<200;i++)s->board[i/10][i%10]=b[40+i];
}
unsigned tetris_request(const u8 *in,unsigned length,u8 *out,unsigned capacity)
{
    struct tetris_state s;u32 op,key,ticks;
    if(length!=TETRIS_REQUEST_BYTES)return 1;
    if(capacity<TETRIS_RESPONSE_BYTES)return 2;
    op=get32(in);key=get32(in+8);ticks=get32(in+12);
    if(op==1) {
        unsigned i;if(key || ticks)return 1;
        for(i=16;i<length;i++)if(in[i])return 1;
        tetris_init(&s,get32(in+4));
    } else if(op==0) {
        if(get32(in+4))return 1;
        tetris_decode(&s,in+16);
        if(tetris_step(&s,key,ticks))return 1;
    } else return 1;
    tetris_encode(&s,out);tetris_render(&s,out+TETRIS_STATE_BYTES);return 0;
}
#ifndef TETRIS_CORE_ONLY
/* Historical emulator adapter; never used as the returning card payload. */
void __main(void){}
int main(void)
{
    struct tetris_state state;u8 frame[ROWS*COLS];unsigned i;
    tetris_init(&state,0);
    while(!state.phase) {
        IO->doorbell=1;while(IO->doorbell){}
        /* Ignore unrecognized terminal input as the original game did. */
        if(tetris_step(&state,IO->key,1))tetris_step(&state,0,1);
        tetris_render(&state,frame);
        for(i=0;i<ROWS*COLS;i++)((volatile u8*)IO->fb)[i]=frame[i];
    }
    if(state.phase==1)for(i=0;i<120;i++){IO->doorbell=1;while(IO->doorbell){}}
    IO->halt=1;return 0;
}
#endif
