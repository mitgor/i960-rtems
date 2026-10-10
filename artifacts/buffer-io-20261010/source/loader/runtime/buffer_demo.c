#include "buffer_io.h"
/* Input: mode byte then arbitrary data. 0 => text + XOR-transformed input;
 * 1 => deterministic 24x80 printable framebuffer. No global mutable state. */
unsigned payload(unsigned long address)
{
    unsigned char *b=(unsigned char *)address,*out=b+BIO_OUTPUT;
    const char *text="Hello from the real i960!\n";
    unsigned int i,n=0,len,needed;
    if(!bio_request_valid(b)) return 1; /* malformed input: never follow lengths */
    len=bio_word(b+12);
    if(!len || b[BIO_INPUT]>1) {bio_put(b+20,1);goto done;}
    needed=b[BIO_INPUT] ? 1920u : (unsigned int)sizeof("Hello from the real i960!\n")-1u+len-1u;
    if(bio_word(b+16)<needed) {bio_put(b+20,2);goto done;}
    if(b[BIO_INPUT]) {
        for(i=0;i<1920;i++) {
            unsigned int row=i/80,col=i%80;
            out[i]=(row==0 || row==23 || col==0 || col==79) ? '#' :
                   (unsigned char)('A'+(row+col)%26);
        }
        n=1920;
    } else {
        while(text[n]) {out[n]=(unsigned char)text[n];n++;}
        for(i=1;i<len;i++) out[n++]=b[BIO_INPUT+i]^0x20;
    }
    bio_put(b+20,0);
done:
    bio_put(b+24,n);
    bio_put(b+28,bio_word(b+8));
    return 0;
}
