/* Tetris for i960, freestanding, text mode. Logic runs on the i960; the host
   renders IO->fb and feeds IO->key. One doorbell == one frame. */
#include "io.h"

/* --- minimal freestanding helpers (GCC may also emit calls to these) --- */
void *memset(void *d, int c, unsigned n){ u8 *p=d; while(n--) *p++=(u8)c; return d; }
void *memcpy(void *d, const void *s, unsigned n){ u8 *p=d; const u8 *q=s; while(n--) *p++=*q++; return d; }
void __main(void){} /* gcc 3.3 calls this from main for ctors; we have none */

/* --- host sync: yield one frame, return the key the host gives back --- */
static int io_sync(void){
    IO->doorbell = 1;
    while (IO->doorbell) { /* host clears it after servicing */ }
    return IO->key;
}

/* --- playfield --- */
#define BW 10            /* board width  */
#define BH 20            /* board height */
static u8 board[BH][BW]; /* 0 empty, else piece-color char */

/* 7 tetrominoes, 4 rotations, each 4 (x,y) cells in a 4x4 box */
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

static int cur, rot, px, py;   /* current piece, rotation, position */
static u32 rng = 0x1234567u;
static int score, gameover;

static u32 rnd(void){ rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5; return rng; }

/* can the piece sit at (nx,ny) with rotation nr? */
static int fits(int p,int nr,int nx,int ny){
    int i;
    for(i=0;i<4;i++){
        int x = nx + shapes[p][nr][i][0];
        int y = ny + shapes[p][nr][i][1];
        if(x<0||x>=BW||y>=BH) return 0;
        if(y>=0 && board[y][x]) return 0;
    }
    return 1;
}

static void spawn(void){
    cur = rnd()%7; rot=0; px=3; py=0;
    if(!fits(cur,rot,px,py)) gameover=1;
}

static void lock_piece(void){
    int i,x,y,r,c,full,yy;
    for(i=0;i<4;i++){
        x=px+shapes[cur][rot][i][0]; y=py+shapes[cur][rot][i][1];
        if(y>=0) board[y][x]=piece_ch[cur];
    }
    /* clear full lines */
    for(r=BH-1;r>=0;r--){
        full=1;
        for(c=0;c<BW;c++) if(!board[r][c]) full=0;
        if(full){
            for(yy=r;yy>0;yy--) memcpy(board[yy],board[yy-1],BW);
            memset(board[0],0,BW);
            score += 100;
            r++; /* recheck same row */
        }
    }
    spawn();
}

/* draw board + current piece into the framebuffer */
static void render(void){
    int r,c,i;
    /* clear screen area */
    memset((void*)IO->fb,' ',ROWS*COLS);
    /* border + cells: board drawn 2 chars wide for aspect */
    for(r=0;r<BH;r++){
        IO->fb[r+1][0]='|'; IO->fb[r+1][BW*2+1]='|';
        for(c=0;c<BW;c++){
            char ch = board[r][c] ? board[r][c] : '.';
            IO->fb[r+1][1+c*2]=ch; IO->fb[r+1][2+c*2]=ch==('.')?' ':ch;
        }
    }
    for(c=0;c<BW*2+2;c++){ IO->fb[0][c]='-'; IO->fb[BH+1][c]='-'; }
    /* overlay falling piece */
    for(i=0;i<4;i++){
        int x=px+shapes[cur][rot][i][0], y=py+shapes[cur][rot][i][1];
        if(y>=0){ char ch=piece_ch[cur]; IO->fb[y+1][1+x*2]=ch; IO->fb[y+1][2+x*2]=ch; }
    }
    /* HUD */
    {
        char *s=(char*)&IO->fb[2][BW*2+5];
        const char *lbl="SCORE:";
        int v=score, k;
        while(*lbl) *s++=*lbl++;
        /* print score as decimal */
        { char buf[8]; k=0; if(v==0) buf[k++]='0'; while(v){ buf[k++]='0'+v%10; v/=10;} while(k--) *s++=buf[k]; }
    }
    if(gameover){
        const char *g="GAME OVER"; char *s=(char*)&IO->fb[10][BW*2+5];
        while(*g) *s++=*g++;
    }
}

int main(void){
    int tick=0, fall_every=20; /* ponytail: gravity knob (frames/row), tune for feel */
    memset(board,0,sizeof board);
    spawn();
    while(!gameover){
        int k = io_sync();
        if(k==K_QUIT){ IO->halt=1; return 0; }
        if(k==K_LEFT  && fits(cur,rot,px-1,py)) px--;
        if(k==K_RIGHT && fits(cur,rot,px+1,py)) px++;
        if(k==K_ROT){ int nr=(rot+1)&3; if(fits(cur,nr,px,py)) rot=nr; }
        if(k==K_DROP){ while(fits(cur,rot,px,py+1)) py++; }
        if(++tick>=fall_every){
            tick=0;
            if(fits(cur,rot,px,py+1)) py++; else lock_piece();
        }
        render();
    }
    render();            /* show final frame */
    { int i; for(i=0;i<120;i++) io_sync(); } /* hold game-over ~a few sec */
    IO->halt=1;
    return 0;
}
