CC ?= cc
FLAGS = -O2 -Wall -Wextra -Werror -fno-builtin -fsanitize=address,undefined -g
NAMES = -Dmemcpy=word_memcpy -Dmemset=word_memset -Dmemmove=word_memmove
all: test
audit-build:
	mkdir -p build
build/word.o: word.c | audit-build
	$(CC) $(FLAGS) $(NAMES) -c $< -o $@
build/check.o: check.c check.h | audit-build
	$(CC) $(FLAGS) $(NAMES) -c $< -o $@
# Generate only unchanged helpers: this also checks forward memmove -> word memcpy.
build/legacy.c: ../session/libc.c Makefile | audit-build
	printf '#include <stddef.h>\nextern void *memcpy(void *, const void *, size_t);\n' > $@
	sed -n '/^void \*memmove(/p' $< >> $@
build/move.o: build/legacy.c | audit-build
	$(CC) $(FLAGS) $(NAMES) -c $< -o $@
build/test: test.c build/check.o build/word.o build/move.o
	$(CC) $(FLAGS) $^ -o $@
test: build/test
	build/test
.PHONY: test all audit-build
