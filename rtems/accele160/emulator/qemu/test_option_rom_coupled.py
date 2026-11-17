#!/usr/bin/env python3
"""Observe SeaBIOS option-ROM PCI setup against the paused stock i960 model."""
import argparse
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--bios', type=Path,
                        help='experimental SeaBIOS that supplies the PCI BDF')
    parser.add_argument('--expected-step-ip',
                        help='assert the interpreter IP after host ROM traffic')
    parser.add_argument('--step-on-ack', action='store_true',
                        help='step the i960 during the ROM ACK-status write')
    parser.add_argument('--seconds', type=float, default=2)
    parser.add_argument('--rom-output', type=Path,
                        help='save the host ROM probe JSON')
    parser.add_argument('--rom-trace-output', type=Path,
                        help='save executed Mylex instruction blocks')
    parser.add_argument('--emulator-output', type=Path,
                        help='save all i960 bridge checkpoints')
    parser.add_argument('--native-report-output', type=Path,
                        help='save the native report after host traffic')
    parser.add_argument('--qemu-stderr-output', type=Path,
                        help='save QEMU PCI/BAR access log')
    parser.add_argument('--allow-post-init-traffic', action='store_true',
                        help='expect the later ROM mailbox submit and status poll')
    parser.add_argument('--post-step-cycles', type=int, default=0,
                        help='additional i960 instructions after QEMU stops')
    parser.add_argument('--inspect-isp', action='store_true',
                        help='read the channel-0 ISP mailbox/status registers after stepping')
    parser.add_argument('--inspect-isp-queue', action='store_true',
                        help='dump channel-0 ISP queue indexes and submitted request entries')
    parser.add_argument('--probe-isp-no-device-vector', type=lambda x: int(x, 0),
                        choices=(0x42, 0x62, 0x72),
                        help='inject one synthetic incomplete status and an exploratory i960 vector')
    parser.add_argument('--probe-isp-no-device-all', action='store_true',
                        help='inject incomplete status for all 15 observed scan commands')
    parser.add_argument('--post-probe-step-cycles', type=int, default=0,
                        help='additional i960 instructions after the ISP response probe')
    parser.add_argument('--probe-mu-vector-after', action='store_true',
                        help='force the stock MU vector after the ISP probe and later stepping')
    parser.add_argument('--post-mu-step-cycles', type=int, default=0,
                        help='additional i960 instructions after the forced MU probe')
    parser.add_argument('--inspect-mu-dma-output', action='store_true',
                        help='compare bounded channel-1 host output with local descriptor data')
    parser.add_argument('--mu-dma-output', type=Path,
                        help='save the verified 512-byte exploratory stock DMA response')
    parser.add_argument('--restore-host-message-after-mu', action='store_true',
                        help='restage the saved host mailbox address after stock MU setup')
    parser.add_argument('--inspect-stock-scan', action='store_true',
                        help='read the installed stock scan object and startup monitor state')
    parser.add_argument('--trace-scan-state3', action='store_true',
                        help='trace bounded stock scan state-3 and field writes')
    parser.add_argument('--explore-stock-isp-config', action='store_true',
                        help='opt-in timer, secondary PCI and bounded ISP protocol probes')
    parser.add_argument('--explore-timer-interrupt', action='store_true',
                        help='deliver opt-in timer 0 vectors during stock ISP replay')
    parser.add_argument('--explore-isp-feature-ack', action='store_true',
                        help='trace past exact observed ISP feature command')
    parser.add_argument('--explore-isp-status-zero', action='store_true',
                        help='test fabricated zero firmware-status outputs')
    parser.add_argument('--explore-isp-init-id-ack', action='store_true',
                        help='trace past exact set-initiator-ID request')
    parser.add_argument('--explore-isp-bus-reset-ack', action='store_true',
                        help='trace past exact bus-1 reset request without SCSI signalling')
    parser.add_argument('--explore-isp-target0-ack', action='store_true',
                        help='trace past the first observed target-0 setup request')
    parser.add_argument('--explore-isp-target-sweep', action='store_true',
                        help='trace ordered target 1..15 setup with target-0 parameters')
    args = parser.parse_args()
    if args.post_step_cycles < 0:
        parser.error('--post-step-cycles must be nonnegative')
    if args.post_probe_step_cycles < 0:
        parser.error('--post-probe-step-cycles must be nonnegative')
    if args.post_probe_step_cycles and args.probe_isp_no_device_vector is None:
        parser.error('--post-probe-step-cycles requires --probe-isp-no-device-vector')
    if args.probe_mu_vector_after and not args.probe_isp_no_device_all:
        parser.error('--probe-mu-vector-after requires --probe-isp-no-device-all')
    if args.restore_host_message_after_mu and not args.probe_mu_vector_after:
        parser.error('--restore-host-message-after-mu requires --probe-mu-vector-after')
    if args.post_mu_step_cycles < 0 or (args.post_mu_step_cycles and
                                       not args.probe_mu_vector_after):
        parser.error('--post-mu-step-cycles requires a nonnegative count and --probe-mu-vector-after')
    if args.inspect_mu_dma_output and not args.restore_host_message_after_mu:
        parser.error('--inspect-mu-dma-output requires --restore-host-message-after-mu')
    if args.mu_dma_output and not args.inspect_mu_dma_output:
        parser.error('--mu-dma-output requires --inspect-mu-dma-output')
    if args.mu_dma_output and args.mu_dma_output.exists():
        raise FileExistsError(args.mu_dma_output)
    if args.native_report_output and args.native_report_output.exists():
        raise FileExistsError(args.native_report_output)
    if args.probe_isp_no_device_all and args.probe_isp_no_device_vector != 0x42:
        parser.error('--probe-isp-no-device-all requires --probe-isp-no-device-vector 0x42')
    if args.explore_timer_interrupt and not args.explore_stock_isp_config:
        parser.error('--explore-timer-interrupt requires --explore-stock-isp-config')
    if args.explore_isp_feature_ack and not args.explore_stock_isp_config:
        parser.error('--explore-isp-feature-ack requires --explore-stock-isp-config')
    if args.explore_isp_status_zero and not args.explore_isp_feature_ack:
        parser.error('--explore-isp-status-zero requires --explore-isp-feature-ack')
    if args.explore_isp_init_id_ack and not args.explore_isp_status_zero:
        parser.error('--explore-isp-init-id-ack requires --explore-isp-status-zero')
    if args.explore_isp_bus_reset_ack and not args.explore_isp_init_id_ack:
        parser.error('--explore-isp-bus-reset-ack requires --explore-isp-init-id-ack')
    if args.explore_isp_target0_ack and not args.explore_isp_bus_reset_ack:
        parser.error('--explore-isp-target0-ack requires --explore-isp-bus-reset-ack')
    if args.explore_isp_target_sweep and not args.explore_isp_target0_ack:
        parser.error('--explore-isp-target-sweep requires --explore-isp-target0-ack')
    with tempfile.TemporaryDirectory(prefix='accele160-rom-coupled-') as directory:
        bridge = Path(directory) / 'bridge.sock'
        emu_log = Path(directory) / 'emulator.log'
        emu_command = [str(args.emulator.resolve()), str(args.image.resolve()),
                       '60000000', '--board-id=11', '--quiet-trace',
                       f'--bridge-socket={bridge}']
        if args.explore_stock_isp_config:
            emu_command += [
                '--explore-timer-interrupt' if args.explore_timer_interrupt
                else '--explore-timer-clock', '--explore-qlogic-pci',
                '--explore-isp-mailbox', '--explore-isp-execute-ack',
                '--explore-isp-about-ack', '--explore-isp-queue-ack',
                '--explore-isp-retry-ack', '--explore-isp-reset-delay-ack',
                '--explore-isp-active-negation-ack',
            ]
            if args.explore_isp_feature_ack:
                emu_command.append('--explore-isp-feature-ack')
            if args.explore_isp_status_zero:
                emu_command.append('--explore-isp-status-zero')
            if args.explore_isp_init_id_ack:
                emu_command.append('--explore-isp-init-id-ack')
            if args.explore_isp_bus_reset_ack:
                emu_command.append('--explore-isp-bus-reset-ack')
            if args.explore_isp_target0_ack:
                emu_command.append('--explore-isp-target0-ack')
            if args.explore_isp_target_sweep:
                emu_command.append('--explore-isp-target-sweep')
        if args.trace_scan_state3:
            emu_command.append('--trace-scan-state3')
        with emu_log.open('w') as emu_stream:
            emu = subprocess.Popen(
                emu_command,
                stdout=emu_stream, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.monotonic() + 90
            while not bridge.exists():
                if emu.poll() is not None:
                    raise AssertionError(f'emulator exited: {emu_log.read_text()[-4000:]}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            rom_command = [
                sys.executable, str(Path(__file__).with_name('run_pci_rom.py')),
                str(args.image.resolve()), '--qemu', str(args.qemu.resolve()),
                '--seconds', str(args.seconds), '--bridge-socket', str(bridge)]
            if args.bios:
                rom_command += ['--bios', str(args.bios.resolve())]
            if args.step_on_ack:
                rom_command += ['--step-on-ack']
            if args.rom_output:
                rom_command += ['--output', str(args.rom_output.resolve())]
            if args.rom_trace_output:
                rom_command += ['--rom-trace-output',
                                str(args.rom_trace_output.resolve())]
            if args.qemu_stderr_output:
                rom_command += ['--qemu-stderr-output',
                                str(args.qemu_stderr_output.resolve())]
            rom = subprocess.run(
                rom_command,
                capture_output=True, text=True, timeout=90)
            if rom.returncode:
                raise RuntimeError(f'ROM probe failed ({rom.returncode}): '
                                   f'{rom.stderr[-4000:]}')
            rom_result = json.loads(rom.stdout)
            assert rom_result['option_rom_entry_executed']
            assert rom_result['option_rom_guest_base'] != '0xc0000', rom_result
            if args.bios:
                assert rom_result['first_bar_accesses'][:5] == [
                    'accele160 bar0 W offset=0x0034 size=1 value=0xff',
                    'accele160 bar0 W offset=0x0010 size=4 value=0x00000000',
                    'accele160 bar0 W offset=0x0014 size=4 value=0x00000000',
                    'accele160 bar0 W offset=0x0018 size=4 value=0x00000000',
                    'accele160 bar0 W offset=0x0020 size=1 value=0x02',
                ], rom_result['first_bar_accesses']
            if args.allow_post_init_traffic:
                accesses = rom_result['first_bar_accesses']
                assert 'accele160 bar0 W offset=0x0020 size=1 value=0x01' in accesses
                assert 'accele160 bar0 R offset=0x002c size=1 value=0x00' in accesses
                assert rom_result['mailbox_requests'] == [{
                    'id': 0x7f, 'opcode': 0x20, 'control': 0x10,
                    'transfer_bytes': 512, 'ioctl': 0x01,
                    'sg0_dma': 0x9f3e0, 'sg0_bytes': 512,
                }], rom_result['mailbox_requests']
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(bridge))
                stream = connection.makefile('rwb', buffering=0)

                def request(line):
                    stream.write((line + '\n').encode('ascii'))
                    answer = stream.readline().decode('ascii').strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError(f'{line}: {answer}')
                    return int(answer, 16)

                bridge_cmd = request('I 1004')
                raid_cmd = request('I 1204')
                doorbell = request('I 1320')
                if args.bios and not args.allow_post_init_traffic:
                    assert (bridge_cmd, raid_cmd, doorbell) == (0x107, 0x107, 2)
                request('S 0' if args.step_on_ack else 'S 1000000')
                remaining = args.post_step_cycles
                probe_gate_steps = 0
                while remaining:
                    chunk = min(remaining, 1000000)
                    request(f'S {chunk}')
                    remaining -= chunk
                if args.probe_isp_no_device_vector is not None:
                    assert args.post_step_cycles >= 400000000
                    probe_count = 15 if args.probe_isp_no_device_all else 1
                    assert request('R 8bf00078 2 0') >= probe_count * 2
                    assert request('R c0600e34 4 0') == 0xc0770790
                    for _ in range(100):
                        probe_cpu_state = request('P')
                        if ((probe_cpu_state & 0x100) and
                                (args.probe_isp_no_device_vector == 0x42 or
                                 (probe_cpu_state & 0xff) <
                                 args.probe_isp_no_device_vector // 8)):
                            break
                        request('S 1000')
                        probe_gate_steps += 1
                    else:
                        raise AssertionError(f'ISP vector remained masked: {probe_cpu_state:08x}')
                    probe_channel_mask = request('R c0384b68 4 0')
                    probe_imsk = request('I ff008504')
                    probe_pending = probe_channel_mask & probe_imsk
                    assert probe_pending and probe_pending & (probe_pending - 1) == 0, (
                        probe_channel_mask, probe_imsk)
                    probe_results = []
                    for index in range(probe_count):
                        for _ in range(100):
                            if request('P') & 0x100:
                                break
                            request('S 1000')
                            probe_gate_steps += 1
                        else:
                            raise AssertionError(f'ISP probe interrupts remained disabled at entry {index}')
                        command = 0xc0600df0 + (2 * index + 1) * 64
                        assert request(f'R {command:08x} 1 0') == 9
                        assert request(f'R {command + 20:08x} 1 0') == 0x12
                        handle = request(f'R {command + 4:08x} 4 0')
                        response = 0xc0604df0 + index * 64
                        for word in range(16):
                            request(f'W {response + word * 4:08x} 4 0')
                        request(f'W {response:08x} 4 103')  # type 3, one entry
                        request(f'W {response + 4:08x} 4 {handle:x}')
                        request(f'W {response + 8:08x} 4 10000')  # incomplete
                        request(f'W 8bf0007a 2 {index + 1:x}')
                        request('W 8bf00070 2 8020')
                        request('W 8bf0000c 2 1')
                        request('W 8bf0000a 2 4')
                        request(f'C ff008500 {probe_pending:x}')
                        vector_ip = request(f'J {args.probe_isp_no_device_vector:x}')
                        request('S 1000000')
                        consumed = request('R c0600d52 2 0')
                        result = request(f'R {handle - 4:08x} 4 0')
                        probe_results.append((consumed, result))
                        if consumed != index + 1:
                            break
                    probe_response_consumer = request('R 8bf0007a 2 0')
                    probe_device_result = request('R c077078c 4 0')
                    remaining = args.post_probe_step_cycles
                    while remaining:
                        chunk = min(remaining, 1000000)
                        request(f'S {chunk}')
                        remaining -= chunk
                    if args.probe_mu_vector_after:
                        assert request('I 1328') & 4 == 0
                        assert request('I 1324') & 4
                        if args.restore_host_message_after_mu:
                            saved_mailbox = re.search(
                                r'checkpoint mailbox-submission dma=([0-9a-f]{16})',
                                emu_log.read_text(errors='replace'))
                            assert saved_mailbox
                            mu_host_dma = int(saved_mailbox.group(1), 16)
                            assert request(f'C 1310 {mu_host_dma:x}') == mu_host_dma
                            assert request('C 1314 0') == 0
                        for _ in range(100):
                            if request('P') & 0x100:
                                break
                            request('S 1000')
                            probe_gate_steps += 1
                        else:
                            raise AssertionError('MU probe interrupts remained disabled')
                        mu_vector_ip = request('J 62')
                        request('S 1000000')
                        if args.restore_host_message_after_mu:
                            saved_bytes = re.search(
                                r'checkpoint mailbox-bytes ([0-9a-f]{128})',
                                emu_log.read_text(errors='replace'))
                            assert saved_bytes
                            mailbox = bytes.fromhex(saved_bytes.group(1))
                            mu_local_header = [request(f'R {0xc00c3730 + offset:08x} 4 0')
                                               for offset in (0, 4)]
                            assert mu_local_header == [
                                int.from_bytes(mailbox[offset:offset + 4], 'little')
                                for offset in (0, 4)], mu_local_header
                        remaining = args.post_mu_step_cycles
                        while remaining:
                            chunk = min(remaining, 1000000)
                            request(f'S {chunk}')
                            remaining -= chunk
                        if args.restore_host_message_after_mu:
                            mu_work = {name: request(f'R {address:08x} 4 0')
                                       for name, address in (
                                           ('queue_head', 0xc0385290),
                                           ('queue_tail', 0xc0385294),
                                           ('active', 0xc0384ac8),
                                           ('request_next', 0xc00c37b4),
                                           ('request_callback', 0xc00c37c8),
                                           ('request_length', 0xc00c3734),
                                           ('request_completed_bytes', 0xc00c3a20))}
                            mu_work['request_status'] = request('R c00c3786 2 0')
                            mu_work['dma0_status'] = request('I 1404')
                            mu_work['dma1_status'] = request('I 1444')
                            mu_work['dma1_control'] = request('I 1440')
                            mu_work['dma1_descriptor'] = request('I 1450')
                            mu_work['outbound_message0'] = request('I 1318')
                            mu_work['outbound_message1'] = request('I 131c')
                            mu_work['outbound_doorbell'] = request('I 132c')
                            dma1_descriptor = mu_work['dma1_descriptor']
                            if 0xc0000000 <= dma1_descriptor <= 0xc0ffffe0:
                                mu_dma_words = [request(
                                    f'R {dma1_descriptor + offset:08x} 4 0')
                                    for offset in range(0, 24, 4)]
                                local_dma = mu_dma_words[3]
                                if 0xc0000000 <= local_dma <= 0xc0ffffe0:
                                    mu_dma_local_prefix = [request(
                                        f'R {local_dma + offset:08x} 4 0')
                                        for offset in range(0, 32, 4)]
                                    if args.inspect_mu_dma_output:
                                        assert mu_dma_words[4:] == [512, 0x3f]
                                        mu_host_words = [request(
                                            f'U {mu_dma_words[1] + offset:08x}')
                                            for offset in range(0, 512, 4)]
                                        mu_local_words = [request(
                                            f'R {local_dma + offset:08x} 4 0')
                                            for offset in range(0, 512, 4)]
                                        assert mu_host_words == mu_local_words
                                        if args.mu_dma_output:
                                            args.mu_dma_output.write_bytes(b''.join(
                                                word.to_bytes(4, 'little')
                                                for word in mu_host_words))
                                        assert mu_work['outbound_message0'] & 0xffff == \
                                            int.from_bytes(mailbox[:2], 'little')
                                        assert mu_work['outbound_message0'] >> 16 == 0
                                        assert mu_work['outbound_doorbell'] & 1
                final_doorbell = request('I 1320')
                final_status = request('I 1324')
                final_mask = request('I 1328')
                if args.native_report_output:
                    words = [request(f'R {0xc0001f00 + i * 4:08x} 4 0')
                             for i in range(25)]
                    if words[0] != 0x32544753 or words[7] != 0x50415353:
                        raise AssertionError('native RTEMS PASS report absent')
                    if words[19] == 0x31545348 and words[16] & 1:
                        raise AssertionError('HST1 report was sampled during update')
                    args.native_report_output.write_text(json.dumps({
                        'raw_words': [f'0x{word:08x}' for word in words],
                        'host_snapshot_marker': words[9] == 0x30545348,
                        'bridge_pci_command': f'0x{words[10]:08x}',
                        'raid_pci_command': f'0x{words[11]:08x}',
                        'inbound_doorbell': f'0x{words[12]:08x}',
                        'inbound_status': f'0x{words[13]:08x}',
                        'inbound_mask': f'0x{words[14]:08x}',
                        'ready_flags': f'0x{words[15]:08x}',
                        'host_monitor_marker': words[19] == 0x31545348,
                        'snapshot_sequence': words[16] if words[19] == 0x31545348 else None,
                        'mailbox_pointer': (f'0x{words[18]:08x}{words[17]:08x}'
                                            if words[19] == 0x31545348 else None),
                        'mailbox_ingress_marker': words[20] == 0x3058424d,
                        'mailbox_ingress_state': (f'0x{words[21]:08x}'
                                                  if words[20] == 0x3058424d else None),
                        'mailbox_command_id': (words[22] if words[20] == 0x3058424d else None),
                        'mailbox_output_bus': (f'0x{words[23]:08x}'
                                               if words[20] == 0x3058424d else None),
                        'mailbox_request_fnv32': (f'0x{words[24]:08x}'
                                                  if words[20] == 0x3058424d else None),
                    }, indent=2) + '\n')
                if args.inspect_isp:
                    isp_mailbox0 = request('R 8bf00070 2 0')
                    isp_isr = request('R 8bf0000a 2 0')
                    isp_semaphore = request('R 8bf0000c 2 0')
                if args.inspect_isp_queue:
                    queue_indexes = [request(f'R {address:08x} 2 0')
                                     for address in (0x8bf00078, 0x8bf0007a)]
                    isp_channel_control = request('R c03e5bc8 4 0')
                    isp_response_consumer = request(
                        f'R {isp_channel_control + 0x52:08x} 2 0') if isp_channel_control else 0
                    isp_response_ring_ptr = request(
                        f'R {isp_channel_control + 0x48:08x} 4 0') if isp_channel_control else 0
                    request_entries = [[request(f'R {0xc0600df0 + entry * 64 + word * 4:08x} 4 0')
                                        for word in range(16)] for entry in range(min(queue_indexes[0], 256))]
                    response_entries = [[request(f'R {0xc0604df0 + entry * 64 + word * 4:08x} 4 0')
                                         for word in range(16)] for entry in range(2)]
                if args.inspect_stock_scan:
                    scan_slot_index = request('R c00c3690 4 0')
                    scan_slot = 0xc03d78b0 + scan_slot_index * 0x5c
                    scan_object = request(f'R {scan_slot + 0x14:08x} 4 0')
                    valid_scan_object = 0xc0000000 <= scan_object <= 0xc0ffffd0
                    scan_state = request(f'R {scan_object + 0x14:08x} 4 0') if valid_scan_object else 0
                    scan_event_status = request(f'R {scan_object + 0x28:08x} 4 0') if valid_scan_object else 0
                    observed_owner = re.search(
                        r'checkpoint scan-state object=([0-9a-f]{8})',
                        emu_log.read_text(errors='replace'))
                    scan_owner = int(observed_owner.group(1), 16) if observed_owner else 0
                    scan_owner_state = request(f'R {scan_owner + 0x14:08x} 4 0') if scan_owner else 0
                    scan_channels = request('R c00c0150 4 0')
                    scan_pending0 = request(f'R {scan_owner + 0x28:08x} 4 0') if scan_owner else 0
                    scan_pending1 = request(f'R {scan_owner + 0x2c:08x} 4 0') if scan_owner else 0
                    scan_channel_status = request('R c0384bb8 4 0')
                    scan_channel_flag = request('R c0384bbc 4 0')
                    isp_response0 = request('R c0604df0 4 0')
                    monitor_state = request('R c03e4710 4 0')
                    monitor_workspace = request('R c03e4718 4 0')
            print(f'option_rom=PASS bridge_command={bridge_cmd:08x} '
                  f'raid_command={raid_cmd:08x} doorbell={doorbell:08x} '
                  f'final_doorbell={final_doorbell:08x} '
                  f'final_status={final_status:08x} '
                  f'final_mask={final_mask:08x} '
                  f'bar_accesses={rom_result["bar_access_count_logged"]}')
            if args.inspect_isp:
                print(f'isp_mailbox0={isp_mailbox0:04x} '
                      f'isr={isp_isr:04x} semaphore={isp_semaphore:04x}')
            if args.inspect_isp_queue:
                print(f'isp_queue_mailbox4={queue_indexes[0]:04x} '
                      f'isp_queue_mailbox5={queue_indexes[1]:04x} '
                      f'channel_control={isp_channel_control:08x} '
                      f'response_consumer={isp_response_consumer:04x} '
                      f'response_ring_ptr={isp_response_ring_ptr:08x}')
                for name, entries in (('request', request_entries),
                                      ('response', response_entries)):
                    for index, words in enumerate(entries):
                        if name == 'request':
                            first = b''.join(word.to_bytes(4, 'little') for word in words[:8])
                            print(f'isp_request_entry{index}='
                                  f'header={first[:4].hex()} '
                                  f'handle={words[1]:08x} '
                                  f'bytes8_31={first[8:32].hex()}')
                        else:
                            print(f'isp_response_entry{index}=' +
                                  ' '.join(f'{word:08x}' for word in words))
            if args.probe_isp_no_device_vector is not None:
                print(f'isp_probe_vector={args.probe_isp_no_device_vector:02x} '
                      f'cpu_state={probe_cpu_state:08x} '
                      f'gate_steps={probe_gate_steps} '
                      f'channel_mask={probe_channel_mask:08x} '
                      f'pending={probe_pending:08x} '
                      f'vector_ip={vector_ip:08x} '
                      f'response_index={probe_response_consumer:04x} '
                      f'device_result={probe_device_result:08x} '
                      f'probe_results={probe_results}')
            if args.probe_mu_vector_after:
                print(f'mu_probe_vector=62 vector_ip={mu_vector_ip:08x} '
                      f'host_dma={mu_host_dma:08x} ' if args.restore_host_message_after_mu else
                      f'mu_probe_vector=62 vector_ip={mu_vector_ip:08x} ',
                      end='')
                print(f'doorbell={final_doorbell:08x} status={final_status:08x} '
                      f'mask={final_mask:08x}')
                if args.restore_host_message_after_mu:
                    print(f'mu_local_header={mu_local_header[0]:08x},'
                          f'{mu_local_header[1]:08x}')
                    print('mu_work=' + ' '.join(
                        f'{name}:{value:08x}' for name, value in mu_work.items()))
                    if 0xc0000000 <= dma1_descriptor <= 0xc0ffffe0:
                        print('mu_dma_descriptor=' + ','.join(
                            f'{value:08x}' for value in mu_dma_words))
                        if 0xc0000000 <= local_dma <= 0xc0ffffe0:
                            print('mu_dma_local_prefix=' + ','.join(
                                f'{value:08x}' for value in mu_dma_local_prefix))
                            if args.inspect_mu_dma_output:
                                print(f'mu_dma_output=PASS words={len(mu_host_words)} '
                                      f'host={mu_dma_words[1]:08x}')
            if args.inspect_stock_scan:
                print(f'scan_slot_index={scan_slot_index} scan_object={scan_object:08x} '
                      f'scan_state={scan_state:08x} '
                      f'scan_event_status={scan_event_status:08x} '
                      f'scan_owner={scan_owner:08x} '
                      f'scan_owner_state={scan_owner_state:08x} '
                      f'scan_channels={scan_channels} '
                      f'scan_pending0={scan_pending0:08x} '
                      f'scan_pending1={scan_pending1:08x} '
                      f'scan_channel_status={scan_channel_status:08x} '
                      f'scan_channel_flag={scan_channel_flag:08x} '
                      f'isp_response0={isp_response0:08x} '
                      f'monitor_state={monitor_state:08x} '
                      f'monitor_workspace={monitor_workspace:08x}')
        finally:
            emu.terminate()
            emu.wait(timeout=5)
            emu_stdout = emu_log.read_text()
            if args.emulator_output:
                args.emulator_output.write_text(emu_stdout)
        steps = [line for line in emu_stdout.splitlines()
                 if line.startswith('checkpoint bridge-step ')]
        assert 'checkpoint host-pci-command local=00001004' in emu_stdout
        assert 'checkpoint host-pci-command local=00001204' in emu_stdout
        expected_steps = (2 if args.step_on_ack else 1) + (
            args.post_step_cycles + 999999) // 1000000 + (
                len(probe_results) if args.probe_isp_no_device_vector is not None else 0
            ) + probe_gate_steps + (
                args.post_probe_step_cycles + 999999) // 1000000 + (
                1 if args.probe_mu_vector_after else 0) + (
                args.post_mu_step_cycles + 999999) // 1000000
        assert len(steps) == expected_steps, steps
        assert all('fault=ffffffff' in step for step in steps), steps
        if args.step_on_ack:
            assert 'count=1000000' in steps[0] and 'count=0' in steps[1], steps
        if args.expected_step_ip:
            assert f'ip={args.expected_step_ip}' in steps[-1], steps[-1]
        for step in steps:
            print(step)


if __name__ == '__main__':
    main()
