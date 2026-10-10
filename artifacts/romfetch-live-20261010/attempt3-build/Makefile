CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump

all: romfetch.bin ram-status.bin icctl-control.bin

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

icctl-control.o: icctl_control.s
	$(CC) -mrp -c $< -o $@

icctl-control.elf: icctl-control.o link.ld
	$(LD) -T link.ld -Map=icctl-control.map icctl-control.o -o $@

icctl-control.bin: icctl-control.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > icctl-control.dis

.PHONY: all
