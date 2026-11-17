#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
if [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ]; then
    # sim5's extended-real representation currently requires x86_64. Run the
    # local build through Rosetta rather than changing guest float semantics.
    clang++ -arch x86_64 -std=gnu++20 -O2 \
        -Ithird_party/sim5/include -I. runner.cc third_party/sim5/src/*.cc \
        -o build/accele160-emu
else
    g++ -std=gnu++20 -O2 -Ithird_party/sim5/include -I. \
        runner.cc third_party/sim5/src/*.cc -o build/accele160-emu
fi
