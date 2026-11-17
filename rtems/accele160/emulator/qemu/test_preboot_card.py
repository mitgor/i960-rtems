#!/usr/bin/env python3
"""Bring stock i960 firmware to MU readiness before a QEMU option-ROM run.

All ISP responses and interrupt entries here are explicit offline probes.
"""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--qemu', type=Path)
    parser.add_argument('--boot-cdrom', type=Path)
    parser.add_argument('--kernel', type=Path)
    parser.add_argument('--initrd', type=Path)
    parser.add_argument('--kernel-append', default='console=ttyS0')
    parser.add_argument('--seconds', type=float, default=5)
    parser.add_argument('--boot-enter-after', type=float)
    parser.add_argument('--boot-enter-on-prompt', action='store_true')
    parser.add_argument('--expect-linux-login', action='store_true',
                        help='require five stock ROM replies and an Alpine login')
    parser.add_argument('--require-natural-priority', action='store_true',
                        help='reject any probe that bypasses the i960 CPU priority gate')
    parser.add_argument('--require-routed-mu', action='store_true',
                        help='require five MU interrupts from inbound status through XINT7')
    parser.add_argument('--probe-isp-pins', action='store_true',
                        help='probe routed pins on the first synthetic ISP response')
    parser.add_argument('--probe-isp-pirsr-bit0', action='store_true',
                        help='offline counterfactual: enable PIRSR bit 0 after stock setup')
    parser.add_argument('--route-isp-pirsr-bit0', action='store_true',
                        help='offline counterfactual: route all ISP responses through XINT0')
    parser.add_argument('--model-isp-no-device-queue', action='store_true',
                        help='ask the guarded queue model to post 15 INCOMPLETE responses')
    parser.add_argument('--auto-isp-no-device-queue', action='store_true',
                        help='let the opt-in queue model post and route during stepping')
    parser.add_argument('--probe-isp-queue-guard', action='store_true',
                        help='verify an unknown CDB is rejected before queue posting')
    parser.add_argument('--probe-isp-polling', action='store_true',
                        help='post guarded responses, then step without ISP interrupt')
    parser.add_argument('--dump-interrupt-page', type=Path,
                        help='export the installed c0053000 interrupt handler page')
    parser.add_argument('--dump-vector-page', type=Path,
                        help='export the installed c0000000 vector page')
    parser.add_argument('--dump-router-page', type=Path,
                        help='export the installed c0050000 interrupt router page')
    parser.add_argument('--memory-mb', type=int, default=64)
    parser.add_argument('--serial-output', type=Path)
    parser.add_argument('--vga-snapshot', type=Path)
    parser.add_argument('--rom-output', type=Path)
    parser.add_argument('--explore-live-firmware', action='store_true')
    parser.add_argument('--explore-set-mbox-trace', action='store_true')
    parser.add_argument('--explore-set-mbox-bridge', action='store_true')
    parser.add_argument('--explore-mmbox-doorbell-observe', action='store_true')
    parser.add_argument('--explore-mmbox-doorbell-control', action='store_true')
    parser.add_argument('--explore-stock-ring-memory', action='store_true')
    parser.add_argument('--explore-stock-ring-mirror', action='store_true')
    parser.add_argument('--explore-stock-followup-observe', action='store_true')
    parser.add_argument('--explore-stock-followup-mirror', action='store_true')
    parser.add_argument('--explore-stock-next-observe', action='store_true')
    parser.add_argument('--explore-stock-next-mirror', action='store_true')
    parser.add_argument('--explore-stock-next-mutate-slot', action='store_true')
    parser.add_argument('--explore-stock-next-mutate-prefill', action='store_true')
    parser.add_argument('--explore-stock-scsi-observe', action='store_true')
    parser.add_argument('--trace-live-reply', action='store_true')
    parser.add_argument('--trace-priority', action='store_true')
    parser.add_argument('--bios', type=Path)
    parser.add_argument('--emulator-output', type=Path)
    parser.add_argument('--qemu-stderr-output', type=Path)
    args = parser.parse_args()
    if args.kernel and args.boot_cdrom:
        parser.error('choose either --kernel or --boot-cdrom')
    if args.initrd and not args.kernel:
        parser.error('--initrd requires --kernel')
    if args.explore_mmbox_doorbell_observe and not args.explore_set_mbox_bridge:
        parser.error('--explore-mmbox-doorbell-observe requires --explore-set-mbox-bridge')
    if args.explore_mmbox_doorbell_control and not args.explore_set_mbox_bridge:
        parser.error('--explore-mmbox-doorbell-control requires --explore-set-mbox-bridge')
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
    if args.explore_mmbox_doorbell_control and args.explore_mmbox_doorbell_observe:
        parser.error('choose one memory-mailbox doorbell observation mode')
    if args.probe_isp_pirsr_bit0 and args.route_isp_pirsr_bit0:
        parser.error('choose one PIRSR counterfactual mode')
    if args.model_isp_no_device_queue and not (args.route_isp_pirsr_bit0 or
                                               args.probe_isp_polling):
        parser.error('the queue model run requires --route-isp-pirsr-bit0')
    if args.auto_isp_no_device_queue and not (args.route_isp_pirsr_bit0 or
                                              args.probe_isp_polling):
        parser.error('the automatic queue run requires --route-isp-pirsr-bit0')
    if args.auto_isp_no_device_queue and args.model_isp_no_device_queue:
        parser.error('choose one queue model trigger')
    if args.probe_isp_queue_guard and not args.model_isp_no_device_queue:
        parser.error('--probe-isp-queue-guard requires the queue model')
    if args.probe_isp_polling and not (args.model_isp_no_device_queue or
                                       args.auto_isp_no_device_queue):
        parser.error('--probe-isp-polling requires a queue model')
    if args.probe_isp_polling and args.route_isp_pirsr_bit0:
        parser.error('--probe-isp-polling uses stock PIRSR routing')
    with tempfile.TemporaryDirectory(prefix='accele160-preboot-') as directory:
        bridge = Path(directory) / 'bridge.sock'
        emu_log = Path(directory) / 'emulator.log'
        emulator = [str(args.emulator.resolve()), str(args.image.resolve()),
                    '60000000', '--board-id=11', '--quiet-trace',
                    f'--bridge-socket={bridge}', '--explore-timer-interrupt',
                    '--explore-qlogic-pci', '--explore-isp-mailbox',
                    '--explore-isp-execute-ack', '--explore-isp-about-ack',
                    '--explore-isp-queue-ack', '--explore-isp-retry-ack',
                    '--explore-isp-reset-delay-ack',
                    '--explore-isp-active-negation-ack',
                    '--explore-isp-feature-ack', '--explore-isp-status-zero',
                    '--explore-isp-init-id-ack', '--explore-isp-bus-reset-ack',
                    '--explore-isp-target0-ack', '--explore-isp-target-sweep']
        if args.trace_priority or args.require_natural_priority:
            emulator += ['--trace-priority']
        if args.auto_isp_no_device_queue:
            emulator += ['--explore-isp-no-device-auto']
        with emu_log.open('w') as output:
            process = subprocess.Popen(emulator, stdout=output,
                                       stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 30
            while not bridge.exists():
                if process.poll() is not None:
                    raise RuntimeError('i960 emulator exited before bridge readiness')
                if time.monotonic() > deadline:
                    raise TimeoutError('i960 bridge did not become ready')
                time.sleep(0.05)
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(bridge))
                stream = connection.makefile('rwb', buffering=0)

                def request(command):
                    stream.write((command + '\n').encode('ascii'))
                    response = stream.readline().strip()
                    if not response or response == b'ERR':
                        raise AssertionError(f'{command}: {response!r}')
                    return int(response, 16)

                def step(count):
                    for _ in range(count):
                        request('S 1000000')

                # Stage the PCI command state and the ROM's initial LP
                # ACK-status event before any stock startup instructions.
                assert request('H 1004 107') == 0x107
                assert request('H 1204 107') == 0x107
                request('D 2')
                step(450)
                for base, destination in ((0xc0053000, args.dump_interrupt_page),
                                          (0xc0000000, args.dump_vector_page),
                                          (0xc0050000, args.dump_router_page)):
                    if destination is None:
                        continue
                    if destination.exists():
                        raise FileExistsError(destination)
                    page = bytearray()
                    for offset in range(0, 4096, 4):
                        value = request(f'R {base + offset:08x} 4 0')
                        page.extend(value.to_bytes(4, 'little'))
                    destination.write_bytes(page)
                request_index = request('R 8bf00078 2 0')
                assert request_index >= 30, request_index
                channel = request('R c0384b68 4 0')
                pending = channel & request('I ff008504')
                assert pending and pending & (pending - 1) == 0
                if args.route_isp_pirsr_bit0:
                    assert request('I 1050') == 0x0e
                    assert request('C 1050 f') == 0x0f
                for index in range(15):
                    if args.auto_isp_no_device_queue:
                        assert index == 0
                        request('S 1000000')
                        if args.probe_isp_polling:
                            assert request('I 1050') == 0x0e
                            step(400)
                            producer = request('R 8bf0007a 2 0')
                            consumer = request('R c0600d52 2 0')
                            isr = request('R 8bf0000c 2 0')
                            mu_mask = request('I 1328')
                            assert (producer, consumer, isr, mu_mask) == (
                                15, 0, 1, 0xffffffff)
                            print('isp_auto_stock_route=PASS '
                                  f'producer={producer:04x} '
                                  f'consumer={consumer:04x} '
                                  f'isr={isr:04x} '
                                  f'mu_mask={mu_mask:08x}')
                            return
                        assert request('R c0600d52 2 0') == 15
                        break
                    if args.model_isp_no_device_queue:
                        assert index == 0
                        if args.probe_isp_queue_guard:
                            cdb = 0xc0600df0 + 64 + 20
                            assert request(f'R {cdb:08x} 1 0') == 0x12
                            request(f'W {cdb:08x} 1 0')
                            assert request('N') == 0
                            assert request('R 8bf0007a 2 0') == 0
                            print('isp_queue_guard=PASS unknown_cdb=REJECTED '
                                  'response_producer=0000')
                            request(f'W {cdb:08x} 1 12')
                        assert request('N') == 15
                        if args.probe_isp_polling:
                            assert request('I 1050') == 0x0e
                            step(400)
                            producer = request('R 8bf0007a 2 0')
                            consumer = request('R c0600d52 2 0')
                            isr = request('R 8bf0000c 2 0')
                            mu_mask = request('I 1328')
                            assert (producer, consumer, isr, mu_mask) == (
                                15, 0, 1, 0xffffffff)
                            print('isp_polling_probe=PASS '
                                  f'producer={producer:04x} '
                                  f'consumer={consumer:04x} '
                                  f'isr={isr:04x} '
                                  f'mu_mask={mu_mask:08x}')
                            return
                        assert request('E 0') == 0xc0000400
                        request('S 1000000')
                        assert request('R c0600d52 2 0') == 15
                        break
                    for _ in range(100):
                        if request('P') & 0x100:
                            break
                        request('S 1000')
                    else:
                        raise AssertionError('ISP vector stayed disabled')
                    command = 0xc0600df0 + (2 * index + 1) * 64
                    assert request(f'R {command:08x} 1 0') == 9
                    handle = request(f'R {command + 4:08x} 4 0')
                    response = 0xc0604df0 + index * 64
                    for word in range(16):
                        request(f'W {response + word * 4:08x} 4 0')
                    request(f'W {response:08x} 4 103')
                    request(f'W {response + 4:08x} 4 {handle:x}')
                    request(f'W {response + 8:08x} 4 10000')
                    request(f'W 8bf0007a 2 {index + 1:x}')
                    request('W 8bf00070 2 8020')
                    request('W 8bf0000c 2 1')
                    request('W 8bf0000a 2 4')
                    if args.probe_isp_pirsr_bit0:
                        assert index == 0
                        original = request('I 1050')
                        assert original == 0x0e, original
                        assert request('E 0') == 0
                        assert request('R c0600d52 2 0') == 0
                        assert request('C 1050 f') == 0x0f
                        handler = request('E 0')
                        assert handler == 0xc0000400, handler
                        request('S 1000000')
                        consumer = request('R c0600d52 2 0')
                        assert consumer == 1, consumer
                        print(f'isp_pirsr_bit0=PASS original={original:08x} '
                              f'override={request("I 1050"):08x} '
                              f'handler={handler:08x} consumer={consumer:04x}')
                        return
                    if args.probe_isp_pins:
                        print(f'pirsr={request("I 1050"):08x} '
                              f'imsk={request("I ff008504"):08x} '
                              f'channel_mask={request("R c0384b68 4 0"):08x}')
                        assert request('R c0384b68 4 0') == 1
                        assert request('I 1050') == 0x0e
                        for pin in (2, 1, 3, 0):
                            handler = request(f'E {pin:x}')
                            active = (request('I ff008500') &
                                      request('I ff008504') &
                                      request('R c0384b68 4 0'))
                            request('S 1000000')
                            consumer = request('R c0600d52 2 0')
                            print(f'isp_pin={pin} handler={handler:08x} '
                                  f'active_channel={active:08x} '
                                  f'consumer={consumer:04x} '
                                  f'isr={request("R 8bf0000c 2 0"):04x}')
                            assert handler == 0 and consumer == 0
                        print('isp_unasserted_pins=PASS routed_vectors=0')
                        return
                    if args.route_isp_pirsr_bit0:
                        assert request('E 0') == 0xc0000400
                    else:
                        request(f'C ff008500 {pending:x}')
                        assert request('J 42') == 0xc0000400
                    request('S 1000000')
                    assert request('R c0600d52 2 0') == index + 1
                step(400)
                mask = request('I 1328')
                assert mask & 4 == 0, f'MU masked: {mask:08x}'
                print(f'preboot=PASS request_index={request_index:04x} '
                      f'response_index={request("R c0600d52 2 0"):04x} '
                      f'mu_mask={mask:08x} cpu={request("P"):08x}')
                stream.close()
            if args.qemu:
                rom = [sys.executable,
                       str(Path(__file__).with_name('run_pci_rom.py')),
                       str(args.image.resolve()), '--qemu',
                       str(args.qemu.resolve()), '--bridge-socket', str(bridge),
                       '--seconds', str(args.seconds), '--memory-mb',
                       str(args.memory_mb)]
                if args.bios:
                    rom += ['--bios', str(args.bios.resolve())]
                if args.explore_live_firmware:
                    rom += ['--explore-live-firmware']
                if args.explore_set_mbox_trace:
                    rom += ['--explore-set-mbox-trace']
                if args.explore_set_mbox_bridge:
                    rom += ['--explore-set-mbox-bridge']
                if args.explore_mmbox_doorbell_observe:
                    rom += ['--explore-mmbox-doorbell-observe']
                if args.explore_mmbox_doorbell_control:
                    rom += ['--explore-mmbox-doorbell-control']
                if args.explore_stock_ring_memory:
                    rom += ['--explore-stock-ring-memory']
                if args.explore_stock_ring_mirror:
                    rom += ['--explore-stock-ring-mirror']
                if args.explore_stock_followup_observe:
                    rom += ['--explore-stock-followup-observe']
                if args.explore_stock_followup_mirror:
                    rom += ['--explore-stock-followup-mirror']
                if args.explore_stock_next_observe:
                    rom += ['--explore-stock-next-observe']
                if args.explore_stock_next_mirror:
                    rom += ['--explore-stock-next-mirror']
                if args.explore_stock_next_mutate_slot:
                    rom += ['--explore-stock-next-mutate-slot']
                if args.explore_stock_next_mutate_prefill:
                    rom += ['--explore-stock-next-mutate-prefill']
                if args.explore_stock_scsi_observe:
                    rom += ['--explore-stock-scsi-observe']
                if args.trace_live_reply:
                    rom += ['--trace-live-reply']
                if args.boot_cdrom:
                    rom += ['--boot-cdrom', str(args.boot_cdrom.resolve())]
                if args.kernel:
                    rom += ['--kernel', str(args.kernel.resolve()),
                            '--kernel-append', args.kernel_append]
                if args.initrd:
                    rom += ['--initrd', str(args.initrd.resolve())]
                if args.boot_enter_after is not None:
                    rom += ['--boot-enter-after', str(args.boot_enter_after)]
                if args.boot_enter_on_prompt:
                    rom += ['--boot-enter-on-prompt']
                if args.serial_output:
                    rom += ['--serial-output', str(args.serial_output.resolve())]
                if args.vga_snapshot:
                    rom += ['--vga-snapshot', str(args.vga_snapshot.resolve())]
                if args.rom_output:
                    rom += ['--output', str(args.rom_output.resolve())]
                if args.qemu_stderr_output:
                    rom += ['--qemu-stderr-output',
                            str(args.qemu_stderr_output.resolve())]
                result = subprocess.run(rom, capture_output=True,
                                        text=True, timeout=max(60, args.seconds + 30))
                if result.returncode:
                    raise RuntimeError(f'QEMU ROM probe failed: {result.stderr[-2000:]}')
                parsed = json.loads(result.stdout)
                if args.explore_live_firmware:
                    assert parsed['stock_ctlr_info_completed'], parsed
                if args.expect_linux_login:
                    assert [item['ioctl'] for item in parsed['mailbox_requests']] == [
                        0x01, 0x11, 0x15, 0xd0, 0x2d], parsed['mailbox_requests']
                    assert len(parsed['stock_completion_lines']) == 5
                    assert 'localhost login:' in parsed['serial_tail']
                if args.require_natural_priority:
                    irq_log = emu_log.read_text(errors='replace')
                    assert 'forced-priority=1' not in irq_log
                    if args.auto_isp_no_device_queue:
                        assert 'isp-no-device-auto responses=15' in irq_log
                        assert 'isp-no-device-auto responses=0 vector=42' in irq_log
                    elif args.model_isp_no_device_queue:
                        assert 'routed-interrupt pin=0 vector=42' in irq_log
                    elif args.route_isp_pirsr_bit0:
                        assert irq_log.count('routed-interrupt pin=0 vector=42') == 15
                    else:
                        assert irq_log.count('forced-priority=0') >= 15
                if args.require_routed_mu:
                    irq_log = emu_log.read_text(errors='replace')
                    assert irq_log.count('routed-interrupt pin=7 vector=62') == 5
                print(f'rom=PASS stock_completion='
                      f'{parsed["stock_ctlr_info_completed"]} '
                      f'requests={parsed["mailbox_requests"]} '
                      f'completions={parsed["stock_completion_lines"]}')
                print(f'guest_serial_tail={parsed["serial_tail"]!r} '
                      f'rom_blocks={parsed["rom_block_count"]}')
        finally:
            if args.emulator_output and emu_log.exists():
                args.emulator_output.write_bytes(emu_log.read_bytes())
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    main()
