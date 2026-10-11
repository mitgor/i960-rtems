/* FNV-1a in the original byte order, four serial updates per RAM word.
 * Keep the multiply unchanged; do not replace validation with a hash. */
typedef unsigned int ray_hash_word __attribute__((__may_alias__));
static unsigned int hash(const unsigned char *p,unsigned int n)
{
 unsigned int h=2166136261u,w;
 while(n && ((unsigned long)p&3)){h=(h^*p++)*16777619u;n--;}
 while(n>=4){
  w=*(const ray_hash_word*)p;
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
  w=__builtin_bswap32(w);
#endif
  h=(h^(w&255))*16777619u;h=(h^((w>>8)&255))*16777619u;
  h=(h^((w>>16)&255))*16777619u;h=(h^(w>>24))*16777619u;
  p+=4;n-=4;
 }
 while(n--)h=(h^*p++)*16777619u;
 return h;
}
