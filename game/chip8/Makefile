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
test: $(BUILD)/test $(BUILD)/libchip8.so $(BUILD)/test-player
	$(BUILD)/test
	$(BUILD)/test-player
	python3 test_host.py
clean:
	rm -rf $(BUILD)

$(BUILD)/libplayer.so: chip8.c chip8.h stream/player.c stream/player.h | $(BUILD)
	$(CC) $(CFLAGS) -shared -fPIC chip8.c stream/player.c -o $@
all: $(BUILD)/libplayer.so

$(BUILD)/test-player: chip8.c chip8.h stream/player.c stream/player.h stream/test_player.c | $(BUILD)
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined chip8.c stream/player.c stream/test_player.c -o $@
