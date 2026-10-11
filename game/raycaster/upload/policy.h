#ifndef QUIET_UPLOAD_POLICY_H
#define QUIET_UPLOAD_POLICY_H
#define QUIET_ADDRESS 0xc004cec0u
#define QUIET_OFFSET (QUIET_ADDRESS-STAGING_BASE)
static int quiet_read_allowed(unsigned int n,unsigned int off,int verified,int armed)
{
    if(!verified || !armed) return 0;
    return (off==QUIET_OFFSET && n==80) ||
           (off==0xc011e22cu-STAGING_BASE && n==4) ||
           (off==0xc0110860u-STAGING_BASE && n==8) ||
           (off==0xc000a2a0u-STAGING_BASE && n==256) ||
           (off==0xc000a120u-STAGING_BASE && n==104);
}
static int quiet_write_allowed(unsigned int n,unsigned int off,int verified,int armed)
{
    return verified && armed && off==QUIET_OFFSET && n==4;
}
#endif
