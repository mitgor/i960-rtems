CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump

all: romhook.bin

start.o: start.s
	$(CC) -mrp -c $< -o $@

romhook.elf: start.o link.ld
	$(LD) -T link.ld -Map=romhook.map start.o -o $@

romhook.bin: romhook.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > romhook.dis

.PHONY: all
