#!/usr/bin/env python3
"""Pinned static QLogic dependencies. No live pointer traversal or ownership claim."""
import hashlib,json,sys
from pathlib import Path
from firmware_audit import RUNTIME
ANCHORS = {'context_pointer': ('0xc006ad40', '7400908c908024700034218c000d60c010392092c85b3ec0'),
 'register_map': ('0xc006b0b0', 'dc03a08c90008570003484908c4b38c000500484'),
 'request_base': ('0xc006ae18',
                  '0d4ea9590034bc887a4e38c00074ad8cf00d60c04ca0f18a4ea0f18a34a0a9920c4ea159'),
 'response_base': ('0xc006ae38',
                   '0c4ea15944a0a9920034a58cf04d60c050a0f18a3ca0a19252a0f18a48a0a192'),
 'request_ring_full': ('0xc0070614',
                       '4c20a1883820a9904e20b1880149ad591450a0599440a5583480a53d2820a1904c20a9883820b1907820a5881550a8590189b5594e20a18a4e20a1889580ad580c00ad3d001e805c0000000a'),
 'request_publish': ('0xc0070a98', '2820a9904c20a188011e805c7860b5887860a58a'),
 'response_irq': ('0xc006ef88',
                  '286021900a20a188022f055a1016305c6c000010c020a1880cde9159c020918a580200097a20a988080000081416a85c7a20a188f81fad3d0616805c5060a18a28090009'),
 'response_consume': ('0xc006f8f4',
                      '0c392890c85b3ec05060a9885260a1889520055a28604990d0050012ff00588c4860a1900120a580'),
 'pending_enqueue': ('0xc0070ad0',
                     '1039a090c85b3ec03020ad900c60053d2c208d920800000810608d9230208d921060f492'),
 'mailbox_publish': ('0xc006bd8c',
                     '00d0a1887060a9887060a18a00d0a1880030e88c0050000020a0a28ac060a188c060e98a')}

def audit(runtime):
    if hashlib.sha256(runtime).hexdigest()!=RUNTIME:raise ValueError('runtime identity')
    for name,(address,hexbytes) in ANCHORS.items():
        off=int(address,16)-0xc0010000
        if runtime[off:off+len(bytes.fromhex(hexbytes))]!=bytes.fromhex(hexbytes):raise ValueError(name)
    return dict(runtime_sha256=RUNTIME,anchors=ANCHORS,
      context_pointer='0xc03e5bc8',channel0_context='0xc0600d00',
      request_storage='0xc0600df0..0xc0604def',response_storage='0xc0604df0..0xc0606def',
      size_basis='profile16 corroborated context capacities: 256/128 entries',
      all_callers_audited=False,live_queue_state_observed=False,memory_reclaimable=False)
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1]).read_bytes()),indent=2))
