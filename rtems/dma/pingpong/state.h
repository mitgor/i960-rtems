/* Opt-in session state. Addresses are supplied only by the owning kernel driver. */
static unsigned pp_bus[2],pp_slot,pp_started;
static volatile unsigned pp_active;
static volatile unsigned pp_gen[2],pp_release[2];
static volatile unsigned pp_marker[8];
static unsigned pp_count,pp_stalls,pp_system_audits;
#define PP_MAGIC 0x31505044u
#define PP_NEXT (fd_desc+8)
