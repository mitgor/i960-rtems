# Exact BSP point-side helper

`--fast-point-side` on either Doom builder selects `point.c`. It is opt-in;
playable builds otherwise keep the original extracted `R_PointOnSide` at `-O0`.
The experimental switch is mutually exclusive with engine `--point-side-o0`.
No node traversal, visibility, quality, ownership or transport policy changes.

The original optimized function miscompiled axis comparisons on this GCC 3.3
i960 toolchain: a compare/branch changed condition codes before a subsequent
`testg` consumed them. The candidate puts each signed compare and boolean test
inside one volatile inline assembly statement with a `cc` clobber. All three
pairs must remain adjacent in emitted disassembly. Boolean direction tests use
unsigned sign bits, rather than relying on flags across branches.

Coordinate subtraction explicitly wraps as unsigned 32-bit arithmetic. Conversion
back to signed values stays representable at every step. Arithmetic right shifts
by 16 are expressed as unsigned high bits minus the sign contribution; products
use signed 64-bit multiplication, followed by unsigned shifting and explicit
32-bit conversion. This preserves the pinned target's sign shortcut, fractional
truncation and `right >= left` tie rule, including both zero-direction cases.
It does not substitute a full-precision geometric cross product (which would
change Doom's rounding and overflow behavior).

Validation:

- `python3 game/doom/point_side/test.py`: independent integer oracle over
  1,002,000 boundary/random cases.
- `probe.py WORKSPACE`: links the actual candidate engine object into a bounded
  RAM payload; compares exact linked text, the protected O0 object and the
  accepted FixedMul text. 1,024 vectors in 32 calls, 32 cases/call. The payload
  compares both implementations to precomputed oracle answers.
- `verify_probe.py PROBE`: independent replay of all paired staging captures,
  command sequence, identities, returns and clean restoration/unload.

See [physical acceptance](../../../artifacts/notes/point-side-20261016.md).
The tested corpus is strong bounded evidence, not a proof of the entire compiler
or exhaustive coverage of every possible six-word input. Existing renderer CPU
sampling measures BSP plus walls; it does not isolate helper CPU time.
