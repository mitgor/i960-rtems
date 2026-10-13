#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-visible-20261013
for ((i=0;i<1200;i++)); do
 if [ ! -d /proc/59894 ]; then break; fi
 sleep 5
done
test ! -d /proc/59894
test ! -f live/error.txt
grep -q 'Resident network tests passed' live.log
P=$PWD/project
W=/home/mit/i960-doom-batch-20261012/freedoom1.wad
python3 "$P/rtems/residentnet/verify.py" --root "$PWD" "$PWD/live" > network-replay.json
python3 "$P/rtems/residentnet/verify_upload.py" "$PWD/live" --doom-heap --doom-shared --doom-runtime --wad-poll --wad "$W" --entry "$PWD/residentnet/entry/runtime-probe.bin" --output upload-replay.json > upload-replay.log
python3 "$P/rtems/residentnet/checkpoint_replay.py" "$PWD/live" --build "$PWD/admission" --output checkpoint-comparison.json > checkpoint-replay.log
python3 "$P/rtems/residentnet/test_startup_evidence.py" "$PWD/live" --build "$PWD/admission" --wad "$W" --output startup-evidence-mutations.json > startup-evidence-tests.log
python3 "$P/rtems/residentnet/test_frame_evidence.py" "$PWD/admission" --capture "$PWD/live" --output frame-evidence-card-mutations.json > frame-evidence-card-tests.log
sudo dmesg > dmesg-final.txt
printf 'REPLAYS COMPLETE\n'
