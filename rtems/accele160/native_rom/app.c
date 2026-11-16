/* Native-ROM RTEMS diagnostic. The default build publishes a scheduler result
 * and read-only host-startup sample. Explicit offline flags add mailbox
 * ingestion, local reply composition, and an emulator-only DMA1 prototype. */
#include "host_startup.h"
#ifdef ACCELE160_READ_ROM_MAILBOX
#include "host_mailbox.h"
#ifndef ACCELE160_OBSERVE_HOST_EVENTS
#error ROM mailbox observation requires host-event observation
#endif
#ifdef ACCELE160_COMPOSE_CTLR_INFO
#include "controller_info.h"
#ifndef ACCELE160_READ_ROM_MAILBOX
#error Controller-info composition requires ROM mailbox ingestion
#endif
#ifdef ACCELE160_EMULATOR_DMA1_REPLY
#ifndef ACCELE160_COMPOSE_CTLR_INFO
#error Emulator DMA1 reply requires controller-info composition
#endif
#endif
#ifdef ACCELE160_EMULATOR_IOCTL11
#ifndef ACCELE160_EMULATOR_DMA1_REPLY
#error IOCTL 0x11 requires emulator DMA1 reply support
#endif
#endif
#ifdef ACCELE160_EMULATOR_IOCTL15
#ifndef ACCELE160_EMULATOR_IOCTL11
#error IOCTL 0x15 requires prior ROM request support
#endif
#endif
#ifdef ACCELE160_EMULATOR_IOCTLD0
#ifndef ACCELE160_EMULATOR_IOCTL15
#error IOCTL 0xd0 requires prior ROM request support
#endif
#endif
#ifdef ACCELE160_EMULATOR_IOCTL2D
#ifndef ACCELE160_EMULATOR_IOCTLD0
#error IOCTL 0x2d requires prior ROM request support
#endif
#endif
#ifdef ACCELE160_EMULATOR_SET_MBOX
#ifndef ACCELE160_EMULATOR_IOCTL2D
#error SET_MEM_MBOX requires the five option-ROM replies
#endif
#endif
#ifdef ACCELE160_EMULATOR_RING_OBSERVER
#ifndef ACCELE160_EMULATOR_SET_MBOX
#error Ring observation requires SET_MEM_MBOX setup
#endif
#endif
#ifdef ACCELE160_EMULATOR_RING_REPLY
#ifndef ACCELE160_EMULATOR_RING_OBSERVER
#error Ring reply requires validated first-slot observation
#endif
#endif
#endif
#endif
#include <rtems/system.h>
#include <rtems/rtems/options.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>

extern unsigned char _bss_start[], _bss_end[];
extern void native_park(unsigned int code) __attribute__((noreturn));
static unsigned char workspace[32768] __attribute__((aligned(16)));
static volatile unsigned int * const report = (volatile unsigned int *)0xc0001f00u;
static volatile unsigned int worker_count, init_count, done;
static rtems_id worker_id;
#ifdef ACCELE160_READ_ROM_MAILBOX
static unsigned int ingress_state, ingress_digest;
static accele160_controller_info_request ingress_request;
#ifdef ACCELE160_COMPOSE_CTLR_INFO
static unsigned char composed_reply[ACCELE160_CONTROLLER_INFO_BYTES];
static unsigned int reply_state, reply_digest;
#ifdef ACCELE160_EMULATOR_DMA1_REPLY
static unsigned int dma_state;
/* GCC 3.3 COFF caps object alignment at 16; align inside this storage. */
static unsigned int dma_descriptor_storage[16];
#ifdef ACCELE160_EMULATOR_IOCTL11
static unsigned int handled_count, current_ioctl, attempted_count;
#ifdef ACCELE160_EMULATOR_SET_MBOX
static accele160_mem_mbox_request mem_mbox_request;
#ifdef ACCELE160_EMULATOR_RING_OBSERVER
static unsigned int ring_state, ring_digest, ring_cursor;
static unsigned int ring_output_bus, ring_output_bytes, ring_command_id;
static unsigned int ring_seen_bits;
#ifdef ACCELE160_EMULATOR_RING_REPLY
static unsigned char ring_composed_reply[ACCELE160_RING_CONTROLLER_INFO_BYTES];
static unsigned int ring_completion_count, ring_reply_digest;
static unsigned int ring_dma_state, ring_status_word0, ring_status_word1;
#ifdef ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER
static unsigned int followup_events, followup_slot_index, followup_slot_address;
static unsigned int followup_digest, followup_state, followup_id;
static unsigned int followup_ioctl, followup_output, followup_bytes;
#ifdef ACCELE160_EMULATOR_RING_HEALTH_REPLY
static unsigned int health_reply_state, health_dma_state, health_status_word0;
#ifdef ACCELE160_EMULATOR_RING_PDEV_REPLY
static unsigned int pdev_reply_state, pdev_dma_state, pdev_status_word0;
#ifdef ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY
static unsigned int repeat_reply_state, repeat_dma_state, repeat_status_word0;
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif

static unsigned int expected_reply_bytes(void)
{
#ifdef ACCELE160_EMULATOR_IOCTL11
    if (current_ioctl == 0x11u) return 128u;
#endif
#ifdef ACCELE160_EMULATOR_IOCTL15
    if (current_ioctl == 0x15u) return 64u;
#endif
#ifdef ACCELE160_EMULATOR_IOCTLD0
    if (current_ioctl == 0xd0u) return 128u;
#endif
#ifdef ACCELE160_EMULATOR_IOCTL2D
    if (current_ioctl == 0x2du) return 512u;
#endif
    return ACCELE160_CONTROLLER_INFO_BYTES;
}

/* Diagnostic only. The emulator accepts this exact descriptor shape and
 * captured ROM output address. The physical PCI DMA mapping is unverified. */
static void transfer_rom_reply(void)
{
    volatile unsigned int * const ndar1 = (volatile unsigned int *)0x1450u;
    volatile unsigned int * const ccr1 = (volatile unsigned int *)0x1440u;
    volatile unsigned int * const csr1 = (volatile unsigned int *)0x1444u;
    unsigned int *dma_descriptor = (unsigned int *)
        (((unsigned int)dma_descriptor_storage + 31u) & ~31u);
    unsigned int i;
    if (ingress_request.output_bus_address != 0x0009f3e0u ||
        ingress_request.output_bytes != expected_reply_bytes() ||
        ingress_request.command_id != 0x7fu) {
        dma_state = 0x101u;
        return;
    }
    dma_descriptor[0] = 0u;
    dma_descriptor[1] = ingress_request.output_bus_address;
    dma_descriptor[2] = 0u;
    dma_descriptor[3] = (unsigned int)composed_reply;
    dma_descriptor[4] = ingress_request.output_bytes;
    dma_descriptor[5] = 0x3fu;
    dma_descriptor[6] = 0u;
    dma_descriptor[7] = 0u;
    __asm__ volatile("syncf" ::: "memory");
    *ndar1 = (unsigned int)dma_descriptor;
    *ccr1 = 1u;
    for (i = 0; i < 10000u && ((*csr1 & 0x100u) == 0u); ++i) { }
    if ((*csr1 & 0x100u) == 0u) {
        *ccr1 = 0u;
        dma_state = 0x102u;
        return;
    }
    *ccr1 = 0u;
    *csr1 = 0x100u; /* write-one-to-clear end-of-chain status */
    __asm__ volatile("syncf" ::: "memory");
    *(volatile unsigned int *)0x1320u = 3u; /* ACK captured inbound bits */
    *(volatile unsigned int *)0x1318u = ingress_request.command_id;
    *(volatile unsigned int *)0x131cu =
#ifdef ACCELE160_EMULATOR_IOCTL11
        current_ioctl == 0x01u ? 0xfffffe00u : 0u;
#else
        0xfffffe00u;
#endif
    __asm__ volatile("syncf" ::: "memory");
    *(volatile unsigned int *)0x132cu = 1u;
    dma_state = 2u;
#ifdef ACCELE160_EMULATOR_IOCTL11
    ++handled_count;
#endif
}

#ifdef ACCELE160_EMULATOR_SET_MBOX
/* Offline SET_MEM_MBOX acknowledgement only. The ring pointers are retained
 * for observation; no guest ring DMA, status entry or command is touched. */
static void complete_set_mem_mbox(void)
{
    *(volatile unsigned int *)0x1320u = 3u; /* ACK captured inbound bits */
    *(volatile unsigned int *)0x1318u = mem_mbox_request.command_id;
    *(volatile unsigned int *)0x131cu = 0x420u; /* observed stock OMR1 */
    __asm__ volatile("syncf" ::: "memory");
    *(volatile unsigned int *)0x132cu = 1u;
    reply_state = 2u;
    reply_digest = 0u;
    dma_state = 3u; /* no output DMA for this command */
    ++handled_count;
}
#endif
#endif

static void compose_rom_reply(void)
{
    unsigned char descriptor[0x390], product[16];
    volatile unsigned char *flash = (volatile unsigned char *)0xfef00000u;
    unsigned int i, result;
#ifdef ACCELE160_EMULATOR_IOCTL11
    if (current_ioctl == 0x11u)
        result = accele160_compose_ioctl11(composed_reply,
                                           ingress_request.output_bytes);
    else
#endif
#ifdef ACCELE160_EMULATOR_IOCTL15
    if (current_ioctl == 0x15u)
        result = accele160_compose_ioctl15(composed_reply,
                                           ingress_request.output_bytes);
    else
#endif
#ifdef ACCELE160_EMULATOR_IOCTLD0
    if (current_ioctl == 0xd0u)
        result = accele160_compose_ioctld0(composed_reply,
                                           ingress_request.output_bytes);
    else
#endif
#ifdef ACCELE160_EMULATOR_IOCTL2D
    if (current_ioctl == 0x2du) {
        for (i = 0; i < 512u; ++i)
            descriptor[i] = flash[0xe0000u + i];
        result = accele160_compose_ioctl2d(composed_reply,
                                           ingress_request.output_bytes,
                                           descriptor, 512u);
    } else
#endif
    {
        /* The stock reset block maps the first flash bank here. */
        for (i = 0; i < sizeof(descriptor); ++i)
            descriptor[i] = flash[0xe0000u + i];
        for (i = 0; i < sizeof(product); ++i)
            product[i] = flash[0xf0040u + i];
        result = accele160_compose_controller_info(
            composed_reply, sizeof(composed_reply), descriptor,
            sizeof(descriptor), product, sizeof(product));
    }
    if (result) {
        reply_state = 0x100u + result;
        return;
    }
    reply_digest = 2166136261u;
    for (i = 0; i < ingress_request.output_bytes; ++i)
        reply_digest = (reply_digest ^ composed_reply[i]) * 16777619u;
    reply_state = 2u; /* composed locally; transfer is separately gated */
#ifdef ACCELE160_EMULATOR_DMA1_REPLY
    transfer_rom_reply();
#endif
}
#endif

/* The bounded QEMU ROM places its first mailbox at 0x9f120. Requiring that
 * exact address keeps this diagnostic from dereferencing an arbitrary host
 * pointer. This is not a general host-DMA transport. */
static void ingest_rom_mailbox(unsigned int message0,
                               unsigned int message1)
{
    unsigned char bytes[64];
    volatile unsigned char *source;
    unsigned int i, parsed;
#ifdef ACCELE160_EMULATOR_IOCTL11
    ++attempted_count;
#endif
    if (message1 != 0u ||
#ifdef ACCELE160_EMULATOR_SET_MBOX
        (handled_count == 5u ?
         (message0 < 0x00100000u || (message0 & 0xfffu) != 0u ||
          message0 > 0x20000000u - 64u) :
         message0 != 0x0009f120u)
#else
        message0 != 0x0009f120u
#endif
        ) {
        ingress_state = 0x200u;
        return;
    }
    source = (volatile unsigned char *)message0;
    __asm__ volatile("syncf" ::: "memory");
    ingress_digest = 2166136261u;
    for (i = 0; i < sizeof(bytes); ++i) {
        bytes[i] = source[i];
        ingress_digest = (ingress_digest ^ bytes[i]) * 16777619u;
    }
    parsed =
#ifdef ACCELE160_EMULATOR_SET_MBOX
        handled_count == 5u ? accele160_parse_set_mem_mbox(
            bytes, sizeof(bytes), &mem_mbox_request) :
#endif
#ifdef ACCELE160_EMULATOR_IOCTL2D
        handled_count == 4u ? accele160_parse_ioctl2d(
            bytes, sizeof(bytes), &ingress_request) :
#endif
#ifdef ACCELE160_EMULATOR_IOCTLD0
        handled_count == 3u ? accele160_parse_ioctld0(
            bytes, sizeof(bytes), &ingress_request) :
#endif
#ifdef ACCELE160_EMULATOR_IOCTL15
        handled_count == 2u ? accele160_parse_ioctl15(
            bytes, sizeof(bytes), &ingress_request) :
#endif
#ifdef ACCELE160_EMULATOR_IOCTL11
        handled_count == 1u ? accele160_parse_ioctl11(
            bytes, sizeof(bytes), &ingress_request) :
#endif
        accele160_parse_controller_info(bytes, sizeof(bytes),
                                       &ingress_request);
    ingress_state = parsed == ACCELE160_MAILBOX_OK ? 2u : 0x100u + parsed;
#ifdef ACCELE160_EMULATOR_IOCTL11
    if (parsed == ACCELE160_MAILBOX_OK) {
        current_ioctl = bytes[21];
#ifdef ACCELE160_EMULATOR_SET_MBOX
        if (current_ioctl == 0x8eu) {
            ingress_request.command_id = mem_mbox_request.command_id;
            ingress_request.output_bus_address = 0u;
            ingress_request.output_bytes = 0u;
        }
#endif
    }
#endif
#ifdef ACCELE160_COMPOSE_CTLR_INFO
    if (ingress_state == 2u) {
#ifdef ACCELE160_EMULATOR_SET_MBOX
        if (current_ioctl == 0x8eu) complete_set_mem_mbox();
        else
#endif
        compose_rom_reply();
    }
#endif
}

#ifdef ACCELE160_EMULATOR_RING_OBSERVER
/* One exact first-ring response, behind a separate offline feature flag.
 * The interpreter models DMA1 output and local aliases for the negotiated
 * guest slot/status windows; physical host DMA/address translation is not
 * established. A failure never posts a status entry or ODB notification. */
#ifdef ACCELE160_EMULATOR_RING_REPLY
static void complete_first_ring_info(void)
{
    unsigned char descriptor[0x390], product[16], status[8];
    volatile unsigned char *flash = (volatile unsigned char *)0xfef00000u;
    volatile unsigned int * const ndar1 = (volatile unsigned int *)0x1450u;
    volatile unsigned int * const ccr1 = (volatile unsigned int *)0x1440u;
    volatile unsigned int * const csr1 = (volatile unsigned int *)0x1444u;
    volatile unsigned int *status_ring;
    volatile unsigned int *command_slot;
    unsigned int *dma_descriptor = (unsigned int *)
        (((unsigned int)dma_descriptor_storage + 31u) & ~31u);
    unsigned int i, result;
    if (ring_output_bytes != ACCELE160_RING_CONTROLLER_INFO_BYTES ||
        ring_command_id != 1u ||
        ring_cursor != mem_mbox_request.command_ring_bus) {
        ring_state = 0x201u;
        return;
    }
    for (i = 0; i < sizeof(descriptor); ++i)
        descriptor[i] = flash[0xe0000u + i];
    for (i = 0; i < sizeof(product); ++i)
        product[i] = flash[0xf0040u + i];
    result = accele160_compose_first_ring_info(
        ring_composed_reply, sizeof(ring_composed_reply),
        descriptor, sizeof(descriptor), product, sizeof(product));
    if (!result)
        result = accele160_compose_first_ring_status(status, sizeof(status));
    if (result) {
        ring_state = 0x200u + result;
        return;
    }
    ring_reply_digest = 2166136261u;
    for (i = 0; i < sizeof(ring_composed_reply); ++i)
        ring_reply_digest =
            (ring_reply_digest ^ ring_composed_reply[i]) * 16777619u;
    dma_descriptor[0] = 0u;
    dma_descriptor[1] = ring_output_bus;
    dma_descriptor[2] = 0u;
    dma_descriptor[3] = (unsigned int)ring_composed_reply;
    dma_descriptor[4] = sizeof(ring_composed_reply);
    dma_descriptor[5] = 0x3fu;
    dma_descriptor[6] = 0u;
    dma_descriptor[7] = 0u;
    __asm__ volatile("syncf" ::: "memory");
    *ndar1 = (unsigned int)dma_descriptor;
    *ccr1 = 1u;
    for (i = 0; i < 10000u && ((*csr1 & 0x100u) == 0u); ++i) { }
    if ((*csr1 & 0x100u) == 0u) {
        *ccr1 = 0u;
        ring_dma_state = 0x102u;
        ring_state = 0x302u;
        return;
    }
    *ccr1 = 0u;
    *csr1 = 0x100u; /* EOC W1C */
    ring_dma_state = 2u;
    status_ring = (volatile unsigned int *)mem_mbox_request.status_ring_bus;
    command_slot = (volatile unsigned int *)ring_cursor;
    /* These model guest windows were registered from the validated 0x8e and
     * first-slot addresses. The status entry is little-endian ID/status 1/0
     * and signed residual -20, matching repeated stock model captures. */
    status_ring[0] = (unsigned int)status[0] |
                     ((unsigned int)status[1] << 8) |
                     ((unsigned int)status[2] << 16) |
                     ((unsigned int)status[3] << 24);
    status_ring[1] = (unsigned int)status[4] |
                     ((unsigned int)status[5] << 8) |
                     ((unsigned int)status[6] << 16) |
                     ((unsigned int)status[7] << 24);
    *command_slot = 0u;
    ring_status_word0 = status_ring[0];
    ring_status_word1 = status_ring[1];
    ring_cursor += 64u;
    *(volatile unsigned int *)0x1320u = 0x10u; /* ACK ring inbound bit */
    __asm__ volatile("syncf" ::: "memory");
    *(volatile unsigned int *)0x132cu = 2u; /* observed stock ring ODB */
    ring_completion_count = 1u;
    ring_state = 3u;
}
#endif
/* The interpreter aliases only the staged 64-byte guest slot at this DMA
 * address. Direct local reads are an exploratory model convenience, not a
 * proved physical i960 DMA mapping. The observer alone writes no ring data;
 * the separate reply gate writes only after a validated DMA1 transfer. */
static void observe_first_ring_slot(unsigned int inbound_bits)
{
    unsigned char bytes[64];
    volatile unsigned char *source;
    accele160_ring_info_request parsed_request;
    unsigned int i, result;
    ring_seen_bits = inbound_bits & 0x10u;
    ring_cursor = mem_mbox_request.command_ring_bus;
    source = (volatile unsigned char *)ring_cursor;
    __asm__ volatile("syncf" ::: "memory");
    ring_digest = 2166136261u;
    for (i = 0; i < sizeof(bytes); ++i) {
        bytes[i] = source[i];
        ring_digest = (ring_digest ^ bytes[i]) * 16777619u;
    }
    result = accele160_parse_first_ring_info(
        bytes, sizeof(bytes), &mem_mbox_request, &parsed_request);
    if (result) {
        ring_state = 0x100u + result;
        return;
    }
    ring_output_bus = parsed_request.output_bus_address;
    ring_output_bytes = parsed_request.output_bytes;
    ring_command_id = parsed_request.command_id;
    ring_state = 2u; /* observed valid, deliberately not completed */
#ifdef ACCELE160_EMULATOR_RING_REPLY
    complete_first_ring_info();
#endif
}
#ifdef ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER
/* This sole follow-up completion is gated separately from observation.
 * The model's low guest status alias and DMA1 transport are exploratory. */
#ifdef ACCELE160_EMULATOR_RING_HEALTH_REPLY
static void complete_first_ring_health(void)
{
    volatile unsigned int * const ndar1 = (volatile unsigned int *)0x1450u;
    volatile unsigned int * const ccr1 = (volatile unsigned int *)0x1440u;
    volatile unsigned int * const csr1 = (volatile unsigned int *)0x1444u;
    volatile unsigned int *status_ring;
    volatile unsigned int *command_slot;
    unsigned int *dma_descriptor = (unsigned int *)
        (((unsigned int)dma_descriptor_storage + 31u) & ~31u);
    unsigned int i, result;
    if (followup_slot_index != 1u || followup_id != 2u ||
        followup_ioctl != 0x11u || followup_bytes != 128u ||
        followup_output != mem_mbox_request.health_bus ||
        ring_cursor != mem_mbox_request.command_ring_bus + 64u ||
        ring_completion_count != 1u) {
        health_reply_state = 0x301u;
        return;
    }
    result = accele160_compose_ioctl11(ring_composed_reply, 128u);
    if (result) {
        health_reply_state = 0x302u;
        return;
    }
    health_reply_state = 2u;
    dma_descriptor[0] = 0u;
    dma_descriptor[1] = followup_output;
    dma_descriptor[2] = 0u;
    dma_descriptor[3] = (unsigned int)ring_composed_reply;
    dma_descriptor[4] = 128u;
    dma_descriptor[5] = 0x3fu;
    dma_descriptor[6] = 0u;
    dma_descriptor[7] = 0u;
    __asm__ volatile("syncf" ::: "memory");
    *csr1 = 0x100u; /* clear a stale EOC before this descriptor */
    *ndar1 = (unsigned int)dma_descriptor;
    *ccr1 = 1u;
    for (i = 0; i < 10000u && ((*csr1 & 0x100u) == 0u); ++i) { }
    if ((*csr1 & 0x100u) == 0u) {
        *ccr1 = 0u;
        health_dma_state = 0x102u;
        health_reply_state = 0x303u;
        return;
    }
    *ccr1 = 0u;
    *csr1 = 0x100u;
    health_dma_state = 2u;
    status_ring = (volatile unsigned int *)mem_mbox_request.status_ring_bus;
    command_slot = (volatile unsigned int *)followup_slot_address;
    /* Observed second status entry: ID 2, status/sense/residual zero. */
    status_ring[2] = 2u;
    status_ring[3] = 0u;
    *command_slot = 0u;
    health_status_word0 = 2u;
    ring_cursor += 64u;
    ring_completion_count = 2u;
    health_reply_state = 3u;
}
#ifdef ACCELE160_EMULATOR_RING_PDEV_REPLY
static void complete_second_ring_pdev(void)
{
    volatile unsigned char *flash = (volatile unsigned char *)0xfef00000u;
    volatile unsigned int * const ndar1 = (volatile unsigned int *)0x1450u;
    volatile unsigned int * const ccr1 = (volatile unsigned int *)0x1440u;
    volatile unsigned int * const csr1 = (volatile unsigned int *)0x1444u;
    volatile unsigned int *status_ring;
    volatile unsigned int *command_slot;
    unsigned int *dma_descriptor = (unsigned int *)
        (((unsigned int)dma_descriptor_storage + 31u) & ~31u);
    unsigned char product[16];
    unsigned int i, result;
    if (followup_slot_index != 2u || followup_id != 1u ||
        followup_ioctl != 0x05u || followup_bytes != 512u ||
        ring_cursor != mem_mbox_request.command_ring_bus + 128u ||
        ring_completion_count != 2u) {
        pdev_reply_state = 0x301u;
        return;
    }
    for (i = 0; i < sizeof(product); ++i)
        product[i] = flash[0xf0040u + i];
    result = accele160_compose_first_ring_pdev(
        ring_composed_reply, 512u, product, sizeof(product));
    if (result) {
        pdev_reply_state = 0x302u;
        return;
    }
    pdev_reply_state = 2u;
    dma_descriptor[0] = 0u;
    dma_descriptor[1] = followup_output;
    dma_descriptor[2] = 0u;
    dma_descriptor[3] = (unsigned int)ring_composed_reply;
    dma_descriptor[4] = 512u;
    dma_descriptor[5] = 0x3fu;
    dma_descriptor[6] = 0u;
    dma_descriptor[7] = 0u;
    __asm__ volatile("syncf" ::: "memory");
    *csr1 = 0x100u;
    *ndar1 = (unsigned int)dma_descriptor;
    *ccr1 = 1u;
    for (i = 0; i < 10000u && ((*csr1 & 0x100u) == 0u); ++i) { }
    if ((*csr1 & 0x100u) == 0u) {
        *ccr1 = 0u;
        pdev_dma_state = 0x102u;
        pdev_reply_state = 0x303u;
        return;
    }
    *ccr1 = 0u;
    *csr1 = 0x100u;
    pdev_dma_state = 2u;
    status_ring = (volatile unsigned int *)mem_mbox_request.status_ring_bus;
    command_slot = (volatile unsigned int *)followup_slot_address;
    /* Observed third status entry: ID 1, status/sense/residual zero. */
    status_ring[4] = 1u;
    status_ring[5] = 0u;
    *command_slot = 0u;
    pdev_status_word0 = 1u;
    ring_cursor += 64u;
    ring_completion_count = 3u;
    pdev_reply_state = 3u;
}
#endif
#endif
#ifdef ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY
static void complete_repeat_ring_info(void)
{
    volatile unsigned char *flash = (volatile unsigned char *)0xfef00000u;
    volatile unsigned int * const ndar1 = (volatile unsigned int *)0x1450u;
    volatile unsigned int * const ccr1 = (volatile unsigned int *)0x1440u;
    volatile unsigned int * const csr1 = (volatile unsigned int *)0x1444u;
    volatile unsigned int *status_ring;
    volatile unsigned int *command_slot;
    unsigned int *dma_descriptor = (unsigned int *)
        (((unsigned int)dma_descriptor_storage + 31u) & ~31u);
    unsigned char descriptor[0x390], product[16], status[8];
    unsigned int i, result;
    if (followup_slot_index != 3u || followup_id != 1u ||
        followup_ioctl != 1u || followup_bytes != 1004u ||
        ring_cursor != mem_mbox_request.command_ring_bus + 192u ||
        ring_completion_count != 3u) {
        repeat_reply_state = 0x301u;
        return;
    }
    for (i = 0; i < sizeof(descriptor); ++i)
        descriptor[i] = flash[0xe0000u + i];
    for (i = 0; i < sizeof(product); ++i)
        product[i] = flash[0xf0040u + i];
    result = accele160_compose_first_ring_info(
        ring_composed_reply, sizeof(ring_composed_reply),
        descriptor, sizeof(descriptor), product, sizeof(product));
    if (!result)
        result = accele160_compose_first_ring_status(status, sizeof(status));
    if (result) {
        repeat_reply_state = 0x302u;
        return;
    }
    repeat_reply_state = 2u;
    dma_descriptor[0] = 0u;
    dma_descriptor[1] = followup_output;
    dma_descriptor[2] = 0u;
    dma_descriptor[3] = (unsigned int)ring_composed_reply;
    dma_descriptor[4] = 1004u;
    dma_descriptor[5] = 0x3fu;
    dma_descriptor[6] = 0u;
    dma_descriptor[7] = 0u;
    __asm__ volatile("syncf" ::: "memory");
    *csr1 = 0x100u;
    *ndar1 = (unsigned int)dma_descriptor;
    *ccr1 = 1u;
    for (i = 0; i < 10000u && ((*csr1 & 0x100u) == 0u); ++i) { }
    if ((*csr1 & 0x100u) == 0u) {
        *ccr1 = 0u;
        repeat_dma_state = 0x102u;
        repeat_reply_state = 0x303u;
        return;
    }
    *ccr1 = 0u;
    *csr1 = 0x100u;
    repeat_dma_state = 2u;
    status_ring = (volatile unsigned int *)mem_mbox_request.status_ring_bus;
    command_slot = (volatile unsigned int *)followup_slot_address;
    status_ring[6] = (unsigned int)status[0] |
                     ((unsigned int)status[1] << 8) |
                     ((unsigned int)status[2] << 16) |
                     ((unsigned int)status[3] << 24);
    status_ring[7] = (unsigned int)status[4] |
                     ((unsigned int)status[5] << 8) |
                     ((unsigned int)status[6] << 16) |
                     ((unsigned int)status[7] << 24);
    *command_slot = 0u;
    repeat_status_word0 = status_ring[6];
    ring_cursor += 64u;
    ring_completion_count = 4u;
    repeat_reply_state = 3u;
}
#endif
/* Record later exact slots. The next-slot observer only acknowledges the
 * inbound notification; separate feature gates can complete a proven slot. */
static void observe_ring_followup(void)
{
    unsigned char bytes[64];
    volatile unsigned char *source;
    accele160_ring_followup_request parsed;
#ifdef ACCELE160_EMULATOR_RING_NEXT_OBSERVER
    accele160_ring_next_request next_parsed;
#endif
    unsigned int i, result, index;
    index = followup_events + 1u;
    followup_slot_index = index;
    followup_slot_address = mem_mbox_request.command_ring_bus + index * 64u;
    source = (volatile unsigned char *)followup_slot_address;
    __asm__ volatile("syncf" ::: "memory");
    followup_digest = 2166136261u;
    for (i = 0; i < sizeof(bytes); ++i) {
        bytes[i] = source[i];
        followup_digest = (followup_digest ^ bytes[i]) * 16777619u;
    }
#ifdef ACCELE160_EMULATOR_RING_NEXT_OBSERVER
    if (index >= 3u) {
        result = accele160_parse_ring_next(
            bytes, sizeof(bytes), &mem_mbox_request, index, &next_parsed);
        if (result) {
            followup_state = 0x100u + result;
        } else {
            followup_id = next_parsed.command_id;
            followup_ioctl = next_parsed.opcode;
            followup_output = next_parsed.output_bus_address;
            followup_bytes = next_parsed.output_bytes;
            followup_state = 2u; /* parsed, with no completion */
#ifdef ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY
            if (index == 3u)
                complete_repeat_ring_info();
#endif
        }
        followup_events = index;
        *(volatile unsigned int *)0x1320u = 0x10u; /* ACK local bit only */
        __asm__ volatile("syncf" ::: "memory");
#ifdef ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY
        if (index == 3u && repeat_reply_state == 3u)
            *(volatile unsigned int *)0x132cu = 2u;
#endif
        return;
    }
#endif
    result = accele160_parse_ring_followup(
        bytes, sizeof(bytes), &mem_mbox_request, index, &parsed);
    if (result) {
        followup_state = 0x100u + result;
    } else {
        followup_id = parsed.command_id;
        followup_ioctl = parsed.ioctl;
        followup_output = parsed.output_bus_address;
        followup_bytes = parsed.output_bytes;
        followup_state = 2u;
#ifdef ACCELE160_EMULATOR_RING_HEALTH_REPLY
        if (index == 1u)
            complete_first_ring_health();
#ifdef ACCELE160_EMULATOR_RING_PDEV_REPLY
        else if (index == 2u)
            complete_second_ring_pdev();
#endif
#endif
    }
    followup_events = index;
    *(volatile unsigned int *)0x1320u = 0x10u; /* ACK inbound bit only */
    __asm__ volatile("syncf" ::: "memory");
#ifdef ACCELE160_EMULATOR_RING_HEALTH_REPLY
    if (index == 1u && health_reply_state == 3u)
        *(volatile unsigned int *)0x132cu = 2u; /* stock ODB2 after status */
#ifdef ACCELE160_EMULATOR_RING_PDEV_REPLY
    if (index == 2u && pdev_reply_state == 3u)
        *(volatile unsigned int *)0x132cu = 2u;
#endif
#endif
}
#endif
#endif
#endif

static unsigned int local_read32(unsigned int address, void *context)
{
    (void)context;
    return *(volatile unsigned int *)address;
}

#ifdef ACCELE160_OBSERVE_HOST_EVENTS
static void publish_host_monitor(const accele160_host_snapshot *s,
                                 unsigned int message0, unsigned int message1)
{
    unsigned int sequence = report[16] & ~1u;
    report[16] = sequence + 1u; /* odd while the snapshot is being updated */
    __asm__ volatile("syncf" ::: "memory");
    report[10] = s->bridge_pci_command;
    report[11] = s->raid_pci_command;
    report[12] = s->inbound_doorbell;
    report[13] = s->inbound_status;
    report[14] = s->inbound_mask;
    report[15] = s->ready_flags;
    report[17] = message0;
    report[18] = message1;
#ifdef ACCELE160_READ_ROM_MAILBOX
    report[21] = ingress_state;
    report[22] = ingress_request.command_id;
    report[23] = ingress_request.output_bus_address;
    report[24] = ingress_digest;
#ifdef ACCELE160_COMPOSE_CTLR_INFO
    report[26] = reply_state;
    report[27] = reply_digest;
#ifdef ACCELE160_EMULATOR_DMA1_REPLY
    report[29] = dma_state;
#ifdef ACCELE160_EMULATOR_IOCTL11
    report[31] = handled_count;
    report[32] = current_ioctl;
#ifdef ACCELE160_EMULATOR_SET_MBOX
    report[33] = mem_mbox_request.command_ring_bus;
    report[34] = mem_mbox_request.status_ring_bus;
    report[35] = mem_mbox_request.health_bus;
#ifdef ACCELE160_EMULATOR_RING_OBSERVER
    report[37] = ring_state;
    report[38] = ring_digest;
    report[39] = ring_cursor;
    report[40] = ring_output_bus;
    report[41] = ring_output_bytes;
    report[42] = ring_command_id;
    report[43] = ring_seen_bits;
    report[44] =
#ifdef ACCELE160_EMULATOR_RING_REPLY
        ring_completion_count;
    report[45] = ring_reply_digest;
    report[46] = ring_dma_state;
    report[47] = ring_status_word0;
    report[48] = ring_status_word1;
#ifdef ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER
    report[50] = followup_events;
    report[51] = followup_slot_index;
    report[52] = followup_slot_address;
    report[53] = followup_digest;
    report[54] = followup_state;
    report[55] = followup_id;
    report[56] = followup_ioctl;
    report[57] = followup_output;
    report[58] = followup_bytes;
    report[59] = ring_completion_count ?
                 mem_mbox_request.status_ring_bus + ring_completion_count * 8u : 0u;
    report[60] = ring_completion_count;
#ifdef ACCELE160_EMULATOR_RING_HEALTH_REPLY
#ifdef ACCELE160_EMULATOR_RING_PDEV_REPLY
#ifdef ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY
    report[61] = followup_events >= 3u ? repeat_reply_state :
                 followup_events >= 2u ? pdev_reply_state : health_reply_state;
    report[62] = followup_events >= 3u ? repeat_dma_state :
                 followup_events >= 2u ? pdev_dma_state : health_dma_state;
    report[63] = followup_events >= 3u ? repeat_status_word0 :
                 followup_events >= 2u ? pdev_status_word0 : health_status_word0;
#else
    report[61] = followup_events >= 2u ? pdev_reply_state : health_reply_state;
    report[62] = followup_events >= 2u ? pdev_dma_state : health_dma_state;
    report[63] = followup_events >= 2u ? pdev_status_word0 : health_status_word0;
#endif
#else
    report[61] = health_reply_state;
    report[62] = health_dma_state;
    report[63] = health_status_word0;
#endif
#endif
#endif
#else
        0u; /* read-only observer has no ring completion */
#endif
#endif
#endif
#endif
#endif
#endif
#endif
    __asm__ volatile("syncf" ::: "memory");
    report[16] = sequence + 2u;
    __asm__ volatile("syncf" ::: "memory");
}
#endif

static void publish_host_snapshot(void)
{
    accele160_host_snapshot s = accele160_sample_host_startup(local_read32, 0);
    report[9] = 0x30545348u; /* HST0 */
#ifdef ACCELE160_OBSERVE_HOST_EVENTS
    publish_host_monitor(&s, local_read32(0x1310u, 0),
                         local_read32(0x1314u, 0));
#else
    report[10] = s.bridge_pci_command;
    report[11] = s.raid_pci_command;
    report[12] = s.inbound_doorbell;
    report[13] = s.inbound_status;
    report[14] = s.inbound_mask;
    report[15] = s.ready_flags;
#endif
}

#ifdef ACCELE160_OBSERVE_HOST_EVENTS
/* Offline monitor loop. The default variant only samples; optional transport
 * code is invoked by the mailbox path after RTEMS passes. */
static void observe_host_events(void) __attribute__((noreturn));
static void observe_host_events(void)
{
    accele160_host_snapshot previous, current;
    unsigned int previous_message0 = ~0u, previous_message1 = ~0u;
    unsigned int message0, message1;
    previous.bridge_pci_command = ~0u;
    previous.raid_pci_command = ~0u;
    previous.inbound_doorbell = ~0u;
    previous.inbound_status = ~0u;
    previous.inbound_mask = ~0u;
    previous.ready_flags = ~0u;
    for (;;) {
        current = accele160_sample_host_startup(local_read32, 0);
        message0 = local_read32(0x1310u, 0);
        message1 = local_read32(0x1314u, 0);
#ifdef ACCELE160_EMULATOR_RING_OBSERVER
        if (handled_count == 6u && ring_state == 0u &&
            (current.inbound_doorbell & 0x10u))
            observe_first_ring_slot(current.inbound_doorbell);
#ifdef ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER
        else if (ring_completion_count >= 1u && followup_events <
#ifdef ACCELE160_EMULATOR_RING_NEXT_OBSERVER
                 4u &&
#else
                 2u &&
#endif
            (current.inbound_doorbell & 0x10u))
            observe_ring_followup();
#endif
#endif
#ifdef ACCELE160_READ_ROM_MAILBOX
        if (
#ifdef ACCELE160_EMULATOR_IOCTL11
            handled_count <
#ifdef ACCELE160_EMULATOR_SET_MBOX
                6u &&
#else
#ifdef ACCELE160_EMULATOR_IOCTL2D
                5u &&
#else
#ifdef ACCELE160_EMULATOR_IOCTLD0
                4u &&
#else
#ifdef ACCELE160_EMULATOR_IOCTL15
                3u &&
#else
                2u &&
#endif
#endif
#endif
#endif
            handled_count == attempted_count &&
            (handled_count != 0u || ingress_state == 0u) &&
            (current.ready_flags & 3u) == 3u &&
            (handled_count != 0u || (current.ready_flags & 4u)) &&
#else
            ingress_state == 0u && (current.ready_flags & 7u) == 7u &&
#endif
            (current.inbound_doorbell & 1u))
            ingest_rom_mailbox(message0, message1);
#endif
        if (current.bridge_pci_command != previous.bridge_pci_command ||
            current.raid_pci_command != previous.raid_pci_command ||
            current.inbound_doorbell != previous.inbound_doorbell ||
            current.inbound_status != previous.inbound_status ||
            current.inbound_mask != previous.inbound_mask ||
            current.ready_flags != previous.ready_flags ||
            message0 != previous_message0 || message1 != previous_message1
#ifdef ACCELE160_READ_ROM_MAILBOX
            || ingress_state != report[21]
            || ingress_digest != report[24]
#ifdef ACCELE160_COMPOSE_CTLR_INFO
            || reply_state != report[26]
#ifdef ACCELE160_EMULATOR_DMA1_REPLY
            || dma_state != report[29]
#ifdef ACCELE160_EMULATOR_IOCTL11
            || handled_count != report[31] || current_ioctl != report[32]
#ifdef ACCELE160_EMULATOR_RING_OBSERVER
            || ring_state != report[37] || ring_digest != report[38]
#endif
#endif
#endif
#endif
#endif
            ) {
            publish_host_monitor(&current, message0, message1);
            previous = current;
            previous_message0 = message0;
            previous_message1 = message1;
        }
    }
}
#endif

void bounded_fatal(unsigned int code) { native_park(0xf0000000u | code); }
#define CHECK(x) do { unsigned int e = (x); if (e) bounded_fatal(e); } while (0)

static void Worker(rtems_task_argument arg)
{
    unsigned int i;
    (void)arg;
    for (i = 0; i < 64; ++i) {
        ++worker_count;
        CHECK(rtems_task_wake_after(0));
    }
    done = 1;
    CHECK(rtems_task_suspend(RTEMS_SELF));
    bounded_fatal(0x201u);
}

static void Init(rtems_task_argument arg)
{
    unsigned int i;
    rtems_task_priority old;
    (void)arg;
    CHECK(rtems_task_create(0x574f524bu, 2, 4096,
                            RTEMS_INTERRUPT_LEVEL(31),
                            RTEMS_DEFAULT_ATTRIBUTES, &worker_id));
    CHECK(rtems_task_start(worker_id, Worker, 0));
    CHECK(rtems_task_set_priority(RTEMS_SELF, 3, &old));
    for (i = 0; i < 256 && !done; ++i) {
        ++init_count;
        CHECK(rtems_task_wake_after(0));
    }
    report[4] = worker_count;
    report[5] = init_count;
    report[6] = done;
    report[7] = (done == 1 && worker_count == 64) ? 0x50415353u : 0x4641494cu;
    publish_host_snapshot();
    __asm__ volatile("syncf" ::: "memory");
#ifdef ACCELE160_OBSERVE_HOST_EVENTS
    if (done == 1 && worker_count == 64) {
        report[8] = 0u;
        observe_host_events();
    }
#endif
    native_park(done == 1 && worker_count == 64 ? 0u : 0x202u);
}

static rtems_initialization_tasks_table tasks[] = {
    { 0x494e4954u, 4096, 1, RTEMS_DEFAULT_ATTRIBUTES,
      Init, RTEMS_INTERRUPT_LEVEL(31), 0 }
};
static rtems_api_configuration_table api = { 2, 0, 0, 0, 0, 0, 0, 0, 1, tasks };
static rtems_configuration_table config = {
    workspace, sizeof(workspace), 0, 10000, 1, 0, 0, 0, 0, 0, 0, 0, &api, 0, 0
};
static rtems_cpu_table cpu = { 0, 0, 0, 0, 1, 2048, 2048, 0, 0, 0 };

void _ISR_Handler(void) { bounded_fatal(0x301u); }
void _CPU_ISR_install_raw_handler(unsigned int v, proc_ptr n, proc_ptr *o)
{
    (void)n; (void)o; bounded_fatal(0x300u | v);
}

void native_main(void)
{
    unsigned char *p;
    for (p = _bss_start; p < _bss_end; ++p) *p = 0;
    report[4] = 0;
    report[5] = 0;
    report[6] = 0;
    report[7] = 0x5254454du; /* entering RTEMS */
#ifdef ACCELE160_OBSERVE_HOST_EVENTS
    report[16] = 0u;
    report[19] = 0x31545348u; /* HST1 with even/odd sequence */
#ifdef ACCELE160_READ_ROM_MAILBOX
    report[20] = 0x3058424du; /* MBX0 diagnostic ingress */
    report[21] = 0u;
    report[22] = 0u;
    report[23] = 0u;
    report[24] = 0u;
#ifdef ACCELE160_COMPOSE_CTLR_INFO
    report[25] = 0x304c5052u; /* RPL0, local composition only */
    report[26] = 0u;
    report[27] = 0u;
#ifdef ACCELE160_EMULATOR_DMA1_REPLY
    report[28] = 0x31414d44u; /* DMA1 diagnostic completion state */
    report[29] = 0u;
#ifdef ACCELE160_EMULATOR_IOCTL11
#ifdef ACCELE160_EMULATOR_SET_MBOX
    report[30] = 0x36514552u; /* REQ6, five ROM plus SET_MEM_MBOX */
#else
#ifdef ACCELE160_EMULATOR_IOCTL2D
    report[30] = 0x35514552u; /* REQ5, five-request diagnostic */
#else
#ifdef ACCELE160_EMULATOR_IOCTLD0
    report[30] = 0x34514552u; /* REQ4, four-request diagnostic */
#else
#ifdef ACCELE160_EMULATOR_IOCTL15
    report[30] = 0x33514552u; /* REQ3, three-request diagnostic */
#else
    report[30] = 0x32514552u; /* REQ2, two-request diagnostic */
#endif
#endif
#endif
#endif
    report[31] = 0u;
    report[32] = 0u;
#ifdef ACCELE160_EMULATOR_RING_OBSERVER
    report[36] = 0x31474e52u; /* RNG1, read-only first ring slot */
    report[37] = 0u;
    report[38] = 0u;
    report[39] = 0u;
    report[40] = 0u;
    report[41] = 0u;
    report[42] = 0u;
    report[43] = 0u;
    report[44] = 0u;
#ifdef ACCELE160_EMULATOR_RING_REPLY
    report[45] = 0u;
    report[46] = 0u;
    report[47] = 0u;
    report[48] = 0u;
#ifdef ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER
    report[49] = 0x32474e52u; /* RNG2 */
    report[50] = 0u;
    report[51] = 0u;
    report[52] = 0u;
    report[53] = 0u;
    report[54] = 0u;
    report[55] = 0u;
    report[56] = 0u;
    report[57] = 0u;
    report[58] = 0u;
    report[59] = 0u;
    report[60] = 0u;
#ifdef ACCELE160_EMULATOR_RING_HEALTH_REPLY
    report[61] = 0u;
    report[62] = 0u;
    report[63] = 0u;
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
    publish_host_snapshot();
    __asm__ volatile("syncf" ::: "memory");
    rtems_initialize_executive(&config, &cpu);
    bounded_fatal(0x302u);
}
