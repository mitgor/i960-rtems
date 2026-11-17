#!/bin/sh
# The experiment branch carries only the saved inputs it needs. The older
# native-ROM/emulator tests read many more saved artifacts that are untracked
# in the main checkout. This links those directories into this worktree,
# read-only by convention. Nothing is copied, committed, or modified in the
# main checkout.
#
# The links are hidden from git through artifacts/current/.gitignore, a file
# that also ignores itself, so it stays local to this worktree. Do NOT use
# .git/info/exclude for this: that file is shared by every worktree and would
# hide the same untracked directories in the main checkout.
#   usage: link-main-checkout-artifacts.sh /path/to/main/checkout
set -eu
main=$(cd "$1" && pwd)
here=$(cd "$(dirname "$0")/../../.." && pwd)
ignore="$here/artifacts/current/.gitignore"
[ -e "$ignore" ] || echo "/.gitignore" > "$ignore"
hide() { grep -qxF "$1" "$ignore" || echo "$1" >> "$ignore"; }
for source in "$main"/artifacts/current/*/; do
  name=$(basename "$source")
  target="$here/artifacts/current/$name"
  if [ -L "$target" ]; then
    hide "/$name"
  elif [ ! -e "$target" ]; then
    ln -s "$source" "$target"
    hide "/$name"
    echo "linked $name"
  else
    # Directory partly carried by the branch: link only its missing entries.
    for entry in "$source"*; do
      child=$(basename "$entry")
      if [ -L "$target/$child" ]; then
        hide "/$name/$child"
      elif [ ! -e "$target/$child" ]; then
        ln -s "$entry" "$target/$child"
        hide "/$name/$child"
        echo "linked $name/$child"
      fi
    done
  fi
done
