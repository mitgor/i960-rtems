#ifndef ACCELE_APP_SERVICE_H
#define ACCELE_APP_SERVICE_H
/* Two bundled, bounded applications; single lwIP/Init owner, no new task or
 * heap. Control packets use an impossible IP version and never drain IP output.
 * Generation checks prevent delayed STOP/run against a replacement lifetime. */
#define AS_MAGIC 0x505041f1u
struct as_app {unsigned generation,running,updates,ms,requests,stops;};
static struct as_app as_apps[2];
static unsigned as_errors;
static unsigned as_word(const unsigned char *p){return p[0]|p[1]<<8|p[2]<<16|(unsigned)p[3]<<24;}
static void as_put(unsigned char *p,unsigned v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
static void as_step(unsigned ms){unsigned i;for(i=0;i<2;i++)if(as_apps[i].running){as_apps[i].updates++;as_apps[i].ms+=ms;}}
static unsigned as_call(const unsigned char *in,unsigned n,unsigned char *out,unsigned cap){
 unsigned id=0,op=0,gen=0,status=0,i,len=0;struct as_app *a=0;
 if(cap<304)return 0xffffffffu;
 if(n<20||n>276||as_word(in)!=AS_MAGIC||as_word(in+4)!=1){status=1;goto reply;}
 op=as_word(in+8);id=as_word(in+12);gen=as_word(in+16);
 if(id<1||id>2){status=2;goto reply;}a=&as_apps[id-1];
 if(op<1||op>4||(op!=4&&n!=20)){status=3;goto reply;}
 if(op!=3&&gen!=a->generation){status=4;goto reply;}
 if(op==1){
  if(a->running){status=5;goto reply;}
  if(a->generation==~0u){status=6;goto reply;}
  a->generation++;a->running=1;a->updates=a->ms=a->requests=0;
 }else if(op==2){if(a->running){a->running=0;a->stops++;}}
 else if(op==4){
  if(id!=2||!a->running){status=7;goto reply;}
  len=n-20;for(i=0;i<len;i++){unsigned char c=in[20+i];out[48+i]=(c>='a'&&c<='z')?c-32:c;}a->requests++;
 }
reply:
 if(status)as_errors++;
 as_put(out,0x525041f1u);as_put(out+4,1);as_put(out+8,status);as_put(out+12,id);
 as_put(out+16,a?a->generation:0);as_put(out+20,a?a->running:0);
 as_put(out+24,a?a->updates:0);as_put(out+28,a?a->ms:0);
 as_put(out+32,a?a->requests:0);as_put(out+36,a?a->stops:0);
 as_put(out+40,as_errors);as_put(out+44,len);return 48+len;
}
#endif
