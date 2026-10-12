ENTRY(_start)
SECTIONS {
 . = 0xc0f8c000;
 _engine_code_start = .;
 .engine_text : { *engine_gate.o(.text* .rodata*) *engine_sha.o(.text* .rodata*) . = ALIGN(16); }
 _engine_code_end = .;
 ASSERT(. <= 0xc0f94000, "engine gate exceeds protected window")
 /* Loaded with the initial bounded upload, outside the BSS clear interval. */
 . = 0xc0f94000;
 _upload_code_start = .;
 .upload_text : { *rtems_sem*.o(.text* .rodata*) *score_coremutex*.o(.text* .rodata*) *score_coresem*.o(.text* .rodata*) *score_threadq*.o(.text* .rodata*) */doom_heap_core.o(.text* .rodata*) */doom_heap_libc.o(.text* .rodata*) */doom_heap_proof.o(.text* .rodata*) */doom_heap_shared.o(.text* .rodata*) */doom_runtime.o(.text* .rodata*) */doom_wad_core.o(.text* .rodata*) *upload.o(.text* .rodata*) *upload_arena.o(.text* .rodata*) *upload_image.o(.text* .rodata*) *upload_protect.o(.text* .rodata*) . = ALIGN(16); }
 _upload_code_end = .;
 ASSERT(. <= 0xc0f9bff0, "resident upload code overlaps upper guard")
 . = 0xc0f2c000;
 .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(16); }
 ASSERT(. <= 0xc0f4c000, "code exceeds immutable 128 KiB")
 . = 0xc0f4c010;
 .data : { *(.data*) . = ALIGN(16); }
 __bss_start = .;
 .bss : { *(.bss*) *(COMMON) . = ALIGN(16); }
 __bss_end = .;
 ASSERT(. <= 0xc0f8c000, "mutable runtime overlaps resident upload code")
}
