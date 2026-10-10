#!/usr/bin/env python3
"""Emit the pinned programming design. Does not send any hardware command."""
from pathlib import Path
import hashlib,json,struct,zlib
ROOT=Path(__file__).resolve().parents[2]

def make_plan():
    stock=(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
    candidate=(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin').read_bytes()
    sha=lambda b:hashlib.sha256(b).hexdigest()
    assert sha(stock)=='43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93'
    assert sha(candidate)=='a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'
    descriptor=stock[0x79c00:0x79d60]
    assert descriptor==candidate[0x79c00:0x79d60]
    assert descriptor[:4]==b'XLYM' and descriptor[10]==5
    assert stock[0x7c000:]==candidate[0x7c000:]
    records=[]
    for i in range(descriptor[10]):
        entry=descriptor[32+64*i:32+64*(i+1)]
        offset,length=struct.unpack_from('<II',entry)
        records.append(dict(type=entry[8],offset=offset,length=length))
    # Example transaction ID=1. Actual submission needs a fresh matched tag.
    mailbox=bytes([0x2b,1,1,0])+bytes(9)
    assert len(mailbox)==13 and mailbox[3]==0
    return dict(design_only=True,flash_ready=False,hardware_programming_executed=False,
                stock_sha256=sha(stock),candidate_sha256=sha(candidate),
                candidate_crc32=f'{zlib.crc32(candidate):08x}',
                staging_cpu_source='C1F2C000',requires_explicit_dcache_invalidation=True,
                descriptor=dict(offset=0x79c00,length=0x160,sha256=sha(descriptor),
                                update_counter=struct.unpack_from('<H',descriptor,8)[0],
                                policy='preserve exact stock bytes; custom full-image route',records=records),
                program_mailbox_example_id_1=mailbox.hex(),
                program_opcode='2b',subcommand=1,bootblock_flag=0,
                erase_rewrite_range=[0,0x7c000],preserved_bootblock_range=[0x7c000,0x80000],
                required_pre_program_dispatch='C001FE98 (stock unsupported handler)',
                temporary_ram_callbacks_must_be_removed=True,
                program_frees_staging_and_clears_pointer=True,
                next_20_allocates_and_byte_copies_flash=True,
                fresh_readback_expected_sha256=sha(candidate),
                prohibit_retry_after_uncertain_program_completion=True,
                recovery_testing='excluded by user')

if __name__=='__main__': print(json.dumps(make_plan(),indent=2))
