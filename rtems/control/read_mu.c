/* Explicit read-only, fixed-offset MU inventory. No queue/APIC/RAM reads.
 * Intel 272736-002 ch17: status RC bits are cleared by writing ones, not reads.
 * This tool does not claim an idle or masked register is available to borrow. */
#define _POSIX_C_SOURCE 200809L
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
#include <time.h>
struct reg {unsigned offset;const char *name;};
static const struct reg regs[]={
 {0x10,"IMR0"},{0x14,"IMR1"},{0x18,"OMR0"},{0x1c,"OMR1"},
 {0x24,"IISR"},{0x28,"IIMR"},{0x30,"OISR"},{0x34,"OIMR"}
};
int main(void){
 const char *base="/sys/bus/pci/devices/0000:37:09.1/";
 char path[256];int fd;uint32_t id;void *map;unsigned i,s;
 snprintf(path,sizeof(path),"%sconfig",base);fd=open(path,O_RDONLY);
 if(fd<0){perror("open config");return 1;}
 if(pread(fd,&id,4,0)!=4||id!=0x00101069u){fprintf(stderr,"not expected DAC960PG\n");close(fd);return 1;}
 close(fd);
 snprintf(path,sizeof(path),"%sresource0",base);fd=open(path,O_RDONLY|O_SYNC);
 if(fd<0){perror("open resource0");return 1;}
 map=mmap(NULL,4096,PROT_READ,MAP_SHARED,fd,0);close(fd);
 if(map==MAP_FAILED){perror("mmap");return 1;}
 puts("{\"read_only\":true,\"device\":\"0000:37:09.1\",\"samples\":[");
 for(s=0;s<3;s++){
  printf("%s{",s?",\n":"");
  for(i=0;i<sizeof(regs)/sizeof(regs[0]);i++){
   uint32_t value=*(volatile const uint32_t*)((const unsigned char*)map+regs[i].offset);
   printf("%s\"%s\":\"0x%08x\"",i?",":"",regs[i].name,value);
  }
  printf("}");fflush(stdout);
  if(s!=2){struct timespec delay={1,0};nanosleep(&delay,NULL);}
 }
 puts("\n],\"ownership_proven\":false}");munmap(map,4096);return 0;
}
