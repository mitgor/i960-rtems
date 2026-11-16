#include "controller_info.h"

/* Nonzero bytes outside product and serial, from the exploratory stock
 * replay. Their semantics and stability across cards are not yet proven. */
static const unsigned char observed[ACCELE160_CONTROLLER_INFO_BYTES] = {
    [0x001]=0x03, [0x002]=0x20, [0x004]=0x21, [0x006]=0x20,
    [0x007]=0x50, [0x010]=0x50, [0x011]=0x43, [0x012]=0x49,
    [0x040]=0x06, [0x042]=0x05, [0x044]=0x05, [0x045]=0x0a,
    [0x046]=0x14, [0x058]=0x10, [0x059]=0x10, [0x05a]=0x20,
    [0x05c]=0x20, [0x09d]=0x08, [0x09e]=0x01, [0x09f]=0x01,
    [0x0a6]=0x01, [0x0af]=0x02, [0x0b0]=0x01, [0x0b1]=0x02,
    [0x0b2]=0x02, [0x0b3]=0x02, [0x0b4]=0x10, [0x0b5]=0x10,
    [0x0b6]=0x10, [0x0d0]=0x10, [0x0d2]=0x08, [0x0dc]=0x42,
    [0x0de]=0x20, [0x0df]=0x84, [0x0f0]=0x04, [0x0fc]=0x42,
    [0x0fe]=0x20, [0x0ff]=0x84, [0x110]=0x64, [0x112]=0x07,
    [0x113]=0x01, [0x1a2]=0x01, [0x1a4]=0xa0, [0x1a5]=0x86,
    [0x1a6]=0x01, [0x1c0]=0x32, [0x1c1]=0x32, [0x1c3]=0x32,
    [0x1c9]=0x04, [0x1cd]=0x04, [0x1d1]=0x02, [0x1d4]=0xff,
    [0x1d5]=0x01, [0x1d9]=0x08,
};

unsigned int accele160_compose_controller_info(
    unsigned char *out, unsigned int out_length,
    const unsigned char *descriptor, unsigned int descriptor_length,
    const unsigned char *product, unsigned int product_length)
{
    unsigned int i;
    if (!out || !descriptor || !product ||
        out_length != ACCELE160_CONTROLLER_INFO_BYTES ||
        descriptor_length < 0x390u || product_length < 16u)
        return 1u;
    /* XLYM is the card-specific flash descriptor signature. */
    if (descriptor[0] != 'X' || descriptor[1] != 'L' ||
        descriptor[2] != 'Y' || descriptor[3] != 'M')
        return 2u;
    /* This composer is limited to the measured AcceleRAID 160 firmware. */
    {
        static const unsigned char expected[] =
            "AcceleRAID 160  ";
        for (i = 0; i < 16u; ++i)
            if (product[i] != expected[i]) return 3u;
    }
    for (i = 0; i < 11u; ++i)
        if (descriptor[0x384u + i] < '0' ||
            descriptor[0x384u + i] > '9') return 4u;
    if (descriptor[0x38fu] != 0u) return 4u;
    for (i = 0; i < out_length; ++i) out[i] = observed[i];
    for (i = 0; i < 16u; ++i) out[0x20u + i] = product[i];
    for (i = 0; i < 11u; ++i) out[0x60u + i] = descriptor[0x384u + i];
    return 0u;
}

unsigned int accele160_compose_ioctl11(unsigned char *out,
                                       unsigned int out_length)
{
    unsigned int i;
    if (!out || out_length != 128u) return 1u;
    for (i = 0; i < out_length; ++i) out[i] = 0u;
    out[0x10u] = 1u;
    out[0x28u] = 1u;
    return 0u;
}

unsigned int accele160_compose_ioctl15(unsigned char *out,
                                       unsigned int out_length)
{
    unsigned int i;
    if (!out || out_length != 64u) return 1u;
    for (i = 0; i < out_length; ++i) out[i] = 0u;
    out[0x04u] = 0x05u;
    out[0x08u] = 0x1cu;
    out[0x18u] = 0x70u;
    out[0x1au] = 0x09u;
    out[0x1fu] = 0x07u;
    out[0x24u] = 0x81u;
    out[0x25u] = 0xabu;
    return 0u;
}

unsigned int accele160_compose_ioctld0(unsigned char *out,
                                       unsigned int out_length)
{
    unsigned int i;
    if (!out || out_length != 128u) return 1u;
    for (i = 0; i < out_length; ++i) out[i] = 0u;
    out[0x00u] = 0x40u;
    out[0x01u] = 0x24u;
    out[0x04u] = 0x66u;
    out[0x05u] = 0x32u;
    out[0x06u] = 0x05u;
    out[0x09u] = 0x02u;
    out[0x0au] = 0x06u;
    out[0x40u] = 0x07u;
    out[0x44u] = 0x01u;
    out[0x45u] = 0x04u;
    out[0x47u] = 0x02u;
    out[0x48u] = 0x01u;
    out[0x49u] = 0x54u;
    return 0u;
}

/* IOCTL 0x2d returns the first 512 bytes of this card's XLYM flash descriptor.
 * This was established by byte-for-byte comparison with two stock replays. */
unsigned int accele160_compose_ioctl2d(unsigned char *out,
                                       unsigned int out_length,
                                       const unsigned char *descriptor,
                                       unsigned int descriptor_length)
{
    unsigned int i;
    if (!out || !descriptor || out_length != 512u ||
        descriptor_length < 512u) return 1u;
    if (descriptor[0] != 'X' || descriptor[1] != 'L' ||
        descriptor[2] != 'Y' || descriptor[3] != 'M') return 2u;
    for (i = 0; i < out_length; ++i) out[i] = descriptor[i];
    return 0u;
}

unsigned int accele160_compose_first_ring_info(
    unsigned char *out, unsigned int out_length,
    const unsigned char *descriptor, unsigned int descriptor_length,
    const unsigned char *product, unsigned int product_length)
{
    unsigned int i, result;
    if (!out || out_length != ACCELE160_RING_CONTROLLER_INFO_BYTES)
        return 1u;
    result = accele160_compose_controller_info(
        out, ACCELE160_CONTROLLER_INFO_BYTES, descriptor,
        descriptor_length, product, product_length);
    if (result) return result;
    for (i = ACCELE160_CONTROLLER_INFO_BYTES; i < out_length; ++i)
        out[i] = 0u;
    return 0u;
}

unsigned int accele160_compose_first_ring_status(
    unsigned char *out, unsigned int out_length)
{
    unsigned int i;
    if (!out || out_length != ACCELE160_RING_STATUS_BYTES) return 1u;
    for (i = 0; i < out_length; ++i) out[i] = 0u;
    out[0] = 1u;      /* command ID 1, zero status and sense */
    out[4] = 0xecu;   /* observed signed residual -20 = 0xffffffec */
    out[5] = 0xffu;
    out[6] = 0xffu;
    out[7] = 0xffu;
    return 0u;
}

unsigned int accele160_compose_first_ring_pdev(
    unsigned char *out, unsigned int out_length,
    const unsigned char *product, unsigned int product_length)
{
    unsigned int i;
    static const unsigned char expected_product[] = "AcceleRAID 160  ";
    static const unsigned char vendor[] = "MYLEX   ";
    static const unsigned char revision[] = "0600";
    if (!out || !product || out_length != 512u || product_length < 16u)
        return 1u;
    for (i = 0; i < 16u; ++i)
        if (product[i] != expected_product[i]) return 2u;
    /* Sparse bytes from the first stock target-0 GET_PDEV_INFO_VALID source.
     * All other fields are zero, including every reserved byte. */
    for (i = 0; i < out_length; ++i) out[i] = 0u;
    out[0x02u] = 7u;
    out[0x04u] = 6u;
    out[0x07u] = 0x10u;
    out[0x08u] = 0x50u;
    out[0x20u] = 0x10u;
    out[0x33u] = 2u;
    out[0x80u] = 0xccu;
    out[0x82u] = 3u;
    out[0x83u] = 2u;
    out[0x84u] = 0x1fu;
    out[0x87u] = 0x32u;
    for (i = 0; i < 8u; ++i) out[0x88u + i] = vendor[i];
    for (i = 0; i < 16u; ++i) out[0x90u + i] = product[i];
    for (i = 0; i < 4u; ++i) out[0xa0u + i] = revision[i];
    return 0u;
}
