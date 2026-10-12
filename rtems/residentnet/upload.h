#ifndef RESIDENT_UPLOAD_H
#define RESIDENT_UPLOAD_H
#ifndef UPLOAD_GUARD_LO
#define UPLOAD_GUARD_LO 0xc02d0000u
#endif
#define UPLOAD_BASE (UPLOAD_GUARD_LO+64u)
#define UPLOAD_BYTES (8u*1048576u)
#define UPLOAD_GUARD_HI (UPLOAD_BASE+UPLOAD_BYTES)
#define UPLOAD_RESERVE (UPLOAD_GUARD_HI+64u)
#define UPLOAD_WORDS 256u
#define UPLOAD_REPLY 16u
unsigned int upload_init(void),upload_guards(void),upload_finish(void);
unsigned int upload_control(unsigned int,unsigned int,unsigned int,unsigned int);
void upload_step(void);
void upload_protect_init(void);
unsigned int upload_protect_all(void),upload_protect_step(void),upload_protect_finish(void);
void upload_protect_report(unsigned int*);
#endif
