#!/usr/bin/env python3
"""Offline unpacking of the normalized DAC960 4.07-0-29 and 4.07-0-39 reference images.

Requires Info-ZIP unzip with method-6 (Implode) support. Never executes firmware.
Vendor binaries and disassemblies should remain outside the public repository.
"""
import argparse
import hashlib
import io
import json
import struct
import subprocess
import tempfile
import zipfile
import zlib
from pathlib import Path

RAW_SHA256 = 'af3df1e17f0ff8b31ceb1a375aa58976922db3a25c96e0acd3045ea6f61b22af'
OUT_SHA256 = '6d35598e082f72c83fcc6030e3b4788dfb6f7c334ada569f7e2a140a9195a3fe'
PROFILES = {
    RAW_SHA256: dict(version='4.07-0-39', output_sha256=OUT_SHA256,
                    compressed_size=167576, crc32=0x31d5040e),
    '8afaebf954bbbf31bba42f1156c76237c3e632b071f6b400d3f17fbcd9d8baa5':
        dict(version='4.07-0-29',
             output_sha256='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195',
             compressed_size=167565, crc32=0x8a9d7f6c),
}
BASE = 0xc0010000
ZIP_OFFSET = 0x7000


def inspect_archive(raw):
    profile = PROFILES.get(hashlib.sha256(raw).hexdigest())
    if profile is None:
        raise ValueError('unsupported normalized firmware hash')
    archive = raw[ZIP_OFFSET:]
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        entries = zf.infolist()
        if len(entries) != 1:
            raise ValueError('expected one embedded ZIP member')
        info = entries[0]
        if (info.filename, info.compress_type, info.file_size, info.compress_size, info.CRC) != (
                'ZIP1', 6, 304120, profile['compressed_size'], profile['crc32']):
            raise ValueError('unexpected embedded ZIP metadata')
    return archive, info


def verify_output(output, info, expected_hash=OUT_SHA256):
    if len(output) != info.file_size or zlib.crc32(output) != info.CRC:
        raise ValueError('unpacked size/CRC mismatch')
    if hashlib.sha256(output).hexdigest() != expected_hash:
        raise ValueError('unpacked hash mismatch')


def unpack(raw):
    archive, info = inspect_archive(raw)
    with tempfile.TemporaryDirectory(prefix='i960-unpack-') as tmp:
        path = Path(tmp) / 'embedded.zip'
        path.write_bytes(archive)
        result = subprocess.run(['unzip', '-p', str(path), 'ZIP1'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=30, check=False)
        if result.returncode:
            raise ValueError('unzip failed: ' + result.stderr.decode(errors='replace'))
        output = result.stdout
    digest = hashlib.sha256(raw).hexdigest()
    profile = PROFILES[digest]
    verify_output(output, info, profile['output_sha256'])
    dispatch = {f'{op:#04x}': f'{struct.unpack_from("<I", output, 0xf804 + 4*(op-1))[0]:#010x}'
                for op in [0x1c, 0x20, 0x21, 0x22, 0x2b]}
    return output, dict(reference_version=profile['version'], running_version='4.07-0-29',
                        raw_sha256=digest, embedded_zip_offset=ZIP_OFFSET,
                        compression_method=6, compressed_size=info.compress_size,
                        unpacked_size=len(output), crc32=f'{info.CRC:08x}',
                        unpacked_sha256=profile['output_sha256'], runtime_base=BASE,
                        runtime_entry=0xc004a2e0, dispatch=dispatch,
                        live_firmware_dump=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        output, manifest = unpack(args.raw.read_bytes())
        with args.output.open('xb') as stream:
            stream.write(output)
        print(json.dumps(manifest, indent=2))
    except (OSError, ValueError, subprocess.TimeoutExpired, zipfile.BadZipFile) as error:
        parser.exit(1, f'firmware unpack failed: {error}\n')
