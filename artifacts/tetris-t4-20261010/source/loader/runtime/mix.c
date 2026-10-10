/* A different program to exercise replacement of already executed code. */
unsigned payload(unsigned value)
{
    return ((value << 7) | (value >> 25)) ^ 0x96040729u;
}
