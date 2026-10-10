# Exact i960 cross tools — 2026-10-11

This preserves the Linux x86-64 tools used for the card builds, so continued
access to the remote PC and upstream download sites is not required.

- `linux-x86_64-installed.tar.xz`: complete `/home/mit/i960/tools` installation,
  including symlinks, compiler specs, binutils, headers, libraries and manuals.
- `installed-files.json`: SHA256 and size for every regular installed file, and
  exact symlink targets. All entries were compared to the local archive.
- `gcc-core-3.3.6.tar.bz2`, `binutils-2.27.tar.bz2`: exact original source packages
  retained on the build host, including their license texts. GCC is GPL-licensed;
  binutils has its own included GPL terms. Keep source packages with binaries.
- `toolchain.sh`: snapshot of the repository's actual build/install recipe.
- `environment.txt`: Ubuntu, kernel, compiler configuration, runtime dependency
  output and remote package checksums.

GCC targets `i960-coff`; the configured assembler/linker are the i960 ELF
binutils 2.27 tools. The executable name does not mean the resulting images are
COFF. The earlier audit found no local changes to original upstream source
files. The unused binutils 2.29.1 tree, compiler build intermediates and host
OS libraries are not included.

Extract the installation into a new directory for inspection. For faithful use
on compatible x86-64 Linux, its configured prefix is `/home/mit/i960/tools`;
GCC specs/configuration contain absolute paths. Do not overwrite an existing
installation. Arbitrary relocation has not been tested. The archived programs
are Linux binaries, not macOS executables. `environment.txt` records glibc/loader
dependencies; this is not a self-contained Linux environment.

For a different prefix or incompatible host, rebuild from the included sources,
using the recipe and its old-GCC flags as a reference. The recipe assumes Ubuntu
packages and uses downloads; for offline use supply the archived tarballs to
its source directory and adapt acquisition accordingly. A complete clean-room
rebuild from this preservation archive was not performed during this audit.

No toolchain binaries were executed on the card during collection.
