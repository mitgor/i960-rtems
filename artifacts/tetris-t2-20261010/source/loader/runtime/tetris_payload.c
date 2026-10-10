#include "buffer_io.h"
#include "../../game/tetris.h"
unsigned payload(unsigned long address)
{
    unsigned char *b=(unsigned char *)address;
    unsigned status;
    if(!bio_request_valid(b))return 1;
    status=tetris_request(b+BIO_INPUT,bio_word(b+12),b+BIO_OUTPUT,bio_word(b+16));
    bio_put(b+20,status);bio_put(b+24,status?0:TETRIS_RESPONSE_BYTES);
    bio_put(b+28,bio_word(b+8));return 0;
}
