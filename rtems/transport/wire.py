"""RIO1: BIO1 framing at 448 KiB, with guarded RTEMS workspace at 128..448 KiB."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bio_original',ROOT/'host/loadrun/buffer_io.py');bio=importlib.util.module_from_spec(spec);spec.loader.exec_module(bio)
bio.OFFSET=0x70000;bio.BASE=0xc0f9c000;bio.IMAGE_SIZE=bio.OFFSET+bio.SIZE;bio.MAGIC=0x314f4952
MUTABLE_START=0x20010;MUTABLE_END=0x6fff0

def prepare(code,incoming=b'',sequence=1):
 if len(code)>MUTABLE_END:raise ValueError('kernel overlaps workspace guard')
 image=bytearray(bio.prepare(code,incoming,bio.OUTPUT_MAX,sequence))
 image[0x20000:MUTABLE_START]=b'\xa7'*16
 image[MUTABLE_END:bio.OFFSET]=b'\x7a'*16
 return bytes(image)

def response(before,after):
 if len(before)!=524288 or len(after)!=524288:raise ValueError('full image required')
 norm=bytearray(after);norm[MUTABLE_START:MUTABLE_END]=before[MUTABLE_START:MUTABLE_END]
 return bio.response(before,norm)

def block(incoming,sequence):return prepare(b'\0'*4,incoming,sequence)[bio.OFFSET:]
