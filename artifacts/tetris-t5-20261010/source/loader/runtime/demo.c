/* Cooperative i960 C ABI: input and result in g0; ordinary returning function. */
unsigned int payload(unsigned int n)
{
    unsigned int a = 0, b = 1, i;
    n &= 31;
    for (i = 0; i < n; ++i) {
        unsigned int next = a + b;
        a = b;
        b = next;
    }
    return a;
}
