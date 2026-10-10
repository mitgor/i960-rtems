import sys
cipher=open(sys.argv[1],'rb').read()
cribs=[b"Mylex Corporation", b"DAC960 BIOS Version", b"DAC960 not responding",
       b"PCIR", b"Run Diagnostics", b"firmware checksum"]
def consistent_map(plain, seg):
    fwd={}; rev={}
    for p,c in zip(plain,seg):
        if p in fwd and fwd[p]!=c: return None
        if c in rev and rev[c]!=p: return None
        fwd[p]=c; rev[c]=p
    return fwd
for crib in cribs:
    L=len(crib); hits=0
    for off in range(len(cipher)-L):
        seg=cipher[off:off+L]
        m=consistent_map(crib,seg)
        if m is not None:
            # require the mapping to be non-trivial-collision: enough distinct pairs
            if len(m)>=len(set(crib))-1:
                hits+=1
                if hits<=3:
                    pairs=sorted(m.items())[:6]
                    print(f"CRIB {crib!r} @off {off}: map sample {[(chr(p),hex(c)) for p,c in pairs]}")
    print(f"  total consistent offsets for {crib!r}: {hits}")
