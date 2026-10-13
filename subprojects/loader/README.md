# Loader: host software to i960 RAM

| Use | Source / guide | Contract |
| --- | --- | --- |
| Small returning C function | [target](../../loader/runtime/README.md), [host](../../host/loadrun/README.md), [recipe](../../docs/loader/SOFTWARE-LOADER.md) | 64 KiB scalar baseline; return promptly |
| Text/framebuffer buffers | [BIO1](../../docs/loader/BUFFER-IO.md) | Bounded request and response, guards and restoration |
| Persistent Tetris session | [host session](../../host/session/README.md), [design](../../docs/loader/PERSISTENT-SESSION.md) | Keep setup between calls; checked close |
| Larger images | [segmented loader](../../loader/segmented/README.md) | Explicit segment/layout admission |
| Resident RTEMS engine | [resident runtime](../../rtems/residentnet/README.md), [Doom runtime](../../game/doom/runtime/README.md) | Owned arena, lifecycle and independent STOP |

Start with the [small C recipe](../../docs/loader/SOFTWARE-LOADER.md#build-and-run) on an
already patched card. Its Fibonacci result establishes upload, execution and
restoration before introducing an OS. The original scalar/BIO1 layouts remain
useful and are not silently enlarged to match Doom's arena.

The older [flash-loader design](../../loader/README.md), postinit, staging CPU,
stockhook and romfetch experiments are retained as research. They are not
alternate production launchers. [Research map](../../docs/research.md).
