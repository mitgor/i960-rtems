CC ?= cc
CFLAGS ?= -std=c99 -O2 -Wall -Wextra -Werror
BUILD ?= build
.PHONY: all test clean
all: $(BUILD)/libchip8.so
$(BUILD):
	mkdir -p $@
$(BUILD)/libchip8.so: chip8.c chip8.h | $(BUILD)
	$(CC) $(CFLAGS) -shared -fPIC chip8.c -o $@
$(BUILD)/test: chip8.c chip8.h test_chip8.c | $(BUILD)
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined chip8.c test_chip8.c -o $@
test: $(BUILD)/test $(BUILD)/libchip8.so
	$(BUILD)/test
	python3 test_host.py
clean:
	rm -rf $(BUILD)
