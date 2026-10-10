import sys
files = sys.argv[1:]
def revbits(b):
    r=0
    for i in range(8):
        r=(r<<1)|((b>>i)&1)
    return r
RB=[revbits(i) for i in range(256)]
def show(name,data,n=64):
    print("===",name,"len",len(data),"===")
    transforms={
      "raw": data[:n],
      "xorC3": bytes(x^0xc3 for x in data[:n]),
      "revbits": bytes(RB[x] for x in data[:n]),
      "revbits+xorC3": bytes(RB[x]^0xc3 for x in data[:n]),
      "xorC3+revbits": bytes(RB[x^0xc3] for x in data[:n]),
    }
    for k,v in transforms.items():
        asc="".join(chr(c) if 32<=c<127 else "." for c in v)
        print(f"  {k:16} {asc}")
for f in files:
    show(f, open(f,'rb').read())
