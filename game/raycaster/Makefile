CC ?= cc
FLAGS = -std=c99 -O2 -fno-builtin -Wall -Wextra -Werror
all: build/libray.so
build:
	mkdir -p $@
build/libray.so: ray.c ray.h trig.h | build
	$(CC) $(FLAGS) -shared -fPIC ray.c -o $@
build/test: ray.c ray.h trig.h test.c | build
	$(CC) $(FLAGS) -fsanitize=address,undefined -g ray.c test.c -o $@
test: all build/test
	$(MAKE) -C ../../rtems/memory test
	build/test
	python3 test_host.py

# Includes complete response-range mutation and transaction fault sweeps.
test-transfer:
	python3 transfer/test.py
.PHONY: test-transfer
