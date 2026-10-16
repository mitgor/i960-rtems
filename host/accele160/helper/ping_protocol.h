#ifndef ACCELE160_PING_PROTOCOL_H
#define ACCELE160_PING_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define AR160_MAILBOX_BYTES 64u
#define AR160_IOCTL_OPCODE 0x20u
#define AR160_HELPER_SUBCOMMAND 0x8fu
#define AR160_HELPER_VERSION 1u
#define AR160_HELPER_PING 1u

/* Admission only. It neither executes a command nor touches card memory. */
enum ar160_ping_status {
    AR160_PING_ACCEPT = 0,
    AR160_PING_BAD_LENGTH = 1,
    AR160_PING_BAD_ENVELOPE = 2,
    AR160_PING_BAD_VERSION = 3,
    AR160_PING_BAD_OPERATION = 4,
    AR160_PING_BAD_NONCE = 5
};

int ar160_ping_validate(const uint8_t *mailbox, size_t length, uint32_t *nonce);
void ar160_ping_build(uint8_t mailbox[AR160_MAILBOX_BYTES],
                      uint16_t command_id, uint32_t nonce);

#endif
