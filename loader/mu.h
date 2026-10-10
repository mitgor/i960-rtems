#ifndef MU_H
#define MU_H
/* Shared loader protocol between the i960 flash loader (loader.c) and the host
 * sender (loadctl.c). The channel is the i960Rx Messaging Unit (MU): four 32-bit
 * registers that are plain hardware (independent of any firmware), so they work
 * the instant the loader runs - no DRAM, no memory-controller init.
 *
 * Register map (confirmed): the card's PG window maps i960 local 0x1300+X -> BAR0+X.
 *   i960 local   host BAR0   name   direction        meaning
 *   0x1310       +0x10       IMR0   host -> i960      command argument (a data word / address)
 *   0x1314       +0x14       IMR1   host -> i960      (seq<<16)|opcode   -- write IMR0 first, this commits
 *   0x1318       +0x18       OMR0   i960 -> host      (ackseq<<16)|status
 *   0x131C       +0x1C       OMR1   i960 -> host      read-back data (OP_READ)
 *
 * Handshake is a sequence number, not the doorbell bits, so it needs no interrupts
 * and does not depend on doorbell clear semantics. Host bumps seq in IMR1; loader
 * echoes the consumed seq in OMR0's high half. A sender must first synchronize
 * with OMR0/IMR1; restarting its counter at zero is NOT safe. See PROTOCOL.md.
 */
#define MU_LOCAL_BASE 0x1300u
#define R_IMR0 0x10
#define R_IMR1 0x14
#define R_OMR0 0x18
#define R_OMR1 0x1C

/* Stage 2 currently supports only the no-DRAM bring-up region. */
#ifdef POSTINIT_PROFILE
/* Experimental exclusive-ownership DRAM window; see postinit/README.md. */
#define PAYLOAD_BASE 0xC0120000u
#define PAYLOAD_END  0xC0130000u
#else
#define PAYLOAD_BASE 0x200u
#define PAYLOAD_END  0x400u
#endif
#define REG_BASE     0x1000u
#define REG_END      0x2000u
#define PAYLOAD_MAGIC 0xBEEF00EEu /* OMR1; OMR0 remains the GO acknowledgement */

static __inline__ int payload_word(unsigned int a)
{
    return !(a & 3u) && a >= PAYLOAD_BASE && a <= PAYLOAD_END - 4u;
}

static __inline__ int register_word(unsigned int a)
{
#ifdef POSTINIT_PROFILE
    (void)a;
    return 0; /* No arbitrary register access in the experimental loader. */
#else
    return !(a & 3u) && a >= REG_BASE && a <= REG_END - 4u &&
           !(a >= MU_LOCAL_BASE + R_IMR0 && a <= MU_LOCAL_BASE + R_OMR1);
#endif
}

#define OP_PING     1   /* arg ignored; just acks (liveness)                    */
#define OP_SET_ADDR 2   /* set the load pointer = arg                           */
#define OP_WRITE    3   /* store arg as a 32-bit word at load pointer; ptr += 4 */
#define OP_READ     4   /* read the word at arg into OMR1 (verify/debug)        */
#define OP_GO       5   /* jump to arg (never returns)                          */
#define OP_SET_REG_ADDR 6 /* explicit register-write mode; arg is local address */
#define OP_REG_WRITE    7 /* register word at selected pointer; no increment */
#define OP_REG_READ     8 /* explicit register read; arg is local address */

#define ST_READY 0x600Du  /* loader booted, waiting (OMR0 low half at reset) */
#define ST_OK    0x0002u
#define ST_BADOP 0x00EEu
#define ST_BADADDR 0x00EFu
#define ST_BADSTATE 0x00F0u
#define ST_HANDOFF 0x600Eu /* GO accepted; no more loader commands */
#endif
