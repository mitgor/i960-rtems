import sys,os
def perm(b):
    r=0
    for i in range(8):
        if (b>>i)&1: r|=1<<(i^6)
    return r
PERM=[perm(i) for i in range(256)]
def decode(data): return bytes(PERM[x^0xc3] for x in data)
base=sys.argv[1]; out=sys.argv[2]
os.makedirs(out,exist_ok=True)
def rd(f): return open(os.path.join(base,f),'rb').read()
# EXE: no container header
open(os.path.join(out,"DAC960FL.EXE"),'wb').write(decode(rd("DAC960FL.EXE")))
# IMG files: 512-byte MIMG container header then body
for src,dst in [("BGJ41041.IMG","BGJ41041.rom"),("407t39b0.img","407t39b0.bin"),("FWPJBBLK.IMG","FWPJBBLK.bin")]:
    full=decode(rd(src))
    open(os.path.join(out,src+".full"),'wb').write(full)   # incl 512 MIMG header
    open(os.path.join(out,dst),'wb').write(full[512:])      # raw image body
print("done")
