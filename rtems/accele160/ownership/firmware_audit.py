#!/usr/bin/env python3
"""Pin/decompress accepted firmware and verify traced engine dependency anchors."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'host/accele160/startup'))
from analyze import analyze
from verify_full_dump import unpack
SHA='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
RUNTIME='09e84895223627edeff8f1a6902d2a9a573c2c3e7769a5ea16caaa32cf07e3db'
def audit(flash):
    if hashlib.sha256(flash).hexdigest()!=SHA:raise ValueError('unrecognized firmware')
    a=analyze(flash);region=next(x for x in a['regions'] if x['selector']==2)
    runtime,_=unpack(flash[a['runtime']['flash_zip_offset']:region['offset']+region['size']-0xa0])
    if hashlib.sha256(runtime).hexdigest()!=RUNTIME:raise ValueError('runtime identity')
    anchors={
      'qlogic_1016_dispatch':(0xc005182c,'0030e88c161000009842a73a'),
      'qlogic_1016_init_call':(0xc0051af8,'28cf0109'),
      'qlogic_1016_init_branch':(0xc006ea20,'70feff08'),
      'qlogic_callback_install':(0xc006e8cc,'0034a492284b38c00034ac92244b38c0'),
      'dma1_descriptor_register':(0xc004f6d4,'0030208c50140000'),
      'dma1_submit_and_enable':(0xc004f6e4,'0010a9920034a192f0ffffff'),
      'aau_next_descriptor_register':(0xc00822b0,'0030a88c0c180000'),
      'aau_submit_and_enable':(0xc00822c0,'005085920074b592f4ffffff'),
      'aau_completion_control':(0xc0082550,'0030f09200180000'),
      'channel_stride':(0xc0053ba0,'dc03988c'),
      'channel_vendor_store':(0xc0053bb0,'0034818a784e38c0'),
      'channel_device_store':(0xc0053bbc,'0034a18a7a4e38c0'),
      'channel_script_pointer_store':(0xc005e7b0,'2ca08d92'),
      'secondary_config_selector':(0xc0053d58,'0030a08ca8120000'),
      'primary_config_selector':(0xc0053d94,'0030a08ca4120000')}
    result={}
    for name,(address,hexbytes) in anchors.items():
        data=bytes.fromhex(hexbytes);off=address-0xc0010000
        if runtime[off:off+len(data)]!=data:raise ValueError('anchor changed: '+name)
        result[name]=dict(address=hex(address),bytes=hexbytes)
    return dict(firmware_sha256=SHA,runtime_sha256=RUNTIME,anchors=result,
      dma1_descriptor_pointer='0xc0494a20',aau_queue=['0xc049b7cc','0xc049b7d0','0xc049b7d4'],
      channel_stride='0x3dc',channel0_vendor_device='0xc0384e78',channel0_revision='0xc0384e7c',
      channel0_core_register_mapping='0xc0384b8c',channel0_pci_register_bar='0xc0384b90',
      channel0_pci_script_bar='0xc0384b94',channel0_core_script_mapping='0xc0384b98',
      symbios_alternate_script_start_offset='0x2c',qlogic_setup='0xc006e890',qlogic_callback_table='0xc0384b24..0xc0384b64',live_chip_identity_proven=False,all_callers_audited=False)
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1]).read_bytes()),indent=2))
