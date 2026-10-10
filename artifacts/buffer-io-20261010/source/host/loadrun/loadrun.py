#!/usr/bin/env python3
"""Load one cooperative i960 function on the validated DAC960PG profile."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import buffer_io as bio

ROM_SHA = 'a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'

def uint(text):
    value = int(text, 0)
    if not 0 <= value <= 0xffffffff:
        raise argparse.ArgumentTypeError('expected unsigned 32-bit integer')
    return value

def validate_payload(data, entry):
    if not data or len(data) > 65536 or len(data) % 4 or entry % 4 or not 0 <= entry < len(data):
        raise ValueError('payload must be 4-byte aligned, 4..65536 bytes, with an aligned entry inside it')

def clean(log):
    return (re.search(r'^experiment-result=-?\d+ pending=0;', log, re.M) is not None
            and all(re.search(r'^'+name+r'-dirty=0$', log, re.M) for name in ('scratch','exec','stage'))
            and not re.search(r'pending=[1-9]|dirty=[1-9]', log))

def verify(folder, payload):
    log = (folder/'result.txt').read_text()
    if not clean(log) or 'experiment-result=0 pending=0;' not in log:
        raise ValueError('transaction failed or RAM/DMA state remains uncertain; inspect result.txt')
    if 'RESTORED firmware image, PING dispatch, code and result RAM; stock health verified' not in log:
        raise ValueError('missing restoration evidence')
    before = (folder/'stage-before-a5.bin').read_bytes()
    if len(before) != 524288 or hashlib.sha256(before).hexdigest() != ROM_SHA:
        raise ValueError('wrong installed firmware image')
    expected = payload + before[len(payload):]
    for phase, data in [('before', before), ('candidate', expected), ('restored', before)]:
        for pattern in ('a5','5a'):
            if (folder/f'stage-{phase}-{pattern}.bin').read_bytes() != data:
                raise ValueError('staging capture mismatch: '+phase)
    result = (folder/'dram-hook-a5.bin').read_bytes()
    if len(result) != 16 or result != (folder/'dram-hook-5a.bin').read_bytes():
        raise ValueError('result capture mismatch')
    value, marker = struct.unpack_from('<II', result)
    if marker != 0x52554e31 or f'PAYLOAD RETURN value={value:08x} decimal={value} marker=52554e31' not in log:
        raise ValueError('missing payload completion marker')
    if len(payload)==bio.IMAGE_SIZE and struct.unpack_from('<I',payload,bio.OFFSET)[0]==bio.MAGIC:
        after=(folder/'payload-after-a5.bin').read_bytes()
        if after != (folder/'payload-after-5a.bin').read_bytes():
            raise ValueError('paired output captures disagree')
        status,output=bio.response(expected,after)
        if f'VERIFIED buffer response sequence={struct.unpack_from("<I",payload,bio.OFFSET+8)[0]} status={status} bytes={len(output)};' not in log:
            raise ValueError('missing kernel output validation')
    return value

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('payload', type=Path)
    ap.add_argument('--module', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path, help='new capture directory')
    ap.add_argument('--argument', type=uint, default=0)
    ap.add_argument('--entry', type=uint, default=0, help='entry offset in linked raw binary')
    ap.add_argument('--expect', type=uint)
    ap.add_argument('--buffer-io', action='store_true', help='use BIO1 request/response ABI')
    ap.add_argument('--input', type=Path, help='BIO1 input bytes, at most 4096')
    ap.add_argument('--capacity', type=uint, default=bio.OUTPUT_MAX)
    ap.add_argument('--sequence', type=uint, default=1)
    ap.add_argument('--framebuffer', action='store_true', help='save 24x80 printable response as frame.txt')
    args = ap.parse_args()
    data = args.payload.read_bytes()
    if args.buffer_io:
        if args.argument: raise ValueError('--argument is reserved for the BIO1 pointer in buffer mode')
        data=bio.prepare(data,args.input.read_bytes() if args.input else b'',args.capacity,args.sequence,args.entry)
        args.argument=bio.BASE
    elif args.input or args.framebuffer:
        raise ValueError('--input and --framebuffer require --buffer-io')
    validate_payload(data, args.entry)
    module = args.module.resolve(strict=True)
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise ValueError('run as root on the Linux host containing the card')
    import fcntl
    with open('/run/lock/i960-loadrun.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ('dac960loadrun','dac960dump','dac960program'):
            if Path('/sys/module', name).exists():
                raise ValueError('probe already loaded: '+name)
        if Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists():
            raise ValueError('card already has a driver; refusing to unbind it')
        args.output.mkdir(parents=True, exist_ok=False)
        digest = hashlib.sha256(data).hexdigest()
        firmware = Path('/lib/firmware/i960')/('runtime-'+digest+'.bin')
        firmware.parent.mkdir(parents=True, exist_ok=True)
        if firmware.exists():
            if firmware.read_bytes() != data: raise ValueError('firmware cache mismatch')
        else:
            with firmware.open('xb') as f: f.write(data)
        (args.output/'payload.bin').write_bytes(data)
        meta = dict(payload_sha256=digest, argument=args.argument, entry=args.entry, buffer_io=args.buffer_io,
                    module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
                    boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        (args.output/'request.json').write_text(json.dumps(meta, indent=2)+'\n')
        proc = subprocess.run(['insmod', str(module), 'pointer_check=1', 'runtime_check=1', 'stage_check=1',
                               'firmware_name=i960/'+firmware.name,
                               'payload_argument='+str(args.argument), 'entry_offset='+str(args.entry),
                               'buffer_io='+str(int(args.buffer_io))],
                              capture_output=True, text=True)
        (args.output/'insmod.txt').write_text(proc.stdout+proc.stderr)
        debug = Path('/sys/kernel/debug/dac960loadrun')
        # Copy before any unload: debugfs reports zero sizes, so read to EOF.
        if debug.exists():
            for path in sorted(debug.iterdir()):
                if path.is_file(): (args.output/path.name).write_bytes(path.read_bytes())
        logpath = args.output/'result.txt'
        if not logpath.exists() or not clean(logpath.read_text()):
            raise ValueError('no clean completion record; module retained if loaded, do not retry or force unload')
        subprocess.run(['rmmod','dac960loadrun'], check=True)
        (args.output/'unloaded.txt').write_text('clean module unload completed\n')
        if proc.returncode: raise ValueError('insmod failed; inspect insmod.txt')
        value = verify(args.output, data)
        if args.buffer_io:
            before=(args.output/'stage-candidate-a5.bin').read_bytes()
            after=(args.output/'payload-after-a5.bin').read_bytes()
            status,output=bio.response(before,after)
            (args.output/'response.bin').write_bytes(output)
            (args.output/'response.json').write_text(json.dumps(dict(status=status,length=len(output),sequence=args.sequence),indent=2)+'\n')
            if status: raise ValueError(f'payload reported BIO1 status {status}; RAM restored and module unloaded')
            if args.framebuffer:
                if len(output)!=1920 or any(c<32 or c>126 for c in output):
                    raise ValueError('framebuffer must contain exactly 24x80 printable ASCII cells')
                (args.output/'frame.txt').write_text(''.join(output[i:i+80].decode('ascii')+'\n' for i in range(0,1920,80)))
            print(f'Captured {len(output)} response bytes in {args.output / "response.bin"}')
        if args.expect is not None and value != args.expect:
            raise ValueError(f'payload returned {value}, expected {args.expect}; RAM restored and module unloaded')
        print(f'Payload returned {value} (0x{value:08x}); RAM restored, module unloaded. Captures: {args.output}')

if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
