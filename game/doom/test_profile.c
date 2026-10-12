/* Test the actual requested-byte accounting, independent of a Doom workload. */
#define main engine_profile_main
#include "profile.c"
#undef main
#include <assert.h>
pixel_t*DG_ScreenBuffer;
int gametic;
struct color colors[256];
void doomgeneric_Create(int argc,char**argv){(void)argc;(void)argv;}
void doomgeneric_Tick(void){}
void Z_CheckHeap(void){}
void DG_ZoneSample(void){}
int main(void){unsigned i;char*a=__wrap_malloc(17),*b=__wrap_calloc(3,11),*c;
 assert(a&&b&&live==50&&peak==50&&allocations==2);
 for(i=0;i<33;i++)assert(!b[i]);memset(a,0x39,17);
 a=__wrap_realloc(a,41);assert(a&&live==74&&peak==74&&largest==41);
 for(i=0;i<17;i++)assert(a[i]==0x39);
 __wrap_free(a);__wrap_free(b);assert(live==0&&allocations==frees);
 c=__wrap_strdup("Mylex");assert(c&&live==6&&!strcmp(c,"Mylex"));
 __wrap_free(c);__wrap_free(NULL);assert(live==0&&peak==74&&allocations==frees);
 assert(!__wrap_calloc((size_t)-1,2)&&failed==1&&live==0);
 puts("requested-byte accounting: allocation, zero, resize, preserve, free, strdup and overflow failure pass");return 0;
}
