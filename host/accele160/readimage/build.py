#!/usr/bin/env python3
"""Generate a narrowly gated myrs derivative from pinned upstream source."""
import hashlib,json,sys
from pathlib import Path
src,hdr,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
s=src.read_text()
# Require reviewed exact input hashes (Linux v6.8).
expected=json.loads((Path(__file__).parent/'sources.json').read_text())
for p,key in [(src,'myrs.c'),(hdr,'myrs.h')]:
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected[key]:raise ValueError('unreviewed upstream source')
s=s.replace('static struct attribute *myrs_shost_attrs[] = {',(Path(__file__).parent/'extension.c').read_text()+'\nstatic struct attribute *myrs_shost_attrs[] = {\n\t&dev_attr_stock_descriptor.attr,\n\t&dev_attr_stock_controller.attr,')
s=s.replace('cs = myrs_detect(dev, entry);','if (strcmp(pci_name(dev),read_bdf) || dev->vendor != 0x1069 || dev->device != 0x0050 || dev->subsystem_vendor != 0x1069 || dev->subsystem_device != 0x0054) return -ENODEV;\n\tcs = myrs_detect(dev, entry);')
s=s.replace('.name\t\t= "myrs",','.name\t\t= "myrsread",\n\t.driver = { .suppress_bind_attrs = true },')
(out/'myrsread.c').write_text(s);(out/'myrs.h').write_bytes(hdr.read_bytes());(out/'Makefile').write_text('obj-m += myrsread.o\n')
