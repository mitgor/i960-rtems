#!/usr/bin/env python3
"""Replay Linux myrs's first LP hardware-mailbox submission without completion."""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time

from inspect_isp_risc import inspect_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--cycles', required=True, type=int)
    parser.add_argument('--observe-cycles', type=int, default=0,
                        help='step stock after host LP initialization and submission')
    parser.add_argument('--explore-timer-clock', action='store_true',
                        help='approximate one 80303 bus clock per i960 instruction')
    parser.add_argument('--explore-timer-interrupt', action='store_true',
                        help='dispatch eligible timer 0 vectors in the i960 model')
    parser.add_argument('--explore-qlogic-pci', action='store_true',
                        help='replay captured ISP10160 secondary PCI configuration reads')
    parser.add_argument('--explore-isp-mailbox', action='store_true',
                        help='model bounded ISP register, RAM, DMA and checksum commands')
    parser.add_argument('--explore-isp-execute-ack', action='store_true',
                        help='acknowledge validated ISP image without executing its code')
    parser.add_argument('--explore-isp-about-ack', action='store_true',
                        help='report captured ISP firmware version without executing its code')
    parser.add_argument('--explore-isp-queue-ack', action='store_true',
                        help='record bounded ISP request/response queues without IOCB execution')
    parser.add_argument('--explore-isp-retry-ack', action='store_true',
                        help='acknowledge the observed ISP SET RETRY COUNT (0, 2)')
    parser.add_argument('--explore-isp-reset-delay-ack', action='store_true',
                        help='acknowledge the observed ISP SET RESET DELAY PARAMS (1, 1)')
    parser.add_argument('--explore-isp-active-negation-ack', action='store_true',
                        help='acknowledge the observed ISP SET ACTIVE NEGATION (0x30, 0x30)')
    parser.add_argument('--explore-isp-feature-ack', action='store_true',
                        help='trace-only acknowledgment of observed ISP SET FW FEATURES (0x16, 0x30)')
    parser.add_argument('--dump-isp-risc', type=Path,
                        help='save uploaded ISP words after the bounded replay')
    parser.add_argument('--emulator-output', type=Path,
                        help='save the complete i960 interpreter log')
    parser.add_argument('--qemu-stderr-output', type=Path,
                        help='save QEMU PCI/BAR diagnostics')
    args = parser.parse_args()
    if args.dump_isp_risc and (not args.explore_isp_mailbox or
                               not args.observe_cycles):
        parser.error('--dump-isp-risc requires --explore-isp-mailbox and --observe-cycles')
    if args.explore_isp_execute_ack and not args.explore_isp_mailbox:
        parser.error('--explore-isp-execute-ack requires --explore-isp-mailbox')
    if args.explore_isp_about_ack and not args.explore_isp_execute_ack:
        parser.error('--explore-isp-about-ack requires --explore-isp-execute-ack')
    if args.explore_isp_queue_ack and not args.explore_isp_about_ack:
        parser.error('--explore-isp-queue-ack requires --explore-isp-about-ack')
    if args.explore_isp_retry_ack and not args.explore_isp_queue_ack:
        parser.error('--explore-isp-retry-ack requires --explore-isp-queue-ack')
    if args.explore_isp_reset_delay_ack and not args.explore_isp_retry_ack:
        parser.error('--explore-isp-reset-delay-ack requires --explore-isp-retry-ack')
    if args.explore_isp_active_negation_ack and not args.explore_isp_reset_delay_ack:
        parser.error('--explore-isp-active-negation-ack requires --explore-isp-reset-delay-ack')
    if args.explore_isp_feature_ack and not args.explore_isp_active_negation_ack:
        parser.error('--explore-isp-feature-ack requires --explore-isp-active-negation-ack')
    request = bytearray(64)
    request[0] = 1                 # MYRS_DCMD_TAG
    request[2] = 0x20              # IOCTL
    request[3] = 0x40              # no_autosense
    request[4] = 32                # 512 * 64-byte command mailboxes, KiB
    request[5] = 4                 # 512 * 8-byte status mailboxes, KiB
    request[21] = 0x8e            # SET_MEM_MBOX
    request[22] = 1                # firmware status buffer size, KiB
    request[24:32] = (0x110000).to_bytes(8, 'little')
    request[32:40] = (0x120000).to_bytes(8, 'little')
    request[40:48] = (0x130000).to_bytes(8, 'little')
    with tempfile.TemporaryDirectory(prefix='accele160-mailbox-') as directory:
        sock = Path(directory) / 'i960.sock'
        emu_log = open(Path(directory) / 'emulator.log', 'w+')
        emu_command = [str(args.emulator.resolve()), str(args.image.resolve()),
                       str(args.cycles), '--board-id=11', '--quiet-trace',
                       f'--bridge-socket={sock}']
        if args.explore_timer_interrupt:
            emu_command.append('--explore-timer-interrupt')
        elif args.explore_timer_clock:
            emu_command.append('--explore-timer-clock')
        if args.explore_qlogic_pci:
            emu_command.append('--explore-qlogic-pci')
        if args.explore_isp_mailbox:
            emu_command.append('--explore-isp-mailbox')
        if args.explore_isp_execute_ack:
            emu_command.append('--explore-isp-execute-ack')
        if args.explore_isp_about_ack:
            emu_command.append('--explore-isp-about-ack')
        if args.explore_isp_queue_ack:
            emu_command.append('--explore-isp-queue-ack')
        if args.explore_isp_retry_ack:
            emu_command.append('--explore-isp-retry-ack')
        if args.explore_isp_reset_delay_ack:
            emu_command.append('--explore-isp-reset-delay-ack')
        if args.explore_isp_active_negation_ack:
            emu_command.append('--explore-isp-active-negation-ack')
        if args.explore_isp_feature_ack:
            emu_command.append('--explore-isp-feature-ack')
        emu = subprocess.Popen(
            emu_command,
            stdout=emu_log, stderr=subprocess.PIPE, text=True)
        qemu = None
        qemu_stderr = ''
        observed = None
        scheduler_state = None
        interrupt_state = None
        cpu_interrupt_state = None
        interrupt_table = None
        secondary_pci_state = None
        try:
            deadline = time.monotonic() + 90
            while not sock.exists():
                if emu.poll() is not None:
                    raise AssertionError(f'emulator exited: {emu.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            qemu = subprocess.Popen(
                [str(args.qemu.resolve()), '-machine', 'pc', '-m', '64',
                 '-display', 'none', '-nodefaults', '-accel', 'qtest',
                 '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
                 '-device', f'accele160-probe,addr=05.1,bridge-socket={sock}',
                 '-qtest', 'stdio'], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1)

            def command(line):
                qemu.stdin.write(line + '\n')
                qemu.stdin.flush()
                response = qemu.stdout.readline().strip()
                if not response.startswith('OK'):
                    raise AssertionError(f'{line}: {response}; qemu={qemu.poll()}')
                return int(response.split()[1], 0) if len(response.split()) > 1 else None

            command('outl 0xcf8 0x80002910')
            command('outl 0xcfc 0xf0000008')
            command('outl 0xcf8 0x80002904')
            command('outw 0xcfc 0x0002')  # BAR enabled; DMA still disabled
            bar = 0xf0000000
            # myrs LP_hw_init acknowledges stale status before probing init.
            command(f'writeb {bar + 0x20:#x} 0x02')
            command(f'write 0x100000 64 0x{request.hex()}')
            command(f'writel {bar + 0x10:#x} 0x00100000')
            command(f'writel {bar + 0x14:#x} 0x00000000')
            assert command(f'readb {bar + 0x20:#x}') == 0
            assert command(f'readb {bar + 0x2c:#x}') == 0
            command(f'writeb {bar + 0x20:#x} 0x01')
            assert command(f'readb {bar + 0x20:#x}') == 0
            command('outw 0xcfc 0x0006')  # enable PCI bus master
            command('outl 0xcf8 0x80002804')
            command('outw 0xcfc 0x0004')  # enable bridge bus master
            command(f'writeb {bar + 0x20:#x} 0x01')
            assert command(f'readb {bar + 0x20:#x}') & 1
            for _ in range(4):
                assert command(f'readb {bar + 0x2c:#x}') == 0
            print('lp_submit=PASS id=1 opcode=20 ioctl=8e '
                  'dma=00100000 idb_full=1 odb_status=0 completion=PENDING')
            if args.observe_cycles:
                qemu.terminate()
                _, qemu_stderr = qemu.communicate(timeout=5)
                qemu = None
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.connect(str(sock))
                    stream = connection.makefile('rwb', buffering=0)

                    def bridge_request(line):
                        stream.write((line + '\n').encode('ascii'))
                        answer = stream.readline().decode('ascii').strip()
                        if not answer or answer == 'ERR':
                            raise AssertionError(f'{line}: {answer}')
                        return int(answer, 16)

                    assert bridge_request('I 1320') & 3 == 3
                    for start in range(0, args.observe_cycles, 1_000_000):
                        bridge_request(f'S {min(1_000_000, args.observe_cycles - start)}')
                    observed = (bridge_request('I 1320'),
                                bridge_request('I 1324'),
                                bridge_request('I 1328'),
                                bridge_request('R c0494cfc 4 0'),
                                bridge_request('Q'))
                    scheduler_state = {
                        f'{address:08x}': bridge_request(f'R {address:08x} 4 0')
                        for address in (0xc00c3690, 0xc00c3700, 0xc00c0300,
                                        0xc00c3718, 0xc04016a0, 0xc03e1e20,
                                        0xc04ad650, 0xc00c0274, 0xc03e2740,
                                        0xc00c0270, 0xc00c0278, 0xc0400e68,
                                        0xc0400e6c, 0xc0400e70, 0xc00c3720,
                                        0xc049fd64, 0xc03e470c, 0xc03e4710,
                                        0xc03e4714, 0xc03e4718, 0xc03e4724,
                                        0xc0770008, 0xc077000c, 0xc0770010,
                                        0xc0770014, 0xc0770018, 0xc0770024,
                                        0xc0770028, 0xc077002c, 0xc0770030,
                                        0xc0384b78, 0xc0384b30, 0xc0384bb8,
                                        0xc0384b80, 0xc00c0150, 0xc048b730)
                    }
                    if args.explore_isp_mailbox:
                        scheduler_state.update({
                            f'{address:08x}': bridge_request(f'R {address:08x} 4 0')
                            for address in range(0xc0600df0, 0xc0600e30, 4)
                        })
                    startup_state = scheduler_state['c049fd64']
                    if 0xc0000000 <= startup_state <= 0xc0fffedc:
                        for offset in (0, 4, 8, 0x14, 0x18):
                            address = startup_state + offset
                            scheduler_state[f'{address:08x}'] = bridge_request(
                                f'R {address:08x} 4 0')
                    callback_object = scheduler_state['c04ad650']
                    if 0xc0000000 <= callback_object <= 0xc0fffedc:
                        address = callback_object + 0x118
                        scheduler_state[f'{address:08x}'] = bridge_request(
                            f'R {address:08x} 4 0')
                    interrupt_state = {
                        f'{address:08x}': bridge_request(f'I {address:08x}')
                        for address in (0xff008500, 0xff008504, 0xff008510,
                                        0xff008528, 0xff000300, 0xff000304,
                                        0xff000308, 0xff000310, 0xff000314,
                                        0xff000318)
                    }
                    cpu_interrupt_state = bridge_request('P')
                    if args.explore_qlogic_pci:
                        secondary_pci_state = (bridge_request('I 12a8'),
                                               bridge_request('I 12b0'))
                    if args.dump_isp_risc:
                        end = bridge_request('L')
                        if not 0x1000 < end <= 0x10000:
                            raise AssertionError(f'ISP load end: {end:#x}')
                        firmware = bytearray()
                        for first in range(0x1000, end, 64):
                            count = min(64, end - first)
                            stream.write(f'K {first:x} {count}\n'.encode('ascii'))
                            answer = stream.readline().decode('ascii').strip()
                            if len(answer) != count * 4:
                                raise AssertionError(f'ISP dump at {first:#x}: {answer}')
                            for index in range(count):
                                firmware.extend(int(answer[index * 4:index * 4 + 4], 16)
                                                .to_bytes(2, 'little'))
                        report = inspect_image(firmware)
                        assert report['end_address'] == end, report
                        args.dump_isp_risc.write_bytes(firmware)
                        print(f'isp_risc_dump=PASS start=1000 end={end:04x} '
                              f'bytes={len(firmware)} sha256='
                              f"{report['sha256']}")
                        print(f"isp_risc_image=PASS words={report['declared_words']:04x} "
                              f"checksum={report['checksum']:04x} "
                              f"header={report['header']}")
                    interrupt_table = bridge_request('V')
                    if 0xc0000000 <= interrupt_table <= 0xc0fffdf0:
                        scheduler_state[f'{interrupt_table + 0x20c:08x}'] = bridge_request(
                            f'R {interrupt_table + 0x20c:08x} 4 0')
                    scheduler_state['c0000418'] = bridge_request('R c0000418 4 0')
        finally:
            if qemu is not None:
                qemu.terminate()
                _, qemu_stderr = qemu.communicate(timeout=5)
            emu.terminate()
            emu.communicate(timeout=5)
            emu_log.seek(0)
            emu_stdout = emu_log.read()
            emu_log.close()
            if args.emulator_output:
                args.emulator_output.write_text(emu_stdout)
            if args.qemu_stderr_output:
                args.qemu_stderr_output.write_text(qemu_stderr)
        assert 'bus master disabled' in qemu_stderr
        assert 'accele160 lp ack-status posted to i960 doorbell bit 1' in qemu_stderr
        assert 'accele160 lp mailbox submitted dma=0x0000000000100000 id=1 opcode=0x20 ioctl=0x8e pending=1' in qemu_stderr
        assert f'accele160 lp mailbox bytes={request.hex()}' in qemu_stderr
        assert 'checkpoint mailbox-submission dma=0000000000100000 id=0001 opcode=20 ioctl=8e completion=unmodeled' in emu_stdout
        assert 'checkpoint exploratory-host-doorbell bits=00000002 state=00000002' in emu_stdout
        assert f'checkpoint mailbox-bytes {request.hex()}' in emu_stdout
        print('controller_received=PASS exact_64_bytes=PASS completion=UNMODELED')
        if observed is not None:
            assert observed[4] == (observed[1] & ~observed[2]), observed
            if not args.explore_qlogic_pci:
                assert interrupt_state['ff008510'] == 0x6000, interrupt_state
                assert interrupt_state['ff008528'] == 0x80000, interrupt_state
                assert cpu_interrupt_state == 0x10c, cpu_interrupt_state
            steps = [line for line in emu_stdout.splitlines()
                     if line.startswith('checkpoint bridge-step ')]
            assert len(steps) == (args.observe_cycles + 999_999) // 1_000_000
            if args.explore_timer_interrupt:
                print('first_bridge_step=' + steps[0])
                traces = [line for line in emu_stdout.splitlines()
                          if line.startswith('checkpoint interrupt-trace ')]
                for line in traces[:8]:
                    print(line)
                for line in emu_stdout.splitlines():
                    if line.startswith(('checkpoint stock-isr-ret ',
                                        'checkpoint fault-origin ',
                                        'checkpoint interrupt-tail')):
                        print(line)
                for index, line in enumerate(steps):
                    if 'fault=ffffffff' not in line:
                        print(f'first_fault_step={index + 1} {line}')
                        break
            assert all('fault=ffffffff' in line for line in steps), steps[-1]
            totals = {}
            for key in ('gate-exits', 'unmask', 'command-dispatch', 'mu-setup',
                        'mu-poll', 'mu-dispatch', 'mu-receive', 'timer0-events',
                        'timer0-interrupts', 'startup-monitor-init',
                        'startup-monitor-tick', 'scan-init', 'scan-tick',
                        'controller-scan-tick', 'scan-worker-schedule',
                        'qlogic-discovery', 'qlogic-setup', 'qlogic-delay',
                        'qlogic-delay-calls', 'isp-mailbox-completions',
                        'console-return',
                        'boot-marker', 'next-wait', 'next-stage'):
                totals[key] = sum(int(re.search(rf'(?:^|\s){re.escape(key)}=(\d+)', line).group(1))
                                  for line in steps)
            for line in emu_stdout.splitlines():
                if line.startswith('checkpoint post-gate '):
                    print(line)
            for line in [entry for entry in emu_stdout.splitlines()
                         if entry.startswith('checkpoint delay-caller ')][-6:]:
                print(line)
            for line in emu_stdout.splitlines():
                if line.startswith(('checkpoint board-callback ',
                                    'checkpoint board-mode ',
                                    'checkpoint init-progress ',
                                    'checkpoint startup-monitor-tick ',
                                    'checkpoint startup-monitor-state ',
                                    'checkpoint startup-allocation ',
                                    'checkpoint monitor-progress ',
                                    'checkpoint scan-state ',
                                    'checkpoint scan-worker-schedule ',
                                    'checkpoint calibrated-delay ',
                                    'checkpoint qlogic-mailbox-poll ')):
                    print(line)
            for line in emu_stdout.splitlines():
                if line.startswith('checkpoint isp-load-call '):
                    print(line)
                if line.startswith(('checkpoint isp-execute-ack-stub ',
                                    'checkpoint isp-about-ack-stub ',
                                    'checkpoint isp-queue-ack-stub ')):
                    print(line)
            for line in [entry for entry in emu_stdout.splitlines()
                         if entry.startswith(('checkpoint isp-hccr ',
                                              'checkpoint isp-unmodeled-command '))][:17]:
                print(line)
            print(f'stock_after_{args.observe_cycles}=doorbell:{observed[0]:08x} '
                  f'status:{observed[1]:08x} mask:{observed[2]:08x} '
                  f'delay-calibration:{observed[3]:08x} '
                  f'unmasked-status:{observed[4]:08x} '
                  f'totals:{totals} final:{steps[-1]}')
            print('stock_scheduler_state=' + ' '.join(
                f'{address}:{value:08x}' for address, value in scheduler_state.items()))
            print('stock_interrupt_state=' + ' '.join(
                f'{address}:{value:08x}' for address, value in interrupt_state.items()))
            print(f'stock_cpu_interrupt_state={cpu_interrupt_state:08x}')
            print(f'stock_interrupt_table={interrupt_table:08x}')
            if secondary_pci_state is not None:
                print('stock_secondary_pci_state='
                      f'selector:{secondary_pci_state[0]:08x} '
                      f'data:{secondary_pci_state[1]:08x}')
            if args.explore_timer_clock or args.explore_timer_interrupt:
                assert totals['timer0-events'] > 0, totals
            if args.explore_qlogic_pci:
                assert scheduler_state['c00c0150'] >= 1, scheduler_state
                print('secondary_pci_discovery=PASS '
                      f'channels={scheduler_state["c00c0150"]} '
                      'mailbox=PENDING')
            if args.explore_timer_interrupt and not args.explore_qlogic_pci:
                assert totals['timer0-interrupts'] > 0, totals
                assert 'checkpoint stock-isr-ret ' in emu_stdout
                print(f'timer_interrupt_gate=PASS vector=82 handler=c0000418 '
                      f'deliveries={totals["timer0-interrupts"]} '
                      'fault=NONE completion=PENDING')
            elif args.explore_timer_clock and not args.explore_qlogic_pci:
                assert interrupt_state['ff008500'] & (1 << 12), interrupt_state


if __name__ == '__main__':
    main()
