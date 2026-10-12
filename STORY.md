# Teaching a dead RAID controller to run Tetris — a field report

*A narrative companion to the technical docs. If you want register maps and exact
offsets, read [FINDINGS.md](FINDINGS.md) and the rest. This is the story of how I
got there, dead ends and all.*

---

The brief was wonderful in its uselessness: there is a retired Mylex DAC960PG
RAID controller sitting in a Linux box, it is built around an Intel i960 CPU, and
the goal is to make that i960 run Tetris in text mode. Not emulate a RAID card.
Not recover data. Run Tetris. On the RAID card. Because it's there.

I want to be honest up front about where this ends, because the fun of a report
like this is the journey and not a fake cliffhanger: Tetris runs today as real
i960 machine code under an interpreter on the host. Tetris now also runs on the card in bounded steps: move, rotate, drop, clear
lines, return a screen. There is no interactive terminal session yet. The code
is uploaded after Linux is already running, executed by the real i960, and
followed by another call without a reboot. The card turned out to be a locked box, and most of this project was the
slow, stubborn business of picking that lock. This report now includes the part
where the key actually turned.

## Act I: Getting a word in edgewise

First you have to find the thing. One SSH session into the bench machine and the
card introduces itself on the PCI bus as two functions: a bridge at `37:09.0`
with Intel's vendor ID `8086:0960`, and the controller proper at `37:09.1`,
`1069:0010` — Mylex's. Linux had already bound its `myrb` driver to the
controller and was patiently waiting for disks that would never come.

The card exposes exactly one 8 KB window to the host through BAR0, mapped at
physical `0xee000000`. That's it. Eight kilobytes is not a lot of room to stage a
takeover of a 32-bit CPU, and it would take me a long time to understand what
those eight kilobytes actually *were*. (Spoiler: a slice of the i960's own local
address space, including its hardware mailboxes. That detail becomes the whole
ballgame later.)

## Act II: Compilers from a museum

Before you can run code on a CPU you need a compiler that targets it, and the
i960 has been dead long enough that the toolchains died with it. binutils dropped
the i960 after **2.27**. GCC dropped it after **3.3.6** — a compiler from 2005.
So I built a cross-toolchain out of these fossils, and they fought me the whole
way:

- binutils 2.27 only builds the i960 target at all if you pass
  `--enable-obsolete`, which is the build system's way of asking "are you sure?"
- The assembler refuses the COFF flavour outright ("this target is no longer
  supported") and only keeps the ELF one. But GCC 3.3.6 wants to *drive* a COFF
  toolchain. The fix was a small lie: symlink `i960-coff-as`, `-ld`, `-objcopy`
  and friends to the `i960-elf-*` binaries. GCC calls the names it expects; the
  ELF tools answer.
- GCC 3.3 itself won't build cleanly on a modern host until you beat it with
  `-std=gnu89 -fcommon -w` and turn off fortify. It's a compiler that predates the
  assumptions every current compiler makes about C.

It works. `i960-coff-gcc -mrp` produces little-endian `elf32-i960` objects, C
symbols pick up a leading underscore, and I was looking at real i960 opcodes for
the first time.

## Act III: A game, and a machine to run it on

The game side was the easy half: a freestanding Tetris in C — all seven pieces,
rotation, collision, line clears, scoring, game over — talking to the outside
world through a tiny shared-memory contract (a `24×80` ASCII framebuffer, a
keypress byte, a doorbell). One surprise: GCC 3.3 quietly emits a call to
`___main` at the top of `main`, a constructor hook, and if you don't provide an
empty `__main` stub the linker drags in libgcc's `atexit` and the whole freestanding
illusion collapses. Four bytes of empty function fixed it.

The *interesting* half was deciding how to "run" it. With the real card still a
mystery, I wrote an interpreter on the host that loads the ELF, builds an i960
call frame, and executes the actual instruction stream GCC emitted — not a
recompile to x86, a genuine decode of i960 machine code. The i960 is a RISC with
personality, and it taught me its quirks by breaking my interpreter in three
instructive ways:

1. **The register file is numbered backwards from my assumption.** Registers
   0–15 are the *locals* (`r0`–`r15`), 16–31 are the *globals* (`g0`–`g15`). I had
   it inverted, and nothing worked until I flipped it.
2. **`ret` uses the full return address.** The i960 stashes return-type bits in
   the low nibble of the *previous frame pointer*, not the return instruction
   pointer. I was masking the RIP to 16-byte alignment, which corrupted every
   8-aligned return address and sent the thing into an infinite call loop.
3. **`test{cond}` is not a branch.** Opcodes `0x20`–`0x27` set a register from the
   condition code; only `0x30`–`0x3f` are the compare-and-branch family. I had
   lumped them together and merrily branched into garbage.

How do you know when an interpreter is *right*? You make it prove itself. I
compiled the same C two ways — once for the i960 (run under the interpreter), once
natively for x86 — and compared outputs. A CPU torture test lands on `-135781`
both ways. The line-clear algorithm lands on `200110` both ways. When the
emulated i960 and the native build agree to the integer, the decoder is honest.
Tetris was now, provably, running as i960 code.

Just not on the i960.

## Act IV: The locked box

Here is the wall the whole project runs into. At power-on the i960 reads an
Initialization Boot Record from a fixed address in its flash and starts executing
*that*. Whether the host gets to intervene first is decided by two strap pins
sampled at reset, which select one of four modes. I read the bridge's control
register (EBCR, config offset `0x40`) and it came back `0x0018` — **Mode 2**.
(I'd first called it Mode 3; the register corrected me.) Mode 2 means the core
boots its own flash firmware and comes up running, and the mode is wired in
hardware. Software can't vote.

So on this card, as wired, you cannot simply hand the i960 a program. It is
always already busy being a RAID controller. The emulator was no longer a
stepping stone — it was, for the moment, the *only* way to run the code. Which
meant if I wanted real silicon, I had to change what lives in that flash. And to
do *that* safely, I first had to read the flash. And read its vendor's firmware.
And understand how the vendor wrote it there.

The project quietly turned from "run a program" into "reverse-engineer a 1997
storage controller."

## Act V: Talking to the firmware

The card's running firmware speaks a command protocol over a hardware mailbox.
I wrote a small, strictly-bounded Linux kernel module that binds the driverless
card, allocates a DMA buffer the IOMMU-correct way, and issues exactly one
command. The first real reply came back and it was glorious in its mundanity: an
Enquiry returned the firmware revision, **4.07-0-29**. The channel was real. The
card was listening.

Then I went looking for the vendor's own firmware image, because the sane way to
build a replacement is to study the original. Fujitsu still hosts the GlobalFlash
packages, and inside them the firmware is *encoded* — not encrypted, but
scrambled enough to stop a casual hex dump. Cracking that encoding was my favorite
afternoon of the project, and also a lesson in how to fool yourself. I chased
several dead ends that each "almost" worked — a whole-file bit reversal, an
XOR of `0x8d` that mapped the filler byte to a plausible letter and *nothing
else*, a nibble-misaligned grep that spelled "DAC960" if you squinted. Each one I
had to talk myself out of. The real transform turned out to be clean and verifiable:
**XOR every byte with `0xC3`, then permute bit `i` to position `i XOR 6`.** Run it
and a valid firmware image falls out, header and trailer and all. No squinting
required.

## Act VI: The dump that wasn't

This is the part I'm most glad I wrote down honestly, because I got it wrong first
and the wrong version was seductive.

I wanted to dump the flash in-system — no desoldering, no programmer. The firmware
has a StoreImage command, opcode `0x21`, and in my head that was "store the image
*to me*." I ran it, pointed it at my DMA buffer, and got back... my own sentinel
byte, `0xA5`, half a megabyte of it. For a while I tried to explain that away.
The truth, once I actually traced the vendor's code, was humbling: `0x21` is an
*upload* — host to card. It copies my bytes *into* the card's staging area. The
first 512-byte upload had overwritten the beginning of the staging I was hoping
to read; the sentinel-filled host buffer was not a dump. It had never been a
dump. I kept flash programming interlocked. Even my name for that operation
needed correcting later: `0x22` was the wrong route for this installed profile.
The working programmer would turn out to be subcommand 1 of `0x2B`. Knowing a
command's name is apparently not the same thing as knowing what it does.

The direction that *reads* is `0x20`. Card to host. Once I had the directions
straight, the reads started returning real, structured data — but was it the
flash, or some cached copy? The test I settled on is simple and strict: read each
region *twice*, once over a buffer pre-filled with `0xA5` and once with `0x5A`.
If both reads come back byte-identical and neither looks like the sentinel, the
card genuinely wrote real data both times. They matched.

## Act VII: The 512 KB that added up

After a fresh boot cleared the damaged staging state, extending the reads across
the whole image window gave a **512 KB image**, captured twice, the two copies
bit-for-bit identical. Then came validation, and this is
where it stopped being a hopeful pile of bytes and became *the* image:

- the firmware region matches Fujitsu's decoded 4.07-0-29 payload **exactly**;
- the boot block matches the vendor boot block **exactly**;
- the x86 BIOS region matches the option ROM I'd independently read out of PCI
  expansion space **exactly** — three completely different provenances agreeing.

And the clincher. The i960's boot record should sit at the very top of flash,
`0xD0` bytes from the end. For a 512 KB chip that's offset `0x7FF30`, which maps to
CPU address `0xFEFFFF30` — precisely the architectural boot address. I read the
eight words there: a first-instruction pointer of `0xFEFFC400`, a control-block
pointer of `0xFEFFD4D0`, and a boot checksum that makes the eight words sum to
**exactly zero**. That last fact is itself a small correction: the manual *describes*
the checksum as "sum the words with `0xFFFFFFFF` and boot if zero," which implies
the eight words sum to one. The real images sum to zero. I trust the silicon over
the prose; my image builder reproduces the stock checksum byte-for-byte on the
zero rule.

The image is internally consistent, agrees with three independent references, and
carries a valid boot record. It's real. But the two reads still came from the same
firmware staging snapshot. Agreement proved a repeatable transfer, not two
independent trips to the flash chip. That distinction would matter when it was
time to write something back.

## Act VIII: The map was wrong

Having the true image immediately corrected a mistake I'd baked into my earlier
plan. I had assumed the flash *was* the ~230 KB firmware payload, based at
`0xFEFC8000`, with the boot record living inside it. Wrong. The chip is 512 KB,
based at `0xFEF80000`. The firmware payload is just a *tenant*, sitting at offset
`0x30000`. The boot record's first-instruction pointer aims into the **boot
block** at `0x7C000`, a separate component entirely. Any custom image has to
respect that real structure — keep the boot block's record and startup intact, or
relocate deliberately — not redirect a pointer inside the firmware payload and
hope. The dump didn't just give me a backup; it redrew the map.

## Act IX: The wall behind the wall

With the geometry understood, I designed the clean endgame: flash a tiny loader
*once*, and from then on push real programs — Tetris included — over the mailbox
at runtime, no reflashing per iteration. I was pleased with it. I hardened the
protocol, wrote real tests, documented it.

Then I did the thing I should have done first and read the i960 manual's section
on internal data RAM, and it quietly demolished the demo. The loader's plan was to
drop a small payload into the chip's 1 KB internal RAM and jump to it, because that
RAM exists at reset with no DRAM setup. But §4.1 is blunt: *"instructions cannot be
fetched from the internal data RAM. Instruction fetches directed to the data RAM
cause an OPERATION.UNIMPLEMENTED fault."* Not undefined — a specified fault. My
jump wouldn't run a single instruction; it would trap.

The consequence is sharper than one broken demo. On this card the *only*
executable RAM is the external DRAM, and DRAM needs the memory controller brought
up first. So any loaded-code path has to initialize DRAM before it can run
anything — and I'd spent real effort fencing the loader *into* the one region that
can't execute code while fencing it *out* of the region that can. It was rigorous
work aimed at the wrong room. Better to find that out from the manual than from a
dead card.

## Act X: Let the people who built it initialize the memory

The installed boot block finally gave up its DRAM register writes. Not the
similar-looking reference I'd studied first — the actual `FWTCBBLK` from this
card. There they were, stores to `0x151C` through `0x1530`, including `0xB43`
and `0xCC`. Useful facts, but not yet a decoded timing sheet: I still hadn't
proved what every field meant or whether later startup changed it.

Then the obvious question arrived rather late: why was I trying to become the
person who initializes this memory? The vendor already had working code for it.
The card had **16 MiB of DRAM**, and its firmware knew how to use it. Let it.

Tracing the real boot path exposed a metadata record near the end of the main
firmware component. The boot block checks that record, copies a bootstrap,
decompresses the main program into DRAM, and eventually branches to an entry
address supplied by the metadata. That entry was a much better place to intervene
than the reset vector. Memory initialized. Program unpacked. Original boot block
still doing its job.

I built an offline prototype that would take over after stock initialization,
with DMA guards and a bounded payload window. It was a plausible route, but it
still meant replacing the controller's working life with my own polling loop.
The next version asked for much less: let the RAID firmware carry on, and give
it one extra command.

## Act XI: Looking for the emergency exit

Before changing flash, I went looking for a way back. There really is a recovery
monitor inside the preserved 16 KB boot block. The code copies it into DRAM;
it can present a different PCI device ID, `1069:0011`, and service image reads,
uploads and programming without the main firmware. That was encouraging.

It was not the same as having recovered a card.

The boot block also has a serial trigger: it sends an `S`, samples input, and
can select the fallback path. One branch even prints `Remove Serial Port Jumper`.
A wonderful little fossil of the factory floor. But the connector pinout,
electrical levels and exact physical procedure were not established, and no
safe SSH-only recovery entry was demonstrated. A valid program that hangs after
the boot checks can stay hung; preserving the boot block is not automatic rollback.

The card's menu option to disable its BIOS offered another tempting shortcut.
That is the PC-facing option ROM, though, not a switch that stops the i960 from
booting its own firmware. It wasn't a demonstrated recovery mechanism either.

The owner had physical access and a spare similar card, and explicitly chose to
continue without testing recovery. That was the decision under which the later
flash write happened. No external programmer had rescued anything, no serial
adapter had been tried, and I wasn't going to quietly promote a disassembly into
a recovery test just because the rest of the project needed a happy ending.

## Act XII: Borrowing a command

The small opening was opcode `0x6F`. In the stock firmware its dispatch-table
entry led to an unsupported-command reply. If I could temporarily change that
one RAM word to point at a tiny function of my own, I could ask a very narrow
question: did my instructions execute?

The staging commands supplied an unexpected tool. Their offset arithmetic wraps
at 32 bits. With the staging base known and the offsets carefully constrained,
the same read/upload machinery could reach selected RAM outside the image.
That made a command-table experiment possible without erasing flash. It also
made host-side bounds checks rather more than good manners.

The first replacement replied with a distinctive status, `0x017E`. Real code,
real silicon. Then subsequent dispatches taught me about stale cache state.
A word read back correctly by DMA is not necessarily the word the CPU is using.
The i960's data cache doesn't snoop those DMA writes. Cache invalidation became
part of the experiment, not a footnote.

There was another question hiding behind the first: could the running card still
fetch instructions from flash after startup? I tried calling what I thought was
a suitable flash address and hung the command. The mistake was mine. An earlier
disassembly had put the firmware component at the wrong base. The correct stock
`RET` instruction lived at `0xFEFB022C`; I'd aimed into unrelated bytes.

Even reading the address map had a trap. On this board's 8-bit flash bus, a
32-bit DMA read was not four consecutive ROM bytes. The captured words carried
the expected flash byte in the low lane, with address-derived values above it.
Bytewise access mattered. Once the mapping was corrected, a RAM callback called
the stock flash `RET`, came back, and returned `0x017F`. The table and temporary
code were restored, and the original unsupported-command reply returned too.

Those failures cost reboots and taught the harness to retain its DMA buffers
when a command's fate was uncertain. A timeout on the host does not mean the
card has stopped touching memory. Nor does it mean “try the write again.”

## Act XIII: Forty-eight bytes, with a rather large rehearsal

The persistent patch ended up being **48 bytes** in a verified padding slot in
the main firmware component. Its boot entry installs the new `0x6F` table word,
then branches to the original program entry. The little handler stays in flash
at `0xFEFE001C`, replies `0x017E`, and uses the stock completion routine.

Putting the handler in flash avoided another lifetime mistake: the firmware's
image-staging allocation can be freed. A permanent command pointer into that
allocation would be an invitation to execute whatever later occupied it.

The image changes were small: the hook, the metadata entry word, and its checksum
word — 56 bytes of replacement material at three locations. The programmer's
work was not small. The matching `2B/1` path rewrites the lower **496 KiB** of the
image, leaving the final 16 KiB boot block alone when its flag is zero. A small
patch does not imply a small erase operation.

So there were rehearsals. Upload the candidate into RAM, read all 512 KiB twice,
check the hash, restore the original, read it twice again. Then a stronger test:
make the i960 itself read the entire candidate through the programmer's memory
alias, with explicit cache invalidation, and calculate its CRC32. It returned
`2012D01F`, the expected value. That closed the gap between “the host can read
these bytes” and “the CPU that will program them can see these bytes.”

The one-shot programming harness checked the exact profile and images, restored
its temporary callbacks before the erase, and had tests for its failure paths.
It was built to submit the programming command once. Uncertainty would leave
evidence and pinned resources, not trigger an optimistic second erase.

## Act XIV: The write, and the wait

With explicit authorization, the harness issued **one `2B/1` command** with the
boot-block flag zero. It completed successfully. The stock routine freed its
staging allocation; subsequent reads rebuilt it through the traced bytewise
physical-flash copy path. Two complete readbacks matched the patched image.
The preserved boot block matched the original byte for byte.

Then came the reboot, and SSH did not come back promptly.

This is where a neat story would insert a diagnosis. The evidence doesn't give
me one. The owner was asked to inspect the PC and power-cycle it if necessary,
then reported it back online. Whether a power cycle actually happened wasn't
specified. Similar delays had happened before the patch, too. All I can honestly
say is that Linux returned with a new boot ID, and then we measured the card.

A dedicated validation probe allowed no uploads. The installed command-table
word pointed to `0xFEFE001C`. Two calls returned `0x017E`. Full-image reads before
and after matched the patched firmware, and the stock Enquiry checks still
reported 4.07-0-29. All **54 commands** completed cleanly.

The patch had survived boot. The new flash handler was executing. The old
firmware was still answering. That is a narrower claim than “every RAID function
works,” but it was the claim the experiment had set out to establish.

## Act XV: Fifty-five

At this point I expected the next step to need another firmware revision. It
didn't. The tools already in hand were enough to borrow the firmware's allocated
DRAM, upload a program, call it, and put the borrowed bytes back.

The runtime loader uses the staging area at `0xC0F2C000` for programs up to
**64 KiB**. A separate **104-byte call gate** invalidates caches, passes a 32-bit
argument to the uploaded function, and collects its 32-bit return value. Before
reporting completion, it restores the dispatch entry to the ROM PING handler.
That last detail matters: a later status check must not accidentally run the
user's program again. User execution is submitted once.

For the first program I chose Fibonacci. Not a framebuffer, not a spinning game
loop, just a small freestanding C function that returns. The old compiler made
it **64 bytes** of i960 code. I uploaded it after Linux was already running and
asked for Fibonacci of ten.

**55.**

The card returned fifty-five, along with the runner's completion marker. Then
the loader restored the staging image, the temporary code and result storage,
checked the PING dispatch and firmware health, and unloaded its kernel module.

Once could still be a lucky arrangement of caches and memory. So the new
command-line loader uploaded the function again with twenty as the argument.
**6765.** Then it replaced the program with different code, a rotate-and-XOR
function. Given `0x12345678`, it returned **`0x8C2F3B20`**, exactly as expected.

Three runs. Two programs. One Linux boot. No further flash writes.

Each run completed **110 firmware commands**, including paired full-image checks
before upload, after upload and after restoration. The native transaction tests
also exercised **194 command-boundary failure cases** and the maximum upload
size under address and undefined-behavior sanitizers. Those tests don't execute
i960 instructions; the three hardware runs do. Both kinds of evidence have a job.

The originals, patched ROM, exact target binaries, kernel modules, source
snapshots and transaction captures are now in the local `artifacts/` tree with
hashes, intended for Git. The loader has a CLI and Markdown instructions, and
the Claude Code handoff points to the current implementation instead of the old
internal-RAM dead end. Computer archaeology is much less satisfying if the
working shovel exists only in somebody's `/tmp` directory on the bench machine.

## Act XVI: The answer grows a screen

Fifty-five was enough to prove execution. It wasn't enough to play a game. The
next extension gave a returning program a bounded input buffer and room for up
to 8 KB of output. The host reads the answer before putting the borrowed firmware
bytes back, checks it twice, and insists that the code, input and guard bytes
haven't changed.

The first answer was `Hello from the real i960!`, followed by input bytes the
card had transformed. Then came a complete **24×80 character framebuffer**: a
border and a letter pattern drawn by the i960, copied back to Linux, and checked
cell by cell against an independent reference. A deliberately tiny output budget
returned an error with no output. Another text request worked afterwards, and
the old Fibonacci test still returned 6765.

Four buffer transactions, 128 firmware commands apiece, plus the scalar regression.
Same boot. Same flash. All borrowed RAM restored. The native tests had caught a
one-byte mistake in the greeting's capacity calculation before the card ever saw
it; the archaeological compiler also needed a small assembly entry stub because
it wouldn't honor a modern-looking section attribute. Even hello-world has a
few opinions when your compiler is old enough to vote.

There is still no running Tetris loop on the card. But its screen now has a way
home. The next change is to make the game advance one bounded step at a time,
returning its state and framebuffer instead of waiting forever for a host
handshake that the firmware command loop cannot service while it is away.

## Act XVII: Two lines on real silicon

The game needed to learn to stop. Its original loop waited for the host to clear
a doorbell, which is fine inside an interpreter and a bad bargain inside a
firmware callback. I split it into explicit state, one bounded update, and a
renderer. The host keeps 240 bytes of state between calls; the card returns those
bytes and the screen. No secret globals left behind in borrowed memory.

Native tests and the interpreted i960 agreed across 1,024 seeded transitions.
The interpreter needed one more instruction, `setbit`, and a less forgiving exit
status when it encounters something it can't execute. Then came the card.

Initialize. Move left. Rotate. Drop. Quit. Restart. Each state and every screen
cell matched the native reference. A constructed board cleared two lines and
returned a score of **200**, with the remaining blocks shifted correctly. A
spawn collision produced **GAME OVER**. An excessive tick count was rejected
without producing output. Nine transactions, all restored and unloaded, on the
same boot as the earlier hello-world experiments.

This is finally Tetris logic on the actual controller, including drawing its
screen. It is not yet me playing Tetris over SSH. The difference is smaller than
it used to be, but it still deserves its own line in the ledger.

## Act XVIII: A thousand times is a different question

One good frame proves a path. A thousand frames ask whether the path keeps
working. I left the conservative loader intact: upload, verify, execute once,
read the answer, restore everything, unload. Then I made it do that a thousand
times, feeding each returned state into the next request and comparing every
state byte and screen cell with the native game.

All one thousand matched. That included eight game-over responses, restarts and
scheduled quits. A separate 64-call run matched too. There were no uncertain
completions, damaged guards or failed restorations. The card stayed on the same
boot throughout. Every capture was kept losslessly, compressed against the common
firmware image, then reconstructed and checked again on the Mac.

The stopwatch was less flattering than the correctness result. A complete loader
call took about **306 milliseconds**: roughly three updates a second. The command
that actually runs the payload occupied about **6.18 milliseconds**, including
its mailbox round trip. Saving, verifying and restoring the borrowed world took
most of the time. The eight-minute test also spent time archiving its own evidence;
that cost was measured separately.

So the next obstacle is wonderfully ordinary. Not secret flash encoding, not an
unexecutable RAM region, not a processor that refuses to listen. Bookkeeping.
For a twenty-frame-per-second game, the host needs a carefully owned session that
saves the furniture once and puts it back when play ends, instead of redecorating
the whole room between every falling block.

## Act XIX: Stop moving the furniture

The first session kept the furniture where it was. Linux saved the borrowed RAM
once, kept the file open, and asked the card for another frame. When the file
closed, everything went back. That alone brought a frame down to about sixty-four
milliseconds. Better, but still a little too leisurely for falling blocks.

There were two more chores to stop repeating. Most frames now check the complete
program and its input/output block twice, with a full half-megabyte inspection
every thirty-two calls and again at the end. And the runner was already clearing
the caches when it returned; the extra cache-control visit between every pair of
frames was redundant. The first call still takes that precaution.

A thousand frames later, every state and screen matched the native game. Median
frame time: **forty-one milliseconds**. A separate four-hundred-frame run held
**twenty updates a second**. The occasional full inspection ran a few milliseconds
late, then the next frame caught up. The controller had not become faster. The
host had finally stopped asking it to pack up after every move.

Keeping RAM borrowed makes closing the door part of the experiment. I killed the
host process while it was opening, running a frame, and closing. Thirteen timed
cases, repeated, all returned the saved bytes. A second owner was refused; an
inherited file descriptor kept ownership until its last copy closed. Uncertain
commands and failed restoration were exercised in the native fault tests, where
retaining the DMA memory is the correct answer, however inconvenient.

The audit tradeoff belongs in the story too: damage beyond the program's region
can now wait until the next full inspection to be noticed. These are small,
trusted, returning functions. This is not a sandbox. Nor is a twenty-second paced
test the same thing as half an hour of somebody actually playing. The keyboard
and terminal client still get their own chapter.

## Act XX: The keyboard finally gets a turn

The next program ran on the host, and that was the point. It translated arrow
keys, measured the time between frames, and put the card's eighty-column screen
into an SSH terminal. The i960 still chose where the pieces went and drew every
cell. The host had become a keyboard and a display with unusually elaborate
manners about borrowed memory.

Left and right moved a piece. Up rotated it. Down or Space dropped it. `r`
started again after GAME OVER; `q` put the furniture back and left. Shrinking the
terminal paused the game instead of turning the board into a scrolling accident.
Only changed rows needed repainting. A flood of keys filled a bounded queue and
dropped the excess; it did not turn into half a minute of unwanted movement.

Then I pulled the SSH connection out from under it. The client noticed the end
of its terminal, closed the session, restored the saved RAM and unloaded. A new
connection worked, and Ctrl-C left both the controller and terminal tidy. That
is a better sort of drama than the earlier reboots.

For the longer test, scripted hands pressed the same keys through a real SSH
pseudo-terminal for half an hour, restarting repeatedly. Every recorded request
and answer was checked afterwards against the native C game. The stopwatch,
input drops and full restoration captures were saved too. This was automated
play, not a claim that I had spent thirty minutes becoming good at Tetris.

There is now a command I can type on the Mac and a game I can play on the RAID
controller. The firmware still gets control back between frames. No new flash
write, no changed boot straps, no private operating system yet. RTEMS will be
another chapter. For once, the next useful instruction is simply: press a key.

## Act XXI: Put the excavation in a box

There is a point in computer archaeology when the next useful tool is Git.
The ROM was on the Mac. So were the patched image, the tests and the evidence.
But a surprising amount of the later work was still sitting outside the index,
which is a poor place to leave the only explanation of why something worked.

I compared the remote project files with the local files and archive contents.
Forty-one missing pieces turned up: old sources, exact ELF builds, linker maps,
and emulator logs. The compiler came home too, with its original source
packages. An executable named `i960-coff-gcc` that produces ELF is exactly the
sort of detail a future archaeologist should not have to rediscover by surprise.

While this was happening, the terminal client was already running on the PC.
I left it alone. It finished, and its saved trace gave us another 2,224 frames
to compare with the native game. Every one matched; the saved RAM went back
and the module unloaded. No special demonstration was needed this time. The
program was simply being used, and it left enough evidence to check its work.

The box has a ledger as well as trophies. Recovery is still untested. The DRAM
registers still do not have a complete timing decode. RTEMS and networking are
still plans. Saving a binary does not make an unanswered question disappear;
it makes it possible for someone else to pick up exactly where we stopped.

## The operating system that learned to come back

“Do as much as possible for RTEMS,” he said. “I'll go to sleep.”

There was a respectable plan on paper. Find an old RTEMS with i960 support,
write a board support package, take ownership of interrupts and timers, invent
a transport that would keep working after the RAID firmware stopped answering.
That is a substantial amount of work to put between a sleeping person and a
first result. More importantly, the card had already taught us a useful trick:
a program could borrow the processor, do something, and return it.

Could an operating system learn the same trick?

RTEMS 4.6.6 still had the i960 code. Not a modern port hidden behind a familiar
name: the actual historical kernel, with Classic tasks, semaphores, message
queues and the context switch written for this family of processors. Its old
RP board code also had assumptions we could not borrow. Different timer
constants. A board-specific write. Interrupt machinery that needed a separate
audit. So those parts stayed on the shelf. The original firmware kept the
interrupts, and our RTEMS ran with them masked, inside its borrowed interval.

The first test started a real RTEMS task and shut the executive down again.
Then two workers changed places, carrying their local cookies intact through
four hundred iterations. A queue carried two hundred messages. A sleeping
task woke on the fifth tick we supplied. The CPU context was forty-eight bytes,
not the forty-four I had initially expected. The card was right; the first
host-side assertion was not.

The next trick was to stop shutting down. A service task saved its context and
switched back to the firmware caller. On the next call it resumed where it had
left off. The kernel, task stacks and counters remained in the same borrowed
RAM. One thousand calls later, both tasks still agreed about how many times
they had been there. At the end, the original bytes went back into place.

There was a small lesson in vocabulary along the way. A binary semaphore in
this old RTEMS could mean an owner-recursive mutex. I had asked it to be a
signal. The first worker never got its turn. A *simple* binary semaphore was
the thing I meant, and once I said so, the worker started answering.

Then came lwIP. Its first answer was an assertion: a DNS record that should
occupy ten bytes occupied sixteen under the i960's aggregate alignment rules.
One carefully packed wire structure later, DNS could exist. TCP supplied the
next lesson. A receive callback that could copy one packet was not necessarily
large enough for the pbuf chain it would eventually receive. The first long
echo stalled at 9,600 bytes. The capture kept the zero window and retries; the
fix kept a complete receive window and wrote it atomically.

After that, the card answered ping. It echoed UDP. It accepted a TCP connection
and returned sixteen thousand bytes without changing one. Linux had a private
TUN interface for it and passed complete IP packets through the PCI transport.
The TCP state machine was on the i960. Linux was the road out.

And then the RAID controller asked a DNS server where `example.com` lived,
opened its own TCP connection and fetched an HTTP page from the Internet.
Eight hundred and ninety-one bytes came back. The host's packet capture could
reassemble them independently, and its hash matched the bytes the card handed
us. No host socket had fetched the page on its behalf.

That deserves a little silence. This was a machine built to be somebody else's
peripheral. It had just made a request of its own.

We let that connection run for half an hour: 4,430 exchanges, nearly nineteen
million bytes echoed exactly, and 29,352 trips into the kernel and back. The
stack guards held. Then we killed the host client on purpose, checked that the
kernel release restored the card, and used its saved journal to put the host
networking back. Even an operating system needs to know how to leave.

It also deserves a precise qualification. Time arrived in the host's requests.
Without polling, RTEMS stopped progressing. There was no autonomous timer,
no preemptive hardware BSP, no TLS, and no promise that a runaway callback
could be interrupted. Three guarded stacks and a long test are evidence about
this program, not a substitute for recovery or a disk-I/O test. We had learned
to run an operating system cooperatively inside the old bargain, not abolished
the bargain.

The sources, exact binaries, failed first attempts and packet captures went
into the same box as the ROM. An operating system is a better trophy when
someone else can build it, run it, and check why you believe it worked.

## A longer address, the same old processor

The next question was whether this arrangement could speak IPv6. It could.
The stack already knew the protocol; the port had been built with that half
switched off. Enabling it meant giving the card a second address family,
letting the virtual interface carry both, and teaching the host gateway to
put everything back afterward.

There was one small archaeological trap inside the network stack itself. The
pinned UDP receive code accepted a zero checksum, which was acceptable for
IPv4 but wrong for this IPv6 profile. A native test caught it. The target and
native builds now share the same narrow correction, alongside the earlier DNS
structure-packing fix.

Then the card answered IPv6 pings, echoed UDP and TCP, asked for an AAAA record,
and fetched an HTTP page over IPv6. The DNS question still went to the existing
IPv4 resolver; the TCP connection to the web server was IPv6 all the way to
the host's NAT66 gateway. The packet capture and the bytes returned from card
memory agreed. During a three-minute transfer it echoed 1,876,865 bytes without
a mismatch, then returned its borrowed RAM. Deliberate packet loss recovered;
killing the client and replaying the journal restored the host's networking.

All of this fit inside the same reservation. No new flash write, no reboot,
no newly claimed megabytes. It remained a cooperative operating system that
needed the host to keep asking, now with a considerably longer address.
The [binaries and captures](artifacts/rtems-ipv6-20261011/README.md) are in the
excavation box too.

## The card gets a front door

IPv6 had first been a way out: a DNS question, a TCP connection, a web page
fetched from somebody else's machine. The next request turned the direction
around. Could the old controller serve a page of its own?

A small HTTP server went into the card's lwIP build. Four connection slots,
a 512-byte request-header limit, one reply per connection, and no filesystem.
It answered ordinary GETs, requests split across packets, repeated connections,
and deliberately oversized headers. The Linux host forwarded an IPv6 TCP port;
it did not manufacture the page. A request from the Mac to the PC's global
IPv6 address on port 8080 came back with a greeting from the i960RP.

That left the larger request: stop borrowing time from the host.

The first useful discovery was that timer zero was already occupied. The stock
firmware had set it up, and its counter was moving. There was another trap in
the manual: reading a timer's mode register clears its terminal-count flag.
Even an inventory needed to know which questions changed the answer. The
observational probe left those registers alone.

Timer one had zero count and reload values, no pending interrupt, and its mask
bit clear. The core's vector cache was enabled, so a dedicated interrupt could
use a saved-and-restored entry in internal RAM without rewriting the interrupt
table in flash. A bounded experiment took that route. While one RTEMS task
spun in a busy loop, eight hardware timer interrupts woke a higher-priority
task eight times. Then the experiment stopped the timer, restored the vector
and mask, returned to firmware, and gave back its RAM.

That was a real hardware-driven task switch. It was not yet permission to
leave the timer running after the host call returned.

The autonomous transport therefore gained a different kind of close operation:
stop the timer first, verify the acknowledgement, and only then restore the
memory containing its handler. A killed client must follow the same rule in
the kernel. Native fault tests exercised 344 command boundaries and a bad stop
acknowledgement. Private RTEMS state could move between reads; immutable code
and the host response still had to agree.

The first background trial found a mistake that the bounded test could hide.
Its timer-only mask stayed installed, masking the firmware sources needed for
continued command service. The initial command returned, but the next read
could not proceed. The new transport did what it was supposed to do on that
failure: it kept the image and DMA pinned. It did not erase a live interrupt
handler to make cleanup look successful.

The failed capture was saved, the background mask was corrected to retain the
stock interrupt sources, and the PC rebooted. It eventually came back. The next
trial really did advance RTEMS while the host was silent, but stopping it found
another mistake: an inline assembly helper had not supplied the value it meant
to put into the processor control register. Again the transport kept the handler
in place, and again the evidence was saved before rebooting.

With that repaired, and timer one set for a hundred ticks per second, the host
asked RTEMS to start and then said nothing for twenty seconds. When it asked
again, 2,009 ticks and 2,009 task wakeups had happened. The card had kept its own
time. STOP restored the timer, vector and masks; the loader restored RAM and
unloaded normally.

The networking build took the same path. Five silent seconds produced 509
ticks. IPv4 and IPv6 echo still worked, an IPv6 Internet HTTP fetch completed,
and a minute of IPv6 stress carried 554,528 bytes. The web page now described
its hardware-driven clock, and the Mac fetched it through the host's global
IPv6 address.

There was one last bookkeeping trap. A deliberately invalid application request
marked the generic session unusable, which also blocked the separate STOP
command. The timer had not been armed in that case, but cleanup correctly
refused to pretend it knew that. The final correction permits only the verified
STOP path after a completed application error. Live SIGTERM, SIGKILL and invalid
request tests then all restored RAM and unloaded; the native tests covered 344
failure boundaries for each of the two autonomous protocol variants.

This is bounded work sharing the processor with stock firmware. Linux still
moves packets, and an arbitrary runaway task is still an arbitrary runaway
task. But the hundred ticks per second no longer come from Linux asking politely.
The card has a clock, tasks waking to it, and a small IPv6 front door.

## A word through another door

The next question was whether Linux could speak to our code without asking the
RAID command loop to carry the message. Two message registers looked promising.
They were zero, their interrupts masked, and the matching firmware offered no
obvious direct use of message number one. That was enough for an experiment,
not enough to declare them ours forever.

Linux wrote a tagged word. The timer interrupt answered through the other
register. Eleven milliseconds, and the firmware command counter had not moved.
A very small conversation, but it had gone through another door.

The first attempt had already answered in six milliseconds. It also taught us
that the outbound status register can be read by the i960 but acknowledged only
by the PCI host. Our simulator had been too generous. Cleanup refused to release
the borrowed memory, as it should; the host needed a reboot. With that distinction
fixed in both code and model, the repeat restored the timer, every borrowed RAM
byte, the message words and their pending bits. The driver unloaded. Vader went
back to answering HTTP.

One echoed word is not a control protocol, and it cannot yet stop a runaway task.
That is the next door: framing, sequence numbers, and a STOP that does not need
the old command loop to cooperate. No new flash was written for this experiment.

## A sentence, and a stop

The single word became a small protocol: halfwords through the same two message
registers, assembled into checked frames in our own RAM. An epoch says which
session a sentence belongs to. A sequence number says whether we have heard it
before. A retry gets the old answer, not a second execution.

On the card, a damaged checksum and a wrong epoch were rejected. Then Linux sent
STOP through this new door. RTEMS stopped at tick 362. Another question came
through, and the answer was still 362. The control interrupt could keep answering
without letting the tasks run again. A final command stopped the timer too.
Through all of this, the old firmware command counter stayed at one.

Cleanup still went through the old, carefully checked path. Every borrowed byte
came back, the driver unloaded, and Vader returned to the web without a reboot.
This was a stop for the bounded tasks we can already run. A task that masks the
control interrupt can still shut that door. Opening it safely means giving
interrupts their own stack and preserving a complete interrupted context. That
is the next piece of the machine we have to earn.

## A stack of our own

The interrupt needed somewhere of its own to work. There was a catch: the card
was already servicing an interrupt when it called us. On this processor, another
interrupt builds its frame on the current stack. Changing the base interrupt
stack pointer would not move the frame we actually cared about.

So we left that frame where the processor put it. A small assembly bridge saved
the globals, moved the C work onto guarded RAM of our own, and came back through
the same hardware return. The processor kept its PC and arithmetic flags; we
saved and restored the trace controls explicitly. No invented return frame.

Three runs took forty-two interrupts each. Register sentinels survived. Twenty-five
levels of calls on each side of the interrupt unwound with their local buffers
intact. The observed process controls came back unchanged. Even a trace-mode bit
deliberately changed inside the handler returned to its old value.

Then the same stack carried the control protocol: another 546 interrupts, STOP,
a status check, and the final timer halt. No guard or frame errors. All borrowed
RAM was restored, and the web server came back without a reboot.

We had earned a private workbench for the interrupt, not permission to leave its
old frame behind. To switch away from an interrupted task, that frame and its
whole stack ancestry must belong to something that will keep them alive. That
ownership problem is now the next piece, rather than an invisible assumption.

## Two unfinished interrupts

The next test let an interrupt remain unfinished. Task A was spinning when the
timer arrived. Its handler saved the machine, entered the scheduler, and stopped
there while task B ran. B then took its own interrupt, on its own stack. For a
moment there were two unfinished returns, each belonging to a different task.

That had been the ownership problem. Now the records named their owners, the
hardware frames stayed in the right task stacks, and the C handlers had separate
workspaces. When the scheduler came back, each interrupt finished the return it
had started. The register patterns in the spinning loops were still there.

Three runs gave the same accounting: thirty-two ticks, sixteen entries and
sixteen returns for each worker, and thirty-one sightings of both interrupt
continuations alive at once. Neither loop volunteered to yield. The timer was
actually taking the processor away and giving it back.

At the end, the controller asked the workers to stop and let both unwind. Only
when every return was accounted for did it remove the timer and return to the
host. No reboot, no changed flash, no missing bytes in the restoration checks.
Vader went back online.

It was still a bounded visit inside the firmware's command. A resident monitor
must accept STOP from outside while those tasks are busy, and it must respect
scheduler critical sections. But two CPU-bound tasks had now shared the card
through real timer preemption, with their unfinished interrupts kept safe.

## Waiting its turn

Preemption also has to know when to wait. We gave task A two nested reasons to
keep the processor, using RTEMS's own dispatch-disable calls, then let the timer
interrupt it anyway. Four ticks passed. We released the inner level. Four more
ticks passed. The clock was working; the other task was ready; the scheduler
still owed A the chance to finish its critical section.

The records caught that distinction on every interrupt. A different heir was
waiting, but A remained the owner. Only releasing the outer level let B start.
By tick nine A was back, returning from the enable call that had finally handed
the processor away.

Three runs agreed. Both workers went on to pass their register checks, every
unfinished interrupt found its way home, and the borrowed RAM matched again.
Vader came back with HTTP 200. No reboot and no new flash writes.

The next question is external: can the host ask these busy tasks to stop over
the independent control channel, and can they unwind safely while a firmware
command is still in progress? We have tested the channel and the task contexts
separately. Their meeting is the next experiment.

## A knock while the door is closed

The firmware command was still waiting for our program to return. That used to
be the awkward part: the usual way to ask the card to do something was already
occupied by the thing we wanted to stop.

This time the host knocked through the message registers. The driver kept the
original command open, waited for a ready signal, and sent a stop word through
the side channel. On the card, a timer interrupt found it while both workers
still owned unfinished interrupt returns. It woke the controller. The workers
noticed the stop flag, finished their checks, and let those returns unwind.

Only then did the card answer: drained. The host checked that the firmware
command was still pending, acknowledged the answer, and let the card clean up
the message words and finally return. The order mattered. A stop request is
not permission to erase the stack of the interrupt carrying it.

Three trials stopped at ticks thirty-four, forty-one and fifty-two. Every entry
had a matching return. The register patterns survived, the borrowed RAM matched,
and Vader came back without a reboot or another flash write.

There is still an honest qualification. These loops do not volunteer to yield,
but they do know how to notice a stop flag. We have not taught the monitor to
safely cancel an arbitrary program that refuses to cooperate. Nor is this yet a
second user command running beside the first: the driver performed the bounded
handshake inside its existing lock. Those are the next doors, now that the knock
and the safe return have met on the real card.

## The request that had to wait

We sent the next stop request at an inconvenient moment on purpose. Task A had
disabled dispatch twice. The timer could still interrupt it, and at tick eighteen
it found the host's request. The controller was ready to act. It had to wait.

Releasing the inner level at tick twenty-eight changed nothing about that debt.
Only the outer release at tick forty let the controller run and the two
unfinished interrupt returns drain. We repeated the experiment with the request
arriving in the remaining inner scope instead, at tick thirty. Same ending.
The clock had continued throughout; the scheduler had respected the boundary.

Then we withheld parts of the conversation. With no STOP word, the card reached
its own one-hundred-and-twenty-eight-tick deadline and wound the workers down.
With no final RELEASE, it counted out its finite waiting loop, recorded the
expected timeout flag, cleaned up its message words, and returned anyway.

Three attempts at each of four cases: twelve returns, twelve complete restoration
checks. No reboot. Vader came back. The timeout flag was evidence that the test
had taken the intended branch, not a fault we quietly ignored.

The host was still there to observe those missing messages and verify the
cleanup. That is a narrower claim than surviving a vanished host, and the workers
still knew how to stop. But the monitor now had two more demonstrated habits:
it could wait through a legitimate critical section, and it could stop waiting
for a message that never came.

## Vader learns to read the clock

The next addition was quieter. Vader's page began telling us about the machine
serving it: RTEMS and lwIP versions, the i960RP, its configured memory, and the
packets moving through its little network interface. The uptime came from the
card's own timer ticks. Refreshing the page made the seconds and counters move.

Some boxes stayed honest and empty. We had measured the timer bus, not the CPU
clock. We had no idle-time accounting to turn into a load percentage, and no
known temperature interface to interrogate. Borrowing the Linux host's numbers
would have made a fuller dashboard and a less truthful one.

Twenty-four HTTP checks passed. We stopped the new runtime, checked that it gave
all the borrowed RAM back, and started it again. The mask still stared out of the
page. Underneath it, the card could now say how long it had been awake.

## A second hand on the controls

Until now, the host driver had arranged its own stop request while waiting for
the card. The next test gave that decision to another host thread. One thread
was still inside the firmware callback. The other used an ioctl to knock through
the message registers without waiting for the first thread's session lock.

That needed a smaller lock and a carefully limited window. The window opened
only after the command was submitted. Before the driver could consume the reply
or restore memory, it closed that window and waited for any control operation
to finish. A late request found a closed window, not memory that had already
been handed back.

We tried competing stop requests. One got through; the other was refused. A
wrong epoch was refused too. Closing an extra descriptor alias did not end the
calls that still held the file. Three card runs drained both interrupt contexts
and restored every borrowed byte. The web page answered again.

This was concurrency with an ownership rule, not permission to kill arbitrary
code. The workers still knew how to stop, and the live close test was an extra
alias, not a forced final close or an unplugged card. Those remaining lifecycle
cases now have a real control API to test against.

## Closing the handle underneath it

The next test closed the last user descriptor while the callback and control
ioctl were still inside the kernel. The number vanished from the process's file
table. The work did not vanish with it. Each syscall still owned a reference,
and final release waited until both were finished before restoring the card.

Then we asked Linux to unbind the driver while the same exchange was running.
Removal reached the session lock and waited. The stop completed, the interrupted
tasks unwound, the borrowed bytes went back, and only then did the driver unmap
its BAR. The old file could still exist, but it could no longer touch the card.
Closing it finally released the experiment object.

One early unbind test caught our evidence machinery rather than the card. The
successful close message was in the kernel log, but the exported log length had
not been updated. The verifier refused the truncated capture. We kept it,
checked the saved bytes against the kernel's completion record, fixed the log
publication, and repeated the tests.

Three final closes and three unbinds then passed with complete raw captures.
The order was the result: finish the active calls, restore what was borrowed,
then release the resources. Vader answered again without a reboot.

The card stayed powered through all of this. Pulling it out, losing the host,
or trying to stop a program that refuses to cooperate are different questions.
This test answered the narrower one we could now ask precisely: what happens
when the owner closes the door while the controlled work is still coming home?

## The answer we refused to guess

The next experiment made the conversation fail halfway through. Once, the host
never sent STOP and closed its last descriptor. Once, it heard that the workers
had drained, withheld RELEASE, and asked Linux to unbind the driver. Both were
controlled omissions. We were testing the host's response to uncertainty, not
pretending to have pulled a PCI card out of a running computer.

The card still had its bounded escape paths. Its completion bit eventually
appeared. That was the tempting part: a light on the dashboard, after the
protocol that explained the light had already failed. The driver declined to
guess. Both calls returned a timeout, the transaction remained pending, and the
borrowed memory stayed marked dirty.

Nothing was put back. Nothing was freed. The DMA buffer, BAR mapping and driver
object remained alive, and an ordinary module unload was refused. Even after
unbind removed the driver's public attachment, its private responsibility did
not disappear with it. The captured state stayed unchanged after the refusal.

We copied the evidence off the PC before rebooting, once for each case. This
was retention until a fresh boot, not a claim that the failed session had cleaned
itself up. The next hard question remains a worker that will not cooperate at
all. But the smaller answer is now measured: when we cannot prove completion,
we can at least refuse to turn somebody else's unfinished work into freed RAM.

## The workers that did not listen

Until now, even the busiest worker eventually looked at the stop flag. That is
a useful agreement, but it is still an agreement. We built another pair that
never looked. The host said STOP; both kept counting for four more timer ticks.
The counters made their refusal visible.

The controller did not manufacture a return address or pretend the interrupted
calls had finished. It suspended both tasks through the scheduler, stopped the
borrowed timer, and kept every unfinished interrupt frame where it was. Then it
lowered its own scheduling priority below the workers. Neither ran. Ten thousand
checks later, the counters were still fixed and the task and interrupt stacks
still had the same checksums.

There was a small but essential change in vocabulary. The reply was QUIESCED,
not DRAINED. Each worker still owned one live interrupt continuation. We wrote
that fact into the report instead of clearing the flags to make it look tidy.
Only after the controller returned through the firmware callback could the host
put the entire borrowed workspace back. We were throwing away this whole tiny
RTEMS world, not promising to cancel one arbitrary task and keep its neighbours
healthy.

Three sessions passed. STOP arrived at ticks 36, 41 and 52; containment followed
at 40, 45 and 56. Both workers stayed comfortably short of the experiment's
emergency iteration ceiling. Every session restored RAM and the message unit,
and the Linux module unloaded normally. The IPv6 Vader page came back without
a reboot.

This buys us a precise new capability: a worker need not agree to stop, provided
interrupts can still reach the controller and the scheduler remains intact. A
worker that masks interrupts forever, smashes a kernel structure or owns a lock
somebody else needs is a different problem. The old card has no new protection
boundary just because we have learned another way to ask its scheduler for help.

## Waiting for the outer door

The next batch put the refusal to stop inside the scheduler's critical sections.
At depth two, STOP arrived at tick 18. At depth one, it arrived at tick 30. The
controller heard both requests, but neither gave it permission to break the
scheduler's own rules. It waited until the outer section released at tick 40.
Four ticks later, both workers were suspended with their unfinished interrupt
frames still intact.

There were six initial passes. The larger report also earned us a Linux compiler
warning: the host's temporary decoding array had pushed a stack frame beyond the
configured warning threshold. We moved that array off the stack and ran all six
again. The second set passed too, including the full restoration after each run.
The warning and the first captures stayed in the archive; they were part of the
work, not something to edit out of the story.

Then we made the conversation fail in three different places. No STOP, while the
last descriptor closed. No RELEASE, while Linux unbound the driver. Finally, a
perfectly good reply whose local decoded marker we deliberately invalidated,
after the card had already completed the callback.

That last one mattered most. The pending flag was clear. The runner was no longer
uncertain. But the proof needed to put memory back had failed validation. The
driver kept the dirty workspace, DMA buffer and BAR mapping, and refused to
unload. Completion was a fact; permission to reclaim memory was another fact,
and we had finally tested that they did not have to travel together.

All three failures kept their resources until reboot. We saved and independently
checked each capture before restarting the PC. The original reply in the third
case still decoded correctly: only the host's validation copy had been damaged.
That distinction is why the experiment tells us something about the refusal
path without pretending the card suffered a physical bus fault.

All three reboots returned to Linux. Fresh firmware checks passed, and the
IPv6 Vader page was back with its live system information.

The next boundary is ownership inside a system we intend to keep running. A
whole disposable RTEMS instance is one thing. A cancelled task whose neighbour
still needs its lock or I/O buffer is another. The machine has earned a stronger
stop contract, not a promise that arbitrary code can now be safely forgotten.

## The lock that could not be given away

The next experiment gave the tasks something worth arguing over: one real
RTEMS mutex, a value halfway through an update, and another task waiting to
read it.

An old operating system has old assumptions. In this RTEMS release, a plain
binary semaphore was not enough to establish ownership. Its priority-inheritance
mutex was. We checked the source, selected that form, then asked the supervisor
to release a lock belonging to somebody else. The card answered with error 23:
not the owner. The waiter stayed asleep. The unfinished value stayed unfinished.

Cancellation became a request with obligations. First, stop lending out the
buffer. Then wait for the outstanding reference to come home. Only the owner
could roll back its staged update and release the mutex. The waiting task saw
the old committed value before making its own change. The retired owner could
then restart, on the same stack and task ID, under a new generation. Messages
from its previous life no longer counted.

There were sixty of those cycles in the three longer sessions, after the first
smoke test. Wrong tickets, duplicate completions and old generations all got
their turn at the door. None persuaded the card to forget a live reference.
These were software leases, deliberately: a model for future I/O ownership,
not a claim that an actual DMA engine had stopped.

For the owner we would not allow to finish, we kept its lock. We suspended the
waiting task too, preserved both stacks, and let the unrelated worker carry on.
Quarantine was not repair. It was an honest way to keep one broken dependency
from becoming everybody else's broken memory.

The host had to learn the same distinction. We closed its last descriptor while
the owner still held the mutex and the waiter still needed it. The firmware
callback was already over; there was no command pending. The driver nevertheless
refused to put the old RAM back. It kept its buffers, mapping and module reference,
and ordinary unload failed. We saved the evidence before asking the PC to reboot.

Linux returned. The same short experiment passed again, including full RAM
restoration, and the IPv6 Vader page answered from the Mac. The captured card
responses matched the native policy through all 1,212 callbacks, including the
three leading up to the deliberately refused close.

The ownership rules now survive across callbacks. They still have to meet the
interrupt-driven containment work in the same program. That meeting is the next
experiment, not something sixty successful handoffs can quietly stand in for.

## The waiter meets the interrupt

Then we put the lock into the experiment that could interrupt its owner.

There were three workers now: the owner halfway through an update, a neighbour
asleep on its mutex, and an unrelated task doing arithmetic. The owner and the
arithmetic task each had their own interrupt stack. The waiting task had no need
to enable interrupts at all. The host sent STOP while the firmware callback was
still running, through the separate control channel we had already earned.

The first run found a problem in the reporting, not in the lock. Eleven words
made forty-four bytes on the Mac. The old i960 compiler gave their structure
forty-eight. A careless `sizeof` copied padding over the next diagnostic, and
the host refused to believe the reply. It kept its memory and refused to unload.
We saved the failed run, changed the wire copy to its exact field count, and
rebooted. The earlier persistent test had escaped this bug only because it wrote
its heartbeat over that same extra word afterward. We fixed that copy too.

With the report corrected, STOP at tick 18 waited for the outer critical section
to open at tick 40. STOP at depth one, tick 30, waited for the same boundary.
The owner came back through its real interrupted call chain. Three times its
cancellation checkpoint found the buffer still lent out. At tick 44 the reference
came home. The owner rolled back and released the mutex; the neighbour saw the
old committed value and continued.

For the owner we would not allow to cooperate, we kept the lock and suspended its
waiter too. Their stacks and the unfinished interrupt frame stayed intact. The
unrelated task ran for four more timer ticks. Containment had finally met a
shared resource without pretending suspension repaired it.

Then we withheld the reference altogether. The card stopped its timer, reported
quiescence, accepted RELEASE and returned to firmware. All of that was true.
The host still refused to reclaim the workspace. A stopped CPU path does not
make a borrowed buffer unborrowed. The module stayed pinned until reboot.

Both reboot recoveries returned to Linux. Ten asynchronous sessions had now
passed full cleanup, and the corrected persistent loader passed another forty-eight
callbacks. The web service came back and the Vader page answered over IPv6.

The leases are still software, and the experiments still end their whole RTEMS
instance. We have not smuggled a DMA completion or a permanently resident operating
system into the conclusion. We have made the next dependency explicit, and seen
the machine refuse to cross it without evidence.

The next experiment kept the instance alive long enough to meet its own past.

We added another lock and another waiter. A held the first lock. B held the
second and waited for A. C waited for B. Stopping A now meant following the
chain all the way to C. The fourth worker had no claim on either lock. It could
keep doing arithmetic without joining the freeze.

On a clean stop, the interrupted owner returned through its original frame,
waited for the borrowed reference and rolled back. B saw the old committed
value; C saw B's completed update. A later host call restarted those same task
IDs on those same stacks. The controller had not rebuilt RTEMS behind our backs.

On the other path, we left A suspended inside its interrupt, with B and C still
waiting. Then we returned to firmware and came back again. The independent
worker ran through twelve more execution epochs on its own interrupt stack. The trapped chain's stack hashes did not move. A reference
could come home later without magically repairing the two locks.

Four sessions completed a hundred and two callbacks and returned all their
borrowed RAM. In a fifth, we closed the host descriptor before saying FINALIZE.
The timer was stopped. The callback had returned. The module still kept the
resident memory and refused to unload. Six good replies had not granted
permission to throw away the seventh thing: the instance itself.

We saved the evidence and rebooted to clear that deliberate refusal. SSH took
long enough to make us ask for a look at the screen, then returned on a new
boot. Another eighteen callbacks passed. The web service came back too, and
Vader answered over IPv6 again.

RTEMS survives between these calls as state, including an unfinished interrupt
frame. Its timer does not keep running beside the stock firmware. That next
step still needs an agreement about who owns the machine when nobody is on
the phone.

So we kept the phone call open.

The next version stopped returning to firmware between bursts of arithmetic.
The firmware's callback stayed parked while RTEMS ran, and the host used the
small independent message channel to grant a lease, renew it, or ask for STOP.
Every tick checked the timer, vector and masks that made the arrangement possible.
The old instruction counter wrapped around instead of ending the worker's day.

A minute passed without a firmware round trip. The host renewed the lease 291
times. The two workers took more than twelve thousand interrupts between them,
then came back through their original frames, gave up their resources and let
the firmware continue. The original RAM was restored and the module unloaded.

A lease also needed a way to say no. Withholding the first grant stopped the
experiment. Granting it and then merely asking for status stopped it too: looking
at a clock is not winding it. The timer enforced the renewal deadline at exactly
512 ticks. Even a diligent host could not renew forever. At 24,000 ticks, after
559 accepted renewals and about a hundred and fifteen seconds, the administrative
cap ended the run. That return and cleanup passed as well.

The chain of locks came along. A, B and C stayed frozen while the independent
worker ran under another lease, and another. Returning a borrowed reference
still did not turn suspension into recovery. Across nine sessions we counted
forty thousand one hundred and eleven hardware checks without a reported change.
The Vader page came back afterward, on the same Linux boot.

We had made continuous execution real, but within a deliberately narrow bargain.
The firmware was waiting for its call to return. Its timer could accumulate
pending work; its SCSI and DMA engines had not signed over their ownership.
A parked continuation and a checked interrupt mask were enough for this test.
They were not permission to call the whole board ours.

## A corridor inside the controller

While the kernel learned how to keep a lease, the application side acquired a
small spaceship. A CHIP-8 interpreter ran as another bounded RTEMS worker,
sending its little monochrome screen back to a browser. Seven hundred and five
replies matched the native version exactly. The browser could move the ship and
restart it; the card could still put everything back afterward.

Then the flat screen acquired depth. Eighty rays crossed a small map using
integer arithmetic, stopping at walls and turning their distances into colored
columns. We could turn and walk through the scene in a browser while the i960
built the picture. Each call had a column budget and each ray a step limit. A
half-finished frame stayed private until its last column was ready.

The surprising part was the stopwatch. A complete frame took about sixty
milliseconds through the kernel path, but rendering and publication added only
seven and a half milliseconds over returning an existing picture. Uploading the
request and arming the callback used nearly thirty-three. The picture occupied
4,800 bytes; the ordinary paired checks read more than nine hundred thousand.
A smaller picture could not make that conversation shorter.

The old memory helpers were measurable too. Copying four kilobytes through the
byte loop took about 1.36 milliseconds, whether the pointer was aligned or one
byte off. A semaphore round trip took about a hundred microseconds. These were
estimates from repeated, bounded work and host command timings, not a newly
discovered CPU clock. They were enough to choose where to look next.

Across the renderer, memory tests and browser session, all five hundred and
forty-eight replies matched the native reference. The browser delivered about
ten updates a second in the short trial. Both sessions restored RAM and unloaded,
and Vader returned over IPv6 without a reboot. There was still no Doom in that
corridor. There was now a picture, a reproducible measurement, and a much better
idea of what stood between the two.

## A door without a caller

Until now, the long-running workers had a useful alibi: somewhere underneath
them, the firmware was still waiting for a callback to finish. The next question
was whether we could enter our own monitor after that caller had gone home.

We could. A short setup call armed the timer and returned. Later, a message from
the host met the card in its interrupt handler. The handler moved onto our owned
stack, kept the original firmware return frame intact, and waited for release.
No firmware command was pending during that conversation.

The first attempt also demonstrated why a conversation needs an ending. We
forgot to consume the ENTER message. When the waiting loop expired, the next
interrupt could see the same invitation and enter again. The host timed out.
Instead of guessing that the card was finished, the driver held onto its memory
and module. Getting back required a reboot and help at the machine. The failed
captures stayed in the archive.

Consuming the invitation fixed that. Then the old compiler supplied a second
surprise: the card said it had denied hardware ownership, but its diagnostic
number said zero. The disassembly told the story. A comparison of the proof mask
was followed by another comparison that overwrote the condition codes before
the result was used. Native tests had passed; the i960 code had not done what the
C said. Explicit result stores removed the ambiguity.

Five final sessions entered the monitor twenty times. Five deliberately
withheld release and came back on their own. Ten requests to take ownership
were refused. Every final session restored its RAM and unloaded, and Darth Vader
returned to the IPv6 page.

The refusal mattered as much as the return. The matching firmware uses both
primary DMA channels. The board also has its own SCSI and cache machinery, with
no established contract for handing those engines over. Six quiet registers
are a photograph, not a permission slip. We have a bounded door into the monitor
without a pending callback. We have not yet earned the right to move the rest of
the controller through it.

## Four bytes at a time

The first optimization was almost embarrassingly literal. The processor could
move a word, but our little C library had been carrying every picture one byte
at a time. We taught the copy routine to line up both addresses and move four.
The clear routine learned the same trick. Misaligned edges still went through
the old byte path; different source and destination alignments kept it entirely.

Before timing anything, we gave those routines awkward jobs: empty copies,
short tails, every small alignment, overlapping moves and negative fill values.
Native guard pages made a reach past a boundary an immediate failure. On the card,
five thousand two hundred and eighty reference cases ran in bounded batches.
Then the normal raycaster answered, with every byte still matching the host.

The stopwatch rewarded the small change. A four-kilobyte copy fell from about
1,358 microseconds to 411. A clear fell from 861 to 186. We ran the old version,
the new one twice, and the old one again, keeping the same checks around them.
The numbers held. All two thousand one hundred and five replies matched, and
all five sessions restored their memory and unloaded.

The whole frame did not become three times faster. Its kernel transaction fell
from 60.31 milliseconds to 57.95: just under four percent. The two picture copies
explained almost all the saved execution time. Uploading, arming and reading the
paired evidence still took most of the trip. Making the card work faster had
made the cost of talking to it easier to see.

It cost 160 bytes of code and no extra working memory. The raycaster kept the
new helpers; the production network service kept its tested build. Vader was
back afterward. The next useful question was now about the conversation, not
how many bytes a load instruction could carry.

## Letting the old job wait

Then came a useful clarification: the card did not have to keep being a RAID
controller while it was running RTEMS. Rebooting to get that job back was fine.
That did not make its hardware harmless, but it removed the obligation to keep
both employers happy at once.

The manual was quite specific about the first trap. Disabling an active DMA
channel suspends it; it does not promise that every buffered transaction has
finished. So the new entrance refused anything but clean, inactive channels.
It also took away PCI bus-master permission and disabled grants to the external
secondary-bus masters. It left the memory decoding that our host control channel
needed. One tempting shortcut, disabling the external local-bus master, was
explicitly forbidden by Intel. We left that one alone.

The rehearsal worked. An ordinary setup call returned, a later timer interrupt
opened our monitor, and two RTEMS workers began competing for the processor.
The firmware's old interrupt frame stayed parked underneath them. A hundred
timer ticks later, both workers drained their interrupt frames, the borrowed
controls went back, and the usual RAM checks passed.

Then we removed the return trip. In the resident experiment the setup callback
was already finished before takeover. The host could ask for frozen status
snapshots without invoking the firmware. A deadline stopped the workers after
1,200 ticks. A second run obeyed a host STOP at tick 581. In both cases every
worker interrupt frame had returned before the monitor parked. The original
firmware continuation stayed exactly where we had left it.

Closing the host handle did not mean the card was finished with its memory.
The driver kept the allocation and its own module pinned. That was deliberate.
The less convenient part was recovery: the first reboot did not bring SSH back
promptly, and help at the machine was needed again.

We now have a tested way to give RTEMS the CPU and fence off the unused PCI
engines for this allocation. We still owe the cache coprocessor a proper
completion contract before claiming the rest of RAM, and the resident system
needs its own packet transport before Vader can move in. The old cooperative
arrangement is still there, documented and working. It has become an option
rather than a condition of every experiment.

## Checking the same bytes

The faster copy routine left a stubborn number on the stopwatch. Uploading and
arming still took nearly thirty-three milliseconds. So we put timestamps around
each command, instead of treating that stretch as one mysterious expense.

There were three uploads in an ordinary frame. One carried the request. One
replaced the old result with a sentinel, so yesterday's answer could not pass
for today's. One changed the dispatch-table word. The last carried only four
bytes, yet its completion wait was about eleven milliseconds. The waiting,
not the amount of data, dominated all three.

We left those guarantees alone. There was cheaper work to do on the host. Every
command counted changed bytes across its DMA buffer one at a time. Every reply
walked the staging image to decide, byte by byte, which parts were allowed to
change. Eight-byte counting and exact range comparisons could ask precisely the
same questions with less arithmetic.

The tests were deliberately fussy. Every immutable byte got its own corruption
attempt. Every possible output boundary was checked. The counter faced more than
half a million pattern, alignment and length combinations, followed by every
pair of adjacent byte values. The failure paths still refused uncertain work.
On the card, five sessions returned two thousand one hundred and five matching
replies and restored their memory afterward.

The paired readback and audit fell from 12.22 milliseconds to 10.61. The full
kernel transaction fell from 57.83 to 55.74. We still read the same nine hundred
thousand bytes in the ordinary paired audit. We still checked the guards and
old code. We had made checking cheaper, not asked the card fewer questions.

Forty-three thousand nine hundred and four command measurements made the next
limit plain. A much larger gain would need a better conversation with the card:
one that could share the cost of those uploads without mistaking an old frame
for a new one or forgetting how to stop. For now, the small gain was real, the
captures replayed, and Vader came back over IPv6.

## A conversation without the firmware

The card had learned to keep RTEMS running while its old firmware waited. The
next question was whether it could keep talking to the host in that condition.
The old network path still needed firmware callbacks to move packets. We wanted
to leave the callback counter at one.

There was an unfinished piece of hardware archaeology first. In the exact
firmware recovered from the card, a routine loaded eight words into a register
block, submitted a command, waited for bit zero and acknowledged it. Another
version waited for DMA and a firmware event as well. That looked like the
beginning of a cache-engine completion contract. It was not yet permission to
reuse every byte of RAM.

The first live readings made that distinction useful. The supposed configuration
register returned its own address. Two neighbouring halfwords resembled pieces
of their addresses too. We saved the values and kept the ownership gate closed.
A completion sequence in a disassembly deserves investigation; an unexplained
number from a board does not deserve a new name just because we need one.

Networking could move ahead inside the memory we already owned. A small protocol
used the card's message registers, four bytes at a time. The host announced a
packet, supplied its words in order, then committed it. The card held outgoing
bytes until the host had copied them and released the buffer. There was no new
DMA descriptor and no need to switch PCI bus mastering back on.

RTEMS kept two workers alive. One ran the IP stack; the other kept counting.
The hardware timer still chose between them. UDP packets came back over IPv4
and IPv6, including packets that filled the link's fifteen-hundred-byte limit.
TCP returned four thousand and ninety-six matching bytes in each family. A tiny
HTTP page answered from the resident kernel. We dropped a TCP data packet in
each family on purpose, and both conversations recovered.

Then we asked it to stop. The first resident run parked at five hundred and
thirty-three ticks. The next ran to its own six-thousand-tick deadline. A final build repeated the resident network test and stopped at eight hundred
and forty-six ticks. In all three runs, the
workers finished their interrupt continuations before parking, and neither
returned to the waiting firmware. Packet requests after that point were refused.
The memory stayed attached to the stopped machine until reboot.

The saved packets supplied a second account of the experiment: two hundred and
thirty-six checked IP packets, matching TCP streams and the retransmissions after our
intentional losses. Fifty-seven damaged versions of the status snapshots were
rejected by the replay checker. The single firmware callback had remained single.

The reboot was still a less polished part of the conversation. SSH disappeared
long enough to ask for a check at the machine, and a later fresh boot proved
recovery without explaining exactly what had made it return. The public service
remained the older cooperative profile. After the final reboot, the paired RAM reads matched the original image and
Vader answered over IPv6 again. The new resident endpoint had proved a
path through the message registers; cache ownership, more RAM and a dependable
exit still needed their own evidence.

## The time spent talking to nobody

The thirty-two milliseconds had looked like the price of asking an old RAID
controller to move data. The next trace found something less dignified.

Before every upload, the firmware printed the offset and size to its serial
port. It waited for each character to leave. The four-byte dispatch change paid
for that little announcement just as faithfully as the much larger request.
Nothing had to be connected to the serial port for the time to be spent.

We could test that without removing a single check. First we matched the live
controller methods, the formatter, the UART routine and the neighboring upload
code against the recovered firmware. Then we changed the first newline of one
format string to a zero byte. The DMA code stayed where it was. The completion
status still had to be right. The sentinel, sequence, paired reads and guards
still had their say. We even added paired reads of the altered string and its
neighboring handler on every request.

The first run was startling. The upload waits nearly vanished. The second run
was useful in a different way: it refused to start.

Our extra cache-and-PING roundtrip had disturbed the delicate first-entry
sequence. The RAM table contained the cache callback, but the processor kept
answering PING. Four harmless attempts were enough. The gate refused to enter
user code, restored the original string and all the borrowed RAM, and unloaded.
The serial chatter had been hiding a dispatch-visibility problem as well as
wasting time.

We kept the original startup handshake and moved the silence just after it,
without inserting another PING. Ten consecutive sessions then opened, ran,
restored and closed. Only after that did we repeat the full comparison.

Baseline, quiet, quiet, baseline. The three upload waits went from 32.129
milliseconds to 0.368. The complete kernel transaction went from 55.840 to
24.141. Restoring the string brought the old delay back. The renderer itself
had not become faster; the card had stopped narrating every upload to nobody.

Five final sessions returned two thousand one hundred and five matching replies.
The discarded startup attempt stayed in the archive beside the successful runs.
The original format byte went back before each unload, the full memory checks
passed, and Vader answered over IPv6 again. The optimization had changed one
byte in RAM for a while. The evidence, including the refusal, was considerably
larger.

## The other cache controller

The register still answered with its own address.

We had found the command, the wait loop and the acknowledgement. They were real
instructions in the matching firmware. But knowing what a routine does is not
quite the same thing as knowing whether this board uses it.

This time we gave the read a control experiment. Known RAM returned the patterns
we had put there. The processor's own registers returned sensible values. The
suspected cache registers, even with the CPU data cache disabled, continued to
say `40800000` and `40800008`. It was time to stop treating that answer as a
status report.

The missing references were in the bootstrap. One branch installed the external
cache commands we had been studying. Another installed a routine that did the
XOR work with the i960's own load, XOR and store instructions. That branch also
used the processor's DRAM controller. The live dispatch table matched its hooks,
including several gloriously unambiguous no-ops where the other branch installed
cache status and acknowledgement functions. The final probe supplied the rest:
board selector six, the CPU XOR pointer, and a firmware report of sixteen
megabytes of memory.

The apparent obstacle had changed shape. We still had to account for SCSI,
firmware allocations and the saved continuation before claiming more memory.
But a completion bit belonging to the other hardware path was not going to
answer those questions for us.

Meanwhile, there was useful space in the allocation we already owned. We gave
the network queue thirty-two packet slots instead of eight. The first longer
run caught a less archaeological bug: when the card said its receive buffer was
busy, the host dropped out of the test instead of keeping the packet. We saved
the failure, kept the packet pending on an explicit busy reply, and left
uncertain operations as failures.

The next run exchanged three rounds of IPv4 and IPv6 traffic, recovered from
intentional TCP loss, and kept running beyond its old one-minute limit. At
exactly twelve thousand ticks it parked, with both task interrupt continuations
drained. The bytes and the failed attempt both went into the archive.

That was more room for the network, not a claim on the rest of the card's RAM.
The distinction was becoming something of a theme.

## The memory that already had an owner

Sixteen megabytes sounded generous until we asked who was using them.

The firmware answered in eight-kilobyte pieces. Its cache began above the low
firmware workspace; 1,876 lines ran up to a table of fifty-two-byte descriptors.
The numbers in the live card matched the arithmetic in the old program. Our
half-megabyte upload buffer was a reservation inside that machinery, not a
lucky patch of unused DRAM. The tempting space immediately above it was still
cache data. We left it alone.

There was room to improve without moving the boundary. The packet queue grew
to sixty-four slots, and the monitor learned to report how full it had become
and how many packets it had refused. We sent ninety-six requests and deliberately
stopped collecting the answers. Sixty-five echoes survived: sixty-four queued
and one already waiting in the transport. Thirty-one were counted as drops.
Then IPv4 and IPv6 clients ran together, and the network recovered.
After the traffic stopped, both tasks kept advancing until the timer reached
exactly sixty thousand ticks. The kernel parked, and we saved the proof before
rebooting the host.

SCSI offered another small piece of honesty. The firmware's own debug strings
named its queue counters. We found the loads, and the increment and decrement
of its outstanding-I/O count. Reading those counters was reasonable. Treating
zero as permission to overwrite every buffer was still a leap: a software
ledger is not a photograph of every engine on the bus. After reboot, the
card reported no outstanding SCSI I/O but still had four scheduler entries.
The short probe restored cleanly, and Vader returned to the IPv6 page.

The next boundary was clearer now. Before moving into the rest of RAM, we had
to retire its old owners and account for everything the monitor would still
need. In the meantime, the memory we had actually earned was doing more work.

## Counting four at a time

With the upload chatter silenced, the next expensive thing was checking that
nothing had happened.

Even a request for a header, without drawing a pixel, spent about five
milliseconds in the callback. The target was walking through twelve kilobytes
of padding, guards and untouched output, one byte at a time. Those checks had
earned their place. They stayed. We taught them to compare four aligned bytes
at once, with the awkward ends still checked individually.

The header-only callback fell to about one and a half milliseconds. The picture
had not changed, partly because there was no picture in that test.

Then came the renderer. A column was sky, wall and floor; it did not need to
rediscover that classification for every pixel. The frame hash could load four
bytes at once too, provided it still fed them through the same arithmetic in the
same order. The old renderer stayed beside the new one as the judge. Every
returned byte had to agree.

The full-frame callback went from 11.925 milliseconds to 7.360. Including the
uploads and audits, the kernel transaction went from 24.169 to 19.471.

We also tried asking the card whether it was finished more often. That worked,
but the bargain was less attractive: about a quarter of a millisecond less
readback time for seventeen percent more host CPU. The faster polling remained
an option. The recommended build kept the old interval.

Eight sessions returned three thousand three hundred and sixty-eight matching
replies. Each one put the borrowed memory and the quieted diagnostic byte back.
The public web server came back, and Vader resumed receiving visitors.

The biggest remaining bill was moving nearly a megabyte through paired reads
for each ordinary frame. We could make that bill disappear from a benchmark by
checking less memory. That would answer a different question. The next transport
would have to explain which bytes belonged to whom, and prove when a frame was
finished, before it could ask to pay less.

## Two pictures, and a receipt

The next experiment gave the renderer somewhere to leave its work. Two small
slots, each with a generation number, an epoch and a marker saying the picture
was finished. The host had to read the picture, compare it with its independent
renderer and the complete memory audit, then send back a receipt before that
slot could be used again. A full queue was allowed to say no.

The first attempt tripped over an ordinary host-side mistake. We made the array
of capture buffers larger and failed to enlarge three loops that managed it.
The first targeted read reached a buffer that had never been allocated. Linux
faulted; the session could not close cleanly. We kept the crash and the exact
binary, rebooted the PC, and wrote a test that exercised the generated driver's
allocation and cleanup rather than supplying convenient buffers of its own.

With that fixed, four sessions returned five hundred and eighteen matching
replies. Every one still paid for two complete half-megabyte reads. Full queues,
stale receipts, duplicate receipts and a new epoch all behaved as intended.
Even a final picture nobody acknowledged disappeared safely when the original
memory was restored.

The stopwatch refused to call it an optimization. Reading a published picture
and its small description took about six tenths of a millisecond. Producing it
and acknowledging it in separate callbacks took nearly forty milliseconds,
against about twenty-one milliseconds for the old single-frame transaction. Two callbacks meant two full audits. The
receipts had made ownership clearer and the bill larger.

So the old path kept its job. The next experiment would combine a receipt with
the next publication, while keeping the complete audits. Vader returned to the
public web page. The queue had proved a rule about when a picture could be
replaced; it had not yet earned a faster frame rate.

## Holding the other processor still

The next useful fact was a device number. The channel structure said `1000:000c`;
a narrowly addressed PCI configuration read said the same thing. The card's
SCSI engine was a Symbios 53C895 on the private secondary bus. The FlashPoint
trail had been interesting. It was not this piece of hardware.

That gave us a more honest way to stop it. We denied bus mastering, checked the
i960 DMA channels, asserted secondary reset, and left it asserted. This was not
a polite request to finish a disk write. It was a forced stop, with reboot as
the way back. RTEMS kept ticking. The primary host channel kept answering.
IPv4 and IPv6 packets crossed the card while the SCSI side stayed in reset.
The first run reached 12,000 ticks, survived a deliberately full packet queue
and lost TCP packets, and came back through an ordinary host reboot.

It was tempting to call the cache memory ours at that point. The next read
explained why we could not. The cached NMI vector still pointed at the old
firmware, and that handler contained a route back into secondary-bus
initialization. Raising interrupt priority does not make an NMI disappear.
The live PRCB pointed into ROM; our RAM-only probe correctly refused to follow
it. The preserved ROM supplied the fault-table pointer instead. These were
specific remaining owners, not an abstract warning about being careful.

So the memory improvement stayed inside the ground we already owned: seventy-two
MTU-sized packet slots in place of sixty-four slightly oversized ones. That
recovered 9,696 useful packet bytes without borrowing a single cache line from
the firmware. There were still 2,256 mutable bytes left in the allocation,
and all the stacks and guards stayed where they belonged.

The longer run reached 36,000 ticks and ten spaced dual-stack traffic rounds.
At its deadline both task interrupt contexts drained and the card parked.
Another ordinary reboot brought the old firmware back; the public Vader page
answered again.

The next door is the NMI and fault machinery. Holding the SCSI processor still
worked. Making sure nothing can quietly start it again is a separate piece of
work, and the captures now say exactly where to begin.

## The receipt rides along

The receipt did not need a journey of its own. The host could say: I have checked
picture forty; you may replace that exact picture with forty-one. The card first
checked both halves of the request. A stale receipt or a malformed drawing order
left the old picture and the renderer untouched. Only then could the slot change.

The audit stayed. Every request still brought back two complete half-megabyte
snapshots, plus the targeted picture reads. There was simply one request where
there had been two. The same host driver ran both versions, and both drew the
same eighty pictures, byte for byte.

Four sessions returned five hundred and eighty-six matching replies and closed
cleanly, even with a last picture still waiting for its receipt. Kernel time per
frame fell from about forty milliseconds to twenty-five. Host CPU time fell by
nearly forty-three percent. This time the clearer ownership rule also saved time.

It was still slower than the earlier single-frame route. Checking the occupied
slot and sealing its replacement had their own cost, and the complete memory
reads still took nearly twelve milliseconds. Those costs stayed visible. The
queue remained an option, Vader returned to the web server, and the next question
became how much time we were spending checking each picture twice in software.

## Teaching the last doors to stay shut

Reset had stopped the SCSI engine. It had not changed where the processor went
when something went wrong. The NMI vector still led into the old firmware, and
the fault table still belonged to a program that might reasonably try to put
its controller back to work.

We gave those doors new destinations. Every fault-table entry became a local
call to our terminal handler. The cached NMI vector moved too, along with the
interrupt-stack pointer. The handler had its own guarded storage and a modest
ambition: write down what happened, keep the host channel answering, and never
return. Recovering the interrupted task could wait. Accidentally restarting
SCSI could not.

The first deliberate `faulte` made the distinction real. The card reported a
constraint-range fault at the instruction we had planted. Its diagnostics
stayed readable. The reset stayed asserted. No second firmware callback was
needed, and no old handler was invited back in.

NMI seemed harder. The instruction set explicitly forbids posting its vector
as a software interrupt. A synthetic call tested the plumbing, but we kept its
label honest. Then the messaging-unit chapter supplied the missing route:
an external PCI agent could ring bit thirty-one of the inbound doorbell.
We armed only that source in a dedicated image and gave its Linux module one
checked, one-shot write. The next record said vector 248. This time the
hardware had knocked, and our handler had answered.

That made one small piece of cache RAM worth testing. We chose a fixed quarter
megabyte, left the firmware's low workspace and our upload alone, and ran four
address-dependent patterns with the data cache controlled. All 262,144 word
checks passed. The adjacent bytes and the checksums of the protected ranges
stayed unchanged. Another deliberate fault preserved the result; another NMI
test repeated it. We had not acquired sixteen megabytes. We had evidence for
one bounded place to put packets.

The new queue could hold 128 MTU-sized frames there. Its old internal storage
remained reserved, and the general allocator still refused arbitrary firmware
RAM. A guard immediately after the queue joined the guards at the ends of the
tested range. There was finally room to grow without pretending that all the
other questions had disappeared.

The traffic test filled those 128 slots. Of 160 burst requests, 129 answers
survived and thirty-one drops were counted. Six IPv4/IPv6 rounds completed,
including deliberately lost TCP packets. At exactly 24,000 timer ticks, both
task interrupt contexts drained and the resident session parked. The quarter
megabyte had done useful work, and the evidence came back over the same host
channel that had once seemed impossible to open. One more host reboot brought
the cooperative server back, and Vader answered from the public IPv6 address.

## Counting the checks

A picture now arrived with an owner, a generation and a receipt. It also arrived
with a bill for checking it. We asked the card to repeat the hash zero, one, four,
eight, sixteen and thirty-two times, checking every result, while the host kept
performing the complete memory audits. The resulting line was gratifyingly straight.

Hashing one reply cost about 1.755 milliseconds. Checking the whole published
slot cost 2.021. Loading words instead of individual bytes, while feeding the
same bytes through the same hash in the same order, brought those costs down to
about 1.317 and 1.341 milliseconds. Every metadata field and every guard byte
still had to agree.

The headline was smaller than the little benchmark. The callback became ten
percent quicker, and the complete kernel transaction improved by four percent:
roughly twenty-five milliseconds became twenty-four. Nearly twelve milliseconds
still belonged to the paired memory audit. The slightly simpler hash-only change
finished almost as quickly overall; host variation was larger than that difference.

Ten sessions returned one thousand six hundred and ninety-one matching replies.
The long run kept both picture slots occupied, tried stale and duplicate receipts,
reset through eight epochs, and finally closed with two pictures nobody had yet
acknowledged. The original memory came back intact. The public server returned,
and the next application job was to let the browser use this carefully checked
queue, with its real display rate measured rather than inferred from a callback.

## Giving the spare bytes a name

The packet queue left a narrow strip of the tested quarter megabyte unused.
It was tempting to call it free memory. This time we had enough evidence to
make the phrase mean something: sixty-nine thousand nine hundred and fifty-two
bytes, between two guards, with the engines still stopped.

The old RTEMS allocator could manage them. Its heap-extension routine could
not attach a lower, distant island to the kernel workspace, so we gave the
application a separate heap. The familiar calls—malloc, calloc, realloc, free—
finally had somewhere larger to go. The kernel kept its old address. The packet
queue kept its hundred and twenty-eight places.

We also gave each allocation an entry in a small ledger and sixteen warning
bytes on either side. Before the allocator followed a pointer, we checked the
chain it was about to trust. The old code had earned its age; it had not earned
the right to chase a damaged address through someone else's memory.

Then we damaged three things on purpose. First the outer guard, then the byte
just beyond a worker's allocation, then a block-size word in the allocator's
own bookkeeping. Each time the card stopped in our terminal handler. Each time
both workers had made fifty allocations during real preemption. The record
showed a hundred and thirty-six allocations and a hundred and thirty-four frees:
the two live buffers were still there. A broken heap was no occasion to tidy up
by trusting it one last time.

The host read each record twice, acknowledged STOP, and found the reset still
held. Reboot was the way out. The Linux test harness supplied another kind of
evidence: the actual old allocator running with thirty-two-bit pointers, faced
with exhaustion, coalescing, failed reallocations and sixty-four different
corruptions. It passed those too. This was a small application heap with a
sixty-four-allocation limit, not a claim on all sixteen megabytes. Small and
accounted for was becoming a useful habit.

One more detail in the old allocator deserved attention. Just before the raw
buffer, it saved the alignment offset that free would later trust to find a
block header. We checked that word too, and required every used block to match
our ledger. Thirty-two flipped offset bits failed safely in the Linux harness.
A fourth deliberate corruption on the card did the same. This time the startup
checks had filled all sixty-four allocation slots as well: two hundred
allocations, a hundred and ninety-eight frees, and the same two live buffers
left alone in a stopped machine.

Finally we left the heap alone to do ordinary work while packets crossed the
host link. Ten IPv4/IPv6 rounds ran alongside the two allocating tasks. We
filled the packet queue, lost TCP data deliberately, and waited for the card's
own deadline. At thirty-six thousand ticks the hardened build stopped both
tasks with thirty-six thousand one hundred allocations and exactly as many
frees. The warning bytes were untouched. The heap had become useful memory,
and had shown what it would do when that usefulness went wrong. A final reboot
brought the cooperative server back, and Vader answered over public IPv6 again.

## The browser was keeping receipts

Twenty-four milliseconds on the card sounded like forty pictures a second.
The browser disagreed. By the time a picture had been rendered, checked, packed,
carried through SSH and painted on a canvas, there were closer to ten. The
processor was doing its part. We had not yet counted all of ours.

The queue finally reached the browser with its receipts attached. One request
at a time, one occupied slot, the old generation acknowledged only when its
picture had survived every comparison. Reset first let that slot go, then began
a newer epoch. We drove forward, turned, reset the position and took focus away.
The card's pixels matched the old native renderer throughout.

Then the host timers found a surprisingly expensive piece of housekeeping.
Compressing each saved half-megabyte audit at gzip's default level took 21.6
milliseconds. The card's whole kernel request took about 24.4. The archive was
nearly another renderer. Turning the compression level down to one brought that
cost to 5.9 milliseconds. Every decompressed byte was still there, and every
request still had its two full reads. Nothing on the card had changed.

With the browser's extra sixteen-millisecond wait removed too, measured delivery
rose from 9.79 to 13.10 frames a second. That was a Chromium canvas reached over
SSH, not a promise about somebody's monitor. It was nevertheless a picture one
could steer, rather than a reciprocal written beside a stopwatch.

We also interrupted the conversation. A termination signal arrived during a
request; the request finished before the session closed. A TCP connection was
reset while the next picture was being made; the server restored the card instead
of trying the input again. Idle expiry and the frame limit took the same audited
way out. Seven sessions, six hundred and sixty-three full paired audits, seven
clean restorations. The public Vader page came back without a reboot.

Six hundred and forty browser draws had made the next question clearer. Some of
the remaining wait still lived in host bookkeeping. The next place to look was
how we wrote the ledger, not which of its entries we could afford to lose.

## A ledger that stopped copying itself

The receipts had acquired a habit: each new entry rewrote the entries before it.
Replaying the same three hundred and twenty-five requests on the Linux host made
that habit visible. Writing metadata averaged roughly five milliseconds per
request, and the last pages took longer than the first.

Appending an intent before execution and a result after verification brought the
same bookkeeping down to about a tenth of a millisecond. The ledger still needed
an ending: a seal written only after the card had been restored and the audit
streams closed. Cut the file short, remove its ending, or change its account of
what happened, and replay refused it. The full snapshots still had their say.

That was a host result, not another speed record for the card. The parallel RTEMS
experiment had the hardware, so the new journal stayed optional. Its next receipt
would have to come from a fresh browser run, with every audit still attached.

## Memory on loan

Having a heap raised a question that counting free bytes could not answer. If
one task had lent a buffer to another, what did it mean to cancel the owner?
The borrower might still be halfway through reading it. Freeing the memory
would turn a clean-looking shutdown into somebody else's corrupted data.

The little resident system acquired a way to say that plainly. A handle named
an allocation and its generation. A reference kept it alive; a pin said that a
task was still using its pointer. Cancellation stopped new borrowing, but an
acknowledgement from a pinned reader came back busy. The owner could leave
while the reader finished. Only the last acknowledgement returned the bytes to
the heap. A task that never answered kept its memory. Uncertainty was still not
permission to reuse it.

We made the two workers act out that conversation over and over. One lent a
buffer, canceled itself and tried the forbidden shortcuts. The other kept the
bytes across interrupts, checked them, refused to let go while pinned, and
finally acknowledged. Old handles stayed old when the slot was reused.

There was another debt in the allocator: time. Timer zero became an independent
stopwatch while timer one kept scheduling the tasks. The large startup calloc
benchmark held the allocator's own mask for nearly fifteen milliseconds;
realloc reached eleven. Zeroing and copying moved outside that mask, with the
buffers reserved until the operation returned. The short card test brought the
measured calloc sections down to about 273 microseconds and realloc below two
milliseconds. The whole machine still had other critical sections, and startup
still had its outer mask. Those numbers were measurements, not a new hard
real-time guarantee.

The longer native test caught our next mistake at update forty-four thousand.
There were enough free bytes, but not one large enough free block. Realloc had
correctly kept the old data. The test had incorrectly demanded success. We kept
the interrupted card run, taught the workload to count ordinary refusals, and
checked the surviving buffer before freeing it. Two hundred thousand native
worker updates then passed, including that refusal, with every allocation
accounted for.

The next long run found the same bookkeeping trap that had troubled the browser.
After twenty minutes, HTTP timed out. The card was still scheduling, its heap
checks were clean, and the captured responses had valid checksums. The host was
rewriting twenty megabytes of packet history after every exchange. Writing a
receipt had grown to roughly two hundred milliseconds; retransmissions were
joining the queue. Appending the complete new record brought that work down to
about two tenths of a millisecond. We kept every packet and started again with
the same card binary.

This time it reached the end. Forty IPv4 and IPv6 rounds ran through a half
hour, including deliberately lost TCP data and a full packet queue. The spare
timer wrapped without losing the accumulated time. Cancellation had been
acknowledged as busy fifty-nine thousand times while readers still held their
pins. At shutdown every one of the 194,154 application allocations was freed,
and all 14,764 shared objects were retired.

The deadline asked for shutdown at tick 180,000. The workers parked eight ticks
later, after the operations already in flight had finished. That small distance
was part of the result: requesting cancellation and proving that the last
pointer is no longer in use are different events. After reboot, the public
Vader page answered again.

The card eventually became free, and the ledger got its next receipt. We ran the
old writer, the journal, the journal again, and the old writer again. Every full
audit stayed. Browser delivery rose from 13.20 to 15.19 frames a second; metadata
writes fell from about nine and a half milliseconds to less than a quarter.
The processor itself was taking almost exactly as long as before.

One extra run had shared its host with a corruption replay test. We kept its
capture and discarded its timing from the comparison. Counting that run and the
shutdown tests, nine sessions produced sixteen hundred and thirty-five complete
audits and nine verified restorations. A signal in mid-request and a broken
browser connection both found the same way home. The public Vader page returned.
The raycaster was ready for someone to play; the next frame no longer needed to
copy the history of every frame before it.

## The queue that had already left

Moving the packet queue into tested RAM had left an expensive souvenir. The old
queue still occupied 102,000 bytes in the upload. It had a legitimate job during
network initialization, before the external memory was admitted. After the
handoff, it sat there with nothing left to do.

We gave that handoff an ending. Check the old pointer, indices and lengths. Copy
any waiting packets. Publish the external queue. Refuse to go back. Only then
could the old storage acquire a new owner. Sixty-four warning bytes at each end
left 101,872 bytes for another RTEMS heap. Together the two arenas held 171,824
bytes, although no single allocation could stretch across the space between them.
The kernel stacks stayed where they were.

The borrowing test moved in too. Every thirty-second cycle used an eighty-kibibyte
object, too large for the original heap. Its owner canceled itself while the
other task kept reading. The same pin and acknowledgement rules now protected
bytes that had belonged to the packet queue a moment earlier.

There was still a long silence around network processing. The worker raised
interrupt priority before entering lwIP and kept it raised while copying packets.
We shortened the part that needed silence. A committed receive buffer stayed
leased until processing finished; another host write came back busy. A transmit
buffer stayed invisible until the copy was complete. The timer could interrupt
the work between those small ownership transfers.

The first physical attempt got through admission and then found a mistake on
the host: the burst test did not recognize the new snapshot version. We kept
the failed capture, put the version table in one place and started again. Three
concurrent IPv4 and IPv6 rounds then passed, including a full queue, deliberately
lost TCP data and a host-requested stop. Every allocation was accounted for.

We also damaged the reclaimed arena on purpose. Changing a warning word brought
the machine into its owned terminal handler. Changing an allocator extent did
the same before the allocator could follow it. In both cases three allocations
remained live and the fault record stayed unchanged when the host asked for STOP.
The broken arena was left alone until reboot.

The half-hour run gave the handoff a longer examination. Forty rounds of IPv4
and IPv6 traffic passed while the workers borrowed and returned memory. Timer
zero wrapped, and its accumulated time kept going. The interrupt-gap maximum
was about 10.688 milliseconds, down from 13.270 in the preceding long run. We
had changed the memory workload too, so that comparison remained a measurement
of these runs rather than a promise about every possible load.

At tick 180,008 the machine had finished the shutdown requested eight ticks
earlier. All 189,150 allocations were free. All 14,138 shared objects had been
retired. The capture held forty complete rounds, 4,524 checked packets and the
retransmissions that had repaired the deliberate losses. The old queue had found
another job without taking its packets back. After reboot, the public Vader
page answered again.

## The room behind the cache

The card had reported sixteen megabytes all along. RTEMS was still using a
48 KiB kernel workspace and 8 KiB task stacks. The reclaimed packet queue had
helped the application heap, but it had not made the kernel's room any larger.

RTEMS initialization itself had to move. It used to happen inside the ARM
callback, while the stock firmware still owned the cache. The new exclusive
profile waits until that callback has returned, the engines are isolated, the
secondary SCSI chip is held in reset, and the fault and NMI paths belong to us.
Only then does it test the proposed memory and initialize the kernel there.

The first room was one megabyte, starting at `c0240000`. Four address-dependent
patterns went through every word, with protected-region hashes around the test.
RTEMS received a 256 KiB workspace and 64 KiB task-stack slots. Two rounds of
IPv4 and IPv6 traffic passed, and STOP drained both interrupt contexts. Four
megabytes followed. This time each worker kept a live 12 KiB object on its stack,
and shutdown checked every word in the unused reserve. That passed too.

Ten megabytes brought a timeout. The RAM patterns and guards had passed, but a
TCP echo did not finish. The control captures showed a host word sometimes
waiting nearly a whole 10 ms timer period: the network worker polled the channel,
and the heap worker did not. Both workers learned to poll it. The retry completed
six dual-stack rounds and reported a successful full reserve scan, including the
check and release of a 128 KiB allocation from the kernel workspace.

Then the host checker objected. Its status page had caught shutdown in progress;
its later RAM page had caught shutdown finished. We had requested exactly that
transition, and the checker had treated the two pages as one instant. The failed
capture stayed in the record while the checker learned the difference.

That capture held another useful embarrassment: one control word had waited
4.459 seconds while the final memory scan ran. The scan now checks in with the
control channel between small chunks, after both task-owned interrupt contexts
have drained. It still reads every word. It still keeps the workspace allocation
alive until the checks finish. It simply answers while doing the work.

The twelve-megabyte run lasted thirty-five minutes. Forty-eight dual-stack
rounds passed, the timer counter carried twice, and all 220,066 application
allocations and 16,402 shared objects retired. Both workers had checked their
stack objects 2,101 times. Every word of the 11,993,024-byte reserve passed its
final scan. The largest measured reply during draining was now 1.845 ms. The
largest IRQ gap was 11.038 ms: checking more memory had a cost, and the ledger
kept that number too. After reboot, the cooperative Vader page answered again.

The larger reserve is still a reserve. A successful pattern test does not create
a general allocator, a larger executable loader, or the missing Doom runtime.
Those have their own plan, starting with an explicitly owned application arena
and a segmented loader that cannot overwrite the monitor keeping it alive.

## A small program with separate rooms

The first allocator and segmented loader were rehearsed in a deliberately small
room: 3,728 bytes inside the buffer the old returning loader already knew how to
restore. The allocator gave each allocation a generation and counted its pins.
Cancelling an owner closed the door to new users; it did not pretend the existing
ones had disappeared. A pin had to come back before the bytes could be reused.

The loader put instructions in one segment, `DATA` in another, and zeroed the
rest of the data segment. It checked the bytes, synchronized the caches and
called the copied instructions. On the actual i960, those instructions read the
separate data segment and returned `e4f1e4e1`. The cancellation test kept the
allocation until completion was acknowledged. Then the old loader restored RAM,
unloaded, and the Vader page went back online.

On the native machine, the same allocator handled a contiguous six-megabyte
allocation and ten thousand allocation/release operations under sanitizers.
That was useful evidence, with a precise boundary: six megabytes on the native
machine, a few kilobytes on the card. The twelve-megabyte reserve still needs its
ownership contract extended. And the resident image has just 1,456 bytes left in
its immutable code window. The next loader needs somewhere to stand while it
builds the larger program around itself.

## The loader moves into the house

The small rehearsal became a resident service. Eight megabytes of the tested
reserve went to a guarded arena, while the allocator's bookkeeping stayed with
RTEMS. The loader itself fitted into a separate 6,416-byte section near the top
of the original upload. Its linker boundary kept it clear of the kernel's BSS.
The host checked those bytes before takeover, and the card watched 135 protected
pages covering the monitor, loader and saved upper tail.

The first manifest did not get through. Five integers occupied twenty bytes on
the host and thirty-two in an i960 C structure; the whole manifest was 172 wire
bytes and 272 compiler bytes. The card rejected it before allocating anything.
The fix was to read the words, rather than ask two compilers to agree about the
space between them.

Then RTEMS received ninety-six kilobytes of code and a separate data segment,
checked their checksums, cleared the BSS and called the little returning probe.
The answer was still `e4f1e4e1`. This time a six-megabyte allocation lived beside
the image, survived a complete fill and readback, and was freed on the card.
There had been only one firmware callback, before takeover. Everything since
had crossed the message registers.

Running uploads alongside networking found a less exotic obstruction on the
host. Upload ioctls slipped between the words of a diagnostic snapshot until the
relay stopped pumping packets long enough for TCP to time out. Giving a whole
snapshot a turn fixed it. Ten dual-stack rounds then passed beside the uploads.
At STOP, a deliberately unfinished image stayed pinned until the task and IRQ
contexts drained; only then did the arena become empty. The final reserve and
protected-page checks passed too.

This is room for a program, and a way to bring one in. The libc heap is still the
old small heap, and arbitrary application tasks still need their runtime and
ownership contract. Doom has not run. But the six-megabyte number now belongs in
the card's column of the ledger, not only in the native tests.

## Seven pixels outside the picture

Before asking the card to draw Doom, the host had to agree with itself. Two runs
of the same demo disagreed in three frames. The timing was fixed, the input was
fixed, and the allocation measurements matched. Across the whole pair of runs,
only seven pixels changed their minds.

The debugger caught one in the act. A sprite's first sample was fifteen units
below zero in a number with sixteen fractional bits. Rounded down, that became
minus one. The drawing routine was also used for walls, where wrapping at 128
pixels made sense. Minus one became 127. This particular sprite post contained
eighteen pixels. The other two stops found the same mistake in posts of three
and thirteen pixels.

The repair gave sprite posts an end. Their samples now stay between the first
pixel and the last, while walls keep their wrapping. It also changed some bad
reads that had been politely returning the same wrong answer every time: 148
pixels in thirty-five frames, compared with one old run. Agreement alone would
have missed them.

Four different heap fills, both Freedoom phases and three demos each then
produced 50,400 captured draws. Every repeated picture, palette and game-tic
trace matched. The i960 engine grew by 240 bytes. Its fifty-eight unresolved
runtime symbols did not disappear, and no Doom instruction ran on the card.
But with eight megabytes now owned on the hardware side and a repeatable picture
on the host side, the next disagreement will at least have a proper reference.

## Giving malloc an address

The eight megabytes already had an owner. Giving Doom a second allocator over
the same memory would have made two convincing maps of the same empty lots.
Instead, its five allocation functions learned to ask the resident loader's
arena. The operating system kept its own smaller heap.

A large copy reserved both allocations, stepped outside the bookkeeping lock,
and checked for STOP every kilobyte. A failed resize left the old pointer alive.
A cancelled resize did the same. On the host, six demos drew another 12,600
pictures through this arrangement. Every picture, palette and game tic matched
the reference; every heap drained. Doom's thousands of internal zone blocks
turned out to need only thirteen ordinary allocator slots in these runs.

On the card, the test asked calloc for six megabytes beside an uploaded image.
It checked every zero, grew another buffer, tried a resize that could not fit,
and checked that the rejected request had left its old data alone. A small
string made the trip through strdup. Sixty-four kilobytes stayed behind on
purpose, patterned and pinned until both task and interrupt contexts had stopped.
Only then did cleanup check the pattern and let the arena become empty.

Six rounds of IPv4 and IPv6 traffic passed alongside it. The complete allocator
command took fifteen seconds, including the host transport and scheduling; the
largest observed interrupt gap was about eleven milliseconds. Those are two
different measurements. Neither is a claim about Doom's frame rate.

The reboot returned, and Vader answered HTTP again. Five unresolved symbols had
become real functions on the card. Fifty-three remained, along with the work of
giving Doom its own task and bringing its WAD across from the host.

## Two tenants, one set of keys

The next problem was less dramatic than getting eight megabytes back from a
RAID controller. Two tasks now wanted to use them without each believing it
owned the whole building.

They received separate allocation records and one shared lock. The loader kept
its image pinned; Doom's allocator kept source and destination pinned while a
large copy stepped outside the lock. A task asking through the other task's
allocator was turned away before it could change even the diagnostic word.
On the host, the thread sanitizer approved of this small exercise in manners.

The first card test found a different kind of ownership problem. To test a
waiting task, the task holding the lock went to sleep. That could leave both
workers asleep, at which point RTEMS had an idle task to run. Our resident
profile had deliberately made that task fatal: nobody had yet earned an
interrupt stack for it. The capture ended with the transport shut down. It did
not preserve the final fault number, so the code-path explanation stayed an
explanation, not a recovered confession.

After reboot, the holder stayed runnable with interrupts enabled while the
other task waited. The timeout worked. So did the recursive-lock refusal.
At the diagnostic snapshot, the second worker had checked its buffer and tried
the wrong allocator 3,305 times. Both tasks kept patterned allocations until
STOP—ninety-six kilobytes for one, sixty-four for the other—and cleanup checked
every byte only after both tasks and their interrupt continuations had drained.
The unfinished uploaded image left at the same time. The arena was empty again.

Six rounds of network traffic passed around this negotiation. Full replay
checked 804 packets and 517 upload commands; damaged captures were rejected.
The little scheduling lesson stayed in the plan: before Doom waits for its WAD,
somebody must remain awake to answer the host, or the idle task must finally
be given a properly owned place to run.

The reboot returned, and Vader answered from the original web server again.
The failed attempt stayed beside the successful one in the archive; the lock
had acquired both a test and a warning about who was allowed to sleep.

## A game asks for a file

The next visitor was only 736 bytes long. It arrived through the loader, took a
small table of services, asked for a kilobyte of memory, and opened a conversation
with the host about a file it could not possibly keep in RAM.

Freedoom's first WAD was nearly twenty-nine megabytes. The card had eight
megabytes to work with, including everything else we wanted to put there. So the
host kept the file and the little program asked for three pieces: the header,
a slice of the directory, and the last thirty-seven bytes. Each reply had a
sequence number, a length and a checksum. The destination stayed borrowed until
the application had finished checking and copying it. Even an old completion
needed its own loan token; it could not return somebody else's newer loan.

The first attempt got as far as the directory. We had left the host free to do
a full audit between noticing a request and answering it, and we were still
polling the old command reply in between reads. The tail reply was refused.
The capture did not give us the final mailbox state, so expiration was a strong
explanation rather than a recovered confession. We kept the failure, rebooted,
and put each query and reply together under the host's audit gate. The card's
five-second deadline and its binary stayed exactly as they were.

On the retry, both ordinary runs returned the same hash as the host. We sent a
bad checksum, shortened a reply, reported a read error and withheld a reply
altogether. The last one took 5.12 seconds to come back. Then the application
read the real file again. Networking kept running, the audits stayed on, and
STOP found no outstanding loans before reclaiming the arena.

This still was not Doom. It was the smaller, necessary trick: an uploaded
program could now call the operating system and fetch its own data without
owning the whole file or stealing another task's memory. The next job was to
teach the much larger visitor those same manners.

## A file that would not fit

The little program could ask for bytes. Doom wanted to put them halfway through
its six-megabyte zone. Those were different promises: the runtime would lend a
whole allocation to a read, while the game handed its file layer a pointer into
something much larger.

The answer was a small waiting room. A separately owned 512-byte buffer received
the reply, a sixteen-kilobyte cache kept recently seen pieces, and the application
copied the checked bytes into its own zone. The file layer would open one named
WAD and no others. Closing it did not turn an old file handle into a new one.

On the host, the actual engine took that route for all six demos. All 12,600
frame hashes still matched. We made the imaginary engine reservation a full
megabyte this time, inside the same eight-megabyte arena, and the game still
finished and gave its allocations back. The cache was useful plumbing, but not
a miraculous speedup: it saved a few percent of requests while aligned reads
brought back a little more data. Making it much larger scarcely helped.

The compiler supplied nine more real routines, mostly the arithmetic the chip
could not do directly. Forty-four imports remained. And the old linker delivered
one more archaeological surprise: it accepted the option to keep relocations,
then left them out of the final executable. So we kept the records from the
relocatable object instead. A small code/data/BSS example, moved using those
records, matched three independently linked binaries byte for byte.

That last experiment stayed on the host. Doom still had not run on the card.
The next visitor would be that small relocated program, with its own initialized
data and pointers, before the much larger engine was allowed through the door.
Meanwhile, the public web page kept answering.

## Where it stands

So, the ledger, honestly kept:

- **Tetris runs as genuine i960 machine code under the host interpreter**, with
  native comparison tests. Its bounded update/render form now runs on the card
  too. The SSH terminal client has completed a half-hour run with 35,846
  byte-exact native comparisons and 68 restarts.
- **The installed firmware was recovered in-system**, with a validated 512 KiB
  image and matching vendor firmware, boot block and independently read PCI BIOS.
- **The real boot path and DRAM initialization writes are recovered.** The
  working approach preserves stock initialization; a complete timing decode is
  no longer a prerequisite for running a program.
- **A stock-preserving flash patch is programmed and boot-validated.** One
  programming command, matching full readbacks, preserved boot block, working
  postboot PING. The hardware boot straps have not changed to Mode 0.
- **Uploaded C programs execute on the real card after PC startup**, repeatedly,
  with verified returns, bounded text/framebuffer output and RAM restoration.
  The current loader supports short,
  cooperative functions, not a resident game loop.
- **RTEMS and TCP/IP run on the card.** Historical RTEMS Classic tasks persist
  across returning callbacks; lwIP handles ICMP, UDP, TCP, DNS and HTTP through
  host routing. The `autonet` profile supplies a hardware interrupt clock and bounded background
  RTEMS work; the host still relays packets. A separate exclusive profile now
  runs preemptible tasks and IPv4/IPv6 networking without a pending firmware
  callback. Owned fault/NMI containment and a tested fixed cache-data range now
  support a 128-slot external packet queue and two guarded application heaps
  totaling 171,824 bytes, with explicit shared references and cancellation. The
  fallback queue becomes the second heap only after external handoff. Network
  processing is now preemptible. A half-hour exclusive run passed forty dual-stack
  rounds and complete application-allocation drain.
  A later exclusive run validated a 12 MiB region, a 256 KiB kernel workspace,
  64 KiB task stacks and thirty-five minutes of networking. An opt-in resident loader now uses an 8 MiB guarded application arena,
  with a live 6 MiB allocation proof and segmented PIO uploads alongside ten
  network rounds. General libc/task adapters, arbitrary application launch,
  graceful engine drain and longer resident service remain open.
- **Recovery remains untested.** Firmware health replies are also not a disk-I/O
  test or a long-duration stability claim. Those gaps stay in the ledger.

The function contract is deliberately small: one argument in, one result out,
return well within the two-second command timeout. The original scalar loader has no OS or automatic BSS initialization. The
RTEMS profile now supplies its own persistent kernel state, explicit BSS setup,
guarded task stacks and a small freestanding runtime.
The host cannot preempt a runaway i960 function. Tetris now uses this path to exchange state, keys and framebuffer data without
monopolizing the firmware command loop. The long hardware replay and timing measurements have now passed. A
persistent session now sustains about twenty updates per second. The interactive
terminal client and its half-hour acceptance test have passed too.

The i960RP, for the record, is roughly a 486-class integer core with no FPU
wrapped in an I/O system-on-chip — a part built to shovel RAID traffic with
hard real-time interrupt behavior. Asking it to drop tetrominoes into an 80×24
grid is comically beneath it. The compute was never the hard part. The hard part
was earning the right to run *anything at all* on a processor that spends its
whole life certain it already has a job.

It still has that job. It has also learned to answer fifty-five.

*For the reproducible version of these last acts, see
[ROM-FETCH-LIVE.md](ROM-FETCH-LIVE.md),
[FIRMWARE-PROGRAMMED.md](FIRMWARE-PROGRAMMED.md), and
[SOFTWARE-LOADER.md](SOFTWARE-LOADER.md), and
[rtems/README.md](rtems/README.md). The story ends here for now; the
captures don't.*
