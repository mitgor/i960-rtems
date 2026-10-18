/* Original PG free-running downcounter; elapsed ticks are begin minus end. */
unsigned doom_platform_wall_clock(void){return *(volatile unsigned*)0xff000304u;}
unsigned doom_platform_wall_clock_faults(void){return 0;}
