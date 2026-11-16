/* AcceleRAID 160 host-facing PCI probe model for QEMU 6.2.
 *
 * Optional local bridge serves the translated upper BAR page from the i960
 * emulator. Normal LP mailbox submission is traced through guest DMA and
 * remains pending until controller-side command handling is implemented.
 * An explicit exploratory switch fabricates four ROM-only IOCTL completions.
 */
#include "qemu/osdep.h"
#include "qapi/error.h"
#include "hw/pci/pci.h"
#include "hw/pci/pci_bridge.h"
#include "hw/qdev-properties.h"
#include "qemu/module.h"
#include "qom/object.h"
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#define TYPE_ACCELE160 "accele160-probe"
#define TYPE_ACCELE160_BRIDGE "accele160-pci-bridge"
#define ACCELE160_BAR_SIZE 0x2000
#define LP_CMDMBX 0x10
#define LP_CMDSTS 0x18
#define LP_IDB 0x20
#define LP_IDB_HWMBOX_ACK_STS 0x02
#define LP_ODB 0x2c
#define LP_IRQMASK 0x34

typedef struct Accele160State {
    PCIDevice parent_obj;
    MemoryRegion bar0;
    uint8_t aperture[ACCELE160_BAR_SIZE];
    char *aperture_file;
    char *bridge_socket;
    int bridge_fd;
    uint32_t piatvr;
    uint8_t lp_idb;
    uint8_t lp_odb;
    uint8_t lp_irqmask;
    uint64_t lp_mbox_address;
    uint8_t last_mailbox[64];
    bool lp_mailbox_pending;
    uint64_t set_mbox_ring;
    uint64_t set_mbox_status_ring;
    uint64_t set_mbox_health;
    bool set_mbox_slot_logged;
    bool stock_first_ring_mirrored;
    bool native_first_ring_mirrored;
    unsigned native_followup_mirror_mask;
    unsigned ring_followup_events;
    bool step_on_ack;
    bool explore_rom_ioctls;
    bool explore_live_firmware;
    bool explore_set_mbox_trace;
    bool explore_set_mbox_bridge;
    bool explore_mmbox_doorbell_observe;
    bool explore_mmbox_doorbell_control;
    bool explore_stock_ring_memory;
    bool explore_stock_ring_mirror;
    bool explore_stock_followup_observe;
    bool explore_stock_followup_mirror;
    bool explore_stock_next_observe;
    bool explore_stock_next_mirror;
    bool explore_stock_next_mutate_slot;
    bool explore_stock_next_mutate_prefill;
    bool explore_stock_scsi_observe;
    bool explore_native_poll;
    bool explore_native_set_mbox;
    bool explore_native_ring_observe;
    bool explore_native_ring_mirror;
    bool explore_native_followup_observe;
    bool explore_native_followup_mirror;
    bool explore_native_next_observe;
    bool explore_native_next_mirror;
    bool trace_live_reply;
    unsigned live_completion_count;
    uint32_t trace_limit;
    uint64_t access_count;
    uint64_t config_access_count;
} Accele160State;

OBJECT_DECLARE_SIMPLE_TYPE(Accele160State, ACCELE160)
static uint32_t accele160_bridge_request(Accele160State *s,
                                         const char *request);

typedef struct Accele160BridgeState {
    PCIBridge parent_obj;
} Accele160BridgeState;

OBJECT_DECLARE_SIMPLE_TYPE(Accele160BridgeState, ACCELE160_BRIDGE)

static Accele160State *accele160_raid_sibling(PCIDevice *bridge)
{
    PCIDevice *raid = pci_find_device(pci_get_bus(bridge),
                                      pci_dev_bus_num(bridge),
                                      bridge->devfn | 1);
    return raid && object_dynamic_cast(OBJECT(raid), TYPE_ACCELE160)
               ? ACCELE160(raid) : NULL;
}

static void accele160_mirror_command(Accele160State *raid,
                                     uint32_t local_register, uint16_t value)
{
    char request[32];
    if (!raid || raid->bridge_fd < 0) {
        return;
    }
    snprintf(request, sizeof(request), "H %04x %04x\n", local_register, value);
    accele160_bridge_request(raid, request);
    fprintf(stderr, "accele160 pci-command local=0x%04x value=0x%04x\n",
            local_register, value);
}

static uint32_t accele160_bridge_request(Accele160State *s, const char *request)
{
    char response[32];
    size_t length = strlen(request);
    size_t used = 0;
    while (used < length) {
        ssize_t sent = write(s->bridge_fd, request + used, length - used);
        if (sent <= 0) { fprintf(stderr, "accele160 bridge write failed\n"); exit(1); }
        used += sent;
    }
    used = 0;
    while (used < sizeof(response) - 1) {
        ssize_t got = read(s->bridge_fd, response + used, 1);
        if (got != 1) { fprintf(stderr, "accele160 bridge read failed\n"); exit(1); }
        if (response[used++] == '\n') break;
    }
    response[used] = 0;
    unsigned result;
    bool valid = used == 9 && response[8] == '\n';
    for (unsigned i = 0; valid && i < 8; ++i)
        valid = g_ascii_isxdigit(response[i]);
    if (!valid || sscanf(response, "%8x", &result) != 1) {
        fprintf(stderr, "accele160 bridge rejected request %c: %s",
                request[0], response);
        exit(1);
    }
    return result;
}

static uint32_t accele160_bridge(Accele160State *s, char op, uint32_t addr,
                                 unsigned size, uint32_t value)
{
    char request[64];
    snprintf(request, sizeof(request), "%c %08x %u %08x\n",
             op, addr, size, value);
    return accele160_bridge_request(s, request);
}

static void accele160_trace_mmbox_object(Accele160State *s, const char *phase)
{
    char query[48];
    uint32_t root = accele160_bridge_request(s, "R c03e5bd0 4 0\n");
    fprintf(stderr, "accele160 EXPLORE mmbox-object phase=%s root=0x%08x",
            phase, root);
    if (root == 0xc048e700u) {
        for (unsigned offset = 0; offset <= 0x68; offset += 4) {
            snprintf(query, sizeof(query), "R %08x 4 0\n", root + offset);
            fprintf(stderr, " +%02x=%08x", offset,
                    accele160_bridge_request(s, query));
        }
    }
    fputc('\n', stderr);
}

static uint64_t accele160_le64(const uint8_t *bytes)
{
    uint64_t value = 0;
    for (unsigned i = 0; i < 8; ++i)
        value |= (uint64_t)bytes[i] << (8 * i);
    return value;
}

static bool accele160_native_set_mbox_shape(Accele160State *s)
{
    const uint8_t *p = s->last_mailbox;
    uint64_t base[4] = {s->lp_mbox_address,
                        accele160_le64(p + 32),
                        accele160_le64(p + 40),
                        accele160_le64(p + 24)};
    const uint32_t span[4] = {64, 32768, 4096, 1024};
    if (!s->explore_native_poll || !s->explore_native_set_mbox ||
        s->live_completion_count != 5 ||
        p[0] != 1 || p[1] || p[2] != 0x20 || p[3] != 0x40 ||
        p[4] != 0x20 || p[5] != 0x04 || p[6] || p[7] ||
        p[21] != 0x8e || p[22] != 1)
        return false;
    for (unsigned i = 8; i < 64; ++i) {
        if ((i >= 24 && i < 48) || i == 21 || i == 22)
            continue;
        if (p[i]) return false;
    }
    for (unsigned i = 0; i < 4; ++i) {
        if (base[i] < 0x00100000u || (base[i] & 0xfffu) ||
            base[i] + span[i] > 0x20000000u)
            return false;
        for (unsigned j = 0; j < i; ++j)
            if (base[i] < base[j] + span[j] &&
                base[j] < base[i] + span[i])
                return false;
    }
    return true;
}

static bool accele160_trace_ring_guest(Accele160State *s,
                                               uint64_t output_bus,
                                               const char *phase)
{
    uint8_t status[8], health[16], output[1004];
    g_autofree gchar *digest = NULL;
    if (pci_dma_read(&s->parent_obj, s->set_mbox_status_ring,
                     status, sizeof(status)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, s->set_mbox_health,
                     health, sizeof(health)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, output_bus,
                     output, sizeof(output)) != MEMTX_OK)
        return false;
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                          sizeof(output));
    fprintf(stderr, "accele160 EXPLORE ring guest phase=%s "
            "status=%02x%02x%02x%02x%02x%02x%02x%02x "
            "health-first=%02x%02x%02x%02x%02x%02x%02x%02x "
            "output-sha256=%s\n", phase,
            status[0], status[1], status[2], status[3],
            status[4], status[5], status[6], status[7],
            health[0], health[1], health[2], health[3],
            health[4], health[5], health[6], health[7], digest);
    return true;
}

/* Seed only the captured guest windows into the exploratory i960 address
 * model. This does not issue a DMA command or copy an i960 result to QEMU. */
static bool accele160_stage_guest_window(Accele160State *s,
                                         char kind, uint64_t address,
                                         unsigned length)
{
    uint8_t bytes[1004];
    char request[48];
    if (!length || length > sizeof(bytes) || (length & 3u) ||
        pci_dma_read(&s->parent_obj, address, bytes, length) != MEMTX_OK)
        return false;
    snprintf(request, sizeof(request), "G %c %016" PRIx64 " %u\n",
             kind, address, length);
    if (accele160_bridge_request(s, request) != 0)
        return false;
    for (unsigned i = 0; i < length; i += 4) {
        uint32_t word = bytes[i] | (uint32_t)bytes[i + 1] << 8 |
                        (uint32_t)bytes[i + 2] << 16 |
                        (uint32_t)bytes[i + 3] << 24;
        snprintf(request, sizeof(request), "W %08" PRIx64 " 4 %08x\n",
                 address + i, word);
        accele160_bridge_request(s, request);
    }
    return true;
}

static bool accele160_stage_ring_slot(Accele160State *s, uint64_t dma,
                                      const uint8_t slot[64])
{
    char request[160];
    size_t used = snprintf(request, sizeof(request), "N %016" PRIx64 " ",
                           dma);
    for (unsigned j = 0; j < 64; ++j)
        used += snprintf(request + used, sizeof(request) - used,
                         "%02x", slot[j]);
    snprintf(request + used, sizeof(request) - used, "\n");
    return accele160_bridge_request(s, request) == 0;
}

static void accele160_trace_ring_model(Accele160State *s,
                                               uint64_t output_bus,
                                               const char *phase)
{
    uint8_t output[1004];
    char request[48];
    g_autofree gchar *digest = NULL;
    uint32_t status0, status1, ring0;
    for (unsigned i = 0; i < sizeof(output); i += 4) {
        uint32_t word;
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                          sizeof(output));
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring);
    status0 = accele160_bridge_request(s, request);
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 4);
    status1 = accele160_bridge_request(s, request);
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_ring);
    ring0 = accele160_bridge_request(s, request);
    fprintf(stderr, "accele160 EXPLORE ring model phase=%s "
            "slot-word0=0x%08x status=%08x%08x output-sha256=%s\n",
            phase, ring0, status0, status1, digest);
    if (!strncmp(phase, "after-", 6)) {
        fprintf(stderr, "accele160 EXPLORE ring model output-hex=");
        for (unsigned i = 0; i < sizeof(output); ++i)
            fprintf(stderr, "%02x", output[i]);
        fputc('\n', stderr);
    }
}

static uint32_t accele160_fnv1a(const uint8_t *bytes, size_t length)
{
    uint32_t digest = 0x811c9dc5u;
    for (size_t i = 0; i < length; ++i)
        digest = (digest ^ bytes[i]) * 0x01000193u;
    return digest;
}

static bool accele160_mirror_native_ring(Accele160State *s,
                                        const uint8_t slot[64],
                                        uint64_t output_bus,
                                        const uint32_t observer[13],
                                        uint32_t outbound)
{
    uint8_t output[1004], guest_output[1004], guest_status[8], guest_slot[4];
    uint8_t zero[4] = {0};
    uint8_t residual[4] = {0xec, 0xff, 0xff, 0xff};
    uint8_t id_status[4] = {1, 0, 0, 0};
    char request[48];
    g_autofree gchar *digest = NULL;

    if (observer[0] != 0x31474e52u || observer[1] != 3u ||
        observer[2] != accele160_fnv1a(slot, 64) ||
        observer[3] != s->set_mbox_ring + 64u ||
        observer[4] != output_bus || observer[5] != 1004u ||
        observer[6] != 1u || observer[7] != 0x10u ||
        observer[8] != 1u || observer[10] != 2u ||
        observer[11] != 1u || observer[12] != 0xffffffecu ||
        outbound != 2u || (s->lp_odb & 2u)) {
        fprintf(stderr, "accele160 EXPLORE native ring mirror rejected: "
                "report/doorbell/DMA state\n");
        return false;
    }
    for (unsigned i = 0; i < sizeof(output); i += 4) {
        uint32_t word;
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                          sizeof(output));
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring);
    if (accele160_bridge_request(s, request) != 1u)
        return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 4u);
    if (accele160_bridge_request(s, request) != 0xffffffecu)
        return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_ring);
    if (accele160_bridge_request(s, request) != 0u ||
        observer[9] != accele160_fnv1a(output, sizeof(output)) ||
        strcmp(digest,
               "a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8")) {
        fprintf(stderr, "accele160 EXPLORE native ring mirror rejected: "
                "model payload/status/slot mismatch\n");
        return false;
    }
    if (pci_dma_read(&s->parent_obj, output_bus, guest_output,
                     sizeof(guest_output)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, s->set_mbox_status_ring, guest_status,
                     sizeof(guest_status)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, s->set_mbox_ring, guest_slot,
                     sizeof(guest_slot)) != MEMTX_OK ||
        memcmp(guest_slot, slot, 4) ||
        memcmp(guest_status, (uint8_t[8]){0}, 8)) {
        fprintf(stderr, "accele160 EXPLORE native ring mirror rejected: "
                "guest memory precondition\n");
        return false;
    }
    for (unsigned i = 0; i < sizeof(guest_output); ++i)
        if (guest_output[i]) {
            fprintf(stderr, "accele160 EXPLORE native ring mirror rejected: "
                    "guest output already written\n");
            return false;
        }
    if (pci_dma_write(&s->parent_obj, s->set_mbox_ring, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, output_bus, output,
                      sizeof(output)) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, s->set_mbox_status_ring + 4,
                      residual, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, s->set_mbox_status_ring,
                      id_status, 4) != MEMTX_OK) {
        fprintf(stderr, "accele160 EXPLORE native ring mirror rejected: "
                "guest DMA write failed\n");
        return false;
    }
    s->lp_odb |= 2u;
    if (!(s->lp_irqmask & 4u))
        pci_set_irq(&s->parent_obj, 1);
    fprintf(stderr, "accele160 EXPLORE native ring mirrored "
            "output=0x%08" PRIx64 " bytes=1004 sha256=%s "
            "status=01000000ecffffff slot-word0=0 outbound=0x02 irq=%u\n",
            output_bus, digest, !(s->lp_irqmask & 4u));
    s->native_first_ring_mirrored = true;
    return true;
}

static bool accele160_mirror_stock_ring(Accele160State *s,
                                       const uint8_t slot[64],
                                       uint64_t output_bus,
                                       uint32_t outbound)
{
    uint8_t output[1004], guest_output[1004], guest_status[8], guest_slot[4];
    uint8_t zero[4] = {0};
    uint8_t residual[4] = {0xec, 0xff, 0xff, 0xff};
    uint8_t id_status[4] = {1, 0, 0, 0};
    char request[48];
    g_autofree gchar *digest = NULL;
    uint32_t descriptor[6];

    if (slot[0] != 1 || slot[1] || slot[2] != 0x20 ||
        slot[3] != 0x50 || slot[4] != 0xec || slot[5] != 0x03 ||
        slot[21] != 1 || slot[40] != 0xec || slot[41] != 0x03 ||
        accele160_le64(slot + 32) != output_bus ||
        output_bus < 0x00100000u || (output_bus & 3u) ||
        output_bus + 1004u > 0x20000000u)
        return false;
    for (unsigned j = 0; j < 64; ++j)
        if (j != 0 && j != 2 && j != 3 && j != 4 && j != 5 &&
            j != 21 && !(j >= 32 && j < 40) &&
            j != 40 && j != 41 && slot[j])
            return false;
    if (outbound != 2u || (s->lp_odb & 2u) ||
        accele160_bridge_request(s, "I 1450\n") != 0xc0611320u)
        return false;
    for (unsigned j = 0; j < 6; ++j) {
        snprintf(request, sizeof(request), "R %08x 4 0\n",
                 0xc0611320u + j * 4u);
        descriptor[j] = accele160_bridge_request(s, request);
    }
    if (descriptor[0] || descriptor[1] != output_bus || descriptor[2] ||
        descriptor[3] != 0xc060c300u || descriptor[4] != 1004u ||
        descriptor[5] != 0x3fu)
        return false;
    for (unsigned i = 0; i < sizeof(output); i += 4) {
        uint32_t word;
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                          sizeof(output));
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring);
    if (accele160_bridge_request(s, request) != 1u)
        return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 4u);
    if (accele160_bridge_request(s, request) != 0xffffffecu)
        return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_ring);
    if (accele160_bridge_request(s, request) != 0u ||
        strcmp(digest,
               "a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8"))
        return false;
    if (pci_dma_read(&s->parent_obj, output_bus, guest_output,
                     sizeof(guest_output)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, s->set_mbox_status_ring, guest_status,
                     sizeof(guest_status)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, s->set_mbox_ring, guest_slot,
                     sizeof(guest_slot)) != MEMTX_OK ||
        memcmp(guest_slot, slot, 4) ||
        memcmp(guest_status, (uint8_t[8]){0}, 8))
        return false;
    for (unsigned i = 0; i < sizeof(guest_output); ++i)
        if (guest_output[i]) return false;
    if (pci_dma_write(&s->parent_obj, s->set_mbox_ring, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, output_bus, output,
                      sizeof(output)) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, s->set_mbox_status_ring + 4,
                      residual, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, s->set_mbox_status_ring,
                      id_status, 4) != MEMTX_OK)
        return false;
    s->lp_odb |= 2u;
    if (!(s->lp_irqmask & 4u))
        pci_set_irq(&s->parent_obj, 1);
    fprintf(stderr, "accele160 EXPLORE stock ring mirrored "
            "output=0x%08" PRIx64 " bytes=1004 sha256=%s "
            "status=01000000ecffffff slot-word0=0 outbound=0x02 irq=%u\n",
            output_bus, digest, !(s->lp_irqmask & 4u));
    s->stock_first_ring_mirrored = true;
    return true;
}

static void accele160_trace_stock_followup(Accele160State *s, unsigned event,
                                           uint64_t pdev_bus)
{
    uint8_t health[128], pdev[512];
    char query[48];
    uint32_t status_words[4], ring_words[2], descriptor[6] = {0};
    uint32_t dma_pointer = accele160_bridge_request(s, "I 1450\n");
    g_autofree gchar *health_sha = NULL;
    g_autofree gchar *pdev_sha = NULL;
    for (unsigned i = 0; i < sizeof(health); i += 4) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 s->set_mbox_health + i);
        uint32_t word = accele160_bridge_request(s, query);
        for (unsigned k = 0; k < 4; ++k)
            health[i + k] = word >> (8 * k);
    }
    health_sha = g_compute_checksum_for_data(G_CHECKSUM_SHA256, health,
                                              sizeof(health));
    if (event >= 2 && pdev_bus) {
        for (unsigned i = 0; i < sizeof(pdev); i += 4) {
            snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                     pdev_bus + i);
            uint32_t word = accele160_bridge_request(s, query);
            for (unsigned k = 0; k < 4; ++k)
                pdev[i + k] = word >> (8 * k);
        }
        pdev_sha = g_compute_checksum_for_data(G_CHECKSUM_SHA256, pdev,
                                                sizeof(pdev));
    }
    for (unsigned j = 0; j < 4; ++j) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 s->set_mbox_status_ring + 8u + j * 4u);
        status_words[j] = accele160_bridge_request(s, query);
    }
    for (unsigned j = 0; j < 2; ++j) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 s->set_mbox_ring + 64u + j * 64u);
        ring_words[j] = accele160_bridge_request(s, query);
    }
    if (dma_pointer == 0xc0611320u)
        for (unsigned j = 0; j < 6; ++j) {
            snprintf(query, sizeof(query), "R %08x 4 0\n",
                     dma_pointer + j * 4u);
            descriptor[j] = accele160_bridge_request(s, query);
        }
    if (descriptor[3] == 0xc060c300u && descriptor[5] == 0x3fu &&
        ((descriptor[1] == s->set_mbox_health && descriptor[4] == 128u) ||
         (event >= 2 && pdev_bus && descriptor[1] == pdev_bus &&
          descriptor[4] == 512u))) {
        uint8_t source[512];
        const unsigned source_length = descriptor[4];
        for (unsigned i = 0; i < source_length; i += 4) {
            snprintf(query, sizeof(query), "R %08x 4 0\n",
                     descriptor[3] + i);
            uint32_t word = accele160_bridge_request(s, query);
            for (unsigned k = 0; k < 4; ++k)
                source[i + k] = word >> (8 * k);
        }
        g_autofree gchar *source_sha =
            g_compute_checksum_for_data(G_CHECKSUM_SHA256, source,
                                        source_length);
        fprintf(stderr, "accele160 EXPLORE stock followup dma1-source "
                "event=%u bytes=%u sha256=%s hex=", event,
                source_length, source_sha);
        for (unsigned i = 0; i < source_length; ++i)
            fprintf(stderr, "%02x", source[i]);
        fputc('\n', stderr);
    }
    fprintf(stderr, "accele160 EXPLORE stock followup model event=%u "
            "slot1=0x%08x slot2=0x%08x "
            "status1=%08x%08x status2=%08x%08x "
            "health-sha256=%s pdev-sha256=%s "
            "inbound=0x%08x inbound-status=0x%08x mask=0x%08x "
            "ring-cursor=0x%08x queue-head=0x%08x "
            "dma1-status=0x%08x dma1-control=0x%08x "
            "dma1-pointer=0x%08x descriptor=%08x,%08x,%08x,%08x,%08x,%08x "
            "outbound=0x%08x\n",
            event, ring_words[0], ring_words[1],
            status_words[0], status_words[1],
            status_words[2], status_words[3], health_sha,
            pdev_sha ? pdev_sha : "none",
            accele160_bridge_request(s, "I 1320\n"),
            accele160_bridge_request(s, "I 1324\n"),
            accele160_bridge_request(s, "I 1328\n"),
            accele160_bridge_request(s, "R c048e70c 4 0\n"),
            accele160_bridge_request(s, "R c03e2740 4 0\n"),
            accele160_bridge_request(s, "I 1444\n"),
            accele160_bridge_request(s, "I 1440\n"), dma_pointer,
            descriptor[0], descriptor[1], descriptor[2],
            descriptor[3], descriptor[4], descriptor[5],
            accele160_bridge_request(s, "I 132c\n"));
}

static bool accele160_mirror_stock_followup(Accele160State *s, unsigned event,
                                           const uint8_t slot[64],
                                           uint32_t outbound)
{
    const unsigned length = event == 1 ? 128u : 512u;
    const uint8_t id = event == 1 ? 2u : 1u;
    const uint8_t ioctl = event == 1 ? 0x11u : 0x05u;
    const char *expected_sha = event == 1 ?
        "67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32" :
        "9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41";
    const uint64_t output_bus = accele160_le64(slot + 32);
    const uint64_t slot_bus = s->set_mbox_ring + event * 64u;
    const uint64_t status_bus = s->set_mbox_status_ring + event * 8u;
    uint8_t output[512], guest_output[512], guest_status[8], guest_slot[4];
    const uint8_t zero[4] = {0};
    const uint8_t status_data[4] = {id, 0, 0, 0};
    char request[48];
    g_autofree gchar *digest = NULL;

    if (event < 1 || event > 2 || slot[0] != id || slot[1] ||
        slot[2] != 0x20 || slot[3] != 0x50 ||
        slot[4] != (uint8_t)length || slot[5] != (uint8_t)(length >> 8) ||
        slot[21] != ioctl || slot[40] != (uint8_t)length ||
        slot[41] != (uint8_t)(length >> 8) ||
        output_bus < 0x00100000u || (output_bus & 3u) ||
        output_bus + length > 0x20000000u ||
        (event == 1 && output_bus != s->set_mbox_health) ||
        outbound != 2u || (s->lp_odb & 2u))
        return false;
    for (unsigned j = 0; j < 64; ++j)
        if (j != 0 && j != 2 && j != 3 && j != 4 && j != 5 &&
            j != 21 && !(j >= 32 && j < 40) && j != 40 && j != 41 &&
            slot[j])
            return false;
    for (unsigned i = 0; i < length; i += 4) {
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        uint32_t word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output, length);
    if (strcmp(digest, expected_sha)) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", slot_bus);
    if (accele160_bridge_request(s, request) != 0u) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", status_bus);
    if (accele160_bridge_request(s, request) != id) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             status_bus + 4u);
    if (accele160_bridge_request(s, request) != 0u) return false;
    if (pci_dma_read(&s->parent_obj, slot_bus, guest_slot, 4) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, status_bus, guest_status, 8) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, output_bus, guest_output, length) != MEMTX_OK ||
        memcmp(guest_slot, slot, 4) ||
        memcmp(guest_status, (uint8_t[8]){0}, 8))
        return false;
    for (unsigned i = 0; i < length; ++i)
        if (guest_output[i]) return false;
    if (pci_dma_write(&s->parent_obj, slot_bus, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, output_bus, output, length) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus + 4u, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus, status_data, 4) != MEMTX_OK)
        return false;
    s->lp_odb |= 2u;
    if (!(s->lp_irqmask & 4u)) pci_set_irq(&s->parent_obj, 1);
    fprintf(stderr, "accele160 EXPLORE stock followup mirrored "
            "event=%u output=0x%08" PRIx64 " bytes=%u sha256=%s "
            "status=%02x00000000000000 slot-word0=0 outbound=0x02 irq=%u\n",
            event, output_bus, length, digest, id, !(s->lp_irqmask & 4u));
    return true;
}

static bool accele160_stage_stock_next_slot(Accele160State *s,
                                            const uint8_t slot[64])
{
    const uint64_t slot_bus = s->set_mbox_ring + 192u;
    const uint64_t output_bus = accele160_le64(slot + 32);
    bool exact = slot[0] == 1 && !slot[1] &&
        slot[2] == 0x20 && slot[3] == 0x50 &&
        slot[4] == 0xec && slot[5] == 0x03 &&
        slot[21] == 1 && slot[40] == 0xec && slot[41] == 0x03 &&
        output_bus >= 0x00100000u && !(output_bus & 3u) &&
        output_bus + 1004u <= 0x20000000u;
    for (unsigned j = 0; j < 64; ++j)
        if (j != 0 && j != 2 && j != 3 && j != 4 && j != 5 &&
            j != 21 && !(j >= 32 && j < 40) && j != 40 && j != 41 &&
            slot[j])
            exact = false;
    if (!exact ||
        !accele160_stage_ring_slot(s, slot_bus, slot) ||
        !accele160_stage_guest_window(
            s, 'S', s->set_mbox_status_ring, 32) ||
        !accele160_stage_guest_window(s, 'T', output_bus, 1004))
        return false;
    return true;
}

static void accele160_trace_stock_next(Accele160State *s,
                                       uint64_t output_bus)
{
    uint8_t output[1004];
    char query[48];
    uint32_t descriptor[6] = {0};
    uint32_t pointer = accele160_bridge_request(s, "I 1450\n");
    for (unsigned i = 0; i < sizeof(output); i += 4) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        uint32_t word = accele160_bridge_request(s, query);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    g_autofree gchar *sha =
        g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                    sizeof(output));
    if (pointer == 0xc0611320u)
        for (unsigned j = 0; j < 6; ++j) {
            snprintf(query, sizeof(query), "R %08x 4 0\n",
                     pointer + j * 4u);
            descriptor[j] = accele160_bridge_request(s, query);
        }
    snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 24u);
    uint32_t status0 = accele160_bridge_request(s, query);
    snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 28u);
    uint32_t status1 = accele160_bridge_request(s, query);
    snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_ring + 192u);
    uint32_t slot0 = accele160_bridge_request(s, query);
    fprintf(stderr, "accele160 EXPLORE stock next model event=3 "
            "slot3=0x%08x status3=%08x%08x output-sha256=%s "
            "ring-cursor=0x%08x dma1-status=0x%08x "
            "dma1-control=0x%08x dma1-pointer=0x%08x "
            "descriptor=%08x,%08x,%08x,%08x,%08x,%08x "
            "outbound=0x%08x no-guest-copy=1\n",
            slot0, status0, status1, sha,
            accele160_bridge_request(s, "R c048e70c 4 0\n"),
            accele160_bridge_request(s, "I 1444\n"),
            accele160_bridge_request(s, "I 1440\n"), pointer,
            descriptor[0], descriptor[1], descriptor[2],
            descriptor[3], descriptor[4], descriptor[5],
            accele160_bridge_request(s, "I 132c\n"));
}

static bool accele160_mirror_stock_next(Accele160State *s,
                                       const uint8_t slot[64],
                                       uint32_t outbound)
{
    const uint64_t slot_bus = s->set_mbox_ring + 192u;
    const uint64_t status_bus = s->set_mbox_status_ring + 24u;
    const uint64_t output_bus = accele160_le64(slot + 32);
    uint8_t output[1004], guest_output[1004], guest_status[8], guest_slot[4];
    const uint8_t zero[4] = {0}, residual[4] = {0xec, 0xff, 0xff, 0xff};
    const uint8_t id_status[4] = {1, 0, 0, 0};
    uint32_t descriptor[6];
    char request[48];
    g_autofree gchar *digest = NULL;
    if (slot[0] != 1 || slot[1] || slot[2] != 0x20 ||
        slot[3] != 0x50 || slot[4] != 0xec || slot[5] != 0x03 ||
        slot[21] != 1 || slot[40] != 0xec || slot[41] != 0x03 ||
        output_bus < 0x00100000u || (output_bus & 3u) ||
        output_bus + 1004u > 0x20000000u ||
        outbound != 2u || (s->lp_odb & 2u) ||
        accele160_bridge_request(s, "I 1450\n") != 0xc0611320u ||
        accele160_bridge_request(s, "R c048e70c 4 0\n") !=
            s->set_mbox_ring + 256u)
        return false;
    for (unsigned j = 0; j < 64; ++j)
        if (j != 0 && j != 2 && j != 3 && j != 4 && j != 5 &&
            j != 21 && !(j >= 32 && j < 40) &&
            j != 40 && j != 41 && slot[j])
            return false;
    for (unsigned j = 0; j < 6; ++j) {
        snprintf(request, sizeof(request), "R %08x 4 0\n",
                 0xc0611320u + j * 4u);
        descriptor[j] = accele160_bridge_request(s, request);
    }
    if (descriptor[0] || descriptor[1] != output_bus || descriptor[2] ||
        descriptor[3] != 0xc060c300u || descriptor[4] != 1004u ||
        descriptor[5] != 0x3fu)
        return false;
    for (unsigned i = 0; i < sizeof(output); i += 4) {
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        uint32_t word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                         sizeof(output));
    if (strcmp(digest,
               "a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8"))
        return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", slot_bus);
    if (accele160_bridge_request(s, request) != 0u) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", status_bus);
    if (accele160_bridge_request(s, request) != 1u) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             status_bus + 4u);
    if (accele160_bridge_request(s, request) != 0xffffffecu) return false;
    if (pci_dma_read(&s->parent_obj, output_bus, guest_output,
                     sizeof(guest_output)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, status_bus, guest_status, 8) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, slot_bus, guest_slot, 4) != MEMTX_OK ||
        memcmp(guest_slot, slot, 4) ||
        memcmp(guest_status, (uint8_t[8]){0}, 8))
        return false;
    /* Linux may reuse the controller-info output buffer from slot 0. */
    if (!s->stock_first_ring_mirrored) return false;
    if (memcmp(guest_output, output, sizeof(output))) {
        for (unsigned i = 0; i < sizeof(guest_output); ++i)
            if (guest_output[i]) return false;
    }
    if (pci_dma_write(&s->parent_obj, slot_bus, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, output_bus, output,
                      sizeof(output)) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus + 4, residual, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus, id_status, 4) != MEMTX_OK)
        return false;
    s->lp_odb |= 2u;
    if (!(s->lp_irqmask & 4u)) pci_set_irq(&s->parent_obj, 1);
    fprintf(stderr, "accele160 EXPLORE stock next mirrored event=3 "
            "output=0x%08" PRIx64 " bytes=1004 sha256=%s "
            "status=01000000ecffffff slot-word0=0 outbound=0x02 irq=%u\n",
            output_bus, digest, !(s->lp_irqmask & 4u));
    return true;
}

static bool accele160_stage_stock_scsi_slot(Accele160State *s,
                                            const uint8_t slot[64],
                                            uint64_t *sense_bus,
                                            uint64_t *data_bus)
{
    uint8_t normalized[64];
    memcpy(normalized, slot, sizeof(normalized));
    memset(normalized, 0, 2);
    memset(normalized + 8, 0, 8);
    memset(normalized + 32, 0, 8);
    g_autofree gchar *sha =
        g_compute_checksum_for_data(G_CHECKSUM_SHA256, normalized,
                                    sizeof(normalized));
    *sense_bus = accele160_le64(slot + 8);
    *data_bus = accele160_le64(slot + 32);
    if (!(slot[0] || slot[1]) ||
        strcmp(sha,
               "e80bb8e10b486807e3959c6d29eeb28eb6dc1582a0fed0200dce26a4735e18ad") ||
        *sense_bus < 0x00100000u || (*sense_bus & 3u) ||
        *sense_bus + 16u > 0x20000000u ||
        *data_bus < 0x00100000u || (*data_bus & 3u) ||
        *data_bus + 36u > 0x20000000u ||
        !(*sense_bus + 16u <= *data_bus ||
          *data_bus + 36u <= *sense_bus))
        return false;
    return accele160_stage_ring_slot(s, s->set_mbox_ring + 256u, slot) &&
        accele160_stage_guest_window(s, 'S',
                                     s->set_mbox_status_ring, 40) &&
        accele160_stage_guest_window(s, 'U', *sense_bus, 16) &&
        accele160_stage_guest_window(s, 'V', *data_bus, 36);
}

static void accele160_trace_stock_scsi(Accele160State *s,
                                       uint64_t sense_bus,
                                       uint64_t data_bus)
{
    char query[48];
    uint8_t sense[16], data[36];
    for (unsigned i = 0; i < sizeof(sense); i += 4) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 sense_bus + i);
        uint32_t word = accele160_bridge_request(s, query);
        for (unsigned k = 0; k < 4; ++k)
            sense[i + k] = word >> (8 * k);
    }
    for (unsigned i = 0; i < sizeof(data); i += 4) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 data_bus + i);
        uint32_t word = accele160_bridge_request(s, query);
        for (unsigned k = 0; k < 4; ++k)
            data[i + k] = word >> (8 * k);
    }
    snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 32u);
    uint32_t status0 = accele160_bridge_request(s, query);
    snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_status_ring + 36u);
    uint32_t status1 = accele160_bridge_request(s, query);
    snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
             s->set_mbox_ring + 256u);
    uint32_t slot0 = accele160_bridge_request(s, query);
    g_autofree gchar *sense_sha =
        g_compute_checksum_for_data(G_CHECKSUM_SHA256, sense, sizeof(sense));
    g_autofree gchar *data_sha =
        g_compute_checksum_for_data(G_CHECKSUM_SHA256, data, sizeof(data));
    fprintf(stderr, "accele160 EXPLORE stock scsi model event=4 "
            "slot4=0x%08x status4=%08x%08x "
            "sense-sha256=%s data-sha256=%s "
            "ring-cursor=0x%08x dma1-status=0x%08x "
            "dma1-control=0x%08x dma1-pointer=0x%08x "
            "outbound=0x%08x no-guest-copy=1\n",
            slot0, status0, status1, sense_sha, data_sha,
            accele160_bridge_request(s, "R c048e70c 4 0\n"),
            accele160_bridge_request(s, "I 1444\n"),
            accele160_bridge_request(s, "I 1440\n"),
            accele160_bridge_request(s, "I 1450\n"),
            accele160_bridge_request(s, "I 132c\n"));
    fprintf(stderr, "accele160 EXPLORE stock scsi model "
            "sense-hex=");
    for (unsigned i = 0; i < sizeof(sense); ++i)
        fprintf(stderr, "%02x", sense[i]);
    fprintf(stderr, " data-hex=");
    for (unsigned i = 0; i < sizeof(data); ++i)
        fprintf(stderr, "%02x", data[i]);
    fputc('\n', stderr);
}

static void accele160_trace_stock_scsi_isp(Accele160State *s,
                                            const char *phase)
{
    char query[48];
    uint32_t control = accele160_bridge_request(
        s, "R c03e5bc8 4 0\n");
    uint32_t consumer = 0xffffffffu;
    if (control >= 0xc0000000u && control <= 0xc0ffffacu) {
        snprintf(query, sizeof(query), "R %08x 2 0\n", control + 0x52u);
        consumer = accele160_bridge_request(s, query);
    }
    fprintf(stderr, "accele160 EXPLORE stock scsi isp phase=%s "
            "producer=0x%08x response=0x%08x "
            "control=0x%08x consumer=0x%08x\n",
            phase,
            accele160_bridge_request(s, "R 8bf00078 2 0\n"),
            accele160_bridge_request(s, "R 8bf0007a 2 0\n"),
            control, consumer);
    for (unsigned entry = 30; entry <= 31; ++entry) {
        fprintf(stderr, "accele160 EXPLORE stock scsi isp phase=%s "
                "entry=%u base=0x%08x hex=",
                phase, entry, 0xc0600df0u + entry * 64u);
        for (unsigned i = 0; i < 64u; i += 4u) {
            snprintf(query, sizeof(query), "R %08x 4 0\n",
                     0xc0600df0u + entry * 64u + i);
            uint32_t word = accele160_bridge_request(s, query);
            for (unsigned k = 0; k < 4u; ++k)
                fprintf(stderr, "%02x", (word >> (8u * k)) & 0xffu);
        }
        fputc('\n', stderr);
    }
}

static void accele160_trace_native_followup_model(Accele160State *s,
                                                   unsigned event,
                                                   uint64_t pdev_bus)
{
    uint8_t health[128], pdev[512];
    char query[48];
    uint32_t status[4];
    for (unsigned i = 0; i < sizeof(health); i += 4) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 s->set_mbox_health + i);
        uint32_t word = accele160_bridge_request(s, query);
        for (unsigned k = 0; k < 4; ++k)
            health[i + k] = word >> (8 * k);
    }
    g_autofree gchar *health_sha =
        g_compute_checksum_for_data(G_CHECKSUM_SHA256, health,
                                    sizeof(health));
    g_autofree gchar *pdev_sha = NULL;
    if (event >= 2 && pdev_bus) {
        for (unsigned i = 0; i < sizeof(pdev); i += 4) {
            snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                     pdev_bus + i);
            uint32_t word = accele160_bridge_request(s, query);
            for (unsigned k = 0; k < 4; ++k)
                pdev[i + k] = word >> (8 * k);
        }
        pdev_sha = g_compute_checksum_for_data(G_CHECKSUM_SHA256, pdev,
                                                sizeof(pdev));
    }
    for (unsigned j = 0; j < 4; ++j) {
        snprintf(query, sizeof(query), "R %08" PRIx64 " 4 0\n",
                 s->set_mbox_status_ring + 8u + j * 4u);
        status[j] = accele160_bridge_request(s, query);
    }
    fprintf(stderr, "accele160 EXPLORE native followup model event=%u "
            "status1=%08x%08x status2=%08x%08x "
            "health-sha256=%s pdev-sha256=%s outbound=0x%08x "
            "no-guest-copy=1\n", event, status[0], status[1], status[2],
            status[3], health_sha, pdev_sha ? pdev_sha : "none",
            accele160_bridge_request(s, "I 132c\n"));
}

static bool accele160_mirror_native_followup(Accele160State *s,
                                             unsigned event,
                                             const uint8_t slot[64],
                                             const uint32_t report[15],
                                             uint32_t outbound)
{
    const unsigned length = event == 1 ? 128u : 512u;
    const uint8_t id = event == 1 ? 2u : 1u;
    const uint8_t ioctl = event == 1 ? 0x11u : 0x05u;
    const char *expected_sha = event == 1 ?
        "67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32" :
        "9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41";
    const uint64_t output_bus = accele160_le64(slot + 32);
    const uint64_t slot_bus = s->set_mbox_ring + event * 64u;
    const uint64_t status_bus = s->set_mbox_status_ring + event * 8u;
    uint8_t output[512], guest_output[512], guest_status[8], guest_slot[4];
    const uint8_t zero[4] = {0};
    const uint8_t status_data[4] = {id, 0, 0, 0};
    char request[48];
    g_autofree gchar *digest = NULL;

    if (event < 1 || event > 2 || slot[0] != id || slot[1] ||
        slot[2] != 0x20 || slot[3] != 0x50 ||
        slot[4] != (uint8_t)length || slot[5] != (uint8_t)(length >> 8) ||
        slot[21] != ioctl || slot[40] != (uint8_t)length ||
        slot[41] != (uint8_t)(length >> 8) ||
        output_bus < 0x00100000u || (output_bus & 3u) ||
        output_bus + length > 0x20000000u ||
        (event == 1 && output_bus != s->set_mbox_health) ||
        outbound != 2u || (s->lp_odb & 2u))
        return false;
    for (unsigned j = 0; j < 64; ++j)
        if (j != 0 && j != 2 && j != 3 && j != 4 && j != 5 &&
            j != 21 && !(j >= 32 && j < 40) && j != 40 && j != 41 &&
            slot[j])
            return false;
    if (report[0] != 0x32474e52u || report[1] != event ||
        report[2] != event || report[3] != slot_bus ||
        report[4] != accele160_fnv1a(slot, 64) || report[5] != 2u ||
        report[6] != id || report[7] != ioctl ||
        report[8] != output_bus || report[9] != length ||
        report[10] != status_bus + 8u || report[11] != event + 1u ||
        report[12] != 3u || report[13] != 2u || report[14] != id)
        return false;
    for (unsigned i = 0; i < length; i += 4) {
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        uint32_t word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output, length);
    if (strcmp(digest, expected_sha)) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", slot_bus);
    if (accele160_bridge_request(s, request) != 0u) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", status_bus);
    if (accele160_bridge_request(s, request) != id) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             status_bus + 4u);
    if (accele160_bridge_request(s, request) != 0u) return false;
    if (pci_dma_read(&s->parent_obj, slot_bus, guest_slot, 4) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, status_bus, guest_status, 8) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, output_bus, guest_output, length) != MEMTX_OK ||
        memcmp(guest_slot, slot, 4) ||
        memcmp(guest_status, (uint8_t[8]){0}, 8))
        return false;
    for (unsigned i = 0; i < length; ++i)
        if (guest_output[i]) return false;
    if (pci_dma_write(&s->parent_obj, slot_bus, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, output_bus, output, length) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus + 4u, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus, status_data, 4) != MEMTX_OK)
        return false;
    s->lp_odb |= 2u;
    if (!(s->lp_irqmask & 4u)) pci_set_irq(&s->parent_obj, 1);
    fprintf(stderr, "accele160 EXPLORE native followup mirrored "
            "event=%u output=0x%08" PRIx64 " bytes=%u sha256=%s "
            "status=%02x00000000000000 slot-word0=0 outbound=0x02 irq=%u\n",
            event, output_bus, length, digest, id, !(s->lp_irqmask & 4u));
    s->native_followup_mirror_mask |= 1u << (event - 1u);
    return true;
}

static bool accele160_mirror_native_next(Accele160State *s,
                                        const uint8_t slot[64],
                                        const uint32_t report[15],
                                        uint32_t outbound)
{
    const uint64_t slot_bus = s->set_mbox_ring + 192u;
    const uint64_t status_bus = s->set_mbox_status_ring + 24u;
    const uint64_t output_bus = accele160_le64(slot + 32);
    uint8_t output[1004], guest_output[1004], guest_status[8], guest_slot[4];
    const uint8_t zero[4] = {0}, residual[4] = {0xec, 0xff, 0xff, 0xff};
    const uint8_t id_status[4] = {1, 0, 0, 0};
    char request[48];
    g_autofree gchar *digest = NULL;
    if (!s->native_first_ring_mirrored ||
        s->native_followup_mirror_mask != 3u ||
        slot[0] != 1 || slot[1] || slot[2] != 0x20 ||
        slot[3] != 0x50 || slot[4] != 0xec || slot[5] != 0x03 ||
        slot[21] != 1 || slot[40] != 0xec || slot[41] != 0x03 ||
        output_bus < 0x00100000u || (output_bus & 3u) ||
        output_bus + 1004u > 0x20000000u ||
        outbound != 2u || (s->lp_odb & 2u))
        return false;
    for (unsigned j = 0; j < 64; ++j)
        if (j != 0 && j != 2 && j != 3 && j != 4 && j != 5 &&
            j != 21 && !(j >= 32 && j < 40) &&
            j != 40 && j != 41 && slot[j])
            return false;
    if (report[0] != 0x32474e52u || report[1] != 3u ||
        report[2] != 3u || report[3] != slot_bus ||
        report[4] != accele160_fnv1a(slot, 64) ||
        report[5] != 2u || report[6] != 1u ||
        report[7] != 1u || report[8] != output_bus ||
        report[9] != 1004u ||
        report[10] != status_bus + 8u ||
        report[11] != 4u || report[12] != 3u ||
        report[13] != 2u || report[14] != 1u ||
        accele160_bridge_request(s, "R c0001f9c 4 0\n") !=
            s->set_mbox_ring + 256u ||
        accele160_bridge_request(s, "R c0001fb0 4 0\n") != 4u)
        return false;
    for (unsigned i = 0; i < sizeof(output); i += 4) {
        snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
                 output_bus + i);
        uint32_t word = accele160_bridge_request(s, request);
        for (unsigned k = 0; k < 4; ++k)
            output[i + k] = word >> (8 * k);
    }
    digest = g_compute_checksum_for_data(G_CHECKSUM_SHA256, output,
                                         sizeof(output));
    if (strcmp(digest,
               "a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8"))
        return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", slot_bus);
    if (accele160_bridge_request(s, request) != 0u) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n", status_bus);
    if (accele160_bridge_request(s, request) != 1u) return false;
    snprintf(request, sizeof(request), "R %08" PRIx64 " 4 0\n",
             status_bus + 4u);
    if (accele160_bridge_request(s, request) != 0xffffffecu) return false;
    if (pci_dma_read(&s->parent_obj, output_bus, guest_output,
                     sizeof(guest_output)) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, status_bus, guest_status, 8) != MEMTX_OK ||
        pci_dma_read(&s->parent_obj, slot_bus, guest_slot, 4) != MEMTX_OK ||
        memcmp(guest_slot, slot, 4) ||
        memcmp(guest_status, (uint8_t[8]){0}, 8))
        return false;
    if (memcmp(guest_output, output, sizeof(output))) {
        for (unsigned i = 0; i < sizeof(guest_output); ++i)
            if (guest_output[i]) return false;
    }
    if (pci_dma_write(&s->parent_obj, slot_bus, zero, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, output_bus, output,
                      sizeof(output)) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus + 4, residual, 4) != MEMTX_OK ||
        pci_dma_write(&s->parent_obj, status_bus, id_status, 4) != MEMTX_OK)
        return false;
    s->lp_odb |= 2u;
    if (!(s->lp_irqmask & 4u)) pci_set_irq(&s->parent_obj, 1);
    fprintf(stderr, "accele160 EXPLORE native next mirrored event=3 "
            "output=0x%08" PRIx64 " bytes=1004 sha256=%s "
            "status=01000000ecffffff slot-word0=0 outbound=0x02 irq=%u\n",
            output_bus, digest, !(s->lp_irqmask & 4u));
    return true;
}

static void accele160_submit_mailbox(Accele160State *s)
{
    char request[160];
    size_t i;
    if (s->lp_mailbox_pending) {
        fprintf(stderr, "accele160 lp mailbox busy, second submit ignored\n");
        return;
    }
    if (!(s->parent_obj.config[PCI_COMMAND] & PCI_COMMAND_MASTER)) {
        fprintf(stderr, "accele160 lp mailbox rejected: PCI bus master disabled\n");
        return;
    }
    if (!s->lp_mbox_address || (s->lp_mbox_address & 3) ||
        s->lp_mbox_address > 0xffffffffULL - sizeof(s->last_mailbox)) {
        fprintf(stderr, "accele160 lp mailbox rejected: invalid DMA pointer\n");
        return;
    }
    if (pci_dma_read(&s->parent_obj, s->lp_mbox_address,
                     s->last_mailbox, sizeof(s->last_mailbox)) != MEMTX_OK) {
        fprintf(stderr, "accele160 lp mailbox rejected: DMA read failed\n");
        return;
    }
    s->lp_mailbox_pending = true;
    s->lp_idb |= 1;
    fprintf(stderr, "accele160 lp mailbox submitted dma=0x%016" PRIx64
            " id=%u opcode=0x%02x ioctl=0x%02x pending=1\n",
            s->lp_mbox_address,
            s->last_mailbox[0] | (s->last_mailbox[1] << 8),
            s->last_mailbox[2], s->last_mailbox[21]);
    if (s->bridge_fd < 0) return;
    snprintf(request, sizeof(request), "M %016" PRIx64 " ", s->lp_mbox_address);
    i = strlen(request);
    for (unsigned j = 0; j < sizeof(s->last_mailbox); ++j) {
        snprintf(request + i, sizeof(request) - i, "%02x", s->last_mailbox[j]);
        i += 2;
    }
    request[i++] = '\n';
    request[i] = 0;
    fprintf(stderr, "accele160 lp mailbox bytes=%.*s\n", 128, request + 19);
    accele160_bridge_request(s, request);
    if (accele160_native_set_mbox_shape(s)) {
        uint32_t outbound = 0;
        for (unsigned attempt = 0; attempt < 20; ++attempt) {
            accele160_bridge_request(s, "S 1000000\n");
            outbound = accele160_bridge_request(s, "I 132c\n");
            if (outbound & 1) break;
        }
        if (outbound & 1) {
            uint32_t omr0 = accele160_bridge_request(s, "I 1318\n");
            uint32_t omr1 = accele160_bridge_request(s, "I 131c\n");
            if (omr0 == 1 && omr1 == 0x420u) {
                for (unsigned j = 0; j < 4; ++j)
                    s->aperture[LP_CMDSTS + j] = omr0 >> (8 * j);
                s->lp_idb &= ~1;
                s->lp_odb |= 1;
                s->set_mbox_ring = accele160_le64(s->last_mailbox + 32);
                s->stock_first_ring_mirrored = false;
                s->native_first_ring_mirrored = false;
                s->native_followup_mirror_mask = 0;
                s->set_mbox_status_ring =
                    accele160_le64(s->last_mailbox + 40);
                s->set_mbox_health =
                    accele160_le64(s->last_mailbox + 24);
                fprintf(stderr, "accele160 EXPLORE native set-mbox completion "
                        "id=1 status=0x0000 data=0x%08x no-dma=1\n", omr1);
            } else {
                fprintf(stderr, "accele160 EXPLORE native set-mbox rejected "
                        "outbound=0x%08x omr0=0x%08x omr1=0x%08x\n",
                        outbound, omr0, omr1);
            }
        } else {
            fprintf(stderr, "accele160 EXPLORE native set-mbox pending "
                    "after bounded i960 steps\n");
        }
    }
    if ((s->explore_set_mbox_trace || s->explore_set_mbox_bridge) &&
        s->explore_live_firmware &&
        s->last_mailbox[0] == 1 && s->last_mailbox[1] == 0 &&
        s->last_mailbox[2] == 0x20 && s->last_mailbox[3] == 0x40 &&
        s->last_mailbox[4] == 0x20 && s->last_mailbox[5] == 0x04 &&
        s->last_mailbox[6] == 0 && s->last_mailbox[7] == 0 &&
        s->last_mailbox[21] == 0x8e && s->last_mailbox[22] == 1) {
        uint32_t routed, outbound = 0, omr0 = 0, omr1 = 0;
        bool rings_valid = true;
        for (unsigned j = 0; j < 3; ++j) {
            unsigned offset = 24 + 8 * j;
            uint64_t address = 0;
            for (unsigned k = 0; k < 8; ++k)
                address |= (uint64_t)s->last_mailbox[offset + k] << (8 * k);
            if (!address || address > UINT32_MAX || (address & 0xfff))
                rings_valid = false;
        }
        for (unsigned j = 48; j < 64; ++j)
            if (s->last_mailbox[j]) rings_valid = false;
        if (!rings_valid) {
            fprintf(stderr, "accele160 EXPLORE set-mbox invalid ring shape\n");
            return;
        }
        for (unsigned attempt = 0; attempt < 100; ++attempt) {
            if (accele160_bridge_request(s, "P\n") & 0x100) break;
            accele160_bridge_request(s, "S 1000\n");
        }
        routed = accele160_bridge_request(s, "E 7\n");
        fprintf(stderr, "accele160 EXPLORE set-mbox route=0x%08x\n", routed);
        for (unsigned attempt = 0; attempt < 20; ++attempt) {
            accele160_bridge_request(s, "S 1000000\n");
            outbound = accele160_bridge_request(s, "I 132c\n");
            omr0 = accele160_bridge_request(s, "I 1318\n");
            omr1 = accele160_bridge_request(s, "I 131c\n");
            fprintf(stderr, "accele160 EXPLORE set-mbox step=%u outbound=0x%08x "
                    "omr0=0x%08x omr1=0x%08x\n", attempt + 1, outbound,
                    omr0, omr1);
            if (outbound & 1) break;
        }
        if (s->explore_set_mbox_bridge && routed == 0xc0000408u &&
            (outbound & 1) && omr0 == 1 && omr1 == 0x420u) {
            for (unsigned j = 0; j < 4; ++j)
                s->aperture[LP_CMDSTS + j] = omr0 >> (8 * j);
            s->lp_idb &= ~1;
            s->lp_odb |= 1;
            s->stock_first_ring_mirrored = false;
            s->native_first_ring_mirrored = false;
            s->native_followup_mirror_mask = 0;
            for (unsigned j = 0; j < 8; ++j)
                s->set_mbox_ring |=
                    (uint64_t)s->last_mailbox[32 + j] << (8 * j);
            s->set_mbox_status_ring =
                accele160_le64(s->last_mailbox + 40);
            s->set_mbox_health =
                accele160_le64(s->last_mailbox + 24);
            fprintf(stderr, "accele160 EXPLORE stock set-mbox completion reflected "
                    "from observed i960 registers\n");
        }
    }
    if ((s->explore_live_firmware || s->explore_native_poll) &&
        s->live_completion_count < (s->explore_native_poll ? 5u : 8u)) {
        uint64_t output_bus = 0;
        uint32_t output_length = 0;
        uint32_t outbound = 0;
        uint32_t message0;
        uint32_t message1;
        uint8_t output[512];
        char query[48];
        unsigned expected = s->last_mailbox[21] == 0x01 ? 512 :
                            s->last_mailbox[21] == 0x11 ? 128 :
                            s->last_mailbox[21] == 0x15 ? 64 :
                            s->last_mailbox[21] == 0xd0 ? 128 :
                            s->last_mailbox[21] == 0x2d ? 512 : 0;
        for (unsigned j = 0; j < 8; ++j)
            output_bus |= (uint64_t)s->last_mailbox[32 + j] << (8 * j);
        for (unsigned j = 0; j < 4; ++j)
            output_length |= (uint32_t)s->last_mailbox[40 + j] << (8 * j);
        if (s->explore_live_firmware) {
            for (unsigned attempt = 0; attempt < 100; ++attempt) {
                if (accele160_bridge_request(s, "P\n") & 0x100) break;
                accele160_bridge_request(s, "S 1000\n");
            }
        }
        if (s->last_mailbox[2] == 0x20 && expected &&
            s->last_mailbox[3] == 0x10 &&
            (s->last_mailbox[4] | s->last_mailbox[5] << 8 |
             s->last_mailbox[6] << 16) == expected &&
            output_length == expected && output_bus &&
            output_bus <= UINT32_MAX - expected &&
            (!s->explore_native_poll ||
             (s->last_mailbox[0] == 0x7f && s->last_mailbox[1] == 0 &&
              output_bus == 0x9f3e0 &&
              ((s->live_completion_count == 0 &&
                s->last_mailbox[21] == 0x01 && expected == 512) ||
               (s->live_completion_count == 1 &&
                s->last_mailbox[21] == 0x11 && expected == 128) ||
               (s->live_completion_count == 2 &&
                s->last_mailbox[21] == 0x15 && expected == 64) ||
               (s->live_completion_count == 3 &&
                s->last_mailbox[21] == 0xd0 && expected == 128) ||
               (s->live_completion_count == 4 &&
                s->last_mailbox[21] == 0x2d && expected == 512)))) &&
            (s->explore_native_poll ||
             (accele160_bridge_request(s, "P\n") & 0x100))) {
            uint32_t routed = accele160_bridge_request(s, "E 7\n");
            if (!s->explore_native_poll && routed != 0xc0000408u)
                return;
            for (unsigned attempt = 0; attempt < 20; ++attempt) {
                accele160_bridge_request(s, "S 1000000\n");
                outbound = accele160_bridge_request(s, "I 132c\n");
                if (outbound & 1) break;
            }
            if (outbound & 1) {
                for (unsigned j = 0; j < output_length; j += 4) {
                    uint32_t word;
                    snprintf(query, sizeof(query), "U %08" PRIx64 "\n",
                             output_bus + j);
                    word = accele160_bridge_request(s, query);
                    for (unsigned k = 0; k < 4; ++k)
                        output[j + k] = word >> (8 * k);
                }
                message0 = accele160_bridge_request(s, "I 1318\n");
                message1 = accele160_bridge_request(s, "I 131c\n");
                if (s->trace_live_reply) {
                    fprintf(stderr, "accele160 EXPLORE live reply ioctl=0x%02x id=%u bytes=%u hex=",
                            s->last_mailbox[21], message0 & 0xffff,
                            output_length);
                    for (unsigned j = 0; j < output_length; ++j)
                        fprintf(stderr, "%02x", output[j]);
                    fputc('\n', stderr);
                }
                if (pci_dma_write(&s->parent_obj, output_bus,
                                  output, output_length) == MEMTX_OK) {
                    for (unsigned j = 0; j < 4; ++j)
                        s->aperture[LP_CMDSTS + j] = message0 >> (8 * j);
                    s->lp_idb &= ~1;
                    s->lp_odb |= 1;
                    ++s->live_completion_count;
                    fprintf(stderr, "accele160 EXPLORE %s firmware completion "
                            "ioctl=0x%02x id=%u status=0x%04x "
                            "residual=0x%08x dma=0x%08" PRIx64 " bytes=%u\n",
                            s->explore_native_poll ? "native" : "stock",
                            s->last_mailbox[21],
                            message0 & 0xffff, message0 >> 16, message1,
                            output_bus, output_length);
                }
            }
        }
    }
    if (s->explore_rom_ioctls) {
        uint64_t dma = 0;
        uint32_t count = 0;
        uint8_t info[512] = {0};
        unsigned expected = s->last_mailbox[21] == 0x01 ? 512 :
                            s->last_mailbox[21] == 0x11 ? 128 :
                            s->last_mailbox[21] == 0xd0 ? 128 :
                            s->last_mailbox[21] == 0x2d ? 512 : 0;
        for (unsigned j = 0; j < 8; ++j)
            dma |= (uint64_t)s->last_mailbox[32 + j] << (8 * j);
        for (unsigned j = 0; j < 4; ++j)
            count |= (uint32_t)s->last_mailbox[40 + j] << (8 * j);
        if (s->last_mailbox[2] == 0x20 && expected &&
            s->last_mailbox[3] == 0x10 &&
            (s->last_mailbox[4] | s->last_mailbox[5] << 8 |
             s->last_mailbox[6] << 16) == expected &&
            count == expected && dma && dma <= UINT32_MAX - expected &&
            pci_dma_write(&s->parent_obj, dma, info, expected) == MEMTX_OK) {
            s->lp_idb &= ~1;
            s->lp_odb |= 1;
            s->aperture[LP_CMDSTS] = s->last_mailbox[0];
            s->aperture[LP_CMDSTS + 1] = s->last_mailbox[1];
            s->aperture[LP_CMDSTS + 2] = 0;
            s->aperture[LP_CMDSTS + 3] = 0;
            fprintf(stderr, "accele160 EXPLORE synthetic IOCTL completion "
                    "ioctl=0x%02x id=%u dma=0x%08" PRIx64 " bytes=%u status=0\n",
                    s->last_mailbox[21],
                    s->last_mailbox[0] | s->last_mailbox[1] << 8,
                    dma, count);
        } else {
            fprintf(stderr, "accele160 EXPLORE IOCTL request rejected; pending\n");
        }
    }
}

static void accele160_trace(Accele160State *s, char operation, hwaddr addr,
                           uint64_t value, unsigned size)
{
    if (s->access_count < s->trace_limit) {
        fprintf(stderr, "accele160 bar0 %c offset=0x%04" HWADDR_PRIx
                " size=%u value=0x%0*" PRIx64 "\n",
                operation, addr, size, size * 2, value);
    } else if (s->access_count == s->trace_limit) {
        fprintf(stderr, "accele160 bar0 trace-limit=%u reached\n",
                s->trace_limit);
    }
    ++s->access_count;
}

static uint64_t accele160_read(void *opaque, hwaddr addr, unsigned size)
{
    Accele160State *s = opaque;
    uint64_t value = 0;
    unsigned i;

    if (addr + size > ACCELE160_BAR_SIZE) {
        return UINT64_MAX;
    }
    if (s->bridge_fd >= 0 && addr >= 0x1000) {
        value = accele160_bridge(s, 'R', s->piatvr + addr, size, 0);
        accele160_trace(s, 'R', addr, value, size);
        return value;
    }
    if (s->bridge_fd >= 0 && size == 1) {
        if (addr == LP_IDB) value = s->lp_idb;
        else if (addr == LP_ODB) value = s->lp_odb;
        else if (addr == LP_IRQMASK) value = s->lp_irqmask;
        if (addr == LP_IDB || addr == LP_ODB || addr == LP_IRQMASK) {
            accele160_trace(s, 'R', addr, value, size);
            return value;
        }
    }
    for (i = 0; i < size; ++i) {
        value |= (uint64_t)s->aperture[addr + i] << (8 * i);
    }
    accele160_trace(s, 'R', addr, value, size);
    return value;
}

static void accele160_write(void *opaque, hwaddr addr, uint64_t value,
                            unsigned size)
{
    Accele160State *s = opaque;
    unsigned i;

    if (addr + size > ACCELE160_BAR_SIZE) {
        return;
    }
    accele160_trace(s, 'W', addr, value, size);
    if (s->bridge_fd >= 0 && addr >= 0x1000) {
        accele160_bridge(s, 'W', s->piatvr + addr, size, value);
        return;
    }
    if (s->bridge_fd >= 0 && size == 1) {
        if (addr == LP_IRQMASK) {
            s->lp_irqmask = value;
            if ((s->explore_native_ring_mirror ||
                 s->explore_stock_ring_mirror) && (s->lp_odb & 2u))
                pci_set_irq(&s->parent_obj, !(s->lp_irqmask & 4u));
            return;
        }
        if (addr == LP_IDB) {
            bool first_ring_already_seen = s->set_mbox_slot_logged;
            if (value & 1) accele160_submit_mailbox(s);
            if ((value & 0x10) &&
                (s->explore_set_mbox_bridge || s->explore_native_ring_observe) &&
                s->set_mbox_ring && !s->set_mbox_slot_logged) {
                uint8_t slot[64];
                bool slot_ok;
                bool stock_window_staged = false;
                uint64_t stock_output_bus = 0;
                s->set_mbox_slot_logged = true;
                slot_ok = pci_dma_read(&s->parent_obj, s->set_mbox_ring,
                                       slot, sizeof(slot)) == MEMTX_OK;
                if (slot_ok) {
                    fprintf(stderr, "accele160 EXPLORE memory-mailbox slot "
                            "dma=0x%016" PRIx64 " hex=", s->set_mbox_ring);
                    for (unsigned j = 0; j < sizeof(slot); ++j)
                        fprintf(stderr, "%02x", slot[j]);
                    fputc('\n', stderr);
                } else {
                    fprintf(stderr, "accele160 EXPLORE memory-mailbox slot "
                            "DMA read failed\n");
                }
                fprintf(stderr, "accele160 EXPLORE memory-mailbox i960 "
                        "inbound=0x%08x mask=0x%08x outbound=0x%08x "
                        "cpu=0x%08x\n",
                        accele160_bridge_request(s, "I 1320\n"),
                        accele160_bridge_request(s, "I 1324\n"),
                        accele160_bridge_request(s, "I 132c\n"),
                        accele160_bridge_request(s, "P\n"));
                if (s->explore_stock_ring_memory && slot_ok) {
                    stock_output_bus = accele160_le64(slot + 32);
                    if (slot[0] == 1 && slot[1] == 0 && slot[2] == 0x20 &&
                        slot[3] == 0x50 && slot[4] == 0xec &&
                        slot[5] == 0x03 && slot[21] == 1 &&
                        slot[40] == 0xec && slot[41] == 0x03 &&
                        stock_output_bus >= 0x00100000u &&
                        !(stock_output_bus & 3u) &&
                        stock_output_bus + 1004u <= 0x20000000u &&
                        accele160_trace_ring_guest(s, stock_output_bus,
                                                   "before-idb10") &&
                        accele160_stage_ring_slot(s, s->set_mbox_ring, slot) &&
                        accele160_stage_guest_window(
                            s, 'S', s->set_mbox_status_ring, 24) &&
                        accele160_stage_guest_window(
                            s, 'H', s->set_mbox_health, 128) &&
                        accele160_stage_guest_window(
                            s, 'O', stock_output_bus, 1004)) {
                        stock_window_staged = true;
                        accele160_trace_ring_model(s, stock_output_bus,
                                                   "before-idb10");
                    } else {
                        fprintf(stderr, "accele160 EXPLORE stock ring "
                                "guest window staging rejected\n");
                    }
                }
                if (s->explore_native_ring_observe && slot_ok) {
                    uint64_t output_bus = accele160_le64(slot + 32);
                    bool exact_slot = slot[0] == 1 && slot[1] == 0 &&
                        slot[2] == 0x20 && slot[3] == 0x50 &&
                        slot[4] == 0xec && slot[5] == 0x03 &&
                        slot[6] == 0 && slot[7] == 0 &&
                        slot[21] == 1 &&
                        slot[40] == 0xec && slot[41] == 0x03 &&
                        slot[42] == 0 && slot[43] == 0 &&
                        output_bus >= 0x00100000u &&
                        !(output_bus & 3u) &&
                        output_bus + 1004u <= 0x20000000u &&
                        !(output_bus < s->set_mbox_ring + 32768u &&
                          s->set_mbox_ring < output_bus + 1004u) &&
                        !(output_bus < s->set_mbox_status_ring + 4096u &&
                          s->set_mbox_status_ring < output_bus + 1004u) &&
                        !(output_bus < s->set_mbox_health + 1024u &&
                          s->set_mbox_health < output_bus + 1004u);
                    for (unsigned j = 8; j < sizeof(slot); ++j)
                        if (j != 21 && !(j >= 32 && j < 40) &&
                            !(j >= 40 && j < 44) && slot[j])
                            exact_slot = false;
                    if (exact_slot &&
                        accele160_trace_ring_guest(s, output_bus,
                                                           "before-idb10")) {
                        if (accele160_stage_ring_slot(
                                s, s->set_mbox_ring, slot) &&
                            accele160_stage_guest_window(
                                s, 'S', s->set_mbox_status_ring, 24) &&
                            accele160_stage_guest_window(
                                s, 'H', s->set_mbox_health, 128) &&
                            accele160_stage_guest_window(
                                s, 'O', output_bus, 1004)) {
                            accele160_trace_ring_model(
                                s, output_bus, "before-idb10");
                            uint32_t local = accele160_bridge_request(s, "D 10\n");
                            fprintf(stderr, "accele160 EXPLORE native ring staged "
                                    "dma=0x%08" PRIx64 " output=0x%08" PRIx64
                                    " local-idb=0x%08x no-completion=1\n",
                                    s->set_mbox_ring, output_bus, local);
                            for (unsigned step = 0; step < 5; ++step)
                                accele160_bridge_request(s, "S 1000000\n");
                            uint32_t observer[13];
                            char query[40];
                            for (unsigned j = 0; j < 13; ++j) {
                                snprintf(query, sizeof(query),
                                         "R %08x 4 0\n",
                                         0xc0001f90u + j * 4u);
                                observer[j] = accele160_bridge_request(s, query);
                            }
                            fprintf(stderr, "accele160 EXPLORE native ring "
                                    "observer marker=0x%08x state=0x%08x "
                                    "digest=0x%08x cursor=0x%08x "
                                    "output=0x%08x length=%u id=%u "
                                    "seen-idb=0x%08x completions=%u "
                                    "output-digest=0x%08x dma-status=0x%08x "
                                    "status-id=%u residual=0x%08x\n",
                                    observer[0], observer[1], observer[2],
                                    observer[3], observer[4], observer[5],
                                    observer[6], observer[7], observer[8],
                                    observer[9], observer[10], observer[11],
                                    observer[12]);
                            accele160_trace_ring_model(
                                s, output_bus, "after-5m");
                            accele160_trace_ring_guest(s, output_bus,
                                                               "after-5m");
                            uint32_t outbound = accele160_bridge_request(
                                s, "I 132c\n");
                            fprintf(stderr, "accele160 EXPLORE native ring "
                                    "outbound=0x%08x no-guest-mirror=1\n",
                                    outbound);
                            if (s->explore_native_ring_mirror &&
                                accele160_mirror_native_ring(
                                    s, slot, output_bus, observer, outbound))
                                accele160_trace_ring_guest(
                                    s, output_bus, "after-mirror");
                        } else {
                            fprintf(stderr, "accele160 EXPLORE native ring "
                                    "model staging rejected\n");
                        }
                    } else {
                        fprintf(stderr, "accele160 EXPLORE native ring "
                                "guest slot rejected or DMA snapshot failed\n");
                    }
                }
                if (s->explore_mmbox_doorbell_observe ||
                    s->explore_mmbox_doorbell_control) {
                    uint32_t local, mask, unmasked, route;
                    accele160_trace_mmbox_object(s, "before-idb10");
                    local = accele160_bridge_request(s,
                        s->explore_mmbox_doorbell_observe ? "D 10\n" : "I 1320\n");
                    mask = accele160_bridge_request(s, "I 1328\n");
                    unmasked = accele160_bridge_request(s, "Q\n");
                    route = accele160_bridge_request(s, "E 7\n");
                    fprintf(stderr, "accele160 EXPLORE mmbox-idb10 mode=%s "
                            "local=0x%08x "
                            "mask=0x%08x unmasked=0x%08x route=0x%08x\n",
                            s->explore_mmbox_doorbell_observe ? "latch" : "control",
                            local, mask, unmasked, route);
                    const unsigned max_steps =
                        s->explore_stock_ring_memory ? 20u : 5u;
                    for (unsigned step = 0; step < max_steps; ++step) {
                        uint32_t ip = accele160_bridge_request(s, "S 1000000\n");
                        fprintf(stderr, "accele160 EXPLORE mmbox-idb10 step=%u "
                                "ip=0x%08x local=0x%08x status=0x%08x\n",
                                step + 1, ip,
                                accele160_bridge_request(s, "I 1320\n"),
                                accele160_bridge_request(s, "I 1324\n"));
                        if (step == 0 && stock_window_staged) {
                            uint32_t descriptor[6];
                            char query[40];
                            for (unsigned j = 0; j < 6; ++j) {
                                snprintf(query, sizeof(query),
                                         "R %08x 4 0\n", 0xc0611320u + j * 4u);
                                descriptor[j] = accele160_bridge_request(s, query);
                            }
                            fprintf(stderr, "accele160 EXPLORE stock dma1-first "
                                    "status=0x%08x control=0x%08x "
                                    "descriptor-pointer=0x%08x descriptor="
                                    "%08x,%08x,%08x,%08x,%08x,%08x "
                                    "queue-control=0x%08x queue-head=0x%08x\n",
                                    accele160_bridge_request(s, "I 1444\n"),
                                    accele160_bridge_request(s, "I 1440\n"),
                                    accele160_bridge_request(s, "I 1450\n"),
                                    descriptor[0], descriptor[1],
                                    descriptor[2], descriptor[3],
                                    descriptor[4], descriptor[5],
                                    accele160_bridge_request(
                                        s, "R c0400e70 4 0\n"),
                                    accele160_bridge_request(
                                        s, "R c03e2740 4 0\n"));
                        }
                    }
                    if (stock_window_staged) {
                        accele160_trace_ring_model(s, stock_output_bus,
                                                   "after-steps");
                        accele160_trace_ring_guest(s, stock_output_bus,
                                                   "after-steps");
                        if (s->explore_stock_ring_memory) {
                            uint32_t descriptor[6];
                            char query[40];
                            for (unsigned j = 0; j < 6; ++j) {
                                snprintf(query, sizeof(query),
                                         "R %08x 4 0\n", 0xc0611320u + j * 4u);
                                descriptor[j] = accele160_bridge_request(s, query);
                            }
                            fprintf(stderr, "accele160 EXPLORE stock dma1-wait "
                                    "status=0x%08x control=0x%08x "
                                    "descriptor-pointer=0x%08x descriptor="
                                    "%08x,%08x,%08x,%08x,%08x,%08x "
                                    "queue-control=0x%08x\n",
                                    accele160_bridge_request(s, "I 1444\n"),
                                    accele160_bridge_request(s, "I 1440\n"),
                                    accele160_bridge_request(s, "I 1450\n"),
                                    descriptor[0], descriptor[1],
                                    descriptor[2], descriptor[3],
                                    descriptor[4], descriptor[5],
                                    accele160_bridge_request(
                                        s, "R c0400e70 4 0\n"));
                            uint32_t outbound = accele160_bridge_request(
                                s, "I 132c\n");
                            fprintf(stderr, "accele160 EXPLORE stock ring "
                                    "outbound=0x%08x no-guest-mirror=1\n",
                                    outbound);
                            if (s->explore_stock_ring_mirror &&
                                accele160_mirror_stock_ring(
                                    s, slot, stock_output_bus, outbound))
                                accele160_trace_ring_guest(
                                    s, stock_output_bus, "after-mirror");
                        }
                    }
                    accele160_trace_mmbox_object(s, "after-steps");
                }
            }
            if ((value & 0x10) &&
                (s->explore_native_ring_mirror ||
                 s->explore_stock_ring_mirror) &&
                first_ring_already_seen && s->set_mbox_ring &&
                s->ring_followup_events < 4) {
                uint8_t status[8];
                ++s->ring_followup_events;
                if (pci_dma_read(&s->parent_obj, s->set_mbox_status_ring,
                                 status, sizeof(status)) == MEMTX_OK) {
                    fprintf(stderr, "accele160 EXPLORE ring followup event=%u "
                            "status=", s->ring_followup_events);
                    for (unsigned j = 0; j < sizeof(status); ++j)
                        fprintf(stderr, "%02x", status[j]);
                    fprintf(stderr, " lp-outbound=0x%02x\n", s->lp_odb);
                }
                for (unsigned slot_index = 1; slot_index <= 4; ++slot_index) {
                    uint8_t followup[64];
                    uint64_t dma = s->set_mbox_ring + slot_index * 64u;
                    if (pci_dma_read(&s->parent_obj, dma, followup,
                                     sizeof(followup)) != MEMTX_OK)
                        continue;
                    fprintf(stderr, "accele160 EXPLORE ring followup "
                            "event=%u slot=%u dma=0x%08" PRIx64 " hex=",
                            s->ring_followup_events, slot_index, dma);
                    for (unsigned j = 0; j < sizeof(followup); ++j)
                        fprintf(stderr, "%02x", followup[j]);
                    fputc('\n', stderr);
                    if ((s->explore_native_followup_observe ||
                         s->explore_stock_followup_observe) &&
                        slot_index <= 2 &&
                        slot_index == s->ring_followup_events &&
                        !accele160_stage_ring_slot(s, dma, followup))
                        fprintf(stderr, "accele160 EXPLORE ring followup "
                                "model staging rejected event=%u slot=%u\n",
                                s->ring_followup_events, slot_index);
                }
                if (s->ring_followup_events == 3 &&
                    s->explore_stock_next_observe &&
                    s->explore_stock_followup_mirror) {
                    uint8_t slot3[64];
                    bool valid = pci_dma_read(
                        &s->parent_obj, s->set_mbox_ring + 192u,
                        slot3, sizeof(slot3)) == MEMTX_OK;
                    uint64_t output = valid ? accele160_le64(slot3 + 32) : 0;
                    if (valid && accele160_stage_stock_next_slot(s, slot3)) {
                        uint32_t local = accele160_bridge_request(s, "D 10\n");
                        uint32_t routed = accele160_bridge_request(s, "E 7\n");
                        uint32_t last_ip = 0;
                        for (unsigned step = 0; step < 20; ++step) {
                            last_ip = accele160_bridge_request(s, "S 1000000\n");
                            if (!routed &&
                                (accele160_bridge_request(s, "I 1320\n") & 0x10u))
                                routed = accele160_bridge_request(s, "E 7\n");
                        }
                        fprintf(stderr, "accele160 EXPLORE stock next "
                                "event=3 local-idb=0x%08x route=0x%08x "
                                "last-ip=0x%08x output=0x%08" PRIx64
                                " no-guest-copy=1\n",
                                local, routed, last_ip, output);
                        accele160_trace_stock_next(s, output);
                        if (s->explore_stock_next_mirror) {
                            uint8_t mirror_slot[64];
                            memcpy(mirror_slot, slot3, sizeof(mirror_slot));
                            if (s->explore_stock_next_mutate_slot)
                                mirror_slot[21] ^= 1u;
                            if (s->explore_stock_next_mutate_prefill) {
                                uint8_t byte;
                                if (pci_dma_read(&s->parent_obj, output,
                                                 &byte, 1) == MEMTX_OK) {
                                    byte ^= 0x80u;
                                    if (pci_dma_write(&s->parent_obj, output,
                                                      &byte, 1) == MEMTX_OK)
                                        fprintf(stderr, "accele160 EXPLORE "
                                                "stock next mutated guest "
                                                "prefill byte=0x%02x\n",
                                                byte);
                                }
                            }
                            if (accele160_mirror_stock_next(
                                    s, mirror_slot,
                                    accele160_bridge_request(s, "I 132c\n")))
                                fprintf(stderr, "accele160 EXPLORE stock next "
                                        "guest-mirror accepted event=3\n");
                            else
                                fprintf(stderr, "accele160 EXPLORE stock next "
                                        "guest-mirror rejected event=3\n");
                        }
                    } else {
                        fprintf(stderr, "accele160 EXPLORE stock next "
                                "event=3 staging rejected\n");
                    }
                } else if (s->ring_followup_events == 4 &&
                           s->explore_stock_scsi_observe &&
                           s->explore_stock_next_mirror) {
                    uint8_t slot4[64];
                    uint64_t sense = 0, data = 0;
                    if (pci_dma_read(&s->parent_obj,
                                     s->set_mbox_ring + 256u,
                                     slot4, sizeof(slot4)) == MEMTX_OK &&
                        accele160_stage_stock_scsi_slot(
                            s, slot4, &sense, &data)) {
                        accele160_trace_stock_scsi_isp(s, "before");
                        uint32_t local =
                            accele160_bridge_request(s, "D 10\n");
                        uint32_t routed =
                            accele160_bridge_request(s, "E 7\n");
                        uint32_t last_ip = 0;
                        for (unsigned step = 0; step < 20; ++step) {
                            last_ip =
                                accele160_bridge_request(s, "S 1000000\n");
                            if (!routed &&
                                (accele160_bridge_request(
                                     s, "I 1320\n") & 0x10u))
                                routed =
                                    accele160_bridge_request(s, "E 7\n");
                        }
                        fprintf(stderr, "accele160 EXPLORE stock scsi "
                                "event=4 local-idb=0x%08x route=0x%08x "
                                "last-ip=0x%08x sense=0x%08" PRIx64
                                " data=0x%08" PRIx64
                                " no-guest-copy=1\n",
                                local, routed, last_ip, sense, data);
                        accele160_trace_stock_scsi(s, sense, data);
                        accele160_trace_stock_scsi_isp(s, "after");
                    } else {
                        fprintf(stderr, "accele160 EXPLORE stock scsi "
                                "event=4 staging rejected\n");
                    }
                } else if (s->ring_followup_events >= 3 &&
                           s->explore_native_next_observe &&
                           s->explore_native_followup_mirror) {
                    const unsigned event = s->ring_followup_events;
                    const uint64_t slot_bus =
                        s->set_mbox_ring + event * 64u;
                    uint8_t submitted[64];
                    bool valid = pci_dma_read(
                        &s->parent_obj, slot_bus,
                        submitted, sizeof(submitted)) == MEMTX_OK;
                    const uint64_t output = valid ?
                        accele160_le64(submitted + 32) : 0;
                    bool shape = valid && output >= 0x00100000u &&
                        output < 0x20000000u &&
                        !(output & 3u) &&
                        submitted[4] == (event == 3 ? 0xec : 0x24) &&
                        submitted[5] == (event == 3 ? 0x03 : 0) &&
                        submitted[40] == submitted[4] &&
                        submitted[41] == submitted[5] &&
                        submitted[2] == (event == 3 ? 0x20 : 0x02) &&
                        submitted[3] == (event == 3 ? 0x50 : 0x10);
                    if (shape && event == 3)
                        shape = submitted[0] == 1 && submitted[1] == 0 &&
                            submitted[21] == 1 &&
                            output + 1004u <= 0x20000000u;
                    if (shape && event == 4)
                        shape = output + 36u <= 0x20000000u;
                    if (shape &&
                        accele160_stage_ring_slot(s, slot_bus, submitted) &&
                        accele160_stage_guest_window(
                            s, 'S', s->set_mbox_status_ring,
                            event == 3 ? 32 : 40) &&
                        (event != 3 ||
                         accele160_stage_guest_window(
                             s, 'T', output, 1004))) {
                        uint32_t local =
                            accele160_bridge_request(s, "D 10\n");
                        for (unsigned step = 0; step < 2; ++step)
                            accele160_bridge_request(s, "S 1000000\n");
                        uint32_t report[15];
                        char query[40];
                        for (unsigned j = 0; j < 15; ++j) {
                            snprintf(query, sizeof(query),
                                     "R %08x 4 0\n",
                                     0xc0001fc4u + j * 4u);
                            report[j] = accele160_bridge_request(s, query);
                        }
                        fprintf(stderr, "accele160 EXPLORE native next "
                                "event=%u local-idb=0x%08x marker=0x%08x "
                                "events=%u slot-index=%u slot-dma=0x%08x "
                                "digest=0x%08x state=0x%08x id=%u "
                                "opcode=0x%02x output=0x%08x length=%u "
                                "status-cursor=0x%08x completions=%u "
                                "outbound=0x%08x no-guest-copy=1\n",
                                event, local, report[0], report[1],
                                report[2], report[3], report[4],
                                report[5], report[6], report[7],
                                report[8], report[9], report[10],
                                report[11],
                                accele160_bridge_request(s, "I 132c\n"));
                        if (event == 3u && s->explore_native_next_mirror &&
                            accele160_mirror_native_next(
                                s, submitted, report,
                                accele160_bridge_request(s, "I 132c\n")))
                            fprintf(stderr, "accele160 EXPLORE native next "
                                    "guest-mirror accepted event=3\n");
                        else if (event == 3u &&
                                 s->explore_native_next_mirror)
                            fprintf(stderr, "accele160 EXPLORE native next "
                                    "guest-mirror rejected event=3\n");
                    } else {
                        fprintf(stderr, "accele160 EXPLORE native next "
                                "event=%u staging rejected\n", event);
                    }
                } else if (s->ring_followup_events > 2) {
                    fprintf(stderr, "accele160 EXPLORE ring followup "
                            "event=%u beyond bounded two-slot model; "
                            "no i960 doorbell or guest copy\n",
                            s->ring_followup_events);
                } else if (s->explore_stock_followup_observe) {
                    uint8_t submitted_slot[64] = {0};
                    bool submitted_valid = pci_dma_read(
                        &s->parent_obj,
                        s->set_mbox_ring + s->ring_followup_events * 64u,
                        submitted_slot, sizeof(submitted_slot)) == MEMTX_OK;
                    uint64_t pdev_bus = 0;
                    if (s->ring_followup_events == 1)
                        fprintf(stderr, "accele160 EXPLORE stock followup "
                                "health-dma1-gate=%u\n",
                                accele160_bridge_request(s, "F\n"));
                    if (s->ring_followup_events >= 2) {
                        uint8_t slot2[64];
                        if (pci_dma_read(&s->parent_obj,
                                         s->set_mbox_ring + 128u,
                                         slot2, sizeof(slot2)) == MEMTX_OK) {
                            pdev_bus = accele160_le64(slot2 + 32);
                            if (!accele160_stage_guest_window(
                                    s, 'P', pdev_bus, 512)) {
                                fprintf(stderr, "accele160 EXPLORE stock "
                                        "followup pdev window rejected\n");
                                pdev_bus = 0;
                            }
                        }
                    }
                    uint32_t local = accele160_bridge_request(s, "D 10\n");
                    uint32_t routed = accele160_bridge_request(s, "E 7\n");
                    uint32_t last_ip = 0;
                    for (unsigned step = 0; step < 20; ++step) {
                        last_ip = accele160_bridge_request(s, "S 1000000\n");
                        if (!routed &&
                            (accele160_bridge_request(s, "I 1320\n") & 0x10u))
                            routed = accele160_bridge_request(s, "E 7\n");
                    }
                    fprintf(stderr, "accele160 EXPLORE stock followup "
                            "event=%u local-idb=0x%08x route=0x%08x "
                            "last-ip=0x%08x "
                            "no-guest-copy=1\n",
                            s->ring_followup_events, local, routed, last_ip);
                    accele160_trace_stock_followup(
                        s, s->ring_followup_events, pdev_bus);
                    if (s->explore_stock_followup_mirror &&
                        submitted_valid &&
                        (s->ring_followup_events == 1 || pdev_bus) &&
                        accele160_mirror_stock_followup(
                            s, s->ring_followup_events, submitted_slot,
                            accele160_bridge_request(s, "I 132c\n"))) {
                        fprintf(stderr, "accele160 EXPLORE stock followup "
                                "guest-mirror accepted event=%u\n",
                                s->ring_followup_events);
                    } else if (s->explore_stock_followup_mirror) {
                        fprintf(stderr, "accele160 EXPLORE stock followup "
                                "guest-mirror rejected event=%u\n",
                                s->ring_followup_events);
                    }
                } else if (s->explore_native_followup_observe) {
                    uint8_t submitted_slot[64] = {0};
                    bool submitted_valid = pci_dma_read(
                        &s->parent_obj,
                        s->set_mbox_ring + s->ring_followup_events * 64u,
                        submitted_slot, sizeof(submitted_slot)) == MEMTX_OK;
                    uint64_t pdev_bus = 0;
                    if (s->ring_followup_events >= 2) {
                        uint8_t slot2[64];
                        if (pci_dma_read(&s->parent_obj,
                                         s->set_mbox_ring + 128u,
                                         slot2, sizeof(slot2)) == MEMTX_OK) {
                            pdev_bus = accele160_le64(slot2 + 32);
                            if (!accele160_stage_guest_window(
                                    s, 'P', pdev_bus, 512)) {
                                fprintf(stderr, "accele160 EXPLORE native "
                                        "followup pdev window rejected\n");
                                pdev_bus = 0;
                            }
                        }
                    }
                    uint32_t local = accele160_bridge_request(s, "D 10\n");
                    uint32_t report[15];
                    char query[40];
                    for (unsigned step = 0; step < 2; ++step)
                        accele160_bridge_request(s, "S 1000000\n");
                    for (unsigned j = 0; j < 15; ++j) {
                        snprintf(query, sizeof(query), "R %08x 4 0\n",
                                 0xc0001fc4u + j * 4u);
                        report[j] = accele160_bridge_request(s, query);
                    }
                    uint32_t outbound =
                        accele160_bridge_request(s, "I 132c\n");
                    fprintf(stderr, "accele160 EXPLORE native followup "
                            "event=%u local-idb=0x%08x marker=0x%08x "
                            "events=%u slot-index=%u slot-dma=0x%08x "
                            "digest=0x%08x state=0x%08x id=%u ioctl=0x%02x "
                            "output=0x%08x length=%u status-cursor=0x%08x "
                            "completions=%u outbound=0x%08x "
                            "reply-state=%u dma-eoc=%u status-word0=0x%08x\n",
                            s->ring_followup_events, local,
                            report[0], report[1], report[2], report[3],
                            report[4], report[5], report[6], report[7],
                            report[8], report[9], report[10], report[11],
                            outbound,
                            report[12], report[13], report[14]);
                    accele160_trace_native_followup_model(
                        s, s->ring_followup_events, pdev_bus);
                    if (s->explore_native_followup_mirror && submitted_valid &&
                        (s->ring_followup_events == 1 || pdev_bus) &&
                        accele160_mirror_native_followup(
                            s, s->ring_followup_events, submitted_slot,
                            report, outbound)) {
                        fprintf(stderr, "accele160 EXPLORE native followup "
                                "guest-mirror accepted event=%u\n",
                                s->ring_followup_events);
                    } else if (s->explore_native_followup_mirror) {
                        fprintf(stderr, "accele160 EXPLORE native followup "
                                "guest-mirror rejected event=%u\n",
                                s->ring_followup_events);
                    }
                }
            }
            if (value & LP_IDB_HWMBOX_ACK_STS) {
                if (s->lp_odb & 1) {
                    s->lp_odb &= ~1;
                    s->lp_mailbox_pending = false;
                    if (s->explore_live_firmware || s->explore_native_poll)
                        accele160_bridge_request(s, "A 1\n");
                    fprintf(stderr, "accele160 lp hardware mailbox status acknowledged\n");
                }
                /* Provisional LP-to-MU mapping: myrs posts ACK_STS during
                 * initialization and stock waits on inbound bit 1. */
                accele160_bridge_request(s, "D 00000002\n");
                fprintf(stderr, "accele160 lp ack-status posted to i960 doorbell bit 1\n");
                if (s->step_on_ack) {
                    uint32_t ip = accele160_bridge_request(s, "S 1000000\n");
                    fprintf(stderr, "accele160 lp ack-status i960-step ip=0x%08x\n", ip);
                }
            }
            if (value & 8) fprintf(stderr, "accele160 lp reset requested; unmodeled\n");
            return;
        }
        if (addr == LP_ODB) {
            if ((value & 1) && (s->lp_odb & 1)) {
                s->lp_mailbox_pending = false;
                if (s->explore_live_firmware || s->explore_native_poll)
                    accele160_bridge_request(s, "A 1\n");
                fprintf(stderr, "accele160 lp hardware mailbox status acknowledged\n");
            }
            if ((value & 2u) && (s->lp_odb & 2u) &&
                (s->explore_native_ring_mirror ||
                 s->explore_stock_ring_mirror)) {
                accele160_bridge_request(s, "A 2\n");
                fprintf(stderr, "accele160 lp memory ring interrupt acknowledged\n");
            }
            s->lp_odb &= ~(uint8_t)value;
            if ((s->explore_native_ring_mirror ||
                 s->explore_stock_ring_mirror) && (value & 2u))
                pci_set_irq(&s->parent_obj, 0);
            return;
        }
    }
    for (i = 0; i < size; ++i) {
        s->aperture[addr + i] = value >> (8 * i);
    }
    if (s->bridge_fd >= 0 && addr >= LP_CMDMBX &&
        addr + size <= LP_CMDMBX + 8) {
        s->lp_mbox_address = 0;
        for (i = 0; i < 8; ++i)
            s->lp_mbox_address |= (uint64_t)s->aperture[LP_CMDMBX + i] << (8 * i);
    }
}

static const MemoryRegionOps accele160_bar_ops = {
    .read = accele160_read,
    .write = accele160_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
    .valid = {
        .min_access_size = 1,
        .max_access_size = 4,
    },
};

static uint32_t accele160_config_read(PCIDevice *pci_dev, uint32_t addr,
                                     int size)
{
    Accele160State *s = ACCELE160(pci_dev);
    uint32_t value = pci_default_read_config(pci_dev, addr, size);

    if (s->config_access_count < s->trace_limit) {
        fprintf(stderr, "accele160 config R offset=0x%02x size=%d "
                "value=0x%0*x\n", addr, size, size * 2, value);
    }
    ++s->config_access_count;
    return value;
}

static void accele160_config_write(PCIDevice *pci_dev, uint32_t addr,
                                   uint32_t value, int size)
{
    Accele160State *s = ACCELE160(pci_dev);

    if (s->config_access_count < s->trace_limit) {
        fprintf(stderr, "accele160 config W offset=0x%02x size=%d "
                "value=0x%0*x\n", addr, size, size * 2, value);
    }
    ++s->config_access_count;
    pci_default_write_config(pci_dev, addr, value, size);
    if (addr < PCI_COMMAND + 2 && addr + size > PCI_COMMAND)
        accele160_mirror_command(s, 0x1204,
                                 pci_get_word(pci_dev->config + PCI_COMMAND));
    if (addr < 0x48 && addr + size > 0x44)
        s->piatvr = pci_get_long(pci_dev->config + 0x44);
}

static void accele160_pci_bridge_write_config(PCIDevice *pci_dev,
                                               uint32_t addr, uint32_t value,
                                               int size)
{
    pci_bridge_write_config(pci_dev, addr, value, size);
    if (addr < PCI_COMMAND + 2 && addr + size > PCI_COMMAND)
        accele160_mirror_command(accele160_raid_sibling(pci_dev), 0x1004,
                                 pci_get_word(pci_dev->config + PCI_COMMAND));
}

static void accele160_pci_bridge_realize(PCIDevice *pci_dev, Error **errp)
{
    pci_bridge_initfn(pci_dev, TYPE_PCI_BUS);
    pci_bridge_disable_base_limit(pci_dev);
    fprintf(stderr, "accele160 pci-bridge-ready 8086:2962 rev=02\n");
}

static void accele160_pci_bridge_exit(PCIDevice *pci_dev)
{
    pci_bridge_exitfn(pci_dev);
}

static void accele160_realize(PCIDevice *pci_dev, Error **errp)
{
    Accele160State *s = ACCELE160(pci_dev);
    g_autofree gchar *contents = NULL;
    gsize length = 0;
    g_autoptr(GError) error = NULL;

    s->bridge_fd = -1;
    s->piatvr = 0xc0000000;
    pci_set_long(pci_dev->config + 0x44, s->piatvr);
    memset(pci_dev->wmask + 0x44, 0xff, 4);

    if (s->aperture_file) {
        if (!g_file_get_contents(s->aperture_file, &contents, &length, &error)) {
            error_setg(errp, "cannot load aperture file %s: %s",
                       s->aperture_file, error->message);
            return;
        }
        if (length != ACCELE160_BAR_SIZE) {
            error_setg(errp, "aperture file must be exactly 8192 bytes");
            return;
        }
        memcpy(s->aperture, contents, length);
    }
    if (s->bridge_socket) {
        struct sockaddr_un address = {0};
        if (strlen(s->bridge_socket) >= sizeof(address.sun_path)) {
            error_setg(errp, "bridge socket path too long");
            return;
        }
        s->bridge_fd = socket(AF_UNIX, SOCK_STREAM, 0);
        if (s->bridge_fd < 0) {
            error_setg_errno(errp, errno, "cannot create bridge socket");
            return;
        }
        address.sun_family = AF_UNIX;
        strcpy(address.sun_path, s->bridge_socket);
        if (connect(s->bridge_fd, (struct sockaddr *)&address, sizeof(address))) {
            error_setg_errno(errp, errno, "cannot connect bridge socket");
            close(s->bridge_fd);
            s->bridge_fd = -1;
            return;
        }
    }

    pci_dev->config[PCI_INTERRUPT_PIN] = 1;
    memory_region_init_io(&s->bar0, OBJECT(s), &accele160_bar_ops, s,
                          "accele160-bar0", ACCELE160_BAR_SIZE);
    pci_register_bar(pci_dev, 0, PCI_BASE_ADDRESS_SPACE_MEMORY |
                     PCI_BASE_ADDRESS_MEM_PREFETCH, &s->bar0);
    fprintf(stderr, "accele160 pci-ready 1069:0050 rev=02 subsystem=1069:0054 "
            "bar0=8192 aperture=%s bridge=%s\n",
            s->aperture_file ? s->aperture_file : "zero-initialized",
            s->bridge_socket ? s->bridge_socket : "none");
}

static void accele160_exit(PCIDevice *pci_dev)
{
    Accele160State *s = ACCELE160(pci_dev);
    if (s->bridge_fd >= 0) close(s->bridge_fd);
}

static Property accele160_properties[] = {
    DEFINE_PROP_STRING("aperture-file", Accele160State, aperture_file),
    DEFINE_PROP_STRING("bridge-socket", Accele160State, bridge_socket),
    DEFINE_PROP_BOOL("step-on-ack", Accele160State, step_on_ack, false),
    DEFINE_PROP_BOOL("explore-rom-ioctls", Accele160State,
                     explore_rom_ioctls, false),
    DEFINE_PROP_BOOL("explore-live-firmware", Accele160State,
                     explore_live_firmware, false),
    DEFINE_PROP_BOOL("explore-set-mbox-trace", Accele160State,
                     explore_set_mbox_trace, false),
    DEFINE_PROP_BOOL("explore-set-mbox-bridge", Accele160State,
                     explore_set_mbox_bridge, false),
    DEFINE_PROP_BOOL("explore-mmbox-doorbell-observe", Accele160State,
                     explore_mmbox_doorbell_observe, false),
    DEFINE_PROP_BOOL("explore-mmbox-doorbell-control", Accele160State,
                     explore_mmbox_doorbell_control, false),
    DEFINE_PROP_BOOL("explore-stock-ring-memory", Accele160State,
                     explore_stock_ring_memory, false),
    DEFINE_PROP_BOOL("explore-stock-ring-mirror", Accele160State,
                     explore_stock_ring_mirror, false),
    DEFINE_PROP_BOOL("explore-stock-followup-observe", Accele160State,
                     explore_stock_followup_observe, false),
    DEFINE_PROP_BOOL("explore-stock-followup-mirror", Accele160State,
                     explore_stock_followup_mirror, false),
    DEFINE_PROP_BOOL("explore-stock-next-observe", Accele160State,
                     explore_stock_next_observe, false),
    DEFINE_PROP_BOOL("explore-stock-next-mirror", Accele160State,
                     explore_stock_next_mirror, false),
    DEFINE_PROP_BOOL("explore-stock-next-mutate-slot", Accele160State,
                     explore_stock_next_mutate_slot, false),
    DEFINE_PROP_BOOL("explore-stock-next-mutate-prefill", Accele160State,
                     explore_stock_next_mutate_prefill, false),
    DEFINE_PROP_BOOL("explore-stock-scsi-observe", Accele160State,
                     explore_stock_scsi_observe, false),
    DEFINE_PROP_BOOL("explore-native-poll", Accele160State,
                     explore_native_poll, false),
    DEFINE_PROP_BOOL("explore-native-set-mbox", Accele160State,
                     explore_native_set_mbox, false),
    DEFINE_PROP_BOOL("explore-native-ring-observe", Accele160State,
                     explore_native_ring_observe, false),
    DEFINE_PROP_BOOL("explore-native-ring-mirror", Accele160State,
                     explore_native_ring_mirror, false),
    DEFINE_PROP_BOOL("explore-native-followup-observe", Accele160State,
                     explore_native_followup_observe, false),
    DEFINE_PROP_BOOL("explore-native-followup-mirror", Accele160State,
                     explore_native_followup_mirror, false),
    DEFINE_PROP_BOOL("explore-native-next-observe", Accele160State,
                     explore_native_next_observe, false),
    DEFINE_PROP_BOOL("explore-native-next-mirror", Accele160State,
                     explore_native_next_mirror, false),
    DEFINE_PROP_BOOL("trace-live-reply", Accele160State,
                     trace_live_reply, false),
    DEFINE_PROP_UINT32("trace-limit", Accele160State, trace_limit, 4096),
    DEFINE_PROP_END_OF_LIST(),
};

static void accele160_class_init(ObjectClass *klass, void *data)
{
    PCIDeviceClass *pc = PCI_DEVICE_CLASS(klass);
    DeviceClass *dc = DEVICE_CLASS(klass);

    pc->realize = accele160_realize;
    pc->exit = accele160_exit;
    pc->config_read = accele160_config_read;
    pc->config_write = accele160_config_write;
    pc->vendor_id = 0x1069;
    pc->device_id = 0x0050;
    pc->subsystem_vendor_id = 0x1069;
    pc->subsystem_id = 0x0054;
    pc->revision = 0x02;
    pc->class_id = PCI_CLASS_STORAGE_RAID;
    dc->desc = "AcceleRAID 160 PCI aperture probe";
    set_bit(DEVICE_CATEGORY_STORAGE, dc->categories);
    device_class_set_props(dc, accele160_properties);
}

static const TypeInfo accele160_info = {
    .name = TYPE_ACCELE160,
    .parent = TYPE_PCI_DEVICE,
    .instance_size = sizeof(Accele160State),
    .class_init = accele160_class_init,
    .interfaces = (InterfaceInfo[]) {
        { INTERFACE_CONVENTIONAL_PCI_DEVICE },
        { },
    },
};

static void accele160_pci_bridge_class_init(ObjectClass *klass, void *data)
{
    PCIDeviceClass *pc = PCI_DEVICE_CLASS(klass);
    DeviceClass *dc = DEVICE_CLASS(klass);
    pc->realize = accele160_pci_bridge_realize;
    pc->exit = accele160_pci_bridge_exit;
    pc->config_write = accele160_pci_bridge_write_config;
    pc->vendor_id = 0x8086;
    pc->device_id = 0x2962;
    pc->revision = 0x02;
    pc->class_id = PCI_CLASS_BRIDGE_PCI;
    pc->is_bridge = true;
    dc->desc = "AcceleRAID 160 companion PCI bridge probe";
    set_bit(DEVICE_CATEGORY_BRIDGE, dc->categories);
}

static const TypeInfo accele160_pci_bridge_info = {
    .name = TYPE_ACCELE160_BRIDGE,
    .parent = TYPE_PCI_BRIDGE,
    .instance_size = sizeof(Accele160BridgeState),
    .class_init = accele160_pci_bridge_class_init,
    .interfaces = (InterfaceInfo[]) {
        { INTERFACE_CONVENTIONAL_PCI_DEVICE },
        { },
    },
};

static void accele160_register_types(void)
{
    type_register_static(&accele160_info);
    type_register_static(&accele160_pci_bridge_info);
}

type_init(accele160_register_types)
