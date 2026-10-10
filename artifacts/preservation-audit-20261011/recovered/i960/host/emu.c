/* Minimal i960 (RP/Jx core) interpreter + text-mode front-end.
   Runs on the Ubuntu host. Executes the exact opcode set GCC 3.3 -mrp emits for
   tetris.c. Loads an elf32-i960 little-endian image, sets up the i960 call frame,
   and renders the shared framebuffer (see game/io.h) to the terminal.

   This genuinely decodes i960 machine code; it is not a recompile to x86.
   Build on remote:  gcc -O2 -o emu emu.c
   Run:              ./emu tetris.elf        (game)
                     ./emu -t test.elf       (self-check: prints IO.frame result)
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <time.h>

typedef uint32_t u32; typedef int32_t i32; typedef uint8_t u8;

#define RAM_SIZE 0x100000u          /* 1 MB flat little-endian RAM */
#define IO_BASE  0x00090000u
#define FP0      0x00040000u        /* initial frame pointer (64-aligned)        */
#define HALT_IP  0xFFFFFFF0u        /* sentinel return address -> stop           */
/* io struct layout mirrors game/io.h */
#define FB_OFF   0
#define FB_BYTES (24*80)
#define DOORBELL (IO_BASE + FB_BYTES)
#define KEY      (DOORBELL + 4)
#define FRAME    (KEY + 4)
#define HALT     (FRAME + 4)

static u8 ram[RAM_SIZE];
static u32 g[16];                    /* global regs; g[15] = FP                   */
/* local register sets, one per call frame; r[0]=PFP r[1]=SP r[2]=RIP            */
static u32 lstack[256][16];
static int lsp;                      /* index of current local frame             */
#define R(i) (lstack[lsp][i])
static u32 ip;
static int ac_cc;                    /* condition code from cmpo/cmpi            */

static u32 rd32(u32 a){ return ram[a]|ram[a+1]<<8|ram[a+2]<<16|ram[a+3]<<24; }
static void wr32(u32 a,u32 v){ ram[a]=v;ram[a+1]=v>>8;ram[a+2]=v>>16;ram[a+3]=v>>24; }
static u32 reg(int i){ return i<16 ? R(i) : g[i-16]; }   /* 0-15 r, 16-31 g      */
static void setreg(int i,u32 v){ if(i<16) R(i)=v; else g[i-16]=v; }

/* ---- i960 call / ret (hardware frame model) ---- */
static void do_call(u32 target,u32 ret_ip){
    u32 newfp = (R(1) + 63) & ~63u;      /* round current SP up to 64             */
    u32 oldfp = g[15];
    lsp++;                                /* push new local register set          */
    memset(lstack[lsp],0,sizeof lstack[lsp]);
    R(0) = oldfp;                         /* PFP                                   */
    R(1) = newfp + 64;                    /* SP                                    */
    R(2) = ret_ip;                        /* RIP                                   */
    g[15] = newfp;                        /* FP                                    */
    ip = target;
}
static void do_ret(void){
    ip = R(2);                            /* RIP (full return address)            */
    g[15] = R(0) & ~0xfu;                 /* restore FP from PFP                   */
    lsp--;                                /* pop to caller's local set            */
}

/* ---- effective address for MEM-format ---- */
static u32 ea(u32 w1,u32 w2,u32 iaddr,int *len){
    u32 mode=(w1>>10)&0xf, abase=(w1>>14)&0x1f, index=w1&0x1f;
    u32 scale=(w1>>7)&7; static const u32 st[]={1,2,4,8,16};
    scale = scale<=4 ? st[scale] : 1;
    if(!(mode&4)){                        /* MEMA: one word                        */
        *len=1; u32 off=w1&0xfff;
        return (mode&8)? reg(abase)+off : off;
    }
    switch(mode){                         /* MEMB                                  */
        case 4:  *len=1; return reg(abase);
        case 5:  *len=2; return iaddr+8+w2;
        case 7:  *len=1; return reg(abase)+reg(index)*scale;
        case 12: *len=2; return w2;
        case 13: *len=2; return w2+reg(abase);
        case 14: *len=2; return w2+reg(index)*scale;
        case 15: *len=2; return w2+reg(abase)+reg(index)*scale;
        default: *len=1; return 0;
    }
}

static int mem_twowords(u32 w1){
    u32 mode=(w1>>10)&0xf;
    if(!(mode&4)) return 0;
    return mode==5||mode==12||mode==13||mode==14||mode==15;
}

/* device service on doorbell: render fb + poll one key */
static int interactive=1;
static void service(void){
    if(interactive){
        char out[FB_BYTES+64*4+64]; int o=0;
        o+=sprintf(out+o,"\x1b[H");               /* cursor home                  */
        for(int r=0;r<24;r++){
            memcpy(out+o, &ram[IO_BASE+r*80], 80); o+=80;
            out[o++]='\x1b';out[o++]='[';out[o++]='K'; /* clear to EOL            */
            out[o++]='\r';out[o++]='\n';
        }
        write(1,out,o);
    }
    if(interactive){ struct timespec d={0,50*1000*1000}; nanosleep(&d,0); } /* ~20fps */
    /* poll stdin nonblocking for one key */
    char c; int k=0;
    if(read(0,&c,1)==1) k=(unsigned char)c;
    wr32(KEY,(u32)k);
    wr32(FRAME, rd32(FRAME)+1);
    wr32(DOORBELL,0);
}

static struct termios saved_tio;
static void raw_on(void){
    tcgetattr(0,&saved_tio); struct termios t=saved_tio;
    t.c_lflag &= ~(ICANON|ECHO); t.c_cc[VMIN]=0; t.c_cc[VTIME]=0;
    tcsetattr(0,TCSANOW,&t);
    fcntl(0,F_SETFL,fcntl(0,F_GETFL)|O_NONBLOCK);
    write(1,"\x1b[2J\x1b[?25l",9);               /* clear + hide cursor           */
}
static void raw_off(void){ write(1,"\x1b[?25h\n",7); tcsetattr(0,TCSANOW,&saved_tio); }

/* ---- load elf32 little-endian ---- */
static u32 load_elf(const char *path){
    FILE *f=fopen(path,"rb"); if(!f){perror(path);exit(1);}
    u8 h[52]; fread(h,1,52,f);
    if(!(h[0]==0x7f&&h[1]=='E'&&h[2]=='L'&&h[3]=='F')){fprintf(stderr,"not elf\n");exit(1);}
    u32 entry = h[24]|h[25]<<8|h[26]<<16|h[27]<<24;
    u32 phoff = h[28]|h[29]<<8|h[30]<<16|h[31]<<24;
    u32 phentsize = h[42]|h[43]<<8;
    u32 phnum = h[44]|h[45]<<8;
    for(u32 i=0;i<phnum;i++){
        u8 p[32]; fseek(f,phoff+i*phentsize,SEEK_SET); fread(p,1,32,f);
        u32 type=p[0]|p[1]<<8|p[2]<<16|p[3]<<24; if(type!=1) continue; /* PT_LOAD */
        u32 off=p[4]|p[5]<<8|p[6]<<16|p[7]<<24;
        u32 vaddr=p[8]|p[9]<<8|p[10]<<16|p[11]<<24;
        u32 filesz=p[16]|p[17]<<8|p[18]<<16|p[19]<<24;
        u32 memsz=p[20]|p[21]<<8|p[22]<<16|p[23]<<24;
        if(vaddr+memsz>RAM_SIZE){fprintf(stderr,"seg oob\n");exit(1);}
        fseek(f,off,SEEK_SET); fread(&ram[vaddr],1,filesz,f);
        memset(&ram[vaddr+filesz],0,memsz-filesz);
    }
    fclose(f); return entry;
}

int main(int argc,char**argv){
    const char *elf=0; int test=0;
    for(int i=1;i<argc;i++){ if(!strcmp(argv[i],"-t")){test=1;interactive=0;} else elf=argv[i]; }
    if(!elf){fprintf(stderr,"usage: %s [-t] file.elf\n",argv[0]);return 1;}
    u32 entry=load_elf(elf);

    /* sentinel frame 0, then call entry with return = HALT */
    lsp=0; memset(lstack[0],0,sizeof lstack[0]);
    g[15]=FP0; R(0)=FP0; R(1)=FP0+64; R(2)=HALT_IP;
    do_call(entry,HALT_IP);

    if(interactive) raw_on();
    long budget = test? 200000000L : 20000000000L;
    struct timespec frame_delay={0,50*1000*1000}; /* ponytail: 50ms/frame knob */

    int trace = getenv("TRACE")!=0; long traced=0;
    while(ip!=HALT_IP && budget-->0){
        if(rd32(HALT)) break;
        u32 w1=rd32(ip); u32 op=w1>>24;
        if(trace && traced++<80) fprintf(stderr,"ip=%05x w=%08x op=%02x lsp=%d g0=%x g5=%x g6=%x\n",ip,w1,op,lsp,g[0],g[5],g[6]);
        if(op>=0x80){                                  /* MEM format              */
            int len=1; u32 w2=0;
            if(mem_twowords(w1)) w2=rd32(ip+4);
            u32 addr=ea(w1,w2,ip,&len);
            int reg1=(w1>>19)&0x1f;
            u32 next=ip+(len*4);
            switch(op){
                case 0x80: setreg(reg1, ram[addr]); break;             /* ldob   */
                case 0x82: ram[addr]=reg(reg1); break;                 /* stob   */
                case 0x88: setreg(reg1, ram[addr]|ram[addr+1]<<8); break; /* ldos*/
                case 0x8a: ram[addr]=reg(reg1);ram[addr+1]=reg(reg1)>>8;break;/*stos*/
                case 0xc0: setreg(reg1,(i32)(int8_t)ram[addr]); break; /* ldib   */
                case 0xc2: ram[addr]=reg(reg1); break;                 /* stib   */
                case 0x8c: setreg(reg1, addr); break;                  /* lda    */
                case 0x90: setreg(reg1, rd32(addr)); break;            /* ld     */
                case 0x92: wr32(addr, reg(reg1));                      /* st     */
                           if(addr==DOORBELL && reg(reg1)) { ip=next; service(); continue; }
                           break;
                case 0x98: setreg(reg1,rd32(addr)); setreg(reg1+1,rd32(addr+4)); break;/*ldl*/
                case 0x9a: wr32(addr,reg(reg1)); wr32(addr+4,reg(reg1+1)); break;/*stl*/
                case 0x84: ip=addr; continue;                          /* bx     */
                case 0x85: setreg(reg1,next); ip=addr; continue;       /* balx   */
                case 0x86: do_call(addr,next); continue;               /* callx  */
                default: fprintf(stderr,"unimpl MEM op %02x @%x\n",op,ip); goto done;
            }
            ip=next; continue;
        }
        if(op<0x20){                                   /* CTRL format             */
            i32 disp=(i32)((w1&0x00fffffc)<<8)>>8;     /* 22-bit*4 signed         */
            switch(op){
                case 0x08: ip=ip+disp; continue;                       /* b      */
                case 0x09: do_call(ip+disp, ip+4); continue;           /* call   */
                case 0x0a: do_ret(); continue;                         /* ret    */
                case 0x0b: g[14]=ip+4; ip=ip+disp; continue;           /* bal->g14*/
                default: fprintf(stderr,"unimpl CTRL op %02x @%x\n",op,ip); goto done;
            }
        }
        if(op>=0x20&&op<0x28){                          /* test{cond} dst (COBR)  */
            int dst=(w1>>19)&0x1f, mask=op&7;
            setreg(dst, (ac_cc&mask)?1:0); ip+=4; continue;
        }
        if(op>=0x30&&op<0x40){                          /* COBR compare-and-branch*/
            int s1=(w1>>19)&0x1f, s2=(w1>>14)&0x1f, m1=(w1>>13)&1;
            i32 disp=(i32)((w1&0x00001ffc)<<19)>>19;    /* 11-bit*4 signed        */
            u32 a = m1? (u32)s1 : reg(s1);
            u32 b = reg(s2);
            int cc; int integer = op>=0x38;
            if(integer){ i32 ia=(i32)a, ib=(i32)b; cc = ia<ib?4: ia==ib?2:1; }
            else       { cc = a<b?4: a==b?2:1; }
            int mask=op&7;
            if(cc&mask){ ip=ip+disp; continue; }
            ip+=4; continue;
        }
        /* REG format */
        {
            u32 opc=((w1>>20)&0xff0)|((w1>>7)&0xf);
            int dst=(w1>>19)&0x1f, s2i=(w1>>14)&0x1f, s1i=w1&0x1f;
            int m1=(w1>>11)&1, m2=(w1>>12)&1;
            u32 s1 = m1? (u32)s1i : reg(s1i);
            u32 s2 = m2? (u32)s2i : reg(s2i);
            switch(opc){
                case 0x581: setreg(dst, s2 & s1); break;               /* and    */
                case 0x582: setreg(dst, s2 & ~s1); break;              /* andnot */
                case 0x586: setreg(dst, s2 ^ s1); break;               /* xor    */
                case 0x587: setreg(dst, s2 | s1); break;               /* or     */
                case 0x58a: setreg(dst, ~s1); break;                   /* not    */
                case 0x58b: setreg(dst, s2 | ~s1); break;              /* ornot  */
                case 0x590: setreg(dst, s2 + s1); break;               /* addo   */
                case 0x591: setreg(dst, (i32)s2 + (i32)s1); break;     /* addi   */
                case 0x592: setreg(dst, s2 - s1); break;               /* subo   */
                case 0x593: setreg(dst, (i32)s2 - (i32)s1); break;     /* subi   */
                case 0x598: setreg(dst, s1>=32?0: s2 >> s1); break;    /* shro   */
                case 0x59b: setreg(dst, s1>=32?0:(u32)((i32)s2 >> s1)); break;/*shri*/
                case 0x59c: setreg(dst, s1>=32?0: s2 << s1); break;    /* shlo   */
                case 0x59e: setreg(dst, s1>=32?0: s2 << s1); break;    /* shli   */
                case 0x5a0: ac_cc = s1<s2?4: s1==s2?2:1; break;        /* cmpo   */
                case 0x5a1:{i32 a=s1,b=s2; ac_cc=a<b?4:a==b?2:1;}break; /* cmpi  */
                case 0x5cc: setreg(dst, s1); break;                    /* mov    */
                case 0x5dc: setreg(dst, reg(s1i)); setreg(dst+1, reg(s1i+1)); break;/*movl*/
                case 0x701: setreg(dst, s2 * s1); break;               /* mulo   */
                case 0x741: setreg(dst, (i32)s2 * (i32)s1); break;     /* muli   */
                case 0x708: setreg(dst, s1? s2 % s1:0); break;         /* remo   */
                case 0x748: setreg(dst, s1? (i32)s2 % (i32)s1:0); break;/* remi  */
                case 0x70b: setreg(dst, s1? s2 / s1:0); break;         /* divo   */
                case 0x74b: setreg(dst, s1? (i32)s2 / (i32)s1:0); break;/* divi  */
                case 0x749: setreg(dst, s1? (i32)s2 % (i32)s1:0); break;/* modi  */
                default: fprintf(stderr,"unimpl REG opc %03x @%x w=%08x\n",opc,ip,w1); goto done;
            }
            ip+=4; continue;
        }
    }
done:
    if(interactive) raw_off();
    if(getenv("TRACE")) fprintf(stderr,"END ip=%x halt=%d budget=%ld\n",ip,rd32(HALT),budget);
    if(test) printf("RESULT=%d\n",(i32)rd32(FRAME));
    return 0;
}
