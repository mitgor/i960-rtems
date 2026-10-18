#ifndef ACCELE_TERMINAL_POLICY_H
#define ACCELE_TERMINAL_POLICY_H
/* Grant-owned uncached pages, separate from console, samples and upload. */
#define AT_RECORD 0xc0777000u
#define AT_STACK 0xc0778000u
#define AT_END 0xc0779000u
#define AT_MAGIC 0x31544641u
#define AT_READY 0x59444152u
#define AT_DONE 0x454e4f44u
#define AT_TRIGGER 0x54455354u
#define AT_GUARD 0xa5a5a5a5u
#define AT_WORDS 176u
#define AT_IRQ_STACK 0xc0779000u
#define AT_IRQ_END 0xc077a000u
static unsigned int at_request(unsigned int nonce,unsigned int seq,
 unsigned int token,unsigned int expected,unsigned int build_test){
 return expected && nonce==expected && seq==1u && token==AT_TRIGGER &&
        (build_test>=1u&&build_test<=4u);
}
/* Non-destructive DMA register offsets; CSR(+4) is deliberately absent. */
static const unsigned int at_dma_offsets[3]={0u,0x10u,0x20u};
#endif
