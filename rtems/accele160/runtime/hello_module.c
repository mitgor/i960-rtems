static unsigned int initialized,calls;
unsigned int accele_net_entry(unsigned int op,unsigned int ms,const unsigned char *in,
 unsigned int n,unsigned char *out,unsigned int cap){
 const char *s="Hello from Accele160 RTEMS segmented application\n";unsigned int i=0;
 (void)ms;(void)in;(void)n;
 if(op==0){if(initialized)return ~0u;initialized=1;return 0;}
 if(!initialized)return ~0u;
 if(op==1)return 0;
 if(op==2){calls++;while(s[i]&&i<cap){out[i]=s[i];i++;}return i;}
 if(op==3){if(cap<4)return ~0u;for(i=0;i<4;i++)out[i]=(calls>>(8*i))&255;return 4;}
 return ~0u;
}
