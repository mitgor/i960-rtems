#include "ping_protocol.h"

/* Raw DAC960 V2 mailbox offsets (Linux v6.8 myrs.h), little endian. The
 * internal stock dispatcher reads the subcommand at +0x15. This code is a
 * native admission model, not installed card firmware. It never dereferences
 * a host-supplied address or DMA descriptor.
 */
int ar160_ping_validate(const uint8_t *m, size_t length, uint32_t *nonce)
{
    size_t i;
    uint32_t value;

    if (!m || !nonce || length != AR160_MAILBOX_BYTES)
        return AR160_PING_BAD_LENGTH;
    if (m[2] != AR160_IOCTL_OPCODE || m[3] != 0x40u ||
        m[20] != 0 || m[21] != AR160_HELPER_SUBCOMMAND)
        return AR160_PING_BAD_ENVELOPE;
    /* Bytes 4..19 include size, SGE count, sense pointer and timeout.
     * Bytes 32..63 are the two SGE records. PING owns none of them. */
    for (i = 4; i < 20; ++i)
        if (m[i]) return AR160_PING_BAD_ENVELOPE;
    for (i = 32; i < 64; ++i)
        if (m[i]) return AR160_PING_BAD_ENVELOPE;
    if (m[22] != AR160_HELPER_VERSION) return AR160_PING_BAD_VERSION;
    if (m[23] != AR160_HELPER_PING) return AR160_PING_BAD_OPERATION;
    if (m[24] != 'I' || m[25] != '9' || m[26] != '6' || m[27] != '0')
        return AR160_PING_BAD_ENVELOPE;
    value = (uint32_t)m[28] | ((uint32_t)m[29] << 8) |
            ((uint32_t)m[30] << 16) | ((uint32_t)m[31] << 24);
    if (!value) return AR160_PING_BAD_NONCE;
    *nonce = value;
    return AR160_PING_ACCEPT;
}

void ar160_ping_build(uint8_t m[AR160_MAILBOX_BYTES],
                      uint16_t command_id, uint32_t nonce)
{
    size_t i;
    for (i = 0; i < AR160_MAILBOX_BYTES; ++i) m[i] = 0;
    m[0] = (uint8_t)command_id;
    m[1] = (uint8_t)(command_id >> 8);
    m[2] = AR160_IOCTL_OPCODE;
    m[3] = 0x40u; /* no_autosense, no DMA direction */
    m[21] = AR160_HELPER_SUBCOMMAND;
    m[22] = AR160_HELPER_VERSION;
    m[23] = AR160_HELPER_PING;
    m[24] = 'I'; m[25] = '9'; m[26] = '6'; m[27] = '0';
    m[28] = (uint8_t)nonce;
    m[29] = (uint8_t)(nonce >> 8);
    m[30] = (uint8_t)(nonce >> 16);
    m[31] = (uint8_t)(nonce >> 24);
}
