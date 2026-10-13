/* Aggregate acceptance budget, independent of each engine/read deadline. */
#ifdef I960_DOOM_STARTUP
#if !defined(I960_RESIDENT_NET) || !defined(I960_OWNED_MIB) || I960_OWNED_MIB != 12
#error Doom startup requires the owned 12 MiB resident profile
#endif
#define EXCLUSIVE_MAX_TICKS 540000u
#elif defined(I960_RESIDENT_NET) && defined(I960_OWNED_MIB)
#define EXCLUSIVE_MAX_TICKS 360000u
#elif defined(I960_RESIDENT_NET)
#define EXCLUSIVE_MAX_TICKS 180000u
#else
#define EXCLUSIVE_MAX_TICKS 6000u
#endif
