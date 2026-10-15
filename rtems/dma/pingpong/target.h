extern unsigned upload_time(void);
static unsigned pp_control(unsigned index,unsigned value){unsigned slot;
 if(index==8||index==9){
  slot=index-8;
  if(pp_active||play_api||pp_bus[slot]||value<4096||value>0xffffffffu-69632)return ~0u;
  if(pp_bus[slot^1] && !(value+69632<=pp_bus[slot^1]-4096 || pp_bus[slot^1]+69632<=value-4096))return ~0u;
  pp_bus[slot]=value;return 0;
 }
 if(index==10){if(value!=1||pp_active||!pp_bus[0]||!pp_bus[1]||fd_phase==1)return ~0u;pp_active=1;return 0;}
 if(index==11){slot=(value-1)&1;if(!pp_active||!value||pp_gen[slot]!=value||pp_release[slot])return ~0u;pp_release[slot]=value;return 0;}
 if(index==12){switch(value){case 0:return pp_count;case 1:return pp_stalls;case 2:return pp_gen[0];case 3:return pp_gen[1];case 4:return fd_phase;case 5:return upload_time()*10u;case 6:return pp_system_audits;default:return ~0u;}}
 return ~0u;
}
static void pp_service(void){unsigned i;
 if(!pp_active){fd_step();return;}
 if(fd_phase==1)fd_step();
 if(fd_phase==2&&play_frame&&play_sequence==fd_report[2]&&!play_ack){play_ack=1;pp_count++;}
 /* Never recycle either destination until the channel has been quiesced. */
 if(fd_phase!=1)for(i=0;i<2;i++)if(pp_gen[i]&&pp_release[i]==pp_gen[i]){pp_release[i]=0;pp_gen[i]=0;}
 if(!play_frame||play_ack||play_api->stopping()||fd_phase==1)return;
 i=(play_sequence-1)&1;
 if(pp_gen[i]){pp_stalls++;return;}
 pp_slot=i;pp_gen[i]=play_sequence;fd_destination=pp_bus[i];fd_no_crc=1;
 fd_report[0]=0x314d4446;fd_report[2]=play_sequence;fd_report[3]=fd_destination;
 fd_report[4]=FD_ADDR(play_frame);fd_report[13]=0;fd_report[14]=1;
 pp_marker[0]=PP_MAGIC;pp_marker[1]=play_sequence;pp_marker[2]=i;pp_marker[3]=65536;
 pp_marker[4]=FD_ADDR(play_frame);pp_marker[5]=play_api->io.ticks_ms();pp_marker[6]=~play_sequence;pp_marker[7]=play_sequence;
 pp_started=pp_marker[5];fd_stage=0;__asm__ volatile("":::"memory");fd_phase=1;
 fd_step(); /* prepare/kick only; return to render the other card buffer */
}

unsigned frame_dma_report_snapshot(unsigned*w){
 if(!frame_dma_isolation_snapshot(w))return 0;
 pp_system_audits++;return 1;
}
