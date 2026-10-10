CC=i960-coff-gcc
CFLAGS=-mrp -O2 -ffreestanding -fno-builtin -Wall
tetris.elf: tetris.o i960.ld
	i960-elf-ld -T i960.ld tetris.o $$($(CC) -mrp -print-libgcc-file-name) -o $@
tetris.o: tetris.c tetris.h io.h
	$(CC) $(CFLAGS) -c tetris.c -o $@
clean:
	rm -f *.o *.elf

.PHONY: test
test:
	python3 check_tetris.py
