#!/bin/bash
# Builds i960 cross toolchain into ~/i960/tools on Ubuntu 22.04.
# binutils 2.27 (last gas with i960, ELF only) + gcc 3.3.6 (last gcc with i960, COFF target
# driven through the ELF as/ld). Use: i960-coff-gcc -mrp -O2 ...; i960-elf-{as,ld,objcopy,objdump}.
set -e
P=$HOME/i960/tools; S=$HOME/i960/src
sudo apt-get install -y build-essential bison flex texinfo wget pciutils
mkdir -p $S && cd $S
wget -nc https://ftp.gnu.org/gnu/binutils/binutils-2.27.tar.bz2
wget -nc https://ftp.gnu.org/gnu/gcc/gcc-3.3.6/gcc-core-3.3.6.tar.bz2
tar xjf binutils-2.27.tar.bz2; tar xjf gcc-core-3.3.6.tar.bz2

rm -rf b-bu && mkdir b-bu && cd b-bu
../binutils-2.27/configure --target=i960-elf --prefix=$P --enable-obsolete \
  --disable-werror --disable-nls --disable-gdb
make -j$(nproc) && make install && cd ..

# gcc expects i960-coff-* tool names
for t in ar ranlib as ld nm objcopy objdump strip; do ln -sf i960-elf-$t $P/bin/i960-coff-$t; done
export PATH=$P/bin:$PATH

rm -rf b-gcc && mkdir b-gcc && cd b-gcc
# old gcc on a modern host: gnu89 inline semantics, -fcommon, no fortify (collect2 open() w/o mode)
CC="gcc -std=gnu89 -fcommon -w -U_FORTIFY_SOURCE -O1" ../gcc-3.3.6/configure \
  --target=i960-coff --prefix=$P --with-as=$P/bin/i960-elf-as --with-ld=$P/bin/i960-elf-ld \
  --enable-languages=c --disable-nls --without-headers --with-newlib \
  --disable-shared --disable-threads --enable-obsolete
make -j$(nproc) MAKEINFO=true all-gcc && make MAKEINFO=true install-gcc
grep -q i960/tools/bin ~/.bashrc || echo 'export PATH=$HOME/i960/tools/bin:$PATH' >> ~/.bashrc
