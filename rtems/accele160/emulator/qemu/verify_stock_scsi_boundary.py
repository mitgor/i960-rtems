#!/usr/bin/env python3
"""Verify the bounded stock SCSI INQUIRY no-completion observation."""
import argparse
import hashlib
import json
import re
from pathlib import Path

SLOT = re.compile(r'ring followup event=4 slot=4 dma=0x([0-9a-f]{8}) '
                  r'hex=([0-9a-f]{128})')
MODEL = re.compile(
    r'stock scsi model event=4 slot4=0x([0-9a-f]{8}) '
    r'status4=([0-9a-f]{16}) sense-sha256=([0-9a-f]{64}) '
    r'data-sha256=([0-9a-f]{64}) ring-cursor=0x([0-9a-f]{8}) '
    r'dma1-status=0x([0-9a-f]{8}) dma1-control=0x([0-9a-f]{8}) '
    r'dma1-pointer=0x([0-9a-f]{8}) outbound=0x([0-9a-f]{8}) '
    r'no-guest-copy=1')
ISP = re.compile(r'stock scsi isp phase=(before|after) '
                 r'producer=0x([0-9a-f]{8}) response=0x([0-9a-f]{8}) '
                 r'control=0x([0-9a-f]{8}) consumer=0x([0-9a-f]{8})')
IOCB = re.compile(r'stock scsi isp phase=(before|after) entry=30 '
                  r'base=0x([0-9a-f]{8}) hex=([0-9a-f]{128})')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    qemu = (a.run / 'qemu.log').read_text()
    slots, models = SLOT.findall(qemu), MODEL.findall(qemu)
    assert len(slots) == len(models) == 1
    slot_dma, slot_hex = slots[0]
    slot = bytes.fromhex(slot_hex)
    assert len(slot) == 64 and slot[2:8] == bytes.fromhex('021024000000')
    assert slot[16:19] == b'\0\0\0' and slot[20] == 14 and slot[21] == 6
    assert slot[22:28] == bytes.fromhex('120000002400')
    assert slot[40:44] == bytes.fromhex('24000000')
    (word0, status, sense_sha, data_sha, cursor, dma_status,
     dma_control, dma_pointer, outbound) = models[0]
    assert word0 == '00000000' and status == '0000000000000000'
    assert sense_sha == hashlib.sha256(bytes(16)).hexdigest()
    assert data_sha == hashlib.sha256(bytes(36)).hexdigest()
    assert int(cursor, 16) == int(slot_dma, 16) + 64
    assert dma_status == dma_control == outbound == '00000000'
    assert 'stock scsi model sense-hex=' + '00' * 16 in qemu
    assert 'data-hex=' + '00' * 36 in qemu
    assert qemu.count('lp reset requested; unmodeled') >= 1
    receipt = {
        'gate': 'PASS', 'observation': 'bounded_no_completion',
        'slot_sha256': hashlib.sha256(slot).hexdigest(),
        'request_id': int.from_bytes(slot[:2], 'little'),
        'sense_dma': f'0x{int.from_bytes(slot[8:16], "little"):08x}',
        'data_dma': f'0x{int.from_bytes(slot[32:40], "little"):08x}',
        'status_hex': '0000000000000000', 'sense_sha256': sense_sha,
        'data_sha256': data_sha, 'outbound': 0,
        'guest_reset_requested': True, 'guest_copy': False,
        'model_steps': 20_000_000,
        'cause_of_no_completion': 'unresolved',
        'physical_card_tested': False, 'safe_to_flash': False,
    }
    isp = {phase: (int(producer, 16), int(response, 16),
                   int(control, 16), int(consumer, 16))
           for phase, producer, response, control, consumer in ISP.findall(qemu)}
    iocb = {phase: (int(base, 16), bytes.fromhex(raw))
            for phase, base, raw in IOCB.findall(qemu)}
    if isp or iocb:
        assert set(isp) == set(iocb) == {'before', 'after'}
        assert isp['before'] == (30, 15, 0xc0600d00, 15)
        assert isp['after'] == (31, 15, 0xc0600d00, 15)
        assert iocb['before'][0] == iocb['after'][0] == 0xc0601570
        request = iocb['after'][1]
        assert request[0] == 9 and request[1] == 1
        assert request[20] == 0x12
        assert int.from_bytes(request[40:48], 'little') == int.from_bytes(slot[32:40], 'little')
        receipt['isp_request_posted'] = True
        receipt['isp_request_index_before'] = 30
        receipt['isp_request_index_after'] = 31
        receipt['isp_response_index_after'] = 15
        receipt['isp_response_consumer_after'] = 15
        receipt['isp_request_entry30_sha256'] = hashlib.sha256(request).hexdigest()
        receipt['first_unmodeled_transition'] = 'ISP response for newly posted type-9 INQUIRY IOCB'
    a.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('stock_scsi_boundary=PASS no_completion_observed=True')


if __name__ == '__main__':
    main()
