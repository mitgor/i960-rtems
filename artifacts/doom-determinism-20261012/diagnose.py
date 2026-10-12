import pathlib,subprocess,os,json
r=pathlib.Path('/home/mit/i960-doom-determinism-20261012')
for frame,x,y in [(497,170,112),(1426,192,117),(1817,204,154)]:
 script=f'set pagination off\nset confirm off\nbreak DG_DrawFrame if frames == {frame-1}\nrun\nbreak R_DrawMaskedColumn if dc_x == {x}\ncontinue\n'
 # Break at actual colfunc dispatch, avoiding other posts in this column.
 script=f"""set pagination off
set confirm off
break DG_DrawFrame if frames == {frame-1}
run
break r_things.c:374 if dc_x == {x} && dc_yl <= {y} && dc_yh >= {y}
continue
printf "frame=%u gametic=%d x=%d yl=%d yh=%d length=%d top=%d\\n", frames, gametic, dc_x, dc_yl, dc_yh, column->length,column->topdelta
printf "sample frac=%d index=%d wrapped=%d source=%p\\n", dc_texturemid+({y}-centery)*dc_iscale, (dc_texturemid+({y}-centery)*dc_iscale)>>16, ((dc_texturemid+({y}-centery)*dc_iscale)>>16)&127, dc_source
bt 4
quit
"""
 (r/f'diagnose-{frame}.gdb').write_text(script)
 with (r/f'diagnose-{frame}.log').open('w') as f:
  subprocess.run(['gdb','-batch','-x',str(r/f'diagnose-{frame}.gdb'),'--args',str(r/'before/host32/doom-profile'),'-iwad','/home/mit/i960-doom-m1-eziNKY/freedoom-0.13.0/freedoom1.wad','-mb','6','-nosound','-timedemo','demo1'],cwd=r/'before-1',env=dict(os.environ,HOME=str(r/'before-1')),stdout=f,stderr=f,check=True)
 print((r/f'diagnose-{frame}.log').read_text()[-1800:])
