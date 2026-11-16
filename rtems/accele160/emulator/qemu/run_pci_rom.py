#!/usr/bin/env python3
"""Boot the actual PCI option ROM on the QEMU AcceleRAID probe device."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import select
import socket
import struct
import subprocess
import tempfile
import time

ROM_OFFSET = 0x30000
ROM_SIZE = 0x7000
GUEST_ROM_BASE = 0xc0000
GUEST_ROM_WINDOW = 0x20000


def extract_rom(image: Path) -> bytes:
    flash = image.read_bytes()
    if len(flash) != 0x100000:
        raise ValueError('expected 1 MiB flash')
    rom = flash[ROM_OFFSET:ROM_OFFSET + ROM_SIZE]
    if rom[:2] != b'\x55\xaa' or rom[2] * 512 != len(rom) or sum(rom) & 255:
        raise ValueError('invalid x86 option ROM')
    return rom


def find_guest_rom(memory: bytes) -> int:
    """Find the Mylex ROM by its PCIR identity, even if init clears 0x55aa."""
    matches = []
    for offset in range(0, len(memory) - ROM_SIZE + 1, 0x800):
        pcir = struct.unpack_from('<H', memory, offset + 0x18)[0]
        header = offset + pcir
        if (pcir < ROM_SIZE - 12 and
                memory[header:header + 4] == b'PCIR' and
                struct.unpack_from('<HH', memory, header + 4) ==
                (0x1069, 0x0050)):
            matches.append(GUEST_ROM_BASE + offset)
    if len(matches) != 1:
        raise RuntimeError(f'expected one Mylex guest ROM, found {matches}')
    return matches[0]


def decode_lp_mailbox(hex_bytes: str) -> dict:
    """Decode fields shared by DAC960 V2 IOCTL command mailboxes."""
    raw = bytes.fromhex(hex_bytes)
    if len(raw) != 64:
        raise ValueError(f'expected 64 mailbox bytes, found {len(raw)}')
    return {
        'id': int.from_bytes(raw[0:2], 'little'),
        'opcode': raw[2],
        'control': raw[3],
        'transfer_bytes': int.from_bytes(raw[4:7], 'little'),
        'ioctl': raw[21],
        'sg0_dma': int.from_bytes(raw[32:40], 'little'),
        'sg0_bytes': int.from_bytes(raw[40:44], 'little'),
    }


def qmp_command(stream, command, arguments=None):
    request = {'execute': command}
    if arguments is not None:
        request['arguments'] = arguments
    stream.write(json.dumps(request).encode() + b'\n')
    stream.flush()
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError(f'QMP closed before {command}')
        reply = json.loads(line)
        if 'return' in reply:
            return reply['return']
        if 'error' in reply:
            raise RuntimeError(reply['error'])


def pci_devices(buses):
    for bus in buses:
        for device in bus.get('devices', []):
            yield device
            yield from pci_devices(device.get('pci_bridge', {}).get('buses', []))


def run_serial_login_probe(connection, seconds):
    """Collect read-only guest state through an Alpine serial login."""
    commands = [
        "printf '__ACCELE_PROBE_BEGIN__\\n'",
        'uname -a',
        'for d in /sys/bus/pci/devices/*; do [ "$(cat "$d/vendor")" = "0x1069" ] && echo "$d device=$(cat "$d/device") driver=$(readlink "$d/driver" 2>/dev/null)"; done',
        'lsmod 2>&1',
        "find /lib/modules -iname '*myrs*' 2>&1",
        "dmesg | grep -Ei 'myrs|DAC960|1069|scsi|raid' 2>&1",
        "printf '__ACCELE_PROBE_END__\\n'",
    ]
    received = bytearray()
    boot_sent = login_sent = False
    command_index = 0
    prompt_end = 0
    started = time.monotonic()
    connection.setblocking(False)
    while time.monotonic() - started < seconds:
        ready, _, _ = select.select([connection], [], [], 0.2)
        if ready:
            data = connection.recv(65536)
            if not data:
                break
            received.extend(data)
        visible = received.decode(errors='replace')
        if not boot_sent and 'boot:' in visible:
            connection.sendall(b'\r')
            boot_sent = True
        if boot_sent and not login_sent and 'localhost login:' in visible:
            connection.sendall(b'root\r')
            login_sent = True
        if login_sent and command_index < len(commands):
            prompts = list(re.finditer(r'(?:^|[\r\n])[^\r\n]*#\s*$', visible,
                                       re.MULTILINE))
            match = prompts[-1] if prompts else None
            if match and match.end() > prompt_end:
                connection.sendall((commands[command_index] + '\r').encode())
                command_index += 1
                prompt_end = len(visible)
        if '__ACCELE_PROBE_END__' in visible and command_index == len(commands):
            # The command is echoed too; wait for a fresh shell prompt.
            if re.search(r'__ACCELE_PROBE_END__[^\r\n]*[\r\n].*#\s*$',
                         visible, re.DOTALL):
                break
    return bytes(received), {
        'boot_enter_sent': boot_sent,
        'root_login_sent': login_sent,
        'commands_sent': command_index,
        'commands_total': len(commands),
        'end_marker_seen': "__ACCELE_PROBE_END__\r\n" in visible or
                           "__ACCELE_PROBE_END__\n" in visible,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--qemu', type=Path, required=True)
    parser.add_argument('--bios', type=Path,
                        help='optional experimental SeaBIOS binary')
    parser.add_argument('--seconds', type=float, default=6)
    parser.add_argument('--boot-enter-after', type=float,
                        help='send Enter to the guest after this many seconds')
    parser.add_argument('--boot-enter-on-prompt', action='store_true',
                        help='send Enter when the ISO boot prompt reaches serial')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rom-trace-output', type=Path)
    parser.add_argument('--cpu-trace-output', type=Path,
                        help='save full QEMU instruction/CPU trace (large)')
    parser.add_argument('--vga-snapshot', type=Path,
                        help='save the SeaBIOS VGA screen as a PPM image')
    parser.add_argument('--rom-memory-snapshot', type=Path,
                        help='save 128 KiB of guest memory at 0xc0000')
    parser.add_argument('--debug-port-output', type=Path,
                        help='save guest writes to SeaBIOS debug port 0x402')
    parser.add_argument('--qemu-stderr-output', type=Path,
                        help='save QEMU PCI/BAR access log')
    parser.add_argument('--aperture-file', type=Path)
    parser.add_argument('--bridge-socket', type=Path,
                        help='connect BAR and PCI commands to a running i960 model')
    parser.add_argument('--step-on-ack', action='store_true',
                        help='run 1 million i960 instructions when ROM posts ACK-status')
    parser.add_argument('--explore-rom-ioctls', action='store_true',
                        help='fabricate four ROM IOCTL completions for host-side exploration')
    parser.add_argument('--explore-live-firmware', action='store_true',
                        help='allow the prebooted i960 probe to answer the first ROM IOCTL')
    parser.add_argument('--explore-set-mbox-trace', action='store_true',
                        help='observe stock 0x8e memory-mailbox command without host completion')
    parser.add_argument('--explore-set-mbox-bridge', action='store_true',
                        help='reflect observed stock 0x8e status to LP host BAR')
    parser.add_argument('--explore-mmbox-doorbell-observe', action='store_true',
                        help='observe local IDB bit 4 and stock ring state after host MMBOX_NEW_CMD')
    parser.add_argument('--explore-mmbox-doorbell-control', action='store_true',
                        help='same bounded stock ring observation without latching local IDB bit 4')
    parser.add_argument('--explore-stock-ring-memory', action='store_true',
                        help='stage exact stock first ring slot and guest windows without completion')
    parser.add_argument('--explore-stock-ring-mirror', action='store_true',
                        help='strictly mirror observed stock first-ring reply to guest')
    parser.add_argument('--explore-stock-followup-observe', action='store_true',
                        help='stage first two later stock guest ring slots and inspect model')
    parser.add_argument('--explore-stock-followup-mirror', action='store_true',
                        help='strictly mirror stock-observed health/pdev replies to guest')
    parser.add_argument('--explore-stock-next-observe', action='store_true',
                        help='forward only observed stock ring slot 3 to the i960 model')
    parser.add_argument('--explore-stock-next-mirror', action='store_true',
                        help='strictly mirror stock-observed slot 3 reply to guest')
    parser.add_argument('--explore-stock-next-mutate-slot', action='store_true',
                        help='negative test: corrupt only the slot 3 mirror input')
    parser.add_argument('--explore-stock-next-mutate-prefill', action='store_true',
                        help='negative test: corrupt reused guest output before slot 3 mirror')
    parser.add_argument('--explore-stock-scsi-observe', action='store_true',
                        help='forward stock SCSI inquiry slot 4 without guest completion')
    parser.add_argument('--explore-native-poll', action='store_true',
                        help='allow bounded native polling firmware to answer the first five ROM IOCTLs')
    parser.add_argument('--explore-native-set-mbox', action='store_true',
                        help='reflect only observed native 0x8e status in the exploratory bridge')
    parser.add_argument('--explore-native-ring-observe', action='store_true',
                        help='stage exact first guest ring slot and observe without completion')
    parser.add_argument('--explore-native-ring-mirror', action='store_true',
                        help='strictly mirror observed native first-ring reply to guest')
    parser.add_argument('--explore-native-followup-observe', action='store_true',
                        help='stage two observed follow-up ring slots for native read-only parsing')
    parser.add_argument('--explore-native-followup-mirror', action='store_true',
                        help='strictly mirror native-observed health/pdev replies to guest')
    parser.add_argument('--explore-native-next-observe', action='store_true',
                        help='stage later native slots 3 and 4 for read-only observation')
    parser.add_argument('--explore-native-next-mirror', action='store_true',
                        help='strictly mirror native-observed repeated slot 3 info reply')
    parser.add_argument('--trace-live-reply', action='store_true',
                        help='log exact output bytes from opt-in live firmware runs')
    parser.add_argument('--boot-disk', type=Path,
                        help='optional raw IDE disk for SeaBIOS handoff testing')
    parser.add_argument('--boot-cdrom', type=Path,
                        help='optional bootable ISO for guest handoff testing')
    parser.add_argument('--kernel', type=Path,
                        help='direct Linux kernel boot for driver probe')
    parser.add_argument('--initrd', type=Path,
                        help='initramfs for direct Linux kernel boot')
    parser.add_argument('--kernel-append', default='console=ttyS0',
                        help='kernel command line for direct boot')
    parser.add_argument('--memory-mb', type=int, default=64)
    parser.add_argument('--serial-output', type=Path,
                        help='save guest serial output')
    parser.add_argument('--serial-login-probe', action='store_true',
                        help='log into Alpine as root and run read-only PCI/driver commands')
    args = parser.parse_args()
    if args.step_on_ack and not args.bridge_socket:
        parser.error('--step-on-ack requires --bridge-socket')
    if args.explore_rom_ioctls and not args.bridge_socket:
        parser.error('--explore-rom-ioctls requires --bridge-socket')
    if args.explore_live_firmware and not args.bridge_socket:
        parser.error('--explore-live-firmware requires --bridge-socket')
    if args.explore_set_mbox_trace and not args.explore_live_firmware:
        parser.error('--explore-set-mbox-trace requires --explore-live-firmware')
    if args.explore_set_mbox_bridge and not args.explore_live_firmware:
        parser.error('--explore-set-mbox-bridge requires --explore-live-firmware')
    if args.explore_mmbox_doorbell_observe and not args.explore_set_mbox_bridge:
        parser.error('--explore-mmbox-doorbell-observe requires --explore-set-mbox-bridge')
    if args.explore_mmbox_doorbell_control and not args.explore_set_mbox_bridge:
        parser.error('--explore-mmbox-doorbell-control requires --explore-set-mbox-bridge')
    if args.explore_mmbox_doorbell_control and args.explore_mmbox_doorbell_observe:
        parser.error('choose one memory-mailbox doorbell observation mode')
    if args.explore_stock_ring_memory and not args.explore_mmbox_doorbell_observe:
        parser.error('--explore-stock-ring-memory requires --explore-mmbox-doorbell-observe')
    if args.explore_stock_ring_mirror and not args.explore_stock_ring_memory:
        parser.error('--explore-stock-ring-mirror requires --explore-stock-ring-memory')
    if args.explore_stock_followup_observe and not args.explore_stock_ring_mirror:
        parser.error('--explore-stock-followup-observe requires --explore-stock-ring-mirror')
    if args.explore_stock_followup_mirror and not args.explore_stock_followup_observe:
        parser.error('--explore-stock-followup-mirror requires --explore-stock-followup-observe')
    if args.explore_stock_next_observe and not args.explore_stock_followup_mirror:
        parser.error('--explore-stock-next-observe requires --explore-stock-followup-mirror')
    if args.explore_stock_next_mirror and not args.explore_stock_next_observe:
        parser.error('--explore-stock-next-mirror requires --explore-stock-next-observe')
    if args.explore_stock_next_mutate_slot and not args.explore_stock_next_mirror:
        parser.error('--explore-stock-next-mutate-slot requires --explore-stock-next-mirror')
    if args.explore_stock_next_mutate_prefill and not args.explore_stock_next_mirror:
        parser.error('--explore-stock-next-mutate-prefill requires --explore-stock-next-mirror')
    if args.explore_stock_scsi_observe and not args.explore_stock_next_mirror:
        parser.error('--explore-stock-scsi-observe requires --explore-stock-next-mirror')
    if args.explore_set_mbox_trace and args.explore_set_mbox_bridge:
        parser.error('choose set-mbox trace or bridge mode')
    if args.explore_native_set_mbox and not args.explore_native_poll:
        parser.error('--explore-native-set-mbox requires --explore-native-poll')
    if args.explore_native_ring_observe and not args.explore_native_set_mbox:
        parser.error('--explore-native-ring-observe requires --explore-native-set-mbox')
    if args.explore_native_ring_mirror and not args.explore_native_ring_observe:
        parser.error('--explore-native-ring-mirror requires --explore-native-ring-observe')
    if args.explore_native_followup_observe and not args.explore_native_ring_mirror:
        parser.error('--explore-native-followup-observe requires --explore-native-ring-mirror')
    if args.explore_native_followup_mirror and not args.explore_native_followup_observe:
        parser.error('--explore-native-followup-mirror requires --explore-native-followup-observe')
    if args.explore_native_next_observe and not args.explore_native_followup_mirror:
        parser.error('--explore-native-next-observe requires --explore-native-followup-mirror')
    if args.explore_native_next_mirror and not args.explore_native_next_observe:
        parser.error('--explore-native-next-mirror requires --explore-native-next-observe')
    if sum((args.explore_live_firmware, args.explore_native_poll,
            args.explore_rom_ioctls)) > 1:
        parser.error('choose one ROM IOCTL exploration mode')
    if args.trace_live_reply and not (args.explore_live_firmware or args.explore_native_poll):
        parser.error('--trace-live-reply requires a live firmware mode')
    if sum((bool(args.boot_disk), bool(args.boot_cdrom), bool(args.kernel))) > 1:
        parser.error('choose one boot source')
    if args.initrd and not args.kernel:
        parser.error('--initrd requires --kernel')
    if args.memory_mb < 64:
        parser.error('--memory-mb must be at least 64')
    if args.boot_enter_after is not None and not 0 <= args.boot_enter_after < args.seconds:
        parser.error('--boot-enter-after must be within the QEMU run')
    if args.boot_enter_on_prompt and (args.boot_enter_after is not None or not args.serial_output):
        parser.error('--boot-enter-on-prompt needs serial output and no fixed key time')
    if args.serial_login_probe and (not args.serial_output or not args.boot_cdrom or
                                    args.boot_enter_after is not None):
        parser.error('--serial-login-probe needs serial output and boot CD-ROM')
    rom = extract_rom(args.image)
    aperture = args.aperture_file.read_bytes() if args.aperture_file else None
    if aperture is not None and len(aperture) != 8192:
        raise ValueError('aperture seed must be 8192 bytes')
    with tempfile.TemporaryDirectory(prefix='accele160-pci-rom-') as tmp:
        base = Path(tmp)
        rom_file = base / 'option.rom'
        trace_file = args.cpu_trace_output or base / 'instructions.log'
        stderr_file = args.qemu_stderr_output or base / 'qemu-stderr.log'
        debug_file = args.debug_port_output or base / 'debug-port.log'
        rom_memory_file = args.rom_memory_snapshot or base / 'rom-memory.bin'
        qmp_file = base / 'qmp.sock'
        serial_file = base / 'serial.sock'
        rom_file.write_bytes(rom)
        device = f'accele160-probe,addr=05.1,romfile={rom_file}'
        if args.aperture_file:
            device += f',aperture-file={args.aperture_file.resolve()}'
        if args.bridge_socket:
            device += f',bridge-socket={args.bridge_socket.resolve()}'
        if args.step_on_ack:
            device += ',step-on-ack=on'
        if args.explore_rom_ioctls:
            device += ',explore-rom-ioctls=on'
        if args.explore_live_firmware:
            device += ',explore-live-firmware=on'
        if args.explore_set_mbox_trace:
            device += ',explore-set-mbox-trace=on'
        if args.explore_set_mbox_bridge:
            device += ',explore-set-mbox-bridge=on'
        if args.explore_mmbox_doorbell_observe:
            device += ',explore-mmbox-doorbell-observe=on'
        if args.explore_mmbox_doorbell_control:
            device += ',explore-mmbox-doorbell-control=on'
        if args.explore_stock_ring_memory:
            device += ',explore-stock-ring-memory=on'
        if args.explore_stock_ring_mirror:
            device += ',explore-stock-ring-mirror=on'
        if args.explore_stock_followup_observe:
            device += ',explore-stock-followup-observe=on'
        if args.explore_stock_followup_mirror:
            device += ',explore-stock-followup-mirror=on'
        if args.explore_stock_next_observe:
            device += ',explore-stock-next-observe=on'
        if args.explore_stock_next_mirror:
            device += ',explore-stock-next-mirror=on'
        if args.explore_stock_next_mutate_slot:
            device += ',explore-stock-next-mutate-slot=on'
        if args.explore_stock_next_mutate_prefill:
            device += ',explore-stock-next-mutate-prefill=on'
        if args.explore_stock_scsi_observe:
            device += ',explore-stock-scsi-observe=on'
        if args.explore_native_poll:
            device += ',explore-native-poll=on'
        if args.explore_native_set_mbox:
            device += ',explore-native-set-mbox=on'
        if args.explore_native_ring_observe:
            device += ',explore-native-ring-observe=on'
        if args.explore_native_ring_mirror:
            device += ',explore-native-ring-mirror=on'
        if args.explore_native_followup_observe:
            device += ',explore-native-followup-observe=on'
        if args.explore_native_followup_mirror:
            device += ',explore-native-followup-mirror=on'
        if args.explore_native_next_observe:
            device += ',explore-native-next-observe=on'
        if args.explore_native_next_mirror:
            device += ',explore-native-next-mirror=on'
        if args.trace_live_reply:
            device += ',trace-live-reply=on'
        command = [str(args.qemu.resolve()), '-machine', 'pc,accel=tcg',
                   '-m', str(args.memory_mb), '-display', 'none',
                   '-serial', (f'unix:{serial_file},server=on,wait=off'
                               if args.serial_login_probe else
                               f'file:{args.serial_output.resolve()}'
                               if args.serial_output else 'none'),
                   '-monitor', 'none', '-no-reboot', '-S',
                   '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
                   '-device', device,
                   '-chardev', f'file,id=romdebug,path={debug_file.resolve()}',
                   '-device', 'isa-debugcon,iobase=0x402,chardev=romdebug',
                   '-qmp', f'unix:{qmp_file},server=on,wait=off',
                   '-d', 'in_asm,cpu,guest_errors' if args.cpu_trace_output
                   else 'in_asm,guest_errors', '-D', str(trace_file)]
        if args.bios:
            command += ['-bios', str(args.bios.resolve())]
        if args.boot_disk:
            command += ['-boot', 'order=c', '-drive',
                        f'file={args.boot_disk.resolve()},format=raw,if=ide']
        if args.boot_cdrom:
            command += ['-boot', 'order=d', '-drive',
                        f'file={args.boot_cdrom.resolve()},format=raw,if=ide,media=cdrom']
        if args.kernel:
            command += ['-kernel', str(args.kernel.resolve()),
                        '-append', args.kernel_append]
            if args.initrd:
                command += ['-initrd', str(args.initrd.resolve())]
        stderr_stream = stderr_file.open('w')
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL,
                                   stderr=stderr_stream, text=True)
        serial_probe = None
        try:
            deadline = time.monotonic() + 15
            while not qmp_file.exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('QEMU did not start its QMP socket')
                time.sleep(0.05)
            with socket.socket(socket.AF_UNIX) as conn:
                conn.settimeout(max(15, args.seconds + 5))
                conn.connect(str(qmp_file))
                with conn.makefile('rwb') as stream:
                    greeting = json.loads(stream.readline())
                    if 'QMP' not in greeting:
                        raise RuntimeError('missing QMP greeting')
                    qmp_command(stream, 'qmp_capabilities')
                    devices = list(pci_devices(qmp_command(stream, 'query-pci')))
                    identity = [d for d in devices
                                if d.get('id', {}).get('vendor') == 0x1069
                                and d.get('id', {}).get('device') == 0x0050]
                    if len(identity) != 1:
                        raise RuntimeError('AcceleRAID PCI identity missing')
                    qmp_command(stream, 'cont')
                    if args.serial_login_probe:
                        with socket.socket(socket.AF_UNIX) as serial_conn:
                            serial_conn.connect(str(serial_file))
                            serial_bytes, serial_probe = run_serial_login_probe(
                                serial_conn, args.seconds)
                        args.serial_output.write_bytes(serial_bytes)
                    elif args.boot_enter_on_prompt:
                        started = time.monotonic()
                        sent = False
                        while time.monotonic() - started < args.seconds:
                            if (not sent and args.serial_output.exists() and
                                    'boot:' in args.serial_output.read_text(errors='replace')):
                                qmp_command(stream, 'human-monitor-command',
                                            {'command-line': 'sendkey ret'})
                                sent = True
                            time.sleep(0.2)
                    elif args.boot_enter_after is not None:
                        time.sleep(args.boot_enter_after)
                        qmp_command(stream, 'human-monitor-command',
                                    {'command-line': 'sendkey ret'})
                        time.sleep(args.seconds - args.boot_enter_after)
                    else:
                        time.sleep(args.seconds)
                    qmp_command(stream, 'stop')
                    if args.vga_snapshot:
                        qmp_command(stream, 'screendump',
                                    {'filename': str(args.vga_snapshot.resolve())})
                    qmp_command(stream, 'pmemsave',
                                {'val': GUEST_ROM_BASE,
                                 'size': GUEST_ROM_WINDOW,
                                 'filename': str(rom_memory_file.resolve())})
            process.terminate()
            process.communicate(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
            stderr_stream.close()
        stderr = stderr_file.read_text(errors='replace')
        trace = trace_file.read_text(errors='replace') if trace_file.exists() else ''
        guest_rom_base = find_guest_rom(rom_memory_file.read_bytes())
        entry = bool(re.search(rf'0x0*{guest_rom_base + 3:x}:\s', trace,
                               re.IGNORECASE))
        rom_blocks = [block.strip() for block in trace.split('IN:')
                      if any(guest_rom_base <= int(address, 16) <
                             guest_rom_base + ROM_SIZE
                             for address in re.findall(r'0x([0-9a-f]+):\s',
                                                       block, re.IGNORECASE))]
        if args.rom_trace_output:
            args.rom_trace_output.write_text('\n\n'.join(rom_blocks) + '\n')
        accesses = [line for line in stderr.splitlines()
                    if line.startswith(('accele160 bar0 R ',
                                        'accele160 bar0 W '))]
        mailbox_submissions = [line for line in stderr.splitlines()
                               if line.startswith('accele160 lp mailbox submitted ')]
        mailbox_bytes = [line.partition('bytes=')[2] for line in stderr.splitlines()
                         if line.startswith('accele160 lp mailbox bytes=')]
        config_accesses = [line for line in stderr.splitlines()
                           if line.startswith('accele160 config ')]
        extended_config = [line for line in config_accesses
                           if int(re.search(r'offset=0x([0-9a-f]+)', line).group(1), 16) >= 0x40]
        result = {
            'image_sha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
            'option_rom_sha256': hashlib.sha256(rom).hexdigest(),
            'option_rom_guest_base': f'0x{guest_rom_base:05x}',
            'aperture_sha256': hashlib.sha256(aperture).hexdigest() if aperture is not None else None,
            'pci_identity': '1069:0050',
            'pci_revision': '02',
            'option_rom_entry_executed': entry,
            'bar_access_count_logged': len(accesses),
            'first_bar_accesses': accesses[:32],
            'bar_trace_limited': 'accele160 bar0 trace-limit=' in stderr,
            'mailbox_submissions': mailbox_submissions[:8],
            'mailbox_bytes_hex': mailbox_bytes[:8],
            'mailbox_requests': [decode_lp_mailbox(value)
                                 for value in mailbox_bytes[:8]],
            'config_access_count_logged': len(config_accesses),
            'first_config_accesses': config_accesses[:32],
            'extended_config_accesses': extended_config[:64],
            'rom_block_count': len(rom_blocks),
            'rom_blocks_sha256': hashlib.sha256('\n'.join(rom_blocks).encode()).hexdigest(),
            'debug_port_bytes': debug_file.stat().st_size if debug_file.exists() else 0,
            'debug_port_text': debug_file.read_text(errors='replace')[-512:]
            if debug_file.exists() else '',
            'serial_tail': args.serial_output.read_text(errors='replace')[-1024:]
            if args.serial_output and args.serial_output.exists() else '',
            'serial_probe': serial_probe,
            'synthetic_ctlr_info_completed':
                'accele160 EXPLORE synthetic IOCTL completion ioctl=0x01' in stderr,
            'stock_ctlr_info_completed':
                'accele160 EXPLORE stock firmware completion ioctl=0x01 id=127 status=0x0000' in stderr,
            'native_ctlr_info_completed':
                'accele160 EXPLORE native firmware completion ioctl=0x01 id=127 status=0x0000' in stderr,
            'stock_completion_lines': [line for line in stderr.splitlines()
                                       if line.startswith('accele160 EXPLORE stock firmware completion ')],
            'first_rom_blocks': rom_blocks[:16],
            'last_rom_blocks': rom_blocks[-8:],
            'stderr_tail': stderr.splitlines()[-8:],
        }
        if args.output:
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        if not entry:
            raise RuntimeError('PCI option ROM entry not executed')


if __name__ == '__main__':
    main()
