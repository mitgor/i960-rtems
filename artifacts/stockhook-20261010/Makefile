CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump

all: stockhook.bin

start.o: start.s
	$(CC) -mrp -c $< -o $@

stockhook.elf: start.o link.ld
	$(LD) -T link.ld -Map=stockhook.map start.o -o $@

stockhook.bin: stockhook.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > stockhook.dis

.PHONY: all
