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

test-upload:
	python3 upload/test.py
.PHONY: test-upload

# Differential candidates retain the unmodified renderer and byte validator.
test-callback:
	python3 callback/test.py
	python3 callback/test_transport.py
.PHONY: test-callback

# Bounded queue protocol, targeted reads and generated driver lifecycle.
test-queue: all
	python3 queue/test.py
	python3 queue/test_transport.py
.PHONY: test-queue

# Same-slot ACK+PUBLISH, including rejected-request state preservation.
test-combined: test-queue
	python3 combined/test.py
.PHONY: test-combined
