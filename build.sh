#!/bin/bash
# Sync sources to the remote box and build everything there.
set -e
R=i9   # ssh alias in ~/.ssh/i960.conf  (mit@192.168.2.75)
ssh -F ~/.ssh/i960.conf $R 'mkdir -p ~/i960/game ~/i960/host'
scp -F ~/.ssh/i960.conf game/*  $R:i960/game/
scp -F ~/.ssh/i960.conf host/*  $R:i960/host/
ssh -F ~/.ssh/i960.conf $R 'cd ~/i960/host && cp ../game/io.h . && export PATH=$HOME/i960/tools/bin:$PATH \
  && (cd ../game && make) && gcc -O2 -w -o emu emu.c \
  && gcc -O2 -o ref ref.c && gcc -O2 -w -o ref_clear ref_clear.c \
  && echo "self-check:" && diff <(./ref) <(./emu -t test.elf) && diff <(./ref_clear) <(./emu -t test_clear.elf) \
  && echo "ALL OK"'
