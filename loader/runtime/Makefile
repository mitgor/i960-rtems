CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump
all: runner.bin demo.bin mix.bin buffer_demo.bin tetris_payload.bin
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

buffer_demo.o: buffer_demo.c buffer_io.h
	$(CC) -mrp -O2 -ffreestanding -fno-builtin -c $< -o $@
buffer_start.o: buffer_start.s
	$(CC) -mrp -c $< -o $@
buffer_demo.elf: buffer_start.o buffer_demo.o buffer.ld
	$(LD) -T buffer.ld -Map=buffer_demo.map buffer_start.o buffer_demo.o -o $@

tetris_core.o: ../../game/tetris.c ../../game/tetris.h ../../game/io.h
	$(CC) -mrp -O2 -ffreestanding -fno-builtin -DTETRIS_CORE_ONLY -c $< -o $@
tetris_payload.o: tetris_payload.c buffer_io.h ../../game/tetris.h
	$(CC) -mrp -O2 -ffreestanding -fno-builtin -c $< -o $@
tetris_payload.elf: buffer_start.o tetris_payload.o tetris_core.o buffer.ld
	$(LD) -T buffer.ld -Map=tetris_payload.map buffer_start.o tetris_payload.o tetris_core.o -o $@
