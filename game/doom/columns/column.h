/* Ordinary high/low columns only. Fuzz and translated columns stay unchanged. */
#ifndef DOOM_COLUMN_KERNEL_H
#define DOOM_COLUMN_KERNEL_H
struct doom_column_job {
 unsigned char *dst, *dst2;
 const unsigned char *source, *map;
 unsigned frac, step, count;
 int post_length;
};
void doom_column_c(const struct doom_column_job *);
void doom_column_asm(const struct doom_column_job *);
extern unsigned doom_column_mode, doom_column_cases;
void doom_column_begin(unsigned);
int doom_column_selftest(void);
#endif
