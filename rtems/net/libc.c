#include <stddef.h>
void *memset(void *p,int c,size_t n){unsigned char*d=p;while(n--)*d++=c;return p;}
void *memcpy(void *d,const void*s,size_t n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
int memcmp(const void*a,const void*b,size_t n){const unsigned char*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;x++;y++;}return 0;}
size_t strlen(const char*p){const char*q=p;while(*q)q++;return q-p;}
int strcmp(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *(const unsigned char*)a-*(const unsigned char*)b;}
void *memmove(void*d,const void*s,size_t n){unsigned char*a=d;const unsigned char*b=s;if(a<b)return memcpy(d,s,n);while(n){n--;a[n]=b[n];}return d;}

int strncmp(const char*a,const char*b,size_t n){while(n){if(*a!=*b)return *(const unsigned char*)a-*(const unsigned char*)b;if(!*a)return 0;a++;b++;n--;}return 0;}
int atoi(const char*s){int n=0,sign=1;while(*s==' '||*s=='\t'||*s=='\n')s++;if(*s=='-'){sign=-1;s++;}else if(*s=='+')s++;while(*s>='0'&&*s<='9'){n=n*10+*s-'0';s++;}return n*sign;}
