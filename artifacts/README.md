# Curated artifacts

Start with [current status](../CURRENT-FINDINGS.md), then the
[stock-card-to-applications guide](../docs/reproduce.md) and [subprojects](../subprojects/README.md).
Source code lives in those subprojects; this directory holds inputs and evidence.

| Area | What to use |
| --- | --- |
| Firmware and recovery inputs | [ROM inventory](ROM-INVENTORY.md), `vendor-fujitsu/`, `private-dumps/`, `romhook-20261010/`, `programmed-rom-20261010/` |
| Reproducible build inputs | `toolchain-20261011/`, `rtems-20261011/sources/`, `doom-m1-20261011/`, `software-loader-20261010/target/runner.bin` |
| Current Doom measurements | [CPU-to-SDRAM application-loop rates](current/cpu-sdram-20261018/README.md); [Old/new cached-card N1 baseline](current/cache-baseline-20261018/README.md); [AcceleRAID private cache-map acceptance](current/cache-map-20261018/README.md); [Half-height four-mode comparison](current/half-height-20261016/README.md); [Flat-plane quality switch](current/flat-planes-20261016/README.md); [earlier exact-span results](current/doom/README.md) |
| AcceleRAID 160 research | [Programmed and boot-tested late PING](current/accele160-flash-candidate-20261016/README.md); [Full stock dump](current/accele160-guarded-20261016/README.md); [startup contract](current/accele160-startup-20261016/README.md); [boot recovery audit](current/accele160-recovery-audit-20261016/README.md); [guarded RAM upload route](current/accele160-ram-route-20261016/README.md); [cache-gate audit](current/accele160-cache-gate-20261016/README.md); [debug-interface trace](current/accele160-debug-interface-20261016/README.md); [helper-site audit](current/accele160-helper-site-20261016/README.md); [stock 0x8f command and native PING model](current/accele160-ping-contract-20261016/README.md); [offline fallback-only dispatcher wiring](current/accele160-dispatch-rehearsal-20261016/README.md); [early PING offline candidate](current/accele160-ping-handler-20261016/README.md); [late-loader PING offline design](current/accele160-late-ping-20261016/README.md); [live stock table snapshot](current/accele160-table-snapshot-20261016/README.md) |
| Historical conclusions | [Milestone notes](notes/); these are dated evidence, not current deployment instructions |
| Integrity and retention | `SHA256SUMS`, `artifact-inventory.json`, [curation receipt](current/curation.json) |

The remaining dated directories have stable paths used by build scripts, offline
regression tests, firmware analysis or replay tools. They are compatibility inputs,
not a list of recommended builds. The curation receipt enumerates them. In
particular, experimental firmware images retained as regression fixtures are
**not** approved flash images. Follow the firmware subproject guide.

## Historical evidence

Superseded build trees, repeated binaries, intermediate captures and temporary-file
recovery bundles were removed from the current checkout on 2026-10-16. Their exact
contents remain in Git snapshot **`a8af272`** (full commit in the curation receipt).
Historical documents can mention payload paths absent from this checkout. Restore
the original milestone outside this working tree before running its old replay:

```sh
mkdir -p /tmp/i960-history
# Example: recover the complete four-span comparison, including original paths.
git archive a8af272 artifacts/span-four-20261016 | tar -x -C /tmp/i960-history
```

Use that snapshot's scripts as well when reproducing a historical run; current
code may have changed. `git show a8af272:artifacts/README.md` provides the old index.
The historical notes explicitly retain their original relative-link context.
This cleanup frees checkout space; it does not rewrite or shrink Git history.

## Retention policy

Keep original firmware, the accepted programmed image and programming proof,
pinned source inputs, necessary regression fixtures, and compact current results.
Keep full ownership checks and full audits during hardware experiments. Commit a
small result summary with exact inputs, flags, hashes, failures and measurements;
retain minimal evidence for unresolved failures. Avoid committing another complete
build environment or binaries for every intermediate variant. Superseded accepted
batches can move to Git history once their conclusions and reproduction inputs
are recorded. Never delete uncommitted work from another task during curation.
