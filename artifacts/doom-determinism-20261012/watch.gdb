set pagination off
set confirm off
set breakpoint pending on
break DG_DrawFrame if frames == 496
run
watch -l I_VideoBuffer[112*320+170]
commands
silent
printf "pixel=%d gametic=%d\n", I_VideoBuffer[112*320+170], gametic
bt 5
info locals
printf "dc x=%d yl=%d yh=%d source=%p\n", dc_x, dc_yl, dc_yh, dc_source
continue
end
break DG_DrawFrame if frames == 497
commands
quit
end
continue
