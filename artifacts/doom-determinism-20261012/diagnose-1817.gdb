set pagination off
set confirm off
break DG_DrawFrame if frames == 1816
run
break r_things.c:374 if dc_x == 204 && dc_yl <= 154 && dc_yh >= 154
continue
printf "frame=%u gametic=%d x=%d yl=%d yh=%d length=%d top=%d\n", frames, gametic, dc_x, dc_yl, dc_yh, column->length,column->topdelta
printf "sample frac=%d index=%d wrapped=%d source=%p\n", dc_texturemid+(154-centery)*dc_iscale, (dc_texturemid+(154-centery)*dc_iscale)>>16, ((dc_texturemid+(154-centery)*dc_iscale)>>16)&127, dc_source
bt 4
quit
