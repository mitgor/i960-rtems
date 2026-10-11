/* Exclusive, reboot-only ownership of the existing 256-byte fault table.
 * All entries become local calls. Install cached NMI first; never restore. */
#ifndef RESIDENT_FAULT_OWNER_H
#define RESIDENT_FAULT_OWNER_H
#define FAULT_TABLE 0xc0000800u
static unsigned int fault_table_install(unsigned int handler){unsigned int i;
 if(handler&3)return 1;
 for(i=0;i<32;i++){FO_WRITE(FAULT_TABLE+i*8+4,0);FO_WRITE(FAULT_TABLE+i*8,handler);}
 for(i=0;i<32;i++)if(FO_READ(FAULT_TABLE+i*8)!=handler||FO_READ(FAULT_TABLE+i*8+4))return 2;
 return 0;
}
static unsigned int fault_table_valid(unsigned int handler){unsigned int i;
 for(i=0;i<32;i++)if(FO_READ(FAULT_TABLE+i*8)!=handler||FO_READ(FAULT_TABLE+i*8+4))return 0;
 return 1;
}
#endif
