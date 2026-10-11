/* Small bounded formatter: no printf, allocation, floating point or sensors. */
#ifndef CARD_SYSTEM_INFO_H
#define CARD_SYSTEM_INFO_H
struct info_writer {char *out;unsigned int size,used,failed;};
static void info_text(struct info_writer*w,const char*s){while(*s){if(w->used+1>=w->size){w->failed=1;if(w->size)w->out[w->used]=0;return;}w->out[w->used++]=*s++;}if(w->size)w->out[w->used]=0;}
static void info_number(struct info_writer*w,unsigned int v){char b[11];unsigned int n=0;do{b[n++]='0'+v%10;v/=10;}while(v);while(n){char c[2];c[0]=b[--n];c[1]=0;info_text(w,c);}}
static void info_row(struct info_writer*w,const char*label,unsigned int v){info_text(w,"<tr><th>");info_text(w,label);info_text(w,"</th><td>");info_number(w,v);info_text(w,"</td></tr>");}
static void system_info(struct info_writer*w,unsigned int seconds,unsigned int requests,unsigned int rx,unsigned int tx,unsigned int drops,unsigned int clients){
 info_text(w,"<section aria-labelledby=\"system\"><h2 id=\"system\">Card system information</h2><p>Live values from the Mylex card, not the Linux host. Refresh to update.</p><table><tbody><tr><th>Runtime uptime</th><td>");
 info_number(w,seconds/86400);info_text(w,"d ");info_number(w,seconds/3600%24);info_text(w,"h ");info_number(w,seconds/60%60);info_text(w,"m ");info_number(w,seconds%60);info_text(w,"s</td></tr>");
 info_text(w,"<tr><th>Operating system</th><td>RTEMS 4.6.6</td></tr><tr><th>TCP/IP stack</th><td>lwIP 2.1.3; IPv4 + IPv6</td></tr><tr><th>Board / CPU</th><td>Mylex DAC960 / Intel i960RP, 32-bit, no FPU</td></tr><tr><th>CPU frequency</th><td>Not measured. Timer bus: approximately 33.333 MHz (previously measured).</td></tr><tr><th>CPU load / temperature</th><td>Unavailable: no CPU idle accounting or card temperature sensor interface.</td></tr><tr><th>Memory configuration</th><td>16 MiB card DRAM; 512 KiB loader staging; 48 KiB RTEMS workspace; 48 KiB lwIP heap. These are capacities, not free-memory readings.</td></tr>");
#ifdef I960_BACKGROUND_NET
 info_text(w,"<tr><th>Clock</th><td>Hardware timer; nominal 100 ticks/s. Uptime starts when this runtime is loaded.</td></tr>");
#else
 info_text(w,"<tr><th>Clock</th><td>Host-supplied elapsed time; uptime starts when this runtime is loaded.</td></tr>");
#endif
 info_row(w,"HTTP page responses since startup",requests);info_row(w,"Open HTTP connections (maximum 4)",clients);info_row(w,"IP packets received",rx);info_row(w,"IP packets transmitted",tx);info_row(w,"Network drops",drops);
 info_text(w,"</tbody></table><p>Packets are relayed through the Linux host; these are card-interface counters, not NIC statistics. CPU-bound preemption experiments run separately from this web runtime.</p><p><a href=\"/\">Refresh system information</a></p></section>");
}
#endif
