#!/usr/bin/env python3
"""Build an isolated myrs8f derivative from exact pinned Linux v6.8 sources."""
import hashlib
import json
import sys
from pathlib import Path

src, hdr, out = map(Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=False)
here = Path(__file__).resolve().parent
expected = json.loads((here.parent / "readimage/sources.json").read_text())
for path, key in ((src, "myrs.c"), (hdr, "myrs.h")):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected[key]:
        raise ValueError("unreviewed upstream source: " + key)
s = src.read_text()
anchor = "static struct attribute *myrs_shost_attrs[] = {"
if s.count(anchor) != 1:
    raise ValueError("upstream attribute anchor changed")
s = s.replace(anchor, (here / "unsupported_extension.c").read_text() +
              "\n" + anchor + "\n\t&dev_attr_stock_unsupported.attr,")
anchor = "cs = myrs_detect(dev, entry);"
if s.count(anchor) != 1:
    raise ValueError("upstream probe anchor changed")
s = s.replace(anchor,
    "if (strcmp(pci_name(dev),probe_bdf) || dev->vendor != 0x1069 || "
    "dev->device != 0x0050 || dev->subsystem_vendor != 0x1069 || "
    "dev->subsystem_device != 0x0054) return -ENODEV;\n\t" + anchor)
anchor = '.name\t\t= "myrs",'
if s.count(anchor) != 1:
    raise ValueError("upstream driver-name anchor changed")
s = s.replace(anchor, '.name\t\t= "myrs8f",\n\t.driver = { .suppress_bind_attrs = true },')
(out / "myrs8f.c").write_text(s)
(out / "myrs.h").write_bytes(hdr.read_bytes())
(out / "Makefile").write_text("obj-m += myrs8f.o\n")
