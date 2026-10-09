/* myflash -- drive the DAC960/i960 firmware command mailbox through BAR0.
   Milestone 0: SAFE, read-only register probe. mmaps the 8 KB PG register window
   (BAR0) and prints the mailbox/doorbell/error registers so we can confirm BAR0 is
   the PG register window and see the live firmware's state. No commands issued, no DMA.

   Build (on the box):  gcc -O2 -o myflash myflash.c
   Run (BAR0 phys passed in, device detached from myrb first):
       sudo ./myflash probe 0xee000000
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

/* PG register offsets within BAR0 (from Linux DAC960 header) */
#define PG_INBOUND_DOORBELL   0x0020
#define PG_OUTBOUND_DOORBELL  0x002C
#define PG_IRQ_MASK           0x0034
#define PG_CMD_OPCODE         0x1000   /* 13-byte command mailbox: 0x1000..0x100C */
#define PG_STATUS_ID          0x1018
#define PG_STATUS             0x101A   /* 16-bit status word */
#define PG_ERROR_STATUS       0x103F
#define PG_WINDOW             0x2000

static volatile uint8_t *bar;
static uint8_t  rb(uint32_t o){ return *(volatile uint8_t  *)(bar+o); }
static uint16_t rw(uint32_t o){ return *(volatile uint16_t *)(bar+o); }
static uint32_t rl(uint32_t o){ return *(volatile uint32_t *)(bar+o); }

int main(int argc,char**argv){
    if(argc<3 || strcmp(argv[1],"probe")){ fprintf(stderr,"usage: %s probe <bar0_phys>\n",argv[0]); return 2; }
    uint64_t phys = strtoull(argv[2],0,0);
    int fd=open("/dev/mem",O_RDONLY|O_SYNC);          /* read-only: cannot perturb anything */
    if(fd<0){ perror("/dev/mem (need root)"); return 1; }
    void *m=mmap(0,PG_WINDOW,PROT_READ,MAP_SHARED,fd,phys);
    if(m==MAP_FAILED){ perror("mmap BAR0"); return 1; }
    bar=m;
    printf("BAR0 @ %#llx (PG window, %d bytes)\n",(unsigned long long)phys,PG_WINDOW);
    printf("  inbound  doorbell [0x20]  = 0x%02x  (b0 MailboxFull, b1 InitInProgress)\n", rb(PG_INBOUND_DOORBELL));
    printf("  outbound doorbell [0x2C]  = 0x%02x  (b0 StatusAvailable)\n", rb(PG_OUTBOUND_DOORBELL));
    printf("  irq mask          [0x34]  = 0x%02x\n", rb(PG_IRQ_MASK));
    printf("  error status      [0x103F]= 0x%02x  (b2 pending)\n", rb(PG_ERROR_STATUS));
    printf("  status id         [0x1018]= 0x%04x\n", rw(PG_STATUS_ID));
    printf("  status word       [0x101A]= 0x%04x\n", rw(PG_STATUS));
    printf("  cmd mailbox [0x1000..0C]  =");
    for(int i=0;i<13;i++) printf(" %02x", rb(PG_CMD_OPCODE+i));
    printf("\n");
    printf("  first 16 words of window  :\n");
    for(int o=0;o<0x40;o+=16){ printf("   +%04x:",o); for(int j=0;j<16;j+=4) printf(" %08x",rl(o+j)); printf("\n"); }
    munmap(m,PG_WINDOW); close(fd);
    return 0;
}
