"""Single-flight browser queue adapter. No retries after any uncertain request."""
import gzip
import json
import re
import secrets
import struct
import sys
import time
from pathlib import Path
from combined.model import Model, request, replace, base
from host import Native, request as ray_request

GAME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GAME / 'transfer'))
from commands import parse


def expected_commands(sequence, mask):
    table = (0xc001f9bc - 0xc0f2c000) & 0xffffffff
    quiet = (0xc004cec0 - 0xc0f2c000) & 0xffffffff
    commands = ([(0x20, 80, quiet)] * 2 if sequence > 1 else [])
    commands += [(0x21, 0x3060, 0x70000)]
    if sequence == 1:
        commands += [(0x21, 4, table)] + [(0x20, 4, table)] * 2 + [(0x6f, 0, 0)]
        for address, size in [(0xc011e22c, 4), (0xc0110860, 8), (0xc000a2a0, 256), (0xc000a120, 104), (0xc004cec0, 80)]:
            commands += [(0x20, size, (address - 0xc0f2c000) & 0xffffffff)] * 2
        commands += [(0x21, 4, quiet), (0x6f, 0, 0)] + [(0x20, 80, quiet)] * 2
    commands += [(0x21, 16, 0x80280), (0x21, 4, table)] + [(0x20, 4, table)] * 2
    commands += [(0x6f, 0, 0)] + [(0x20, 4, table)] * 2 + [(0x20, 16, 0x80280)] * 2
    commands += [(0x20, 64, 0x70000 + 0x1050)] * 2
    for slot in range(2):
        if mask & (1 << slot):
            commands += [(0x20, base.SIZE, base.OFFSET + slot * base.SIZE)] * 2
    commands += [(0x20, min(61440, 524288 - off), off) for _ in range(2) for off in range(0, 524288, 61440)]
    return commands


class AuditedQueue:
    def __init__(self, board, output, epoch=None):
        if not __debug__:
            raise RuntimeError('validation requires Python without -O')
        self.board, self.output = board, Path(output)
        self.model = Model()
        self.epoch = epoch if epoch is not None else secrets.randbelow(0xffff0000) + 1
        self.failed = False
        self.closed = False
        self.frame = None
        self.rows = []
        self.requests = []
        self.commands = gzip.open(self.output / 'commands.jsonl.gz', 'wt')
        self.snapshots = gzip.open(self.output / 'full-audits.bin.gz', 'wb', compresslevel=1)
        (self.output / 'queue-test.json').write_text(json.dumps(dict(queue=True, epoch=self.epoch, pipeline='combined', full_audit_gzip_level=1)) + '\n')

    def transact(self, label, data):
        if self.failed or self.closed:
            raise RuntimeError('session is closed or faulted; no retry permitted')
        try:
            # Record intent before execution, including a possibly incomplete last call.
            self.requests.append((label, data.hex()))
            (self.output / 'browser-requests.json').write_text(json.dumps(self.requests) + '\n')
            start, cpu = time.monotonic_ns(), time.process_time_ns()
            reply = self.board.step(data)
            end, cpu_end = time.monotonic_ns(), time.process_time_ns()
            seq = self.board.sequence
            assert reply == self.model.step(data, seq)
            assert struct.unpack_from('<I', reply, 8)[0] == 0
            oracle_end = time.monotonic_ns()
            debug = self.board.debugfs
            first = (debug / 'payload-after-a5.bin').read_bytes()
            second = (debug / 'payload-after-5a.bin').read_bytes()
            assert len(first) == 524288 and first == second
            snapshot_end = time.monotonic_ns()
            self.snapshots.write(first)
            self.snapshots.flush()
            archive_end = time.monotonic_ns()
            assert first[base.OFFSET:base.OFFSET + 2 * base.SIZE] == b''.join(self.model.slots)
            assert (debug / 'frame-descriptor-a5.bin').read_bytes() == reply == (debug / 'frame-descriptor-5a.bin').read_bytes()
            slots = {}
            for slot in range(2):
                if self.model.mask & (1 << slot):
                    one = (debug / f'frame-slot{slot}-a5.bin').read_bytes()
                    two = (debug / f'frame-slot{slot}-5a.bin').read_bytes()
                    assert one == two == self.model.slots[slot]
                    base.validate(one, self.model.epoch, self.model.gen[slot], slot)
                    slots[str(slot)] = one.hex()
                    if slot == 0:
                        self.frame = one[64:4928]
            slots_end = time.monotonic_ns()
            log = (debug / 'result.txt').read_text()
            commands = parse(log)
            assert [(c['op'], c['count'], c['offset']) for c in commands] == expected_commands(seq, self.model.mask)
            match = re.search(r'RAYPROFILE seq=(\d+) upload=(\d+) arm=(\d+) execute=(\d+) verify=(\d+) audit=(\d+) total=(\d+) bytes=(\d+)', log)
            assert match
            row = dict(zip(['sequence', 'upload_ns', 'arm_ns', 'execute_ns', 'verify_ns', 'audit_ns', 'kernel_ns', 'audit_bytes'], map(int, match.groups())))
            q = re.search(r'FQPROFILE seq=(\d+) mask=(\d+) targeted_ns=(\d+) full_audit_ns=(\d+)', log)
            assert q
            qs, mask, target, full = map(int, q.groups())
            assert qs == row['sequence'] == seq and mask == self.model.mask and row['audit_bytes'] == 524288
            assert target + full <= row['audit_ns']
            assert sum(row[k] for k in ['upload_ns', 'arm_ns', 'execute_ns', 'verify_ns', 'audit_ns']) == row['kernel_ns']
            log_end = time.monotonic_ns()
            row.update(host_oracle_ns=oracle_end-end, host_snapshot_read_ns=snapshot_end-oracle_end, host_archive_ns=archive_end-snapshot_end, host_slot_check_ns=slots_end-archive_end, host_log_check_ns=log_end-slots_end)
            row.update(label=label, wall_ns=end-start, cpu_ns=cpu_end-cpu, mask=mask, targeted_ns=target, full_audit_ns=full)
            self.rows.append(row)
            self.commands.write(json.dumps(dict(sequence=seq, commands=commands, log=log, slots=slots)) + '\n')
            self.commands.flush()
            (self.output / 'phases.json').write_text(json.dumps(self.rows, indent=2) + '\n')
        except BaseException:
            self.failed = True
            # Preserve raw debug evidence before CLOSE replaces its result log.
            failure = self.output / f'browser-failure-{self.board.sequence:06d}'
            failure.mkdir(exist_ok=True)
            for source in self.board.debugfs.iterdir():
                try:
                    if source.is_file():
                        (failure / source.name).write_bytes(source.read_bytes())
                except OSError:
                    pass
            raise

    def step(self, data):
        w = struct.unpack('<8I', data)
        if w == struct.unpack('<8I', ray_request(op=0, columns=0)):
            if self.model.mask:
                self.transact('browser-reset-ack', request(2, self.epoch, 0, self.model.gen[0]))
            if self.model.epoch:
                if self.epoch == 0xffffffff:
                    raise RuntimeError('epoch exhausted')
                self.epoch += 1
            self.transact('browser-init', request(0, self.epoch))
            # Match the original reset reply without advancing the renderer.
            native = Native()
            return native.step(data)
        if data != ray_request(keys=w[3]) or w[3] > 15:
            raise ValueError('browser accepts only full bounded frames')
        if self.model.last == 0xffffffff:
            raise RuntimeError('generation exhausted')
        if self.model.mask:
            req = replace(self.epoch, 0, self.model.last + 1, self.model.gen[0], w[3])
            label = 'browser-combined'
        else:
            req = request(1, self.epoch, 0, self.model.last + 1, w[3])
            label = 'browser-publish'
        self.transact(label, req)
        return self.frame

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            return self.board.close()
        finally:
            self.commands.close()
            self.snapshots.close()


def open_backend(payload, module, output):
    if not __debug__:
        raise RuntimeError('validation requires Python without -O')
    from host import card_backend
    board = card_backend(payload, module, output)
    try:
        return AuditedQueue(board, output)
    except BaseException:
        board.close()
        raise
