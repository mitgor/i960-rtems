import sys
# decoded = PERM(stored ^ 0xc3); PERM swaps bit i <-> bit (i^6); involution
def perm(b):
    r=0
    for i in range(8):
        if (b>>i)&1: r|=1<<(i^6)
    return r
PERM=[perm(i) for i in range(256)]
def decode(data): return bytes(PERM[x^0xc3] for x in data)
if __name__=="__main__":
    src,out=sys.argv[1],sys.argv[2]
    off=int(sys.argv[3]) if len(sys.argv)>3 else 0
    d=open(src,'rb').read()
    open(out,'wb').write(decode(d[off:]))
    print("wrote",out)
