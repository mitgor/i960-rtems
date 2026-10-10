import sys
cipher=open(sys.argv[1],'rb').read()
# clustered known matches (crib, offset) with the shared bijection
known=[(b"Mylex Corporation",18465),(b"DAC960 BIOS Version",18497),
       (b"DAC960 not responding",18553),(b"Run Diagnostics",18877),
       (b"firmware checksum",18921)]
fwd={}
ok=True
for crib,off in known:
    for i,p in enumerate(crib):
        c=cipher[off+i]
        if p in fwd and fwd[p]!=c:
            print("CONFLICT",chr(p),hex(fwd[p]),hex(c)); ok=False
        fwd[p]=c
print("pairs:",len(fwd),"conflicts:",not ok)
# test closed forms
def revbits(b):
    r=0
    for i in range(8): r=(r<<1)|((b>>i)&1)
    return r
RB=[revbits(i) for i in range(256)]
def nib(b): return ((b<<4)|(b>>4))&0xff
forms={
 "xor k":      lambda x,k: x^k,
 "revbits^k":  lambda x,k: RB[x]^k,
 "revbits(x^k)":lambda x,k: RB[x^k],
 "nib^k":      lambda x,k: nib(x)^k,
 "nib(x^k)":   lambda x,k: nib(x^k),
 "add k":      lambda x,k:(x+k)&0xff,
 "sub k":      lambda x,k:(x-k)&0xff,
 "(x^k) neg":  lambda x,k:(~(x^k))&0xff,
}
for name,fn in forms.items():
    for k in range(256):
        if all(fn(p,k)==c for p,c in fwd.items()):
            print(f"MATCH closed-form: {name} k={hex(k)}")
# print full map sorted
print("MAP:")
for p in sorted(fwd): print(f"  {chr(p)!r} {hex(p)} -> {hex(fwd[p])}")
