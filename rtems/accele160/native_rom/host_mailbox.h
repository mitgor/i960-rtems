#ifndef ACCELE160_HOST_MAILBOX_H
#define ACCELE160_HOST_MAILBOX_H

/* Decode only the observed 64-byte DAC960 V2 ROM requests. The caller
 * owns the host-DMA transport and must not issue DMA on parse failure. */
typedef struct {
    unsigned int command_id;
    unsigned int output_bus_address;
    unsigned int output_bytes;
} accele160_controller_info_request;

/* The observed Linux SET_MEM_MBOX request carries three guest DMA bases.
 * Ring lengths come from the myrs request format, not from a DMA descriptor
 * in this 64-byte hardware mailbox. Parsing does not authorize touching the
 * ring memory. */
typedef struct {
    unsigned int command_id;
    unsigned int command_ring_bus;
    unsigned int status_ring_bus;
    unsigned int health_bus;
} accele160_mem_mbox_request;

typedef struct {
    unsigned int command_id;
    unsigned int output_bus_address;
    unsigned int output_bytes;
} accele160_ring_info_request;

/* Observation only: parsing these later slots never authorizes output DMA. */
typedef struct {
    unsigned int slot_index;
    unsigned int command_id;
    unsigned int ioctl;
    unsigned int output_bus_address;
    unsigned int output_bytes;
} accele160_ring_followup_request;

/* Read-only shape of the two subsequent Linux slots. A successful parse
 * does not authorize a command completion or a DMA transfer. */
typedef struct {
    unsigned int slot_index;
    unsigned int command_id;
    unsigned int opcode;
    unsigned int output_bus_address;
    unsigned int output_bytes;
    unsigned int sense_bus_address;
} accele160_ring_next_request;

enum {
    ACCELE160_MEM_COMMAND_RING_BYTES = 32768,
    ACCELE160_MEM_STATUS_RING_BYTES = 4096,
    ACCELE160_MEM_HEALTH_BYTES = 1024
};

enum {
    ACCELE160_MAILBOX_OK = 0,
    ACCELE160_MAILBOX_SHORT = 1,
    ACCELE160_MAILBOX_UNSUPPORTED = 2,
    ACCELE160_MAILBOX_ADDRESS = 3
};

unsigned int accele160_parse_controller_info(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out);
unsigned int accele160_parse_ioctl11(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out);
unsigned int accele160_parse_ioctl15(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out);
unsigned int accele160_parse_ioctld0(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out);
unsigned int accele160_parse_ioctl2d(
    const unsigned char *bytes, unsigned int length,
    accele160_controller_info_request *out);
unsigned int accele160_parse_set_mem_mbox(
    const unsigned char *bytes, unsigned int length,
    accele160_mem_mbox_request *out);
unsigned int accele160_parse_first_ring_info(
    const unsigned char *bytes, unsigned int length,
    const accele160_mem_mbox_request *setup,
    accele160_ring_info_request *out);
unsigned int accele160_parse_ring_followup(
    const unsigned char *bytes, unsigned int length,
    const accele160_mem_mbox_request *setup, unsigned int slot_index,
    accele160_ring_followup_request *out);
unsigned int accele160_parse_ring_next(
    const unsigned char *bytes, unsigned int length,
    const accele160_mem_mbox_request *setup, unsigned int slot_index,
    accele160_ring_next_request *out);

#endif
