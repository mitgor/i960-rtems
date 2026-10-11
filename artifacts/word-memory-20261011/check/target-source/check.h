#ifndef I960_MEMORY_CHECK_H
#define I960_MEMORY_CHECK_H
/* Each batch tests one length/source offset against all destination offsets.
 * Exact same byte-reference checks run natively and in the bounded RTEMS task.
 */
#define MEMORY_LENGTHS 33u
#define MEMORY_BATCHES (MEMORY_LENGTHS*8u)
unsigned int memory_check_batch(unsigned int batch);
#endif
