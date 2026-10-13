#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-sidefix-ack-20261013
for ((i=0;i<1200;i++)); do
 if [ ! -d /proc/10490 ]; then break; fi
 sleep 5
done
test ! -d /proc/10490
test ! -f live/error.txt
grep -q 'Resident network tests passed' live.log
P=$PWD/project
W=/home/mit/i960-doom-batch-20261012/freedoom1.wad
python3 "$P/rtems/residentnet/verify.py" --root "$PWD" "$PWD/live" > network-replay.json
python3 "$P/rtems/residentnet/verify_upload.py" "$PWD/live" --doom-heap --doom-shared --doom-runtime --wad-poll --wad "$W" --entry "$PWD/residentnet/entry/runtime-probe.bin" --output upload-replay.json > upload-replay.log
python3 "$P/rtems/residentnet/checkpoint_replay.py" "$PWD/live" --build "$PWD/admission" --output checkpoint-comparison.json > checkpoint-replay.log
python3 "$P/rtems/residentnet/test_startup_evidence.py" "$PWD/live" --build "$PWD/admission" --wad "$W" --output startup-evidence-mutations.json > startup-evidence-tests.log
python3 "$P/rtems/residentnet/test_irq_rejection_evidence.py" "$PWD/live" --output irq-evidence-mutations.json > irq-evidence-tests.log
sudo dmesg > dmesg-final.txt
tar -czf card-evidence.tar.gz project residentnet residentnet-module live live.log kernel-build.log module.log ram-audit.json boot-id.txt dmesg-final.txt status.py i960-sidefix-ack-live.sh i960-sidefix-ack-build.sh i960-sidefix-ack-postrun.sh checkpoint-barrier-tests.log network-replay.json upload-replay.json upload-replay.log startup-evidence-mutations.json startup-evidence-tests.log irq-evidence-mutations.json irq-evidence-tests.log checkpoint-comparison.json checkpoint-replay.log
sha256sum card-evidence.tar.gz > card-evidence.sha256
printf 'REPLAYS AND ARCHIVE COMPLETE\n'
