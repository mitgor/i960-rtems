/* Transport-neutral, one-slot polled control protocol. No hardware addresses. */
#ifndef I960_CONTROL_H
#define I960_CONTROL_H
typedef unsigned int ctl_u32;
typedef char ctl_word_must_be_32_bits[(sizeof(ctl_u32)==4)?1:-1];
#define CTL_MAGIC 0x314c5443u
#define CTL_VERSION 1u
#define CTL_WORDS 16
#define CTL_STATUS 0u
#define CTL_PING 1u
#define CTL_STOP 2u
#define CTL_OK 0u
#define CTL_BAD_FRAME 1u
#define CTL_BAD_EPOCH 2u
#define CTL_BAD_SEQUENCE 3u
#define CTL_BAD_OPERATION 4u
#define CTL_NOT_QUIESCENT 5u
#define CTL_STOPPED 6u
struct ctl_state {ctl_u32 epoch, sequence, heartbeat, stopped;};
/* Implementations MUST provide platform visibility/ordering, not just volatile.
 * Called around snapshots and commit publication. Host does the same. */
struct ctl_hooks {void (*barrier)(void *); int (*quiesce)(void *); void *arg;};
ctl_u32 ctl_checksum(const ctl_u32 *words, unsigned int count);
int ctl_init(struct ctl_state *, ctl_u32 epoch);
void ctl_tick(struct ctl_state *);
/* req/resp point to separate 64-byte slots with single-writer ownership.
 * Returns 0 for empty/duplicate/torn request, 1 when a response is published.
 * No scheduling, MMIO, DMA, cache, masking or timer side effects occur here. */
int ctl_poll(struct ctl_state *, volatile ctl_u32 *req,
             volatile ctl_u32 *resp, const struct ctl_hooks *);
#endif
