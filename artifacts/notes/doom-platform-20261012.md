> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Private Doom runtime and physical cache bridge — 2026-10-12

**The engine candidate now links with zero unresolved imports. The cache bridge
passed on the real card. Doom itself has not executed there.**
[Private runtime contract](../../game/doom/runtime/platform/README.md) ·
[Cache contract](../../game/doom/runtime/cache/README.md).

## Link-complete candidate, tested offline

The final candidate resolves all 44 previous imports using the pinned Newlib
1.11.0 sources, real soft-float libgcc, and an application-private platform port.
All overlapping libc/port definitions and references are renamed, including
stdio/reentrancy/errno/ctype and allocation state. Kernel libc is not overridden.
No missing symbol is assigned to zero or replaced with fake successful file I/O.

- Final REL object SHA-256:
  `b1aa49f887cea1f2933f22a15592c14d082197a5bceb671c24cd7a8656f6d068`.
- Private library SHA-256:
  `2d425440401261b39523eba2e54d5e1894a5ef6c03b48b7bc6665ee277dc1807`.
- **359,680 text + 70,900 data + 322,212 BSS bytes**; 430,580 file bytes and
  **752,804-byte aligned section span**. Debug sections are not loaded.
- **13,113 retained R_960_32 relocations**. Rebasing matches three independent
  links byte for byte at `0x10000`, `0x200000`, `0xc02d0050`. Zero-base template
  SHA-256: `4d245ea67e7aaa2afb04b14068dd42c8e3a914841964e0e7ffe0e248b8637cfb`.
- The entire private 32-bit Newlib/port plus the real arena/heap passes
  **ASan/UBSan with leak checking and halt-on-error**. Tests cover formatting
  (float, 64-bit, truncation, `%lln`), scanning, allocation/OOM/overflow/realloc,
  immutable stdio/cache/EOF/errors, refused writes and shell operations,
  frame/palette bytes, bounded keys/logging, clock-API forwarding, exit and drain.
  The standalone platform fixture supplies a deterministic clock; it is not an
  RTEMS timing/stack proof.
- The existing host Doom hash corpus belongs to the earlier allocator/cache
  profile. Complete Doom under this new private libc has not been exercised.

The 1 MiB conservative image reservation still exceeds this static span by
295,772 bytes. The previous host dynamic peak of 6,473,545 bytes plus that
reservation leaves 866,487 bytes before guards/alignment, **new private-libc
costs and retained test buffers**. A measured complete engine memory/stack
budget is still required; the separate platform unit test is not that budget.

The candidate has no admitted engine entry/STOP protocol yet. ABI v1 supplies
allocation, release, clock and bounded reads; it does not supply owned yield,
owner/STOP queries or an engine termination contract. Its libc exit boundary
uses i960 setjmp/longjmp that has been linked, not tested on card. The frame/key
hooks hold real bounded state but have no concurrent browser publisher yet.
The current whitelist continues to refuse general engine launch.

## Physical cache acceptance

Target SHA-256:
`c8e4c52e0433694191454e415ee1214b08c60fda2bfe453c04ef6cb0f055606c`.
Module SHA-256:
`889a06f80d84af30d8c3e8c0ef6f847db29acdbe029951fdd2d5343164a3d4fb`.
Reviewed application: **1,760 bytes, eleven relocations**, SHA-256
`fe91bbc3275aa801648dc8df6e747cfd84a69b6fd96b366e54801d5818566f9a`.
It ran at `0xc02d0050`, using the existing runtime table and shared arena.

The first physical attempt passed:

- Both normal calls returned the independent FNV oracle **2488633422** over
  header, cross-line range, directory and EOF-tail bytes. The target also checks
  repeated-hit miss counts and an untouched destination prefix. The destination
  is an interior pointer; only the separate exact bounce allocation crosses the
  kernel runtime read API.
- Normal calls required **seven host reads each** (six full 512-byte lines and
  one 196-byte EOF line). Repeated header and cross-line reads generated no
  extra requests. The cache is 16 KiB, with a 512-byte bounce and stack metadata.
- CRC, short non-EOF response, explicit host error and withheld-response timeout
  returned the reviewed error result, followed by a successful fresh cache entry.
  **18 cache requests / 17 replies**; final combined WAD report was
  `[WAD1, 28, 20, 4, 2, 0, 0, 28795076]`, including the earlier runtime tests.
  No outstanding loans or mailbox state remained. Same-instance cache recovery
  and STOP during a read are native-tested; physical STOP followed all entries.
- No-image/incomplete-image refusal and modified code with a **correct file CRC**
  passed. The old code/data/BSS relocation proof and WAD probe also passed again.
- Normal entries took **13.218 s / 11.608 s**, including transport and full-audit
  scheduling; timeout took **5.141 s**. The 500-tick target deadline is unchanged.
  The host completion bound is 60 s for this seven-read probe (seven individual
  five-second waits can exceed the old 30 s bound); uncertain writes are never
  retried. This is correctness acceptance, not a startup-throughput claim.
- **Six dual-stack rounds / 812 replayed packets**, burst saturation and deliberate
  loss passed. Full paired snapshots/protected-code/guard checks remained on.
- STOP at **tick 17,855** drained both workers and their IRQ contexts, reclaimed
  the partial image and retained buffers, and left parked state/handle zero.
  Ten image cancellations were accounted for. Maximum IRQ gap **10.797 ms**.
- Actual-C sanitized replay checked **625 commands / 1,610 upload ioctls** plus
  the complete WAD stream. Independent cache-line modeling checked every read,
  byte, error mode and the absence of redundant host reads. **48 evidence
  mutations** were rejected: 24 snapshots, eight WAD, seven relocation and nine
  cache cases. Copied baseline fixtures must pass before mutation testing.
- Protected upper code is **25,312 bytes**. BSS still ends at `c0f8b940`; the
  34,496-byte interval before protected upper code is unchanged. No flash write,
  forced unload, second firmware callback or wider RAM claim was used.

## Findings during implementation

1. **Old Newlib `%lln` indirection bug.** Its format implementation treated
   `quad_ptr_t` (already a pointer) as `quad_ptr_t *`. A build-local patch fixes
   the count write and is tested, with original/modified hashes recorded.
2. **Hosted i386 longjmp privilege setting.** The first native run reached exit,
   then faulted on CLI. Newlib's intended `_I386MACH_ALLOW_HW_INTERRUPTS` setting
   omits privileged CLI/STI for hosted testing. The original failure binary,
   build metadata and debugger trace are preserved. i960 assembly is unchanged.
3. **Caller-owned strdup lifetime.** Newlib routes strdup through `_malloc_r`.
   The port must not classify that returned string as disposable internal libc
   storage. Dedicated caller-owned wrappers now preserve it; finish explicitly
   refuses while the string remains live. The final sanitized test covers this.
4. **Linker path wildcard.** `*doom*.o` also matched the workspace name
   `i960-doom-platform-20261012`, putting ordinary kernel objects into the upper
   window. The existing limit rejected the offline build. Explicit complete
   Doom object suffixes fix selection without changing any boundary. Neutral
   and Doom-named temporary paths now give identical correct layouts; an
   independent replay of the original rule reproduces its incorrect placement.
   The original failed build log/map are preserved. No faulty image reached card.

A final host API check moves invalid completion-deadline refusal ahead of
publication/sequence consumption. Native tests verify no I/O occurs for invalid
bounds. The valid physical commands are unchanged; this invalid-input guard is
not a separately injected hardware case.

## Archives and reproduction

| Archive | Contents |
|---|---|
| `card-evidence.tar.gz` | Exact physically tested project/target/module, generated proof templates and link oracles, full raw audits and network/upload/WAD/STOP captures, RAM/build logs and original linker-path failure |
| `platform-final-evidence.tar.gz` | Final corrected private runtime source, i960 object/final ELF/library, sanitized native library/test, all build/source/rename hashes, complete engine relocation oracle and initial hosted-longjmp failure |
| `newlib-tested-sources.tar.gz` | Exact extracted Newlib tree used by the builds, including headers, machine sources and licenses |
| `link-path-acceptance.tar.gz` | Neutral/Doom-path fixtures for current and original selectors, symbol outputs and regression result |
| `verification-update.tar.gz` | Later mutation-test/baseline checks and documentation overlay; no physically tested target change |
| `platform-evidence.tar.gz` | Historical pre-final library candidate and native checks; superseded by `platform-final-evidence.tar.gz` |

Archive SHA-256 values are in the repository's tracked artifact inventory.
The immutable Freedoom 0.13.0 WAD is already tracked in
`artifacts/doom-m1-20261011/freedoom-0.13.0.zip`; it is not duplicated here.

Remote workspace: `/home/mit/i960-doom-platform-20261012`. Same resident build
flags as the previous proof; live adds `--upload-concurrent --ticks 36000
--rounds 6 --round-interval 2 --burst --parallel --drop-data --wad WAD`.

Extract the card archive to ROOT and apply the verification overlay afterward.
Run from ROOT/project, using absolute ROOT/WAD paths:

```
python3 rtems/residentnet/verify.py --root ROOT ROOT/live
python3 rtems/residentnet/verify_upload.py ROOT/live --doom-heap --doom-shared --doom-runtime --wad WAD --output replay.json
python3 rtems/residentnet/test_cache_evidence.py ROOT/live --wad WAD --build ROOT/residentnet/entry/cache --output cache-tamper.json
python3 rtems/residentnet/test_runtime_evidence.py ROOT/live --wad WAD --output runtime-tamper.json
python3 rtems/residentnet/test_relocate_evidence.py ROOT/live --build ROOT/residentnet/entry/relocate --output relocation-tamper.json
```

The verifier executes actual native C cache/runtime/heap/loader code; it does
not emulate i960 instructions. The separate physical capture proves i960
execution. To reproduce private runtime builds, extract the final platform and
Newlib archives, then follow the platform contract above using the extracted
`cross/doomgeneric-.../doomgeneric` headers and pinned compiler.

## Remaining gates and restoration

Next: owned engine entry/yield/STOP and i960 exit-boundary acceptance; admission
of the larger manifest and its 52,452-byte relocation-offset list; then measured
WAD batching and bounded initialization, RAM/stack peaks, and first-frame oracle.
Browser publication/input and endurance follow those gates. Recovery and idle
IRQ ownership remain untested.

The exclusive batch released resources by reboot, not module unload. Boot
`ee5281f5-1496-4555-8966-acd43df7030f` returned; the original cooperative public
IPv6 relay is **PID 6154**. The Mac independently received **HTTP 200**. Restoration
command/status/headers/body are recorded here. Visitor statistics remain on the
host and were not copied into Git.
