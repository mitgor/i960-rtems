import sys
src, off, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d=open(src,'rb').read()[off:]
open(out,'wb').write(bytes(x^0xc3 for x in d))
print("wrote",out,len(d),"bytes from",src,"off",off)
