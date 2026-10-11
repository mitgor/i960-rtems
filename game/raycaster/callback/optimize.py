"""Exact opt-in source transformations; ray.c remains the independent oracle."""
from pathlib import Path
HERE=Path(__file__).resolve().parent

def once(s,old,new):
    assert s.count(old)==1,old
    return s.replace(old,new)

def request_words(s):
    s=once(s,'static inline int bio_request_valid', (HERE/'uniform.h').read_text()+'\nstatic inline int bio_request_valid')
    s=once(s,'    unsigned int i;\n    if(bio_word(b)', '    if(bio_word(b)')
    old='''    for(i=32;i<BIO_HEADER;i++) if(b[i]) return 0;
    for(i=BIO_INPUT+bio_word(b+12);i<BIO_GUARD1;i++) if(b[i]) return 0;
    for(i=0;i<16;i++) if(b[BIO_GUARD1+i]!=0xa5 || b[BIO_GUARD2+i]!=0x5a) return 0;
    for(i=0;i<BIO_OUTPUT_MAX;i++) if(b[BIO_OUTPUT+i]!=0xcc) return 0;
'''
    return once(s,old,'''    if(!bio_uniform(b+32,BIO_HEADER-32,0) ||
       !bio_uniform(b+BIO_INPUT+bio_word(b+12),BIO_INPUT_MAX-bio_word(b+12),0) ||
       !bio_uniform(b+BIO_GUARD1,16,0xa5) ||
       !bio_uniform(b+BIO_GUARD2,16,0x5a) ||
       !bio_uniform(b+BIO_OUTPUT,BIO_OUTPUT_MAX,0xcc)) return 0;
''')

def render_fast(s):
    s=once(s,'static unsigned int hash(const unsigned char*p,unsigned int n){unsigned int h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}',(HERE/'hash.h').read_text())
    s=once(s,'unsigned int step,side=0,dist=1024,height,y;int material=1,top,bottom;', 'unsigned int step,side=0,dist=1024,height,y;int material=1,top,bottom;unsigned int pixel;unsigned char color;')
    s=once(s,' for(y=0;y<RAY_H;y++)s->back[y*RAY_W+col]=(int)y<top?0:((int)y>=bottom?1:2+(material-1)*2+side);', ''' /* Three clipped runs avoid reclassifying every pixel. Same column order. */
 if(top<0)top=0;
 if(top>RAY_H)top=RAY_H;
 if(bottom<0)bottom=0;
 if(bottom>RAY_H)bottom=RAY_H;
 color=2+(material-1)*2+side;pixel=col;
 for(y=0;y<(unsigned int)top;y++,pixel+=RAY_W)s->back[pixel]=0;
 for(;y<(unsigned int)bottom;y++,pixel+=RAY_W)s->back[pixel]=color;
 for(;y<RAY_H;y++,pixel+=RAY_W)s->back[pixel]=1;''')
    return s
