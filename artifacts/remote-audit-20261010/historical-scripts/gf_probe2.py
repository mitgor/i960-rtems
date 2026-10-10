import sys
def revbits(b):
    r=0
    for i in range(8): r=(r<<1)|((b>>i)&1)
    return r
RB=[revbits(i) for i in range(256)]
TR={
 "raw": lambda d: d,
 "xorC3": lambda d: bytes(x^0xc3 for x in d),
 "revbits": lambda d: bytes(RB[x] for x in d),
 "revbits+xorC3": lambda d: bytes(RB[x]^0xc3 for x in d),
}
def asc(v): return "".join(chr(c) if 32<=c<127 else "." for c in v)
for f in sys.argv[1:]:
    d=open(f,'rb').read()
    print("######",f)
    # full header region first 128 under revbits
    print(" HDR revbits   :",asc(TR['revbits'](d[:128])))
    print(" HDR xorC3     :",asc(TR['xorC3'](d[:128])))
    for off in (504,508,512,516,520):
        seg=d[off:off+32]
        print(f"  off {off}:")
        for k,fn in TR.items():
            print(f"    {k:14}",fn(seg).hex(),asc(fn(seg)))
