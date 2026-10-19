/* Profile 14 only. Fixed 48-read whitelist, no CSR/ASR, config cycles or writes.
 * Record extension stays in the existing 4 KiB terminal page (words 256..311).
 * Not atomic across engines; no idle/drain/ownership inference. */
static const unsigned int at_engine_regs[48]={
 0x1400u,0x140cu,0x1410u,0x1414u,0x1418u,0x141cu,0x1420u,0x1424u,
 0x1440u,0x144cu,0x1450u,0x1454u,0x1458u,0x145cu,0x1460u,0x1464u,
 0x1480u,0x148cu,0x1490u,0x1494u,0x1498u,0x149cu,0x14a0u,0x14a4u,
 0x1600u,0x104cu,0x1800u,0x1808u,0x180cu,0x1820u,0x1824u,0x1828u,
 /* Fixed firmware channel-0 metadata and AAU queue anchors, not chip MMIO. */
 0xc0384b6cu,0xc0384b70u,0xc0384b8cu,0xc0384b90u,0xc0384b94u,0xc0384b98u,
 0xc0384b9cu,0xc0384ba0u,0xc0384ba4u,0xc0384ba8u,0xc0384bacu,
 0xc0384e78u,0xc0384e7cu,0xc049b7ccu,0xc049b7d0u,0xc049b7d4u
};
static void at_engine_snapshot(volatile unsigned int *record,unsigned int nonce,
 unsigned int seq,unsigned int phase){unsigned int i;
 record[256]=0x31474e45u;record[257]=1;record[258]=nonce;
 record[259]=seq;record[260]=phase;record[261]=48;
 record[262]=0;record[263]=0;
 for(i=0;i<48;i++)record[264+i]=REG(at_engine_regs[i]);
}
