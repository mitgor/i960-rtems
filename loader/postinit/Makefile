CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump
HOSTCC ?= cc
CFLAGS = -mrp -O2 -ffreestanding -fno-builtin -Wall -DPOSTINIT_PROFILE
all: loader.bin hello.bin loadctl
start.o: start.s
	$(CC) -mrp -c $< -o $@
loader.o: ../loader.c ../mu.h
	$(CC) $(CFLAGS) -c $< -o $@
loader.elf: start.o loader.o loader.ld
	$(LD) -T loader.ld -Map=loader.map start.o loader.o -o $@
loader.bin: loader.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > loader.dis
hello.o: hello.s
	$(CC) -mrp -c $< -o $@
hello.elf: hello.o
	$(LD) -Ttext=0xC0120000 -e _start hello.o -o $@
hello.bin: hello.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > hello.dis
loadctl: ../loadctl.c ../mu.h
	$(HOSTCC) -std=c99 -O2 -Wall -Wextra -Werror -DPOSTINIT_PROFILE ../loadctl.c -o $@
.PHONY: all
test:
	$(HOSTCC) -std=c99 -Wall -Wextra -Werror test_profile.c -o test_profile
	./test_profile
	python3 -B -m unittest -v test_image.py test_preflight.py test_package_update.py test_audit_recovery.py test_staging_geometry.py
.PHONY: test
