CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump

all: romfetch.bin ram-status.bin

start.o: start.s
	$(CC) -mrp -c $< -o $@

romfetch.elf: start.o link.ld
	$(LD) -T link.ld -Map=romfetch.map start.o -o $@

romfetch.bin: romfetch.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > romfetch.dis

ram-status.o: ram_status.s
	$(CC) -mrp -c $< -o $@

ram-status.elf: ram-status.o ram-link.ld
	$(LD) -T ram-link.ld -Map=ram-status.map ram-status.o -o $@

ram-status.bin: ram-status.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > ram-status.dis

.PHONY: all
