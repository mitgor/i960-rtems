/* Offline candidate policy, not a runtime RAM grant. No target writes use this.
 * A future exclusive profile may request this fixed cache-data subrange only
 * after physical topology/reset validation, dependency audit and alias testing.
 * Default ram_reclaim() remains unconditionally false. */
#ifndef RESIDENT_RAM_TRANSFER_H
#define RESIDENT_RAM_TRANSFER_H
#define RAM_TRANSFER_BASE 0xc0200000u
#define RAM_TRANSFER_BYTES 0x40000u
#define RAM_TRANSFER_GUARD 64u
struct ram_transfer_evidence {
 unsigned int topology,reset_held,secondary_disabled,dma_idle,cpu_exclusive;
 unsigned int dependencies_checked,capacity_checked,patterns_checked;
};
static unsigned int ram_transfer_admit(const struct ram_transfer_evidence*e){
 if(e->topology!=0x31504353u)return 1;
 if(e->reset_held!=1||e->secondary_disabled!=1||e->dma_idle!=1)return 2;
 if(e->cpu_exclusive!=1||e->dependencies_checked!=1)return 3;
 if(e->capacity_checked!=1||e->patterns_checked!=1)return 4;
 return 0;
}
static unsigned int ram_transfer_range(const struct ram_transfer_evidence*e,unsigned int start,unsigned int bytes){
 const unsigned int lo=RAM_TRANSFER_BASE+RAM_TRANSFER_GUARD;
 const unsigned int hi=RAM_TRANSFER_BASE+RAM_TRANSFER_BYTES-RAM_TRANSFER_GUARD;
 if(ram_transfer_admit(e))return 0;
 return bytes&&start>=lo&&start<hi&&bytes<=hi-start;
}
#endif
