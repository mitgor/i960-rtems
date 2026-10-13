/* Immutable post-return frame archive. Allocated only after private engine
 * allocations retire; never exposes arbitrary addresses or a live renderer. */
#ifdef ENGINE_VISIBLE_OFFSET
static struct arena *frame_arena;
static unsigned frame_handle,frame_serial,frame_selected,frame_offset,frame_window;
static unsigned char *volatile frame_bytes;
static unsigned frame_release(void){unsigned h=frame_handle;frame_bytes=0;frame_selected=frame_window=0;
 if(h){if(!arena_unpin(frame_arena,h)||!arena_release(frame_arena,h))return 0;frame_handle=0;}return 1;}
static unsigned frame_copy(struct seg_image*s){unsigned i,h;unsigned char*p;
 if(!digest(s,ENGINE_VISIBLE_OFFSET,131072,engine_visible_sha,0))return 0;
 if(frame_handle||frame_serial==~0u||!doom_shared_enter((void*)1))return 0;
 h=arena_alloc(s->arena,131072);p=h?arena_pin(s->arena,h):0;doom_shared_leave((void*)1);if(!p)return 0;
 frame_handle=h;frame_arena=s->arena;
 for(i=0;i<131072;i++){p[i]=s->base[ENGINE_VISIBLE_OFFSET+i];if(!(i&1023))doom_shared_yield();}
 frame_serial++;frame_bytes=p;return 1;
}
unsigned engine_frame_control(unsigned op,unsigned index,unsigned value){
 if(!frame_bytes)return ~0u;
 if(op==0x6c){frame_selected=frame_window=0;if(index||value!=frame_serial)return ~0u;frame_selected=value;return 0;}
 if(frame_selected!=frame_serial)return ~0u;
 if(op==0x6d){frame_window=0;if(index||(value&1023)||value>131072-1024)return ~0u;frame_offset=value;frame_window=1;return 0;}
 if(op==0x6e&&frame_window&&index<256&&!value)return word(frame_bytes+frame_offset+index*4);
 return ~0u;
}
unsigned engine_frame_finish(void){return frame_release();}
#else
unsigned engine_frame_control(unsigned op,unsigned index,unsigned value){(void)op;(void)index;(void)value;return ~0u;}
unsigned engine_frame_finish(void){return 1;}
#endif
