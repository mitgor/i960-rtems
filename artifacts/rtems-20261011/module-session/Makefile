obj-m += dac960rtems.o
KDIR ?= /lib/modules/$(shell uname -r)/build
all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules
clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean

.PHONY: test-guards
test-guards:
	$(CC) -std=c99 -Wall -Wextra -Werror test_staging_pointer.c -o /tmp/i960-test-staging-pointer
	/tmp/i960-test-staging-pointer ../../artifacts/staging-allocation-20261010/control/enquiry-before.bin

.PHONY: test-scratch
test-scratch:
	$(CC) -std=c99 -Wall -Wextra -Werror test_ram_scratch.c -o /tmp/i960-test-ram-scratch
	/tmp/i960-test-ram-scratch
