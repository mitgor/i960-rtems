#ifndef LOADRUN_POLICY_H
#define LOADRUN_POLICY_H
#define LOAD_MAX 0x73060u
#define LOAD_RESULT_ADDRESS 0xc0fac280u
#define LOAD_RESULT_OFFSET 0x80280u
#define LOAD_RESULT_SIZE 16u
static int load_valid(unsigned int size, unsigned int entry)
{
    return size && size <= LOAD_MAX && !(size & 3) && !(entry & 3) && entry < size;
}
static int load_upload_allowed(unsigned int count,unsigned int offset,
                               unsigned int size,int verified,int armed)
{
    if (!verified || !armed || !count || (count&3) || count>0xf000u) return 0;
    return (offset==LOAD_RESULT_OFFSET && count==LOAD_RESULT_SIZE) ||
           (!(offset&3) && count<=size && offset<=size-count);
}
#endif
