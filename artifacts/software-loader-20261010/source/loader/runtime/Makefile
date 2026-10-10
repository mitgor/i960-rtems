CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump
all: runner.bin demo.bin mix.bin
runner.o: runner.s
	$(CC) -mrp -c $< -o $@
runner.elf: runner.o runner.ld
	$(LD) -T runner.ld -Map=runner.map $< -o $@
%.o: %.c
	$(CC) -mrp -O2 -ffreestanding -fno-builtin -c $< -o $@
%.elf: %.o payload.ld
	$(LD) -T payload.ld -Map=$*.map $< -o $@
%.bin: %.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > $*.dis
