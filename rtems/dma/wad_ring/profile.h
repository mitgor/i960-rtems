/* Read-only timer 0 profiling. The exclusive shared heap already owns and
 * starts this bus/8 downcounter. No timer programming or IRQ masking here.
 * Totals are elapsed time including interrupts, not task CPU cycles. */
#ifdef I960_WAD_PROFILE
#ifndef WR_COUNTER
#define WR_COUNTER() (*(volatile unsigned*)0xff000304u)
#endif
static unsigned wp_stats[19][3],wp_bench,wp_done;
static unsigned wp_now(void){return WR_COUNTER();}
static void wp_add(unsigned k,unsigned start){unsigned d=start-wp_now(),old=wp_stats[k][1];wp_stats[k][0]++;wp_stats[k][1]+=d;if(wp_stats[k][1]<old)wp_stats[k][2]++;}
static unsigned wp_report(unsigned i){
 if(owned_running||wr||leases)return ~0u;
 if(i==0)return 0x31525057u;if(i==1)return
#ifdef I960_PEER_YIELD
 4;
#else
 2;
#endif
 if(i==2)return 4166700u;
 if(i==3)return wp_done;if(i==4)return 64;if(i==5)return WR_BLOCK;
#ifdef I960_PEER_YIELD
 if(i==6||i==7){extern unsigned exclusive_peer_report(unsigned);return exclusive_peer_report(i-6);}
#endif
 if(i<8)return 0;return i<65?wp_stats[(i-8)/3][(i-8)%3]:~0u;
}
#define WP_START(name) unsigned name=wp_now()
#define WP_ADD(k,name) wp_add(k,name)
#else
#define WP_START(name)
#define WP_ADD(k,name)
#endif
