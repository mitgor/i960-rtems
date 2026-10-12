# Target toolchain: GCC 3.3.6 + binutils 2.27. Native tests need only HOSTCC/Python.
CC = i960-coff-gcc
LD = i960-elf-ld
OC = i960-elf-objcopy
OBJDUMP = i960-elf-objdump
NM = i960-elf-nm
HOSTCC ?= cc
PYTHON ?= python3
CFLAGS = -mrp -O2 -ffreestanding -fno-builtin -Wall
HOSTCFLAGS ?= -std=c99 -O2 -Wall -Wextra -Wconversion -Werror
RUN = 0xFEFCCD44

all: loader.bin hello.bin loadctl

start.o: start.s
	$(CC) -mrp -c $< -o $@
loader.o: loader.c mu.h
	$(CC) $(CFLAGS) -c $< -o $@
loader.elf: start.o loader.o loader.ld
	$(LD) -T loader.ld -Ttext=$(RUN) -Map=loader.map start.o loader.o -o $@
loader.bin: loader.elf check_build.py
	$(OC) -O binary $< $@
	$(PYTHON) check_build.py --kind loader --elf $< --binary $@

hello.o: hello.c mu.h
	$(CC) $(CFLAGS) -c $< -o $@
hello.elf: hello.o payload.ld
	$(LD) -T payload.ld -Map=hello.map hello.o -o $@
hello.bin: hello.elf check_build.py
	$(OC) -O binary $< $@
	$(PYTHON) check_build.py --kind payload --elf $< --binary $@

loadctl: loadctl.c mu.h
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $<
test_protocol: test_protocol.c loadctl.c loader.c mu.h
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $<
test: loadctl test_protocol
	$(PYTHON) segmented/test.py
	./test_protocol
	$(PYTHON) -B -m unittest -v test_build.py

# check is a target-toolchain gate; inspect the generated disassembly before flash.
check: loader.bin hello.bin
	$(OBJDUMP) -dr loader.elf > loader.dis
	$(OBJDUMP) -dr hello.elf > hello.dis
	$(NM) -u loader.elf > loader.undefined
	$(NM) -u hello.elf > hello.undefined
	@test ! -s loader.undefined && test ! -s hello.undefined

image: check
	@test -n "$(STOCK)" || { echo 'Set STOCK to the decoded stock firmware .bin'; exit 1; }
	$(PYTHON) check_build.py --kind loader --elf loader.elf --binary loader.bin --stock "$(STOCK)"
	$(PYTHON) ../host/mkimage.py --stock "$(STOCK)" --code loader.bin --at 0x4d44 --out loader-fw.img

clean:
	rm -f *.o *.elf loader.bin hello.bin loadctl test_protocol loader-fw.img *.map *.dis *.undefined
.PHONY: all test check image clean
.DELETE_ON_ERROR:
