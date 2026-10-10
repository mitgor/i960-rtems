# i960 flash loader + host sender. Build the i960 side with the cross-toolchain
# (i960-coff-gcc / i960-elf-*, on PATH); build loadctl with the native gcc.
CC   = i960-coff-gcc
LD   = i960-elf-ld
OC   = i960-elf-objcopy
CFLAGS = -mrp -O2 -ffreestanding -fno-builtin -Wall
RUN  = 0xFEFCCD44          # loader run address = stock base 0xFEFC8000 + mkimage --at 0x4d44

all: loader.bin hello.bin loadctl

start.o: start.s ;            $(CC) -mrp -c $< -o $@
loader.o: loader.c mu.h ;     $(CC) $(CFLAGS) -c loader.c -o $@
loader.elf: start.o loader.o loader.ld
	$(LD) -T loader.ld -Ttext=$(RUN) start.o loader.o -o $@
loader.bin: loader.elf ;      $(OC) -O binary $< $@

hello.o: hello.c ;            $(CC) $(CFLAGS) -c hello.c -o $@
hello.elf: hello.o payload.ld ; $(LD) -T payload.ld hello.o -o $@
hello.bin: hello.elf ;        $(OC) -O binary $< $@

loadctl: loadctl.c mu.h ;     gcc -O2 -Wall -o loadctl loadctl.c

# Assemble the loader into a flashable firmware image (needs the decoded stock image).
# STOCK must point at a decoded stock firmware .bin (payload+header+trailer).
image: loader.bin
	python3 ../host/mkimage.py --stock $(STOCK) --code loader.bin --at 0x4d44 --out loader-fw.img

clean: ; rm -f *.o *.elf *.bin loadctl loader-fw.img
.PHONY: all image clean
