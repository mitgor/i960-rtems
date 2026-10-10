CROSS ?= i960-coff-
CC = $(CROSS)gcc
LD = $(CROSS)ld
OC = $(CROSS)objcopy
OD = $(CROSS)objdump

all: return-status.bin

return-status.o: return_status.s
	$(CC) -mrp -c $< -o $@

return-status.elf: return-status.o link.ld
	$(LD) -T link.ld -Map=return-status.map return-status.o -o $@

return-status.bin: return-status.elf
	$(OC) -O binary $< $@
	$(OD) -dr $< > return-status.dis

clean:
	rm -f return-status.o return-status.elf return-status.bin return-status.map return-status.dis

.PHONY: all clean
