/* Native reference: one binary request on stdin, exact response on stdout. */
#include <stdio.h>
#include "tetris.h"
int main(void)
{
    u8 in[TETRIS_REQUEST_BYTES],out[TETRIS_RESPONSE_BYTES];unsigned status;
    if(fread(in,1,sizeof(in),stdin)!=sizeof(in) || getchar()!=EOF)return 3;
    status=tetris_request(in,sizeof(in),out,sizeof(out));
    if(status)return status;
    return fwrite(out,1,sizeof(out),stdout)==sizeof(out)?0:4;
}
