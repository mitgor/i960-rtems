#include <assert.h>
#include <stdio.h>
#include "staging_pointer.h"
int main(int argc, char **argv)
{
    unsigned char p[512];
    FILE *f;
    unsigned int i;
    assert(argc==2);
    f=fopen(argv[1],"rb"); assert(f);
    assert(fread(p,1,sizeof(p),f)==sizeof(p)); fclose(f);
    assert(sp_profile(p));
    for(i=0;i<512;i++) {
        unsigned char old=p[i]; p[i]^=1;
        if(i==4 || i==5 || i==6 || (i>=0x18 && i<0x24) || i==0x68 || i==0x69)
            assert(!sp_profile(p));
        p[i]=old;
    }
    assert(sp_allowed(512,0,0));
    assert(!sp_allowed(4,POINTER_OFFSET,0));
    assert(sp_allowed(4,POINTER_OFFSET,1));
    assert(!sp_allowed(8,POINTER_OFFSET,1));
    assert(!sp_allowed(4,POINTER_OFFSET+4,1));
    assert(!sp_allowed(4,0xfffffffc,1));
    assert(!sp_allowed(0,0,1));
    assert(!sp_allowed(0x10000,0,1));
    assert(sp_allowed(4,0x7fffc,0));
    assert(!sp_allowed(8,0x7fffc,0));
    assert((STAGING_BASE+POINTER_OFFSET)==0xc0112a70u);
    assert(!sp_runtime_allowed(16,0xc004a2e0u-STAGING_BASE,0));
    assert(sp_runtime_allowed(16,0xc004a2e0u-STAGING_BASE,1));
    assert(sp_runtime_allowed(8,0xc011e22cu-STAGING_BASE,1));
    assert(sp_runtime_allowed(512,0xc0110780u-STAGING_BASE,1));
    assert(!sp_runtime_allowed(512,0xc0110784u-STAGING_BASE,1));
    assert(!sp_runtime_allowed(32,0xc004a2e0u-STAGING_BASE,1));
    assert(!sp_runtime_allowed(4,0xe0600000u-STAGING_BASE,1));
    assert((STAGING_BASE+DRAM_HOOK_OFFSET)==DRAM_HOOK_ADDRESS);
    assert(!sp_dram_hook_allowed(64,DRAM_HOOK_OFFSET,0,1));
    assert(!sp_dram_hook_allowed(64,DRAM_HOOK_OFFSET,1,0));
    assert(sp_dram_hook_allowed(64,DRAM_HOOK_OFFSET,1,1));
    assert(!sp_dram_hook_allowed(16,DRAM_HOOK_OFFSET,1,1));
    assert(!sp_dram_hook_allowed(64,DRAM_HOOK_OFFSET+4,1,1));
    assert((STAGING_BASE+ROM_TABLE_OFFSET)==ROM_TABLE_ADDRESS);
    assert(!sp_rom_table_allowed(4,ROM_TABLE_OFFSET,0,1));
    assert(!sp_rom_table_allowed(4,ROM_TABLE_OFFSET,1,0));
    assert(sp_rom_table_allowed(4,ROM_TABLE_OFFSET,1,1));
    assert(!sp_rom_table_allowed(8,ROM_TABLE_OFFSET,1,1));
    assert(!sp_rom_table_allowed(4,ROM_TABLE_OFFSET+4,1,1));
    return 0;
}
