/* Consume before publishing PARKED. Otherwise expiry can immediately re-enter
 * on the still-latched ENTER word at the next timer interrupt. */
static unsigned int monitor_take(unsigned int epoch){
 if(MONITOR_READ()!=(0x81000000u|epoch))return 0;
 MONITOR_WRITE(0);return MONITOR_READ()==0;
}
