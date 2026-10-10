import sys
d=open(sys.argv[1],'rb').read()
# patterns that store an immediate opcode into mailbox byte0:
#  26 c6 07 XX      movb XX, es:(bx)
#  c6 07 XX         movb XX, (bx)
#  26 c6 47 00 XX   movb XX, es:0(bx)
#  c6 46 XX YY      movb YY,(bp+XX)   -- too generic, skip
pats=[]
for op in (0x20,0x21,0x22):
    pats.append((bytes([0x26,0xc6,0x07,op]),f"movb ${op:#x},es:(bx)"))
    pats.append((bytes([0xc6,0x07,op]),f"movb ${op:#x},(bx)"))
    pats.append((bytes([0x26,0xc6,0x47,0x00,op]),f"movb ${op:#x},es:0(bx)"))
    pats.append((bytes([0xb0,op]),f"mov al,{op:#x}"))
for pat,desc in pats:
    i=0; hits=[]
    while True:
        j=d.find(pat,i)
        if j<0: break
        hits.append(j); i=j+1
    if hits and not desc.startswith("mov al"):
        print(f"{desc:24} -> {[hex(h) for h in hits[:12]]}")
# also report mov al occurrences count only (too many)
