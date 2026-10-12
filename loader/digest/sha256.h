#ifndef LOADER_SHA256_H
#define LOADER_SHA256_H
struct sha256 {unsigned h[8],bytes,used;unsigned char block[64];};
void sha256_init(struct sha256*);
int sha256_update(struct sha256*,const void*,unsigned);
void sha256_finish(struct sha256*,unsigned char[32]);
#endif
