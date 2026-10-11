"""Exact target-only slot helpers and separately selected bounded diagnostics."""
from pathlib import Path
from combined.optimize import once
GAME=Path(__file__).resolve().parents[1]

def header(s,mode):
 assert mode in ('byte','hash','words')
 if mode=='byte':return s
 old='static inline unsigned int fq_hash(const unsigned char*p,unsigned int n){unsigned int h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}'
 new=(GAME/'callback/hash.h').read_text().replace('ray_hash_word','fq_hash_word').replace('static unsigned int hash(', 'static inline unsigned int fq_hash(')
 s=once(s,old,new)
 if mode=='words':
  uniform=(GAME/'callback/uniform.h').read_text().replace('bio_scan_word','fq_scan_word').replace('bio_uniform','fq_uniform')
  s=once(s,'/* Shared pure validation',uniform+'\n/* Shared pure validation')
  s=once(s,' unsigned int i;\n if(!epoch',' if(!epoch')
  s=once(s,' for(i=32;i<64;i++)if(p[i]!=0xa5)return 0;\n for(i=64+FQ_FRAME;i<FQ_SLOT_SIZE;i++)if(p[i]!=0x5a)return 0;',
   ' if(!fq_uniform(p+32,32,0xa5)||!fq_uniform(p+64+FQ_FRAME,FQ_SLOT_SIZE-64-FQ_FRAME,0x5a))return 0;')
  old='static inline unsigned int fq_word(const unsigned char*p){return (unsigned int)p[0]|(unsigned int)p[1]<<8|(unsigned int)p[2]<<16|(unsigned int)p[3]<<24;}'
  new='''typedef unsigned int fq_meta_word __attribute__((__may_alias__));
static inline unsigned int fq_word(const unsigned char*p){
 if(!((unsigned long)p&3)){
  unsigned int w=*(const fq_meta_word*)p;
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
  w=__builtin_bswap32(w);
#endif
  return w;
 }
 return (unsigned int)p[0]|(unsigned int)p[1]<<8|(unsigned int)p[2]<<16|(unsigned int)p[3]<<24;
}'''
  s=once(s,old,new)
 return s

def diagnostic(s):
 s=once(s,'if(op>4||slot>1||!epoch||(op!=4&&fq_word(in+20))', 'if(op>5||slot>1||!epoch||(op!=4&&op!=5&&fq_word(in+20))')
 s=once(s,'  if(op==1||op==4){', '''  if(op==5){
   unsigned int which=fq_word(in+20);
   if(gen>32||(which!=1&&which!=2)){status=FQ_BAD;goto done;}
   if(!(s->mask&(1u<<slot))){status=FQ_STALE;goto done;}
   p=slots+slot*FQ_SLOT_SIZE;
   for(i=0;i<gen;i++){
    /* Compiler barrier prevents invariant hoisting. No timer/IRQ is borrowed.
     * Each result is checked; benchmark success is the ordinary descriptor. */
    __asm__ volatile("":::"memory");
    if(which==1){if(fq_hash(p+64,FQ_FRAME)!=fq_word(p+20)){status=FQ_CORRUPT;goto done;}}
    else if(!fq_valid(p,s->epoch,s->gen[slot],slot)){status=FQ_CORRUPT;goto done;}
   }
  }else if(op==1||op==4){''')
 return s
