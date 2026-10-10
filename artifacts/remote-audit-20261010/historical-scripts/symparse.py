import sys,re
d=open(sys.argv[1],'rb').read()
# find symtab: scan for plausible [len][name ascii][6 bytes] records in tail
best=[]
start=0x59000
i=start
ents=[]
while i < len(d)-8:
    L=d[i]
    if 3<=L<=40 and i+1+L+6<=len(d):
        name=d[i+1:i+1+L]
        if all(32<=c<127 for c in name) and (name[0:1]==b'_' or name[0:1].isalpha()):
            off=int.from_bytes(d[i+1+L:i+1+L+2],'little')
            seg=int.from_bytes(d[i+1+L+2:i+1+L+4],'little')
            fileoff=0x1800+seg*16+off
            ents.append((name.decode(),off,seg,fileoff))
            i+=1+L+6
            continue
    i+=1
want=sys.argv[2:] if len(sys.argv)>2 else None
for name,off,seg,fo in ents:
    if want is None or any(w.lower() in name.lower() for w in want):
        print(f"{name:30} off={off:#06x} seg={seg:#06x} file={fo:#08x}")
