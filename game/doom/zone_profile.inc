
/* Host-only occupancy scan after each allocation: no zone double counting. */
extern unsigned prof_zone_peak,prof_zone_static_peak,prof_zone_cache_peak,prof_zone_size,prof_zone_blocks;
void DG_ZoneSample(void){memblock_t*b;unsigned used=sizeof(*mainzone),fixed=sizeof(*mainzone),cache=0,count=0;if(!mainzone)return;
 prof_zone_size=mainzone->size;
 for(b=mainzone->blocklist.next;b!=&mainzone->blocklist;b=b->next){
  if(b->tag!=PU_FREE){used+=b->size;count++;if(b->tag>=PU_PURGELEVEL)cache+=b->size;else fixed+=b->size;}
 }
 if(used>prof_zone_peak)prof_zone_peak=used;
 if(fixed>prof_zone_static_peak)prof_zone_static_peak=fixed;
 if(cache>prof_zone_cache_peak)prof_zone_cache_peak=cache;
 if(count>prof_zone_blocks)prof_zone_blocks=count;
}
