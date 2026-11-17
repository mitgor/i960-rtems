#ifndef ACCELE160_CONTROLLER_INFO_H
#define ACCELE160_CONTROLLER_INFO_H

/* Compose the observed stock ROM responses. These functions do not perform
 * host DMA or MU completion. */
enum {
    ACCELE160_CONTROLLER_INFO_BYTES = 512,
    ACCELE160_RING_CONTROLLER_INFO_BYTES = 1004,
    ACCELE160_RING_STATUS_BYTES = 8
};

unsigned int accele160_compose_controller_info(
    unsigned char *out, unsigned int out_length,
    const unsigned char *descriptor, unsigned int descriptor_length,
    const unsigned char *product, unsigned int product_length);

/* Exact 128-byte exploratory stock reply for ROM IOCTL 0x11. */
unsigned int accele160_compose_ioctl11(unsigned char *out,
                                       unsigned int out_length);
unsigned int accele160_compose_ioctl15(unsigned char *out,
                                       unsigned int out_length);
unsigned int accele160_compose_ioctld0(unsigned char *out,
                                       unsigned int out_length);
unsigned int accele160_compose_ioctl2d(unsigned char *out,
                                       unsigned int out_length,
                                       const unsigned char *descriptor,
                                       unsigned int descriptor_length);
/* Exact first memory-ring GET_CTLR_INFO model response; composition only. */
unsigned int accele160_compose_first_ring_info(
    unsigned char *out, unsigned int out_length,
    const unsigned char *descriptor, unsigned int descriptor_length,
    const unsigned char *product, unsigned int product_length);
unsigned int accele160_compose_first_ring_status(
    unsigned char *out, unsigned int out_length);
/* Exact observed slot-2 IOCTL 0x05 response for this validated product. */
unsigned int accele160_compose_first_ring_pdev(
    unsigned char *out, unsigned int out_length,
    const unsigned char *product, unsigned int product_length);

#endif
