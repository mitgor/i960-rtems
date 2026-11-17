#include "host_mailbox.h"

static unsigned int read32(const unsigned char *p)
{
    return (unsigned int)p[0] | ((unsigned int)p[1] << 8) |
           ((unsigned int)p[2] << 16) | ((unsigned int)p[3] << 24);
}

static unsigned int parse_ioctl(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out,
    unsigned int ioctl, unsigned int expected_bytes)
{
    unsigned int address;
    accele160_controller_info_request parsed;
    if (!bytes || !out || length != 64u)
        return ACCELE160_MAILBOX_SHORT;
    if (bytes[2] != 0x20u || bytes[3] != 0x10u ||
        read32(bytes + 4) != expected_bytes || bytes[21] != ioctl ||
        read32(bytes + 40) != expected_bytes)
        return ACCELE160_MAILBOX_UNSUPPORTED;
    address = read32(bytes + 32);
    if (!address || (address & 3u) ||
        address > 0xffffffffu - expected_bytes ||
        read32(bytes + 36) != 0u)
        return ACCELE160_MAILBOX_ADDRESS;
    parsed.command_id = (unsigned int)bytes[0] | ((unsigned int)bytes[1] << 8);
    parsed.output_bus_address = address;
    parsed.output_bytes = expected_bytes;
    *out = parsed;
    return ACCELE160_MAILBOX_OK;
}

unsigned int accele160_parse_controller_info(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out)
{
    return parse_ioctl(bytes, length, out, 0x01u, 512u);
}

unsigned int accele160_parse_ioctl11(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out)
{
    return parse_ioctl(bytes, length, out, 0x11u, 128u);
}

unsigned int accele160_parse_ioctl15(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out)
{
    return parse_ioctl(bytes, length, out, 0x15u, 64u);
}

unsigned int accele160_parse_ioctld0(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out)
{
    return parse_ioctl(bytes, length, out, 0xd0u, 128u);
}

unsigned int accele160_parse_ioctl2d(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out)
{
    return parse_ioctl(bytes, length, out, 0x2du, 512u);
}

static unsigned int dma_range_ok(unsigned int base, unsigned int size)
{
    /* The offline Debian guest has 512 MiB. This rejects low legacy RAM,
     * misalignment, truncation and any range beyond that guest aperture. */
    return base >= 0x00100000u && (base & 0xfffu) == 0u &&
           base <= 0x20000000u - size;
}

static unsigned int disjoint(unsigned int a, unsigned int asize,
                             unsigned int b, unsigned int bsize)
{
    return a + asize <= b || b + bsize <= a;
}

unsigned int accele160_parse_set_mem_mbox(
    const unsigned char *bytes, unsigned int length,
    accele160_mem_mbox_request *out)
{
    accele160_mem_mbox_request parsed;
    unsigned int i;
    if (!bytes || !out || length != 64u)
        return ACCELE160_MAILBOX_SHORT;
    /* This is the one observed myrs SET_MEM_MBOX variant. Reject all spare
     * bytes, flags and SG shapes until stock evidence supports them. */
    for (i = 0; i < length; ++i) {
        unsigned char expected = 0u;
        if (i == 0) expected = 1u;
        if (i == 2) expected = 0x20u;
        if (i == 3) expected = 0x40u;
        if (i == 4) expected = 0x20u;
        if (i == 5) expected = 0x04u;
        if (i == 21) expected = 0x8eu;
        if (i == 22) expected = 1u;
        if ((i >= 24u && i < 32u) || (i >= 32u && i < 40u) ||
            (i >= 40u && i < 48u)) continue;
        if (bytes[i] != expected) return ACCELE160_MAILBOX_UNSUPPORTED;
    }
    if (read32(bytes + 28) || read32(bytes + 36) || read32(bytes + 44))
        return ACCELE160_MAILBOX_ADDRESS;
    parsed.command_id = 1u;
    parsed.health_bus = read32(bytes + 24);
    parsed.command_ring_bus = read32(bytes + 32);
    parsed.status_ring_bus = read32(bytes + 40);
    if (!dma_range_ok(parsed.command_ring_bus,
                      ACCELE160_MEM_COMMAND_RING_BYTES) ||
        !dma_range_ok(parsed.status_ring_bus,
                      ACCELE160_MEM_STATUS_RING_BYTES) ||
        !dma_range_ok(parsed.health_bus, ACCELE160_MEM_HEALTH_BYTES) ||
        !disjoint(parsed.command_ring_bus, ACCELE160_MEM_COMMAND_RING_BYTES,
                  parsed.status_ring_bus, ACCELE160_MEM_STATUS_RING_BYTES) ||
        !disjoint(parsed.command_ring_bus, ACCELE160_MEM_COMMAND_RING_BYTES,
                  parsed.health_bus, ACCELE160_MEM_HEALTH_BYTES) ||
        !disjoint(parsed.status_ring_bus, ACCELE160_MEM_STATUS_RING_BYTES,
                  parsed.health_bus, ACCELE160_MEM_HEALTH_BYTES))
        return ACCELE160_MAILBOX_ADDRESS;
    *out = parsed;
    return ACCELE160_MAILBOX_OK;
}

unsigned int accele160_parse_first_ring_info(
    const unsigned char *bytes, unsigned int length,
    const accele160_mem_mbox_request *setup,
    accele160_ring_info_request *out)
{
    accele160_ring_info_request parsed;
    unsigned int i;
    if (!bytes || !setup || !out || length != 64u)
        return ACCELE160_MAILBOX_SHORT;
    /* Exactly the first observed Debian myrs ring slot. This parser does
     * not interpret a general memory-mailbox command. */
    for (i = 0; i < length; ++i) {
        unsigned char expected = 0u;
        if (i == 0 || i == 21) expected = 1u;
        if (i == 2) expected = 0x20u;
        if (i == 3) expected = 0x50u;
        if (i == 4 || i == 40) expected = 0xecu;
        if (i == 5 || i == 41) expected = 0x03u;
        if (i >= 32u && i < 36u) continue;
        if (bytes[i] != expected) return ACCELE160_MAILBOX_UNSUPPORTED;
    }
    parsed.command_id = 1u;
    parsed.output_bus_address = read32(bytes + 32);
    parsed.output_bytes = 1004u;
    if (parsed.output_bus_address < 0x00100000u ||
        (parsed.output_bus_address & 3u) ||
        parsed.output_bus_address > 0x20000000u - parsed.output_bytes ||
        !disjoint(parsed.output_bus_address, parsed.output_bytes,
                  setup->command_ring_bus, ACCELE160_MEM_COMMAND_RING_BYTES) ||
        !disjoint(parsed.output_bus_address, parsed.output_bytes,
                  setup->status_ring_bus, ACCELE160_MEM_STATUS_RING_BYTES) ||
        !disjoint(parsed.output_bus_address, parsed.output_bytes,
                  setup->health_bus, ACCELE160_MEM_HEALTH_BYTES))
        return ACCELE160_MAILBOX_ADDRESS;
    *out = parsed;
    return ACCELE160_MAILBOX_OK;
}

unsigned int accele160_parse_ring_followup(
    const unsigned char *bytes, unsigned int length,
    const accele160_mem_mbox_request *setup, unsigned int slot_index,
    accele160_ring_followup_request *out)
{
    accele160_ring_followup_request parsed;
    unsigned int i, count, ioctl, id, address;
    if (!bytes || !setup || !out || length != 64u)
        return ACCELE160_MAILBOX_SHORT;
    if (slot_index == 1u) {
        id = 2u; ioctl = 0x11u; count = 128u;
    } else if (slot_index == 2u) {
        id = 1u; ioctl = 0x05u; count = 512u;
    } else {
        return ACCELE160_MAILBOX_UNSUPPORTED;
    }
    /* These exact observed shapes are useful only for read-only diagnosis.
     * Parsing never grants permission to DMA to their output addresses. */
    for (i = 0; i < length; ++i) {
        unsigned char expected = 0u;
        if (i == 0u) expected = (unsigned char)id;
        if (i == 2u) expected = 0x20u;
        if (i == 3u) expected = 0x50u;
        if (i == 4u || i == 40u) expected = (unsigned char)count;
        if (i == 5u || i == 41u) expected = (unsigned char)(count >> 8);
        if (i == 21u) expected = (unsigned char)ioctl;
        if (i >= 32u && i < 36u) continue;
        if (bytes[i] != expected) return ACCELE160_MAILBOX_UNSUPPORTED;
    }
    address = read32(bytes + 32);
    /* IOCTL 0x11 uses the negotiated health buffer itself; IOCTL 0x05 has
     * a separate output. These are observation checks, never DMA grants. */
    if (address < 0x00100000u || (address & 3u) ||
        address > 0x20000000u - count ||
        !disjoint(address, count, setup->command_ring_bus,
                  ACCELE160_MEM_COMMAND_RING_BYTES) ||
        !disjoint(address, count, setup->status_ring_bus,
                  ACCELE160_MEM_STATUS_RING_BYTES) ||
        (slot_index == 1u ? address != setup->health_bus :
         !disjoint(address, count, setup->health_bus,
                   ACCELE160_MEM_HEALTH_BYTES)))
        return ACCELE160_MAILBOX_ADDRESS;
    parsed.slot_index = slot_index;
    parsed.command_id = id;
    parsed.ioctl = ioctl;
    parsed.output_bus_address = address;
    parsed.output_bytes = count;
    *out = parsed;
    return ACCELE160_MAILBOX_OK;
}

unsigned int accele160_parse_ring_next(
    const unsigned char *bytes, unsigned int length,
    const accele160_mem_mbox_request *setup, unsigned int slot_index,
    accele160_ring_next_request *out)
{
    accele160_ring_next_request parsed;
    unsigned int i, output, sense;
    if (!bytes || !setup || !out || length != 64u)
        return ACCELE160_MAILBOX_SHORT;
    if (slot_index == 3u) {
        accele160_ring_info_request first_shape;
        unsigned int result = accele160_parse_first_ring_info(
            bytes, length, setup, &first_shape);
        if (result) return result;
        parsed.slot_index = 3u;
        parsed.command_id = first_shape.command_id;
        parsed.opcode = 0x01u; /* repeated GET_CTLR_INFO shape */
        parsed.output_bus_address = first_shape.output_bus_address;
        parsed.output_bytes = first_shape.output_bytes;
        parsed.sense_bus_address = 0u;
        *out = parsed;
        return ACCELE160_MAILBOX_OK;
    }
    if (slot_index != 4u)
        return ACCELE160_MAILBOX_UNSUPPORTED;
    /* Observed Linux SCSI_10_PASSTHRU, standard INQUIRY CDB for 0:0:0.
     * Command ID and two guest DMA addresses varied between captures. */
    for (i = 0; i < length; ++i) {
        unsigned char expected = 0u;
        if (i == 2u) expected = 2u;
        if (i == 3u) expected = 0x10u;
        if (i == 4u || i == 26u || i == 40u) expected = 36u;
        if (i == 19u) expected = 0x55u;
        if (i == 20u) expected = 14u;
        if (i == 21u) expected = 6u;
        if (i == 22u) expected = 0x12u;
        if (i < 2u || (i >= 8u && i < 12u) ||
            (i >= 32u && i < 36u)) continue;
        if (bytes[i] != expected) return ACCELE160_MAILBOX_UNSUPPORTED;
    }
    if ((bytes[0] | bytes[1]) == 0u)
        return ACCELE160_MAILBOX_UNSUPPORTED;
    sense = read32(bytes + 8);
    output = read32(bytes + 32);
    if (sense < 0x00100000u || (sense & 3u) ||
        sense > 0x20000000u - 14u ||
        output < 0x00100000u || (output & 3u) ||
        output > 0x20000000u - 36u ||
        !disjoint(sense, 14u, output, 36u) ||
        !disjoint(sense, 14u, setup->command_ring_bus,
                  ACCELE160_MEM_COMMAND_RING_BYTES) ||
        !disjoint(sense, 14u, setup->status_ring_bus,
                  ACCELE160_MEM_STATUS_RING_BYTES) ||
        !disjoint(sense, 14u, setup->health_bus,
                  ACCELE160_MEM_HEALTH_BYTES) ||
        !disjoint(output, 36u, setup->command_ring_bus,
                  ACCELE160_MEM_COMMAND_RING_BYTES) ||
        !disjoint(output, 36u, setup->status_ring_bus,
                  ACCELE160_MEM_STATUS_RING_BYTES) ||
        !disjoint(output, 36u, setup->health_bus,
                  ACCELE160_MEM_HEALTH_BYTES))
        return ACCELE160_MAILBOX_ADDRESS;
    parsed.slot_index = 4u;
    parsed.command_id = (unsigned int)bytes[0] | ((unsigned int)bytes[1] << 8);
    parsed.opcode = 2u;
    parsed.output_bus_address = output;
    parsed.output_bytes = 36u;
    parsed.sense_bus_address = sense;
    *out = parsed;
    return ACCELE160_MAILBOX_OK;
}
