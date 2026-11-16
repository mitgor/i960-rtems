#!/bin/sh
# The experiment branch carries only the saved inputs it needs. The older
# native-ROM/emulator tests read many more saved artifacts that are untracked
# in the main checkout. This links those directories into this worktree,
# read-only by convention, and hides the links from git locally. Nothing is
# copied, committed, or modified in the main checkout.
#   usage: link-main-checkout-artifacts.sh /path/to/main/checkout
set -eu
main=$(cd "$1" && pwd)
here=$(cd "$(dirname "$0")/../../.." && pwd)
exclude=$(git -C "$here" rev-parse --git-path info/exclude)
mkdir -p "$(dirname "$exclude")"
for source in "$main"/artifacts/current/*/; do
  name=$(basename "$source")
  target="$here/artifacts/current/$name"
  if [ ! -e "$target" ]; then
    ln -s "$source" "$target"
    echo "/artifacts/current/$name" >> "$exclude"
    echo "linked $name"
  elif [ ! -L "$target" ]; then
    # Directory partly carried by the branch: link only its missing entries.
    for entry in "$source"*; do
      child=$(basename "$entry")
      if [ ! -e "$target/$child" ]; then
        ln -s "$entry" "$target/$child"
        echo "/artifacts/current/$name/$child" >> "$exclude"
        echo "linked $name/$child"
      fi
    done
  fi
done
