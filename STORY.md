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

## The small visitor arrives

The next program was only 184 bytes, but it brought luggage: eight bytes of
initialized data, a pointer into its own BSS, and thirty-two counters that had
to begin as zero. Six addresses needed to move with it. This was the part a
position-independent hello world had politely avoided.

The loader gave it a room at `0xc02d0050`, checked the luggage, moved the six
addresses, and let it run. It allocated through the RTEMS runtime, filled its
counters, followed the relocated pointer and returned **1228486293**. The loader
checked every counter and every initialized byte, put the room back as it had
been, and invited the same program in again. Same answer.

Changed code, changed data and the wrong entry point were refused at the door.
The full audits stayed on. Six rounds of IPv4 and IPv6 traffic went through,
and both workers drained at tick 14,903 with their allocations accounted for.

Even the evidence had an archaeological footnote. Linux reused a TCP port for
a later connection; our replay tool mistook the two conversations for one and
reported a gap. The handshakes and closes were all there. We taught the verifier
to recognize that boundary, then checked that a real gap or conflicting
retransmission still failed. Nothing in the capture needed to be excused.

Doom still had forty-four missing imports. But the little program with luggage
had now walked through the real door, twice. The next problem was supplying the
larger visitor's runtime, not guessing whether its addresses could move. After
the required reboot, the old web page was answering again.

## Giving the visitor a library

The next missing pieces were less glamorous than a renderer: errno, strings,
formatting, files, a clock, and somewhere for a frame to go. There were forty-four
unresolved names. We gave the application its own copy of Newlib and its own
small platform, keeping the kernel's library and heap to themselves. Files could
read the one pinned WAD. Saving, renaming and launching a shell returned honest
errors.

The old library had two surprises waiting. Its `%lln` formatter added one pointer
indirection too many. Its hosted x86 longjmp tried to turn interrupts off and on,
something Linux does not let an ordinary process do. One needed a local source
fix; the other needed the library's own hosted setting. Then there was a quieter
ownership detail: a duplicated string belongs to its caller, even when Newlib
allocates it through an internal-looking function. Cleanup had to remember that.
The sanitizer checks passed with that string still protected.

The missing-name count reached zero. The candidate occupied 752,804 bytes before
its dynamic allocations, and thirteen thousand one hundred and thirteen address
fixups matched three independent links. That earned it a place in the build
ledger. It did not yet earn it the right to become a running task.

A smaller visitor went first: the real WAD cache, in 1,760 bytes of relocated
code. It copied across cache lines into an interior destination while the kernel
borrowed only its exact bounce buffer. Reading the same bytes again needed no
new host requests. Bad CRC, short data, a host error and silence all took their
proper paths, and the next clean entry worked. Both normal calls returned
**2488633422**.

The build itself briefly fell into a trap made of its own name. A linker wildcard
for Doom objects also matched “doom” in the working directory, sending ordinary
kernel code into the small upper window. The limit stopped it before the card
saw anything. Explicit object names fixed the placement; the old rule still
failed in the regression fixture.

The real run kept all its audits, moved 812 packets through six rounds of both
IP versions, and drained at tick 17,855. The cache was correct. It was also slow
enough to keep us honest: seven wire reads took about twelve seconds with the
audits running. Doom had a complete library now, but still needed an owned entry
and exit, a larger admitted manifest, and a better way to bring its WAD data
across. After the reboot, the old web page was answering again.

## A visitor that could leave

The first owned entry refused to open. RTEMS's old interrupt-level getter had a
small trick in its pocket: restoring the processor control word overwrote the
value it was about to report. It told a runnable caller that interrupts were
masked. We kept the failed capture, read the control word without changing it,
and tried the small visitor again.

This one carried the library's original i960 setjmp and longjmp. It walked six
nested frames, waited through real task switches, checked its stack canaries,
and took two deliberate jumps home. Normal entry, application STOP, normal
entry: all three returned with their buffer freed. A stale invitation could not
cancel the next guest. The final global STOP drained at tick 21,511. The old
getter itself stayed in the kernel backlog; the new door no longer trusted it.

## Making room for the larger visitor

The full engine and its private library now occupied 754,448 bytes, with 13,175
addresses to move. Their recipe alone needed 52,700 bytes. Embedding all that in
the small trusted loader window was over. We gave the loader a protected SHA256
gate inside its existing room, and sent the image and address list separately.
Their exact identities were still decided by the reviewed build, not by the
visitor carrying its own CRC.

The native preflight formatted real numbers, checked a six-megabyte allocation,
drew a known test pattern, read the WAD header and cleaned up after STOP. It also
found a less glamorous obstacle: retained proof buffers split the free arena.
Eight megabytes in total did not mean six megabytes in one piece. Reserving a
megabyte for the image before placing those buffers made the native layout work.

On the card, changed code and a changed address list were refused. Then, while
the clean image was still coming aboard, the interrupt and drain guard reported bit sixty-four. The active-state
snapshot pointed toward the timer rejecting a task or live continuation, but
the shared flag could not name the branch. We kept the refusal instead
of teaching the timer to overlook it. No engine entry had run. The evidence
replayed the two closed doors and the partial upload; it could not turn that
into a successful visit.

That is the next door to understand. The larger preflight remains optional,
the six-megabyte layout has its native proof, and Doom still has not started.
After the reboot, Vader was answering over IPv6 again.

## Between two stacks

The guard finally gave us a name for the problem. Worker zero was published as
running, and its old interrupt continuation was still alive. But the interrupt
frame was sitting on worker one's stack. For a few instructions, the kernel's
answer to “who is running?” disagreed with the processor's feet.

The dispatcher had announced the incoming task, enabled interrupts, and only
then moved the context. We kept interrupts masked across that crossing. Just as
important, we kept the caller's original interrupt level for the journey home;
reading it again halfway through would have mistaken our temporary mask for the
level we owed back. The original dispatcher reproduced the gap in a native test.
The patched one returned callers to both of the levels we tested, twenty and
thirty-one. Nobody new was invited onto the interrupt stack.

There was another queue at the door. Reading an entire diagnostic page while
holding the host lock could keep a WAD reply waiting past its five-second lease.
We froze the same page and read every word in smaller groups, allowing replies
through between them. The application could also poll the existing mailbox while
waiting. Its checks and deadline stayed in place.

This time the larger visitor came in. Normal entry, STOP, normal entry. The
private library formatted its numbers, the six-megabyte allocation fit, the test
pattern matched, and the WAD header arrived. After each visit we checked the
executable bytes again. At tick 100,085 the final STOP had drained the tasks,
interrupt continuations, image and heap. The rejection record was empty.

Even the replay had one last small trap. On the Mac, recorded WAD replies could
arrive so quickly that all three reads finished in the same clock tick. The
probe was supposed to reject a clock that had not moved, and it did. Giving the
native transport model time to pass made its answer match the card without
changing the probe or its expected result. All 7,853 recorded commands replayed;
forty-four deliberate evidence changes were refused.

The visitor was still the diagnostic entry linked with Doom, not Doom opening
its first level. That distinction matters. We now had a tested way in and a
tested way home. Moving the game data efficiently, and asking the engine to draw
its first real frame, came next.

## Eight envelopes, one question

The first-frame trace had a peculiar number in it: 27,648. That was how many
times the host cache had asked for another 512 bytes of the game. The card could
read the bytes. It was spending too much effort asking for them.

We kept the small envelopes and changed the question. One request could now
cover four kilobytes, delivered in eight ordered fragments. Nothing reached the
caller until the lengths, offsets and checksums all agreed. The temporary
assembly buffer belonged to the application arena and stayed pinned while the
host filled it. STOP and the five-second deadline still had the final word.

The same first-frame read trace needed 4,747 questions. The bytes did not change.
Six host demos kept every one of their 12,600 frame hashes. On the card, the
smaller cache exercise went from twenty-four requests to seven; its two-run
average fell from 3.59 seconds to 1.65. Those were transfer measurements, not a
Doom frame rate. The game still had not opened its first level on the i960.

We broke the last fragment's checksum, shortened it, returned an error, stopped
mid-delivery, and withheld the rest until time ran out. Then we asked again.
The good reads still matched, and the final STOP drained at tick 101,897.

The host found one last mistake after that: it expected fourteen cancelled
images, forgetting the fifteenth image we had just added. Its failed assertion
stayed in the archive. The final reply was already in the raw journal, so the
replay could check it without pretending the original harness had passed.
The reconstructed view was labelled as such, and the full memory and packet
checks stayed in place. All 7,949 upload commands matched the native replay;
eighteen new deliberate corruptions of the batching evidence were rejected.

The next visitor would have to do more than read a header. It would have to
start the engine, stay within its memory grant, and bring back a real frame.

## The first real start

The next image carried the real engine and its own small C library. On the host,
it could open the WAD, build the level, present a frame and retire all its private
allocations. We stopped it during a read, made its clock run out, and returned a
read error. Fresh starts still produced the same pixels. The first picture was
mostly black: the beginning of Doom's screen wipe, before the level became
visible. Even that picture required the engine to do its work first.

The card spent most of its first attempt asking for the WAD. We kept the checks
running beside it. Every delivered fragment was correct. The first 4,674 requests
followed the host exactly; then the texture requests took another route. After
4,769 requests, the control channel stopped answering. There was no accepted
frame and no clean final drain to put in the ledger. The complete failed run
came home before the machine rebooted.

There was a concrete difference to investigate. This compiler gave several
ordinary C structures sixteen-byte alignment. Doom's zone allocator promised
four. A side record occupied thirty-two bytes on the i960 and twenty on the
host; even the zone's own block header differed. The compiler's older layout
option brought fifty-five checked layout constants into agreement, while leaving
the RTEMS function table intact. It belonged inside Doom's private library, not
across the operating system.

The host needed attention too. Its long audit reads could leave network packets
waiting between snapshots. Forwarding packets between groups of four audit words
kept every check and every word. The complete acceptance run also needed room for
two long starts, so the startup profile received a ninety-minute session budget.
Each WAD read still had five seconds, and each engine start thirty minutes.

The revised image reached the same fork in the texture requests. It completed
4,764 requests, all delivered correctly, then lost the control channel too. The
layout correction was real, but it had not explained the failure. The network
made it through thirty-six rounds this time instead of six. We saved the final
incomplete audit page alongside the complete ones, without counting it as a pass.

The next useful evidence is inside the startup itself: where level setup ends,
which textures it chooses, whether drawing begins, and whether the owned exit is
reached. Until those checkpoints tell us where the card leaves the host's path,
there is no first frame to claim. The two failed runs belong in the record just
as much as the host's matching picture.

## The height of the camera

We put small numbered notes inside startup. The engine could report four integers
without allocating anything or waiting for the host. A separate read-only channel
collected them while the full memory and packet checks kept running. The notebook
had room for 512 entries; it would refuse more rather than overwrite the beginning
of the story. Its sixteen kilobytes came from the same eight-megabyte allowance.

The first fifty notes agreed. Textures had been built. Level counts matched, and
a fingerprint of every side's texture numbers matched too. The player stood at
zero, minus one hundred and sixty, facing north. Then the two machines disagreed
about where the player's eyes were. The host said forty-one units high. The card
said minus thirty-one. The difference was already there before the texture reads
went their separate ways.

That did not prove which calculation was wrong. A matching count is not a matching
map, and the new notes had not yet recorded the player's floor, ceiling or height
updates. But the search had moved from thousands of file reads to a particular
piece of game state. Every delivered WAD byte still matched the original file.

The card got further than silence had allowed us to see. It finished the BSP
render, drew the planes, and finished the masked objects. Then the notes stopped,
before the frame callback. The control channel timed out again. We saved 170 notes,
274 complete memory-check pairs and the unfinished final page. Thirty-seven network
rounds had completed beside the engine. There was still no returned frame, no tested
STOP for that invocation and no clean drain to claim.

The next questions became smaller: where did the camera lose seventy-two units,
and what happened between the end of rendering and the frame callback? They might
have the same answer. The evidence did not yet give us permission to say so.

## The wrong side of a line

The next notes began earlier, when Doom chose a place for the player to stand.
Every sector's recorded floor and ceiling heights matched the host. The player's
coordinates matched too. The card simply put those coordinates in another room:
sector eighty-two, with a floor seventy-two units below sector zero. Add the usual
forty-one units of eye height and minus thirty-one was exactly the answer to expect.
The height calculation had been answering the question it was given.

The generated machine code contained a less innocent sequence. It compared the
direction of a wall, then compared the player's position while deciding whether
to branch, then tested the flags from a comparison. The second comparison had
replaced the first one's flags. On the root partition of this map, that sent the
player down the wrong side of the tree. Following the emitted order on the original
map reached precisely the sector the card had reported.

That still deserved a test smaller than Doom. We took the same 160-byte function
body, checked it against the engine object, and asked it nine questions through
the ordinary returning RAM loader. There was no RTEMS scheduler or WAD service
in that experiment. The optimized function answered two questions incorrectly.
Turning off instruction scheduling corrected one answer and left the other wrong.
The unoptimized version answered all nine correctly. Each of the twenty-seven
calls brought its complete paired memory checks and clean restoration home.

The old compiler had become part of the archaeological site. We had not repaired
it yet, and nine correct answers did not make a replacement toolchain. They did
explain why changing the camera height would have been the wrong repair.

The long run still failed to deliver its first frame. It brought back 279 complete
memory-check pairs, thirty-seven network rounds and 188 startup notes. The last
note retrieved this time said the planes were drawn. The newer notes around the
HUD, wipe and final copy had not reached the host before control was lost. A note
written on a stranded card is not the same thing as a note recovered from it.
The next investigation needed to account for that distinction too.

The public web server went back up after the captures were saved. Doom remained
unfinished, but the next question was no longer why forty-one had become minus
thirty-one. It was how to give this processor comparisons whose answers survived
the compiler.

## One function, and a receipt

The next change was deliberately small. `R_PointOnSide` moved into a file of
its own, with its original source and Doom's original types. That file alone
was compiled without optimization. The rest of the game kept its existing
flags. So did RTEMS. A broken comparison was not a reason to quietly replace
the compiler underneath everything that already worked.

The new function occupied 416 bytes. Before asking it to choose a room again,
we compared those bytes with the small scalar test program, then sent twenty-five
questions through the card: vertical lines, horizontal lines, both directions,
points on either side, points exactly on the line, and the original failing
root-node decision. Twenty-five correct answers came back. Each call still paid
for the complete memory audits, restoration and clean unload.

There was another lesson from the previous attempt. A checkpoint written by the
card was not necessarily a checkpoint received by the host. The game could run
past a marker and fail before we had copied it out. The new experiment therefore
asked for a receipt at selected boundaries. The host read every word, saved the
record, and acknowledged its number and invocation. Only then could the card
continue. A missing receipt had a deadline; STOP still had a way out.

The host's reference frames and all five native checkpoint streams stayed
unchanged. The small program had answered correctly on real silicon. Then the full
startup finally answered. The player appeared in sector zero, with the camera
forty-one units above its floor. All 199 checkpoints matched the host. Rendering
returned. The wipe ran. The framebuffer copy finished. Doom called `DG_DrawFrame`
and left through its owned exit, with both frame hashes matching the reference.

It was the first, mostly black wipe frame, not a playable scene. And the two
changes had run together: the corrected comparison and the acknowledged markers.
We could say where the player belonged, and that this build reached the end. We
could not honestly assign the old hang to a single cause from that result alone.
STOP worked too. The fresh repeat then found a mistake in our receipt: its
record number travelled through an eight-bit field. The first invocation had
only 199 records. The second reached record 272, which arrived as sixteen. The
card refused it, correctly, and we kept the failed capture.

The correction gave the number and the invocation a full word each, in two
ordered packets. The first packet only staged the number; the second could
release the checkpoint after checking both. Native tests drove the actual host
packet builder through record 512. The new card batch crossed record 272, kept going through record 400, and
returned the same first frame again. Fifty receipts, all accounted for. STOP
between the two invocations had worked too.

Then the final, system-wide STOP found another boundary. A shared-heap assertion
put the card into its terminal handler. The host caught a snapshot changing from
ordinary status to the terminal record halfway through the read, then retrieved
the complete terminal record separately. We had two matching Doom frames, but
not a successful global drain. The native shared-peer replay also aborted; we
kept both failures without pretending they had the same cause.

The archive held 613 clean pairs of full memory audits, every WAD fragment, both
checkpoint streams, and the failed ending. After a power-cycle the public web
server answered again. Doom had reached its first presentation twice. Before
asking for a visible scene, the next job was to make the ending as dependable as
the beginning.

## Waiting for the other worker

The ending had a race hidden inside it. One worker could see STOP and start
returning shared buffers while the other was still finishing its last iteration.
The second worker had already decided to acquire a handle. Before it reached the
lock, the first returned the last reference. The acquire then refused a buffer
that no longer existed, and the assertion did exactly what it had been built to
do.

A small, freestanding 32-bit program made that order happen deliberately, using
the actual RTEMS allocator and our actual shared-heap functions. It produced
error ten, equal allocation and free counts, and zero live bytes—the same
signature as the card's failed ending. The old card capture could not name the
particular assertion, so the reproduction was evidence for the race, not a
recovered instruction-by-instruction account of that run.

The repair was two arrival flags. Each worker had to leave its work loop before
either could cancel shared references. The first to arrive kept interrupts and
control polling alive while waiting for its peer. A time bound and an iteration
bound covered a peer that never arrived. Once both were there, the ordinary
ownership checks and drains still had their work to do. In the small test, the
same forced interruption now ended with a valid empty heap.

The native replay had its own, less exotic trouble. Its producer could issue
commands with none of the card's PIO delay, taking the shared mutex again and
again while the audit peer waited. Under the native sanitizers, the bounded wait
could expire. One millisecond between completed host-model commands, outside
all target locks, let the peer make progress without extending the target's
mutex deadline.

That exposed an old analysis helper in the remote workspace. It had omitted the
checkpoint-log allocation, putting a modeled address 17,200 bytes away from the
card's answer. The current helper already knew about the log. With it restored,
all 7,832 captured command replies matched on both Linux and macOS. The failed
physical shutdown remained a failure; passing a repaired replay could not
rewrite the ending of an earlier run.

The full card repeat kept the same Doom image and every memory audit. Both
first frames returned, with the same hashes and all 199 normal checkpoints
matching the native reference each time. STOP between them returned cleanly.
Then, after seventy-five network rounds, the system-wide STOP finally reached
its parked state. All 306,981 allocations were freed. All 10,209 shared handles
were retired. Six hundred and twenty-six pairs of full memory audits survived
the ending as well as the beginning.

The complete native replay matched all 7,832 replies, including the physical
parked query. Deliberately damaged startup evidence was refused in all twenty-four
cases. The initial wipe frame was still mostly black, and each full startup still
took about twenty-five minutes with these audits. This was no claim of playable
Doom. It was a smaller, necessary achievement: the first-frame experiment could
now start, stop, repeat, and give its memory back.

The archive was copied home and hash-checked before reboot. Once Linux returned,
the unchanged public RTEMS web server answered over IPv6 again. Its visitors
could return to Darth Vader while Doom waited for its first visible scene.

## The picture comes home

The next change was small enough to sound like cheating: skip the opening wipe.
Doom had already drawn a room behind that transition. Our one-frame stop had
caught the curtain coming up, which was technically a frame and mostly black.
The new, explicitly selected build left the ordinary path alone and stopped
after two visible presentations instead.

On the native build, a room appeared. So did the enemies, the ammunition counter,
and the face in the status bar. The two pictures were identical. The checkpoints
showed game ticks two and three, but nothing visible had moved between them.
That was a useful correction to make before calling this animation.

Getting the picture home needed a lifetime of its own. Each frame kept 64,000
palette indices, its 768-byte palette and zero padding. Together the two slots
occupied 128 KiB. Once Doom had returned and its private allocations had retired,
the gate checked the complete picture against a compiled digest and copied it
into a separate allocation in the same eight-megabyte arena. Only then could the
engine image be discarded. Starting another engine attempt invalidated that
archive; the final system drain had to return it too.

The host could ask for a generation and a one-kilobyte window. It could not ask
for an arbitrary card address. Every returned byte had to match the independently
built native reference before a PNG could appear in the browser. The target
carried the expected digest, not a hidden copy of the reference picture.

Then the real card did it. All 218 checkpoints matched. The room came back over
the mailbox, palette and padding included, and the browser showed it. The first
layout stretched the picture sideways; setting the image height to follow its
width fixed that ordinary web-page bug. It was a pleasant change of scale from
finding a compiler comparison on the wrong side of a branch.

STOP invalidated the first archive. A fresh startup returned the same two frames
again. Across both starts and the intervening stop there were 441 checkpoints
and sixty-six explicit acknowledgements. Seventy-five network rounds and 604
pairs of full memory audits reached another clean ending: all 322,731 allocations
freed, all 9,917 shared handles retired. The native replay accepted all 8,152
command replies. Deliberately damaged startup evidence failed in twenty-four
cases, and damaged framebuffer evidence failed in thirteen more.

This still ran at the pace of an investigation. Each startup took about
twenty-five and a half minutes. Reading the two-frame archive took fifteen
seconds the first time and eighteen the second, including waits behind the full
audits. Serving a resulting PNG to the Mac took about nineteen milliseconds.
Those numbers described three different jobs; dividing two pictures by the
startup time would not tell us Doom's frame rate.

The browser had Previous, Next and Refresh. It did not have movement or shooting.
The next step was to demonstrate visible motion, then keep the engine and its
frame ownership alive long enough to exchange input. But the room on the screen
was no longer a native preview standing in for a hoped-for result. Its pixels
had come from the RAID controller, and every one of them had survived the trip.

The archives were copied home and their hashes checked before another reboot.
Linux returned, the public RTEMS page answered over IPv6 again, and the saved
Doom gallery came back beside it. Looking at the picture no longer needed to
borrow the card from its next experiment.

[The exact builds, complete captures and browser instructions](artifacts/notes/doom-visible-20261013.md)
keep the receipts for this part of the story.

## A game needs a keyboard

At this point the owner of the card asked a reasonable question: could we stop
turning every frame into a separate research programme and just play Doom?

The two-frame proof had done its job. The next build kept Doom alive, started
Freedoom's first level, and gave its renderer a place to wait while Linux read
the picture. A browser canvas supplied the screen. Key presses travelled back
through a small queue; the engine still owned its memory, and STOP still had to
bring that ownership home. The renderer and game remained on the i960. Linux
encoded the picture and carried the keys.

The first attempt taught us something before it drew anything. Cancelling
startup worked, but a repeated cancellation caught the host sending one last
WAD reply after the target had already stopped asking. We saved the evidence,
removed that race, and gave loading its own time allowance instead of spending
the player's half hour before the game appeared. The corrected build passed its
native input and cleanup tests, then delivered six frames on the card. Forward
input moved the view; release and STOP brought the engine home. Each picture
took about six seconds to reach the browser. A host comparison found seven or
eight pixel differences in one tiny patch, which went into the notebook rather
than becoming another prerequisite to touching the keyboard. The game was
slow, but now it had a screen, an input path and a way out. A fresh session
then delivered the same first picture. The browser check caught a less exotic
mistake: this DoomGeneric wanted its own fire and use codes. We corrected the
host mapping and used a small, serialized input bridge to avoid throwing away
the loaded game. The next screenshot had a muzzle flash and forty-eight rounds
where there had been fifty. The person who had asked to play could finally
point a browser at it.

We also put the workshop in order. Forty-six reports left the repository root
for named documentation folders. Firmware, loader, RTEMS, Tetris, Doom and the
web server acquired entry points, and Tetris acquired its own source directory.
The original ROMs, failed experiments and old coexistence work stayed. They are
how we know what the card did, and how someone with another card can repeat the
parts that apply to it. A new build recipe now reconstructs the Doom runtime in
a fresh workspace rather than relying on the archaeology of our home directory.

## Two words at a time

The room was on screen. Getting its pixels home was taking most of the time.
The playable reader asked the card for a single 32-bit word, waited for its
reply, and asked again. Including the checks and first-window reread, each
picture needed 16,770 message exchanges. The card spent more than five seconds
holding a finished frame while the host collected it.

A larger shared buffer would need a new ownership proof. The existing low PCI
window still contained firmware tables and stack state. We stayed inside the
message registers we already owned: one word in the usual reply register and
a second in the consumed request register. A short bounded poll caught quick
replies before putting the Linux task to sleep. The frame stayed immutable,
its generation stayed checked, and all the memory audits stayed in place.

Four frozen frames came back byte for byte through both readers. Then we ran
the old path, the new path twice, and the old path again. Readback fell from
5.447 seconds to 0.509. Delivery rose from 0.167 frames per second to 0.999—
almost six times faster. One frame a second still leaves plenty of work, but
the wait between pictures had become visibly shorter.

All twenty-eight frames reached the Mac. Thirty full audit pairs passed, the
engine stopped, both workers drained, and all 95,622 application allocations
were freed. The native comparison still found six to eight differing pixels
in the same tiny patch of the room. The first six card pictures exactly matched
the earlier card run. We had improved their journey home without hiding that
remaining rendering question.

The complete captures, exact binaries and replay checks now live in
[the bulk-transfer batch](artifacts/notes/doom-bulk-20261014.md). About half a
second per frame remains outside the new transfer. That is the next place to
measure. The twenty-three-minute level load also remains its own problem. After the
captures were safely home, we rebooted the retained test module and restored
the public IPv6 web page.

## Letting the I/O processor move the bytes

The next question was fair: this was a RAID controller. Why were we asking its
CPU to hand over pixels a few bytes at a time when the chip had DMA engines?
The exclusive profile had deliberately disabled them. Owning the processor and
owning a device that can write into the host's memory were separate promises.

We gave DMA1 a small, explicit job. Linux allocated a guarded buffer for this
card. The i960 got one descriptor, one fixed source, and no next link. Firmware
stayed parked, the other channels stayed disabled, and every transfer had to
return the primary bus to its isolated state. All the full memory audits stayed.
There was no new flash patch and no need to move the PCI window.

The first attempt timed out. This one was our mistake: the completion check read
0x1448 where the manual said 0x144c. The native model had repeated the same error.
We kept that failed run, retained the mapping, and rebooted. The corrected model
now refuses the reserved address, and the driver saves the destination buffer
and error report instead of leaving the next diagnosis short of evidence.

The second run moved the bytes. Twenty-four transfers ranged from one byte to
64 KiB, including deliberately unaligned destinations. Every complete host
buffer matched, guards included. Sixty-one full audit pairs passed. The network
still answered over IPv4 and IPv6, STOP drained the workers, and all 1,709
application allocations were freed. The DMA mapping itself stayed pinned until
reboot; a completed experiment was not permission to invent a new unmap protocol.

There was a useful warning in the stopwatch. Preparing the pattern, polling the
engine and checking the source inside the control path left a worst interrupt
gap of about 111 milliseconds. The proof had established a way home for the
bytes, but it was not yet the right way to schedule a game. The next version
needs task-owned preparation and a short completion path. Only after that do we
compare DMA and mailbox copies of the same Doom frame and count frames again.
The [DMA batch](artifacts/notes/dma-owned-20261014.md) keeps both attempts.
Replaying it on the Mac found one last boundary: Linux and macOS assign different
numbers to ESTALE. The reader now checks the Linux ABI that produced the capture.
The bytes stayed unchanged. After both archives were safely home and the retained
session had been rebooted, the public Vader page answered again.

## Let the timer have its turn

Moving bytes was not permission to silence the clock. We moved the preparation,
launch and checking into the second RTEMS worker, which already owned a proper
interrupt stack. The command handler now accepts a job and gets out of the way.
Linux asks for completion separately, releasing its lock between questions so
STOP can still get through. The fixed code region remained exactly 128 KiB.
Nothing was gained by quietly borrowing a few more bytes beyond its boundary.

The same twenty-four transfers passed again, with every buffer byte and full
memory audit intact. This time the worst interrupt gap was 10.71 milliseconds,
down from 111.48. The diagnostic job itself took longer: filling and checking
64 KiB now had to share the processor. That was the intended trade. We had made
the clock responsive, not yet made a claim about frames per second.

Then we submitted another large job and asked it to stop. The reply came back
in 1.26 milliseconds. The worker canceled before launch; every byte of the host
buffer still held its original guard pattern. After saving and replaying that
run, we rebooted and repeated the transfers with the same target and module.
This time the thirty-second RTEMS deadline did the stopping. Again, the pending
job was canceled before it could write into the host. The worst interrupt gap
was 10.99 milliseconds. Both workers retired and both sets of heaps emptied.

There is still a distinction worth keeping. We tested a real session timeout
on the card. We did not deliberately wedge its DMA engine and then declare that
clearing an enable bit had repaired it. The native tests exercise polling
exhaustion and retention; a genuinely stuck physical engine remains another
experiment. The mappings stayed pinned until reboot in both successful runs.

The [asynchronous DMA batch](artifacts/notes/dma-async-20261014.md) keeps the
exact builds, both captures and the independent replays. Forty-eight transfers
and 124 full audit pairs later, the next experiment is finally about pixels:
copy the same pinned Doom frame through DMA and the mailbox, compare every byte,
and only then count browser frames again. After the second archive was safely
home, the retained mapping was released by reboot and the public Vader page
answered over IPv6 once more.

## The pixels arrive before the receipt

The next experiment finally put Doom's own picture in the DMA descriptor. Same
engine, same WAD, same 64 KiB framebuffer. First read a pinned frame through DMA,
then read it again through the mailbox and compare every byte. After four of
those, alternate timing blocks. Let the card move the picture, and keep the
receipt just as strict as before.

Review interrupted the first two startups. A DMA submission could arrive between
the worker checking for work and deciding to release the frame on STOP. Adding
a pending check exposed the smaller version of the same problem: an interrupt
could still arrive between that check and clearing the pointer. The final fix
masks interrupts across those few operations and restores the old priority.
Preparation, checksums and DMA polling still run in the task with interrupts
on. Both interrupted startups stopped cleanly before issuing any frame DMA.
Their captures stayed in the archive. They were review findings, not corrupted
pictures, and pretending they had never happened would make a poor field report.

On the third startup, four pictures came home through both paths and matched
exactly. The mailbox took about 499 milliseconds per picture; DMA, including
both source CRC passes and complete destination guards, took about 225. A little
over twice as fast. The browser showed the scene, and the first mailbox timing
block managed about 0.95 frames per second.

Frame eleven made it through DMA too. Frame twelve was the reminder that a
picture and a receipt are different things.

The host submitted the transfer, received pending replies, and then the completion
poll timed out. The driver refused further work and retained everything. Reading
the retained host buffer later showed the exact expected twelfth picture, with
both guards untouched. But PCI bus mastering was still enabled. The final state
had never been proved. We had no right to acknowledge that frame or hand its
memory back merely because the pixels looked convincing.

So this entry has a useful number and an unfinished result. Four same-frame
comparisons establish a 2.21-fold transfer improvement. They do not establish a
DMA frame rate: the first DMA timing block never finished. The twenty-three full
memory audits all passed before the pictures started; there is no post-DMA audit
or successful final heap drain to quietly borrow from another run. The full
verifier rejects this capture. A separately labelled failed-prefix inspection
reconstructs the eleven delivered frames and the recorded audits, and deliberate
mutations still get rejected.

The small native/card rendering discrepancy stayed in its familiar three-by-three
patch. The new mystery is elsewhere: after the bytes arrive, before the transfer
gets its validated terminal state. The next job is to mark those phases and retain
fault/context evidence through a transport failure, then reproduce the stall.
Longer timeouts and fewer checks would only make the receipt less honest.

The [complete failed batch](artifacts/notes/doom-dma-20261014.md) preserves all
three builds and runs, the retained twelfth picture, and the exact limits of what
we learned. The archive was copied and checked locally before reboot; the public Vader
page answered over IPv6 again afterward. Ordinary
browser play keeps its accepted transport while this path earns the rest of its
proof.

## Giving the stalled transfer a voice

A picture reaching the host was not enough. The twelfth picture had arrived,
but the processor had not told us that the transfer was retired. We added a
small trail of phase markers: checksum, descriptor, start, polling, channel off,
bus master off, checksum again. If the card reached its terminal fault handler,
it would freeze those markers with the fault record. A poisoned host session
could ask for that record, within a fixed deadline, without gaining permission
to acknowledge another frame or recycle the memory.

Then the diagnostic build did something inconveniently useful: it passed.
Twenty-eight pictures, four complete mailbox-versus-DMA comparisons, sixteen
DMA transfers, twenty-eight full memory audit pairs, owned STOP and global
shutdown. Every picture matched the earlier physical mailbox run. The browser
showed frame twenty-eight. Mailbox delivery measured 0.966 frames per second;
DMA measured 1.384, about forty-three percent more. Copying the picture itself
was about 2.29 times faster, but Doom still had to render it.

That was a measurement, not an explanation. Adding stores changes timing, and
adding C changes what this old compiler emits. We saved and replayed the whole
batch, rebooted, and prepared another run with the exact previously failing
processor binary. Only the host gained the ability to ask for a frozen fault
record. If the failure returned, we wanted its address, not another guess.

The [diagnosis batch](artifacts/notes/doom-dma-cleanup-20261014.md) keeps the
instrumented build and its successful comparison. The exact earlier binary passed too: another twenty-eight pictures, twenty-eight
full audits and complete shutdown, at 1.380 versus 0.969 frames per second.
That made the performance result repeatable and the failure intermittent. It
also took away the tempting explanation that the new markers had cured it.
There was no new fault record to explain. The next tool should be a small,
repeated-frame stress test that makes interruption during polling and cleanup
routine, without paying for a whole level load each time. The root cause is
still open; ordinary browser play has not been switched to DMA. Both archives
were checked locally before reboot, and the public IPv6 page answered again.

## The safety check that stopped a successful transfer

The smaller test did what another level load could not. A few hundred bytes of
admitted i960 code filled the same pinned framebuffer with a known pattern and
asked the same DMA worker to send it. No monsters, no WAD cache, no renderer to
suspect. On frame forty-one, the receipt failed to arrive again.

This time the card could tell us why. The descriptor had finished: byte count
zero, next descriptor zero, every destination byte correct. The worker had not
yet disabled its channel or bus mastering. A timer interruption had let another
RTEMS task run, and that task checked its heap before doing any work.

The heap check was quite deliberately suspicious. To trust its RAM, it required
exclusive isolation. The isolation check still carried an older rule: all DMA
engines must be idle. We had taught one worker to use an engine, but had not
taught its neighbour how to recognize that worker's ownership. The neighbour
saw bus mastering enabled, poisoned the heap, and stopped the machine. Linux
reported a timeout because the card had obeyed its own safety rules too well.

The fix gives that rule a precise exception. A pending transfer must name the
current pinned frame, the exact descriptor and destination, and one of the
known enable, poll or cleanup stages. Descriptor contents, error bits, other
engines and the secondary-bus reset are still checked. The exception changes a
local validation snapshot; it neither writes the hardware nor holds off the
timer. Completion still has to restore the original idle state.

There was one more mundane stumble. The first fixed run delivered all 512
pictures, then Linux rejected a new read-only diagnostic query because I had
forgotten its ioctl allowlist entry. That run did not earn a shutdown pass. Its
captures were kept, the specific query was added and tested, and an early check was added before asking the producer to start. That check
caught the companion build-script omission too: the generated driver lacked the
feature macro for the new query. Both small mistakes kept their captures;
neither became a DMA success by being inconvenient.

The final repeat delivered all 512 pictures. Eighty-nine times, a safety check
saw the owned transaction in progress and correctly let it continue. Thirty
complete memory-audit pairs passed, followed by owned STOP and global shutdown.
The little producer sustained just under three frames per second with those
checks included. The important number was eighty-nine: this time we knew the
awkward timing window had actually happened.

The [stress-test evidence](artifacts/notes/frame-dma-stress-20261014.md) keeps
both incomplete runs as well as the final acceptance results. Ordinary browser
play remains on its existing transport until the fixed worker has its next
Doom comparison. A pattern producer is excellent at finding this fault; it is
not a new Doom frame-rate result. The closed captures were checked locally
before the final reboot, and the public IPv6 page was answering again afterward.

## The fix returns to Doom

The little producer had explained why a successful transfer could still end in
a fault. It had not yet earned a result for Doom. So the next run put the same
engine back on the card, with the same WAD, the same brief forward movement,
and the same four blocks: mailbox, DMA, DMA, mailbox.

The familiar twenty-three-minute startup was still there. The fix was about
ownership during a transfer, not loading a level. Full audits kept running
while the game made its way through that work. Then the pictures arrived.

This time all twenty-eight frames completed. The four frames read through both
paths were identical, and every frame matched the earlier physical mailbox
capture. The small native/card rendering difference was still there too;
changing how a picture travels does not fix how it was drawn. Twenty-nine full
monitor/RAM pairs passed, followed by owned STOP and the final heap drain.

The mailbox delivered 0.973 frames per second. DMA delivered 1.377: a 41.5 percent
increase, with average transfer time falling from 503 to 229 milliseconds.
The Mac received all twenty-eight PNGs with matching hashes. That measured
image delivery, not the browser's paint clock, and it described this short
scripted scene rather than every possible fight in Doom.

Both machines replayed the complete evidence. Thirty damaged frame/journal
records and twenty-four damaged snapshots were rejected. Only after the exact
build and captures were safely copied and replayed locally did the host reboot
to release the retained mapping. DMA remains an explicit option; the next test
is a longer session with a person at the controls and its lifecycle exercised.
The fix has now survived both the small stress producer and the actual game.
[The fixed comparison](artifacts/notes/doom-dma-fixed-20261014.md) keeps the
numbers and the captures together.

## Two pictures and a missing waiter

The next experiment stopped treating every image as a photograph to encode.
Doom already had indexed pixels and a palette. The browser could turn those
into a Canvas image itself. Two frame slots would let the card prepare one
picture while the host dealt with the preceding one. CRC became an explicit
choice for play, with bounds, guards, generations and hardware completion still
mandatory in either mode.

The first pictures arrived. Four mailbox/DMA pairs matched, including two with
CRC disabled, and the browser displayed the indexed image correctly. Then the
eighth frame stopped everything. The destination buffer had not been touched.
The card's heap and isolation checks were healthy, but a DMA request was queued.

Allowing the renderer to get ahead had introduced another dependency. Doom
could ask the host for WAD data before reaching the next point where its task
serviced DMA. The host was waiting for DMA and no longer serving that WAD
request. The correction kept the WAD channel moving during pending DMA polls.
A model now refuses to complete DMA until that service happens, so the wait
cannot quietly become exclusive again.

A second attempt exposed a different problem before rendering: a TCP startup
test timed out, and executor shutdown waited for Doom while the main audit loop
had already unwound. WAD progress looked reassuring; it was not full acceptance.
That run was stopped through the normal owner path. The harness now records the
network error, requests owned STOP and keeps auditing until the owner exits,
then reports the failure. Neither timeout was enlarged.

Both incomplete attempts were preserved before reboot. The next comparison
used the same card binaries, the corrected host service loop, and all full
system audits. This time all fifty-two frames completed. Twenty-nine full audit
pairs, owned STOP and heap drain passed. CRC-on delivered 1.396 frames per
second; CRC-off delivered 2.070, a 48.3 percent increase. It was a useful gain,
not the hoped-for three to five times. Every binary packet reached the Mac
with its expected hash, and the browser displayed the final frame. The seven
native/card pixel differences remained, with identical palettes and padding.
Both machines replayed the evidence and rejected all deliberate corruptions
before the host rebooted to release the mapping. [The pipeline ledger](artifacts/notes/doom-pipeline-20261014.md)
records the acceptance status, the failures and the exact builds together.

## Bringing the level through the other door

The pictures were finally arriving faster. The level still took almost half an
hour to arrive at all. The host had the WAD in memory; Doom was waiting for us
to carry it across the mailbox, a few words at a time. The reference run counted
more than four million control exchanges for 5,100 reads.

The DMA engine already knew how to take a picture out of the card. PCI Memory
Read let the owning task bring a block in. A coherent host allocation supplied
4 KiB at a time, with guards on both sides. The card used a separate guarded
staging allocation and kept it pinned until the host checked and acknowledged
the exact completion. Only then did Doom receive the bytes. WAD CRC was omitted
by explicit choice; identity, bounds, ownership, guards and full system audits
stayed. Those checks cannot detect every changed byte inside a valid block.

The first physical run completed all fifty-two pictures and the menu restart.
They matched the mailbox run byte for byte. Review still found a teardown race:
a late interrupt could queue work between checking the stage and freeing it.
The corrected release masks interrupts and refuses outstanding work. Passing a
run did not make that race acceptable.

Bulk data exposed another expense. Request-query calls alone had consumed more
than two hundred seconds. The next driver gave WAD control replies sixteen
short polls before returning to the existing sleep, with the same deadlines and
completion checks. The first attempt never reached that code: concurrent engine
upload starved a startup TCP check. Its failure archive remains in the ledger.
The host now finishes the network proof before admitting the large upload;
packet service and periodic audits continue while it waits.

The final run brought initial loading down from twenty-seven minutes and
twenty-three seconds to five minutes and eighteen seconds: 5.16 times faster.
Restarting the same level fell from 10.29 seconds to 3.07. All fifty-two pictures
matched the mailbox captures exactly; fourteen full audit pairs, owned STOP and
heap drain passed. The Mac received every binary frame with the expected hash.
Request queries still consumed 181 seconds. There was another bottleneck to
investigate, but now the experiment could end with someone actually playing.

The [WAD transfer ledger](artifacts/notes/wad-dma-20261014.md) records the final
comparison, exact images and failed attempts. The [play instructions](game/doom/play/PLAY.md)
cover getting into the game without having to reconstruct the experiment.

## The frame that was copied twice

Removing the framebuffer CRC had made Doom less patient. It had not made it
fast. There was still another checksum, FNV, in the adapter, and there was still
another copy. Doom drew into its persistent screen, copied that into its display
buffer, and the adapter copied the display buffer into the slot the host could
read. The second copy had become a habit rather than a requirement.

We kept Doom's persistent screen. Partial redraws and cached pointers gave it a
reason to exist. Instead, we pointed the display buffer at the next free delivery
slot. “Free” still meant something precise: the preceding slot's exact ACK had
arrived, publication had succeeded, and the host could no longer be reading it.
A failed publication could not rotate the pointer. Native tests held ACKs back
and checked that the old picture did not change underneath them.

The first physical experiment found another contribution from the old compiler.
A range selector chose the wrong benchmark mode on frame one. The host rejected
it; that run earned no performance number. Its disassembly and failed capture
went into the archive. A tiny table replaced the range comparisons, and the next
run selected every mode correctly.

Then came fifty-two pictures: checksum and copy, no checksum and copy, no checksum
and no second copy, and back to the beginning. The two baseline blocks delivered
1.95 and 1.98 frames per second. The direct path delivered 2.47. Four complete
DMA/mailbox comparisons, fourteen full audit pairs, every guarded frame, STOP
and the final allocation drain all passed. The pictures matched the earlier card
run exactly; the familiar seven-pixel difference from the native renderer stayed
visible in the findings rather than disappearing into a tolerance.

The clocks also made the next problem clearer. Rendering occupied about 317
milliseconds. The screen copy we still needed cost about 47. The hardware DMA
interval averaged only a few milliseconds on a ten-millisecond clock. Waiting
for the task to service DMA was much longer than DMA itself. The measured 26%
gain included the host no longer recomputing FNV during profiling, so it was not
a promise about an uninstrumented game. Nor was it ten frames per second.

But it was a useful answer. The bus was no longer where most of the time went.
The next substantial gain would have to come from understanding the renderer
and its scheduling, or asking it to draw less.

## Drawing less, and finding the other half

Doom already knew how to draw wider columns. We gave that old low-detail path a
controlled entrance: the same picture size, the same palette, the same DMA
packet, but half as many horizontal view samples. The experiment went high,
low, low, high. Nothing else got a holiday—not the guards, the ownership checks,
the full RAM audits, or the final drain.

We also stopped calling all elapsed rendering time CPU time. RTEMS's old usage
counter counted context switches as well as ticks, which made it unsuitable for
this question. A separate sampler counted timer interrupts that found the Doom
task running. It was still a ten-millisecond sample, with all the limits that
implies, but it could distinguish the task from its peers.

High detail delivered 2.48 frames per second. Low detail delivered 3.18, a 28%
gain. One low block managed 3.50; another managed 2.91, including an 884-millisecond
frame interval. We kept that interval in the result. Its long host completion
wait did not become evidence of a slow PCI bus merely because it happened in the
transfer code.

The more useful number was underneath: roughly 315 milliseconds of high-detail
rendering contained 158 milliseconds attributed to Doom. Low detail reduced
those to 210 and 105. The renderer appeared to have about half the processor.
That made scheduling worth measuring next, without pretending it would erase
the remaining screen copy or turn a hundred-millisecond renderer into ten frames
per second for free.

Fifty-two frames, fourteen full audit pairs and the owned shutdown passed. The
high-detail pictures matched the earlier card run. Low detail retained four
native/card pixel differences in the same tiny region where high detail had
seven. The wider columns made the game cheaper; they did not make that old
rendering discrepancy cease to exist. Both pictures and every differing pixel
went into the record.

## A function call for every pixel

The game was already running native i960 instructions. There was no interpreter
left to remove. But the disassembly had a smaller embarrassment: an ordinary
column called a helper for every pixel, then loaded the texture and colormap
pointers again. The helper kept masked sprites inside their finite posts. That
was a useful rule, and one we were not going to optimize away.

We moved the decisions outside the loop instead. One C routine handled wrapping
walls and clamped posts, with separate single and doubled stores. A small i960
assembly routine did the same job in local registers. No self-modifying code,
no masked interrupts, no borrowed ownership. Before Doom loaded, both routines
had to pass forty-eight Python-generated cases on the actual card: negative
fractions, overflow, empty columns, full-height columns and the untouched bytes
around them. Ninety-six successful checks bought them admission to the picture.

Then the experiment went original, C, assembly, original. The original delivered
3.48 frames per second. C delivered 3.86. Assembly delivered 3.82. Both brought
rendering from about 211 milliseconds to 180, and sampled Doom CPU from 106 to
90. Writing assembly had not bought another meaningful step. Showing the old
compiler a simpler C loop had done most of the useful work.

The eleven-percent gain was real for that bounded scene; ten frames per second
was still not. We kept all fifty-two guarded frames, fourteen full audit pairs,
the paired mailbox reads, STOP and the final drain. The optimized images matched
the previous card images exactly. The same four pixels still disagreed with the
native oracle. Thirty-five corrupted replays still failed. The full set of HTTP
frames matched the captures too.

The next candidate would therefore be C, with the assembly kept as a reference.
There were still planes to draw, a screen to copy and another half of the CPU's
time to account for. The card had not needed a new language. It had needed one
less conversation per pixel.

## Two landing pads, one receipt

The next suggestion was appealingly direct: let the card put the next picture
in host RAM itself. Give it two places to land. While Linux reads one, the card
fills the other. Stop asking the RAID controller for permission to move every
single frame.

That needs two kinds of ownership. The card cannot reuse its source until DMA
really finishes; the host destination cannot be overwritten until Linux releases
it. I built a small producer to separate those rules from Doom. Each transfer
has two descriptors: the picture, then a receipt containing its generation and
address. Linux checks that receipt in its own RAM. It still has to release the
slot, but it no longer has to start each transfer or fetch the receipt over the
mailbox. Two full landing pads mean waiting, not overwriting a picture somebody
is still reading.

The first thing the real card taught us had nothing to do with DMA. The larger
service crossed another code page. Our protection table had room for 144 pages;
the image now needed 145. Admission refused to proceed. That was a useful failure:
the right fix was another table entry, plus an offline capacity check, rather
than leaving a page out of the audit. A native test now corrupts every one of
the 145 modeled pages and checks that each corruption is caught. There are 304
bytes left at the end of the mutable kernel region.

The next attempt got through RAM admission and networking, then stopped on a
missing Python import path before the producer started. I had tested the C
pieces but missed that integration detail. The runner now imports this client
before taking ownership of the card. The next host check caught a timeout value outside the uploader's allowed
budgets. Then the first real baseline request exposed a missing fallback: before
ping-pong activation, the new service had forgotten to service the old path.
That produced a pending request, not an accepted measurement. Those failures are
preserved too, and the tests now cover the full client sequence and the switch
from host-started DMA to card-started DMA.

The completed run delivered 80 frames and deliberately left two more waiting in
host memory. Both three-second stalls left the buffers unchanged. Delivery
resumed after the first; STOP ended the engine during the second. All 17 complete
system audits passed, along with every captured byte, five mailbox comparisons
and the final allocation drain. The little producer moved from 8.12 to 9.82 frames
per second. This was a transport proof, not Doom suddenly reaching ten FPS.

The timing also found an old waiter still hanging around. Although frame
completion now lived in host memory, the generic uploader still asked the card
whether the entire engine had returned after every frame. Those questions cost
about 42.5 milliseconds each. Asking that separate question once a second made the producer faster, and
uncovered another old assumption. A full system snapshot saw our own running
DMA channel and marked it unexpected. The heap checker already knew how to
validate that exact lease; the snapshot path did not. Previously the host lock
had kept those snapshots away from active transfers. The new overlap removed
that accidental protection.

I did not accept the faster run just because the pictures and STOP passed. The
full audit had failed. The snapshot now validates the same pinned source,
generation, destination and descriptor chain before representing the transaction
as owned activity in its local report. A wrong descriptor or another active DMA
channel still raises an error. The next run explicitly required an audit to
catch DMA in progress. It caught five.

That final run delivered 256 frames, held two more, passed 20 complete audit
pairs and drained cleanly. The synthetic producer went from 7.92 to 14.24 frames
per second, about eighty percent faster. The host observed completion an
estimated 8–30 milliseconds after the card's start marker; copying, checking,
logging and releasing the whole capture brought that to 62–83 milliseconds.
Those are coarse-clock transport measurements, not a claim about Doom's render
time or what a browser has painted. Every capture can be replayed, and corrupted
copies are rejected.

Doom still needs one more piece of plumbing before using this: its WAD transfers
and the frame transfers both program DMA1. They need an explicit turn-taking
rule. The two landing pads work; we still have to keep the game from sending
another aircraft down the same runway.

## The game takes both landing pads

The little producer had proved that the card could send pictures without asking
permission for every one. Doom introduced the other passenger on the bus: the
WAD reader. Both wanted DMA1. Giving the game two destinations did not give the
chip two channel ones.

The rule stayed deliberately unexciting. Before the engine published a WAD
request, its own task finished any outstanding framebuffer transfer. Only then
could the WAD reader start. No preparation or checking moved into the interrupt
handler. The full system audit learned to recognize either exact owned lease,
without forgiving an unknown channel or a damaged descriptor.

Even this small addition ran into the walls of the house. The main code window
was 64 bytes too small. The audit helper moved into the existing protected engine
window, with the same guards and the same 145 protected pages. An attempted
section attribute reminded us that this compiler came from another century;
the linker got an ordinary object file instead. The mutable reserve remained
304 bytes. Nothing went into flash.

The first browser run delivered fifty-two frames, survived a three-second pause
with both landing pads occupied, and stopped with the last two still held. It
also received real keyboard input. That made it a useful interactive test and a
bad controlled benchmark. We kept the evidence and did it again, this time with
the browser keyboard disabled for the bounded run.

The repeat delivered a hundred frames and passed 108 full paired audits.
Host-triggered DMA managed 3.50 frames per second; card-triggered ping-pong
managed 3.89. Eleven percent was a good deal less than the synthetic producer's
eighty percent, and a good deal more believable for a game that still had to
draw the room. Host transfer and capture fell from 213 milliseconds to 41.
Waiting for the previous publication fell from 81 milliseconds to zero.
Rendering still took about 208 milliseconds, followed by another 44 for the
screen copy that remained inside the engine.

After the timing window, automatic menu input restarted the level. Fifty-five
more WAD blocks crossed the same DMA channel, then the pictures resumed. Both
host buffers stayed unchanged during the deliberate stall, and frames 99 and
100 stayed unchanged across STOP. The first fifty-two controlled pictures kept
the same four known differences from the native oracle; the palettes matched.
The browser received all hundred complete payloads.

The replay had its own small correction. Removing the last piece of a second
capture initially escaped detection because an earlier complete copy existed.
The verifier now accounts for every complete capture cycle, including the one
after STOP. All twenty-four damaged-evidence cases were rejected. A successful
picture was still not allowed to stand in for the rest of the proof.

A third landing pad was tempting. But the game was no longer waiting for the
second one. Drawing and copying already used almost the whole 257-millisecond
frame interval. Another host buffer might smooth a scheduling pause; it could
also keep an old picture waiting for another quarter of a second. The estimate
was little or no steady gain, roughly zero to two percent in this scene. The
next large improvement would have to come from the work that made the picture,
not another place to park it.

The exact builds, both runs, timing limits and replay results are in
`artifacts/doom-pingpong-20261015/`. This remained a bounded, opt-in transport,
not a declaration that every future game session was now qualified.

## The WAD stops asking permission for every handful of bytes

There was still something absurd about the loading screen. This was a RAID
controller, a machine built to move data, and Doom could spend nearly five
minutes asking the host for the pieces of its WAD. The DMA engine was already
there. The conversation around it was the problem: discover a request, prepare
one small transfer, wait, check, acknowledge, begin again.

We gave the two machines a shared notebook. Two guarded host buffers held
requests, replies and completions; the card could ask for two 32 KiB pieces
before collecting either one. The host answered from its immutable WAD copy.
The same RTEMS task still owned DMA1, so a framebuffer transfer had to finish
before a WAD transfer could begin. A generation belonged to its slot until both
sides had finished with it. Each slot kept a single writer and an explicit generation.

The first result was a useful embarrassment: **456 seconds to the first
frame**. The ring worked, the game ran, all 162 full audit pairs passed, and
shutdown drained the heap. It was also slower. We had removed mailbox waits
and replaced some of them with repeated byte-by-byte scans of the new guards.
Read-ahead had another bill: about 59 MB crossed the bus during the test,
because asking for the neighboring bytes does not guarantee they will be useful.

The next build checked the same guard bytes at the same points using word
loads, and used word operations for the staging fill and copy. Nothing was
sampled and no audit was skipped. First-frame time fell to **186.6 seconds**.
Another hundred frames, another level restart, another held-buffer STOP, and
88 full audit pairs passed. The first 52 pictures still differed from native
Doom at exactly the same four recorded pixels, with identical palettes.

That did not make read-ahead an unconditional win. Warm restart took **4.24
seconds**, and the smaller old transfers had previously done better. The matched old path took **290.1 seconds** to start and **2.84 seconds** to
restart the level: about 36 percent saved at startup, about 49 percent lost on
the warm restart. The new ring stayed an explicit experiment. A faster loading
screen is useful; a benchmark that admits where it got
slower is useful too. The exact first attempt and its successor are preserved
in `artifacts/wad-ring-20261015/`, including the regression.

## The bytes were fast. Their itinerary was not.

The next question was reasonable: this was a RAID controller. Why did loading
one WAD take minutes when moving disk data was the job it had been built for?

We gave it a smaller question. One host buffer stayed pinned and immutable while
the card read the same 32 KiB sixty-four times. The descriptor checks, ownership
loans and complete guards stayed in place. Timer 0, already owned by the
exclusive runtime, measured the pieces separately. Nothing was made faster by
turning off a check.

The final run observed about **20.6 MB/s** between starting DMA and seeing it
complete. Including the ordinary transfer's setup, cleanup and guard scans
brought that to **6.8 MB/s**. The extra byte-for-byte comparisons had their own
bill, outside both figures. These were short measurements with interrupts still
running, not a claim about the card's maximum disk bandwidth.

Then the rest of the accounting arrived. Across startup, a hundred frames and
a level restart, DMA completion intervals added up to **2.84 seconds**. Full
guard scans took **35.8 seconds**. Copying staging data into the borrowed output
buffer took **13.6 seconds**. Clearing and initializing staging took another
**8.8 seconds**. Allocation and freeing themselves cost **5.7 seconds**, with
ownership-loan work accounted for separately.

The largest entry was further up the stack. The WAD cache still filled its
windows with byte-copy loops: **78 seconds** copying fetched windows into the
cache, then another **15.7 seconds** copying cache or bounce-buffer bytes into
Doom. The engine consumed about 14.8 MB while the read-ahead cache fetched 59.1
MB. Fast DMA could not cancel that much repeated software work.

The measuring equipment needed debugging too. The first attempt was stopped
before the game because the frame validator still required zeros where the new
timing trailer belonged. The first completed run then faithfully reported an
unused stdio cache. We had instrumented the wrong cache. Its capture stayed in
the archive, with those zero timings explicitly disqualified. The corrected
build read the actual WAD backend, and its native tests required nonzero counters
before another card run was allowed.

Both completed runs passed their full system checks: **200 frames and 178 audit
pairs**, level restarts, held-buffer STOP and heap drain. The controlled pictures
still had exactly the four known native/card pixel differences. The final
capture also survived independent replay and rejected altered frame, WAD and
timing records. The new numbers were elapsed time, including interruptions;
the cache's clock still had ten-millisecond steps. They were useful measurements
without becoming precision claims.

The next target became much more specific: improve the actual cache's copies,
then remove unnecessary buffer lifetimes and copies while preserving ownership.
The DMA engine had already demonstrated that it could move the bytes. We had
finally measured how often the software asked the i960 to carry them again.

The sources, binaries, imperfect first measurements and corrected evidence are
preserved together in `artifacts/wad-profile-20261015/`.

## Teaching the cache to carry four bytes

The DMA profile had given us an awkward answer: the PCI engine could move data
quickly, but our WAD cache was still carrying it one byte at a time. Across the
bounded loading run those three loops spent almost ninety-four seconds copying
bytes that had already arrived.

The fix was small enough to inspect in the disassembly. Equally aligned pointers
now move through `ld` and `st`, four bytes at a time, with byte prefixes and tails.
Unequal alignments keep the old byte path. No extra byte is read past an EOF,
and no ownership check or guard scan has been negotiated away.

On the card, the same first level arrived in 117.57 seconds instead of 192.07,
with the eighty-second engine upload counted separately. The warm restart fell
from 4.51 to 2.89 seconds. The cache copies themselves dropped from 93.64 to
17.98 seconds. Gameplay stayed at about 3.8 frames per second: making the loading
screen shorter does not make the renderer faster.

The hundred frames passed sixty-eight full audit pairs at the same cadence as
before, held-buffer STOP and final heap drain. The controlled pictures matched
the earlier card run, including the same four pixels that still differ from the
native oracle. Captures survived replay and thirty-three deliberate mutations
were rejected. The next costs are now easier to see: staging, guards, allocation
and repeated read-ahead. Those are the next experiments, not permission to stop
checking who owns the memory.

## The other byte loop

The WAD-cache fix shortened loading, but Doom still ran at about 3.8 frames per
second. The next copy was sitting in plain sight: two hundred calls to Newlib's
`memcpy`, one for each row of the screen. On this build, that routine was another
byte loop. Every frame paid for all sixty-four thousand pixels again.

There was a tempting shortcut: point Doom straight at the delivery buffers.
But Doom remembers its screen. Its renderer caches row pointers, the HUD updates
parts of the image, and the zone allocator owns the backing storage. Our two
DMA slots rotate under a different contract. A pointer swap would not erase
those obligations; it would just hide them until a frame was being transmitted.

So the persistent screen stayed. The fixed indexed mode got one bounded pass,
four aligned words at a time. Other layouts kept the original path. In the
matched card run the copy fell from 44 to 12 milliseconds, and the delivered rate
rose from 3.815 to 4.517 frames per second. Rendering itself barely moved. This
was an eighteen-percent gain from carrying the same pixels more efficiently.

The hundred frames passed sixty-seven full audit pairs, held-buffer STOP and
heap drain. The first fifty-two controlled pictures matched the previous card
run exactly, with the same four old native-reference differences. Linux and Mac
replay passed; thirty-three deliberate capture mutations failed as intended.
The copy is no longer the large easy target. Doom still spends roughly two
hundred milliseconds of wall time rendering a frame, and that is where the
next serious question lives.

## Letting the other worker finish its sentence

A parallel investigation asked whether the original RAID firmware was stealing
our time. In exclusive mode it was parked. The competitor was ours: a second
RTEMS worker, at the same priority as Doom, continually doing useful checks and
then taking another turn. Raising Doom's priority would have made the pictures
happier by making the control path less dependable. That was a poor bargain.

Instead, the peer finished a complete service pass and yielded the rest of its
turn while the owned engine was running. Nothing skipped its heap check. Neither
worker went to sleep, and STOP kept its familiar two-worker rendezvous. The first
experiment reached 5.32 FPS, but made upload take 107 seconds. That was a useful
reminder that a scheduling policy has more than one customer. Restricting the
yield to owned execution brought upload back to 80 seconds and delivered 5.27 FPS,
up from 4.52. Startup execution fell from 117 seconds to 100.

One hundred pictures, fifty-eight full paired audits, held buffers, STOP and heap
drain all passed. The pictures still matched the previous card run, including
the four pixels where the native comparison already disagreed. But the final
interrupt report had a 59.9 ms maximum gap where the earlier runs had roughly
10.6 ms. The capture could tell us it happened, not where. So the faster policy
stays an option, not the default. The next instrument needs to catch the long gap
in the act. Even the CPU samples needed care: yielding near the timer changes
which worker the timer sees. The frame rate was measured; a claim that we had
magically doubled the processor would not have been.

## The missing six ticks

The 59.9 ms gap turned out to have a useful address in time: after the last
picture, during STOP. The saved reports stayed below eleven milliseconds through
gameplay. Then one worker went through its final buffer checks with interrupts
masked, as the old shutdown path had always asked it to do.

The ordinary repeats were frustratingly polite. Their remaining buffers were
small, the drains took a few milliseconds, and the gap did not return. So we made
the existing large-buffer case easier to hit: an 80 KiB shared pin every cycle,
held longer. Nothing stopped checking its contents. On the card, the old drain
took 56 milliseconds while the RTEMS tick count did not move at all. The IRQ gap
was 60.24 milliseconds. We had found the missing time.

Both workers already had to reach a STOP barrier before either could cancel its
shared references. After that barrier, no new work could begin, and the payload
being checked still had its pin. Its allocator operations already had their own
short locks. The outer interrupt mask was keeping the timer out of a byte scan
that did not need it. We let the timer back in for the drain, then masked again
before publishing completion and suspending. The controller still demanded both
workers and both interrupt continuations back before reclaiming anything.

The same large-buffer test with the fix took 60.75 milliseconds to drain, and
six timer ticks arrived during it. The maximum IRQ gap stayed at 10.50 ms. The
scan had not become faster; it had stopped silencing the clock. Across the two
normal runs and the two stress runs, four hundred pictures and 249 full paired
audits kept the memory and ownership evidence alongside the timing result.

The normal fixed run delivered 5.19 FPS and a 10.73 ms maximum IRQ gap. This was
a shutdown repair, not another renderer speedup. The evidence now keeps elapsed
drain time and tick progress beside the full audits, so a last long masked scan
cannot disappear merely because there is no following interrupt to measure it.

## Seventy-two trips for one picture

The card was already putting a whole frame into host memory. We then collected
it with seventy-two separate reads. The bus had finished its work; our host
interface was still asking for the picture a kilobyte at a time.

The replacement was deliberately mundane: one bounded copy of the entire
73,728-byte allocation, guards and completion record included. Nothing became
writable sooner. The slot stayed owned until a complete successful copy, then
an explicit release. A partial copy earned no release credit. That last rule
also exposed a small flaw in the older chunk path, which now follows it too.

One hundred frames later, all fifty-one full audit pairs had passed, along with
the held-slot stall, STOP and shared-heap drain. Ninety-five frames fetched over
HTTP matched the saved bytes. The kernel and Doom engine were the same binaries
as before. Capture calls fell from seventy-two to one, and their summed time
fell from 43.18 milliseconds to 0.28. Completion through release fell from
61.40 milliseconds to 26.40.

The FPS counter refused to join the celebration: 5.19 became 4.80 in this run.
The renderer still occupied roughly 190 milliseconds, and the earlier release
now spent longer waiting in the control path. Audit and scheduling phase moved
too. We had removed a real inefficiency, but had not demonstrated a faster game.
The evidence says both things, and keeps all the inconvenient intervals.

The full captures, exact module and replay instructions are in
`artifacts/bulk-capture-20261015/`. The next question is what release is waiting
for—not whether we can make the audits look away.

## Making the picture wait less

The next experiment separated two things that had been sharing one stopwatch:
waiting for the host audit lock, and actually executing the frame release. The
card was often innocent. A release could spend thirteen milliseconds queued
behind the host's own careful reading of frozen audit pages.

We kept the careful reading. Every word still had to be checked. But the audit
now let go of the lock between words, and a pending release got the next turn.
Once a complete frame had passed its ownership and guard checks, its immutable
host copy could also become available to the browser before the synchronous
release finished. The card buffer remained owned until that exact generation
was released. Nothing was recycled on faith.

Two longer, interleaved runs brought the release lock wait from 13.40 to 2.66
milliseconds, and completion-to-HTTP availability from 25.18 to 4.77. That is a
real reduction in delivery latency. It is not a browser paint measurement, and
it did not make the renderer faster: the matched frame rate stayed at about
4.84 FPS. The earlier 5.19 had partly been a short-window backlog effect.

We also gave the private C library its existing aligned word-copy and clear
paths. They passed the memory boundary tests, deterministic native runs and a
third full card run. They bought only 0.40 percent in the measured frame rate,
far too little to call a repeatable win. That switch stays optional. The renderer
still spends roughly 107 milliseconds in BSP work and 58 in planes; those are
better places to ask the next question.

The three runs delivered 1,560 frames and completed 186 full paired audits.
Every corresponding card picture agreed, the same four native pixel differences
remained, and stalled-host handling, held-frame STOP and heap drain all passed.
The useful result was a picture that waited less, plus a clearer account of why
it still took about a fifth of a second to draw the next one.

## The floor gets its turn

The next saving came from drawing the picture. The profile put about 108
milliseconds in BSP and wall work, and another 58 in the planes. We left the
old point-side compiler workaround alone. Its object file did not change by a
single byte. Instead, three renderer files got selective speed optimization,
and the span loop learned to calculate two samples together. In low detail it
looked up each color once, duplicated it, and used an aligned word store when
the destination allowed one. Odd ends and unaligned spans kept their byte stores.

Then we ran the original, the candidate, the candidate again, and the original
again: 520 frames each, with the same input and full audits. Every corresponding
picture agreed. The plane stage fell from 57.91 to 40.03 milliseconds. The whole
renderer fell from 187.64 to 168.18, and the sustained rate rose from 4.831 to
5.334 frames per second. This time, five frames per second survived the longer
window and the reversed run order.

The BSP/wall stage improved only slightly, from 108.31 to 106.50 milliseconds.
The experiment grouped compiler flags and span code, so it cannot award every
saved instruction to one cause. It can say where most of the measured time went.
It can also say what stayed: the ownership checks, release priority, the full
audits, and the same four known pixel differences from native rendering.

Four runs, 2,080 frames, 243 paired audits. Stalled-host handling, held-frame STOP
and heap drain passed every time. The linked image grew by 272 bytes, without
adding renderer state or moving the mutable-memory bounds. The new build switch
stays optional while we try more scenes. The floor is cheaper now; the walls
still have most of the remaining budget.

## The walls follow

The backlog put columns next. We already had a specialized C loop from an older
experiment; now it had to earn its place beside the faster spans. The loop chose
wall wrapping or finite-post clamping once, before drawing the column. It also
chose single or doubled output once. The original range checks and pixel values
stayed, and the point-side compiler workaround remained byte-for-byte unchanged.

Four more 520-frame runs put the span baseline at 5.330 frames per second and the
column candidate at 6.204. Rendering fell from 168.70 to 141.81 milliseconds.
Walls and BSP work lost about 22.6 milliseconds, sprites another 4.3; the planes
stayed where we had left them. The image grew by 480 bytes. The heap did not need
another allocation.

There was one wrinkle in the comparison. Both candidate runs matched every
reference picture. The last unchanged baseline repeated the main menu at frame
64, where the reference had already entered episode selection. It matched again
from frame 65 onward. All pictures in the declared timing window agreed. The
asynchronous input path could explain the transition, but we had not recorded
which frame consumed each key, so that remained an inference. The strict image
checker kept its failure. The report kept the picture.

The system checks were less ambiguous: 2,080 frames, 234 paired audits, the full
replays and tamper tests, stalled-host handling, held-frame STOP and heap drain
all passed. The gain belonged to drawing the same scene faster. It did not buy
permission to remove the checks, and it did not quietly turn down the detail.

Quality became a setting again. The profiling adapter had been forcing low
detail before every frame. An opt-in mode now chooses the initial preference
once, then lets Doom's F5/menu control it. One card session went low, high, low
without replacing the binary. The renderer reported each transition, and another
100 frames and 45 paired audits completed with STOP and drain intact.

That test also earned its debugging notes. A host hook tried to examine a frame
number too early; its failed capture stayed in the archive, and a regression
test now catches that path. Then a tamper test found that the replay check for
held-frame STOP metadata was skipped for the shorter capture lengths. We fixed
the parentheses and kept the test. The real capture passed; the edited one no
longer did. Faster columns and a detail button were useful. So was a check that
had learned to say no in one more case.

## The division underneath

The next suspect was not a pixel loop. It was the small fixed-point divide that
Doom called from its wall and sprite calculations. The linked code led into a
general 64-bit helper, with normalization, quotient correction and several
hardware divide/remainder operations. The processor had a narrower instruction
for the job we actually needed.

We kept the original saturation rule, divided unsigned magnitudes with `ediv`,
and restored the sign. The awkward INT_MIN cases kept their original path.
There was no reciprocal approximation to explain away later. A profiler counted
47 source call sites, and both builds compared the new routine with the old one
32 times before every display. Those checks happened on the i960 itself.

Four more 520-frame runs put the instrumented original at 6.047 frames per
second and the candidate at 6.309. Rendering fell from 144.94 to 138.08
milliseconds. The division brackets fell from 9.588 to 3.669 milliseconds per
frame, mostly in wall scaling and point-to-distance work. They included timer
reads and interruptions; calling them exact CPU time would have made the story
neater and the measurement wrong. Both builds paid the profiling overhead, so
ordinary-play speed still needed its own test.

This time all corresponding pictures agreed, including the menus. So did every
per-frame divide count. We had 231 full paired audits, 66,560 successful target
arithmetic comparisons, the same four native pixel differences, and clean stall,
STOP and drain tests. The largest interrupt gap was 10.81 milliseconds. Frame
delivery itself had not become faster. The renderer simply finished its work
about seven milliseconds sooner.

The new switch stays optional. It is a measured gain in one scene, not a promise
about every map. The earlier menu-timing discrepancy still needs input-consumption
tracing, and the profiler still needs to come out before we quote a new ordinary
play rate. A smaller job for division was enough progress for this experiment.

## Taking the divide profiler out

The arithmetic had earned its place, but it was still carrying its measuring
instruments. Every divide read a timer, and every display compared another 32
answers against the original routine. Useful evidence, but not work the game
needed to do forever.

We separated the switches. The exact divide could now stand on its own, with
Doom calling its usual entry point. The original signed fallback stayed. The
actual C and assembly objects were identical to the ones we had already tested
on the card. The divide counters and self-tests disappeared from the linked
image; the frame, CPU and WAD counters stayed for the comparison.

Another four 520-frame runs put the original at 6.224 frames per second and the
exact divide at 6.412. The two candidate runs were almost indistinguishable:
6.413 and 6.410. Rendering fell from 141.25 to 136.93 milliseconds, mostly in
the walls. Delivery did not improve. It was a three-percent gain, not a shortcut
to ten frames per second, and worth keeping on its own terms.

All the pictures agreed again. We kept 230 full paired audits, stalled the host
with both slots held, stopped the engine with frames outstanding, and checked
that the heap drained. The largest interrupt gap was 10.79 milliseconds. The
same four pixels still separated the native oracle from the card. Removing the
divide profiler had not removed the surrounding ownership or audit checks.

The option stays explicit. One scene at low detail is a useful qualification,
not every map. The earlier menu discrepancy still deserves a record of which
frame actually consumed each key. For now, the processor spends a little less
time dividing, and the evidence for that claim fits beside the code.

## Following the key

The next question was about a menu picture, not a faster pixel loop. Once, an
unchanged build had repeated a menu frame. The host knew when it sent the key,
but that was not the same as knowing when Doom used it.

We put a small optional recorder beside the input path. It marked a key leaving
the card queue, entering the menu responder and leaving it, with the display
generation and both game-loop tic counters. The records travelled in the
existing owned frame. A full recorder reported overflow instead of hiding loss.

The first card attempt found a mistake in the host logger: it tried to read a
frame variable outside its scope. We saved the failed run, passed the frame
explicitly, added a regression test and repeated the run with the same card
binary. That failure belongs in the evidence too.

The successful traces were precise. Escape sent after host frame 60 was used
for display frame 62 at game tic 61. The Enter pairs followed at frames 64, 66
and 68. Both traced runs agreed, including the menu opening and closing. The
host was observing a pipeline already in flight. Two display generations were
not a direct measurement of input-to-screen latency, and the old untraced
capture still could not tell us exactly what had happened that time.

The exact divide became the normal playable build, with an explicit switch
back to the original. Tracing stayed optional. Four accepted runs measured
6.432 frames per second without it and 6.412 with it. All 2,080 pictures agreed;
228 full paired audits and the stall, STOP and heap-drain checks passed. The
largest interrupt gap was 10.83 milliseconds. We had gained a useful way to
ask when a key took effect without giving up the checks around the game.

## Keeping the comparison together

The old wrong-floor bug had left a small monument in the build: one BSP function
compiled without optimization, because this compiler could let a branch replace
the condition codes before a later instruction read them. That workaround had
earned its place. Removing it required more than a promising disassembly.

The replacement made the wrapping arithmetic explicit and kept each comparison
and its boolean result in one inseparable instruction pair. A million host
cases, a thousand and twenty-four physical vectors, and then four more complete
Doom runs agreed. Every one of the 2,080 pictures matched. The held buffers,
STOP, heap drain and 229 full audit pairs agreed too.

The stopwatch was less dramatic: 6.428 against 6.431 frames per second.
The repeats varied by more than that apparent improvement. The function became
smaller and its arithmetic better defined, but this experiment did not discover
a hidden frame-rate reserve. It stays optional; the old workaround stays
available. The next useful question is how much time belongs to traversing the
tree, and how much to drawing the walls reached through it.

C columns also remain an explicit build choice, even though the benchmark builds
use them. The exact divide is the optimization now enabled by default. Small
switches, but worth recording: a reproducible result includes knowing which
machine code was actually running. The public IPv6 page was restored afterward;
the [captures](artifacts/notes/point-side-20261016.md) keep the full account.

## The tree was not the forest

The profiler had called one large number “BSP.” That sounded like eighty
milliseconds spent walking a tree. It was really the whole journey through the
tree and the work done at its leaves, including drawing the walls.

Four nested stopwatches made the distinction visible. In the measured view,
traversal and culling took about five milliseconds. Other subsector work took
fifteen, wall setup twenty-one, and the wall loop forty. The stopwatches included
interrupts and their own cost, so these were elapsed brackets, not a census of
CPU instructions. But they were enough to move an iterative tree rewrite down
the list. Most of that old number had belonged to other work.

We also tried compiling the wall module for speed instead of size. The two
candidate runs came in just ahead of both references: 6.323 against 6.358 frames
per second when pooled, and about one millisecond less rendering time. A small
result, honestly kept. The wall loop itself had not become faster, and the
experiment did not explain every shift between the other buckets.

There was a price for knowing more. With the stopwatches out, the plain control
ran at 6.427 frames per second. Instrumentation had cost about 2.7 milliseconds
of renderer time. Both new switches stay optional; normal play keeps the clocks
out, and the compiler choice still needs an uninstrumented comparison before it
becomes a default.

All 2,600 pictures agreed. The 285 full audit pairs, held buffers, STOP, heap
drain and independent replays agreed too. We restored the public web page and
kept the [complete evidence](artifacts/notes/walls-20261016.md). The next useful
experiment is in the floor and ceiling spans: another forty-millisecond stage,
with an exact two-sample loop to compare against a carefully bounded wider one.

## Four samples, four runs

The next experiment looked small enough to understand by inspection: take four
floor or ceiling samples through the span loop instead of two. The coordinate
arithmetic stayed unsigned, the duplicated low-detail pixels stayed exact, and
the old tails handled whatever remained. The larger loop added 304 bytes of
machine code. Its registers held the working values without spilling to a stack.

The pictures agreed. More than a hundred thousand primitive cases per version,
repeated native runs, and all 2,080 card images passed their comparisons. The
228 full audit pairs, held buffers, STOP and heap drain passed too. Nothing in
this experiment required giving up a check around the game.

For three runs, the stopwatch seemed to offer another small improvement. The
first reference managed 6.431 frames per second; the candidates managed 6.456
and 6.443. Then the final reference, using the very same two-sample binary as
the first, ran at 6.814. It was faster throughout the measured window, not just
in one lucky frame. The images were still identical.

That last run belonged in the result. Pooling the complete comparison put the
references at 6.617 and the candidates at 6.449. The hashes, options, framebuffer
addresses and ten-millisecond interrupt period did not explain the difference.
Cache and scheduling state were questions to investigate, not answers we had
proved. Calling the wider loop a speedup would have meant looking away from the
best reference run.

So the four-sample version stays available behind a switch, and two samples
remain the default. The next job is to understand how the unchanged reference
became faster before trusting another small improvement. The
[complete captures](artifacts/notes/span-four-20261016.md) keep the surprising
run alongside the others. The public IPv6 page was restored after the captures
were safe. A useful experiment can end with a better question.

## A cheaper floor, at the press of a key

The next gain was visible before it was measurable. Press F6, and the patterned
floor became a solid grey plane. The ceiling lost its texture too. The walls,
window frames, sky, pistol and status bar kept doing exactly what they had done
before. Press F6 again, and the texture came back. No new firmware, no level
restart, no second binary pretending to be the same experiment.

This was an honest quality trade. Each plane kept its boundaries and sector
lighting, but used one palette colour from its texture instead of mapping the
texture and shading it by distance. The same clipped spans still determined
where the floor belonged. We had made the floor cheaper to draw, not given the
renderer permission to write outside it.

One 520-frame run switched textured, flat, flat, textured through four measured
windows after loading the level. The textured windows delivered 6.476 and
6.433 frames per second; the flat windows delivered 7.897 and 7.857. Together,
that was **6.454 to 7.877 FPS**, a 22 percent gain. Plane rendering fell from
about 41 milliseconds to 13.5. The walls and sprites had scarcely moved in the
profile. This time the explanation and the measurement pointed to the same
piece of work.

The safety machinery stayed on. Fifty-six complete audit pairs, the stalled
host, both held DMA slots, STOP and heap drain all passed. The native comparison
still had its four familiar differing pixels, in both modes; those did not
become acceptable to forget just because the floor was now grey. A single
scene and a short session did not prove eight frames per second everywhere,
and the older interactive transport did not inherit the benchmark's absolute
speed by association. But the quality switch itself worked on the card and
returned to the original picture. That was a useful bargain, and now it had a
button.

[Measurements and before/after pictures](artifacts/current/flat-planes-20261016/README.md).

## Half the rows did not mean twice the speed

The next switch was F7. It could leave the floors textured or flat, independently
of F6, and could return to full height without rebuilding the engine. Instead of
changing Doom's projection, we shaded alternate rows and copied each into the
row below. The world kept its shape. The HUD stayed sharp. The card still owned
the same buffers, and every full audit stayed in place.

Then we measured it. A 920-frame run visited all four combinations twice, in a
balanced order. Full-height textures gave 6.362 FPS; half-height textures gave
6.404. Flat planes alone gave 7.723, while half-height plus flat planes gave
7.111. The new option worked, but the attractive arithmetic of “half the pixels”
did not survive the whole pipeline.

There was a real saving inside it: textured plane rendering fell from 43.88 to
26.12 milliseconds. But wall-column work and the sprite stage, which now also
included row expansion, took most of that budget back. Geometry and the 64 KiB
frame transfer had not become smaller. Flat planes already made floor shading
cheap enough that adding half-height actually slowed the frame down.

We kept the switch, with full height as the default, and kept the result honest.
The native engine reproduced the card's quality sequence, including the same
four known pixel differences moving exactly as alternate-row sampling predicted.
STOP, stalled buffers and heap cleanup passed. An extra three-switch native test
also caught a mistake in the test itself: Doom stops polling after key-up, so a
second event must remain pending rather than disappear when its scheduled frame
passes. Fixing that made F5, F6 and F7 coexist in the test as they should.

The next question is narrower now: can a specialized half-column loop and cheaper
row expansion preserve the plane saving? That is a measured place to look, rather
than another promise of ten frames per second.

## A second card, and four honest kilobytes

The 100 MHz AcceleRAID arrived beside the old card, not in its place. That made
the first rule simple: every command named a PCI function, and the old DAC960PG
stayed unbound. The new card gave us its complete one-megabyte flash image, then
its boot chain: reset code, a small unpacker below the main image, and 6.00-05
expanding into RAM. It also offered an eight-kilobyte PCI BAR that looked too
small to be useful.

The Intel manual changed the meaning of those eight kilobytes. The lower half
was the 80303 messaging unit. The upper half was a real translated window into
local RAM. Its mask said eight kilobytes; its translation value said
`c0000000`. Moving that value for a read and restoring it under an exit trap let
us inspect the live card without inventing a memory map.

At `c0001e00`, 256 bytes were zero before the first store. We wrapped the
80-byte probe in guards, wrote the record through the window, read every byte
back, and put every zero back. The complete four-kilobyte page had the same
SHA-256 before and after. The translation register returned to its stock value,
SSH stayed up, and the old card never acquired a driver. The new card now had a
proven RAM upload route.

It did not yet have a proven call route. The tempting diagnostic hook ended in
the firmware's memory-mailbox setup routine. Worse, both its pointer and its
dispatcher lived in cacheable RAM, and the 80303 does not snoop host writes.
The host could see a new pointer while the processor still saw the old one. On
this command, stale meant performing a real configuration operation, not merely
missing our marker. So we stopped with the probe restored and uncalled.

That distinction is the useful result: transport works; execution still needs
an i960-side cache barrier and a normal-return handoff. Four kilobytes were
enough to prove the first fact without pretending they proved the second.

[The exact receipt and next gate](artifacts/current/accele160-ram-route-20261016/README.md).

The next evening we traced the cache barrier we had hoped the stock firmware
already knew how to perform. The raw image did contain data-cache invalidation
instructions. One belonged to an interactive debug menu; others sat among
transfer code and memory tests. None gave the host a demonstrated, bounded way
to refresh both caches and return to a command. A `sysctl` instruction looked
promising until its operand, `0x300`, decoded as processor reinitialization.

An empty interrupt vector was no shortcut. The 80303 remembers software
interrupt priority inside the processor and can keep vectors internally too;
writing pending bits over PCI does not make it rescan at a known time. We left
the probe uncalled. The audit narrowed the work to a genuine firmware call
route or a small recoverable helper, and the old card was still untouched.

[The cache and interrupt audit](artifacts/current/accele160-cache-gate-20261016/README.md).

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
  network rounds. A small freestanding runtime and owned Doom entry now support two matching
  first-frame startups, an intervening STOP and complete system drain. A later
  bounded build returns two visible frames per startup, with byte-exact native
  comparisons and a browser gallery. The next persistent browser build delivered
  six frames, forward/release input and clean owned STOP. It is extremely slow—
  about one frame every six seconds—and a small native/card pixel discrepancy
  remains recorded. The subsequent paired-mailbox reader reaches about one frame per second,
  with full audits and shutdown passing. Startup and the small rendering
  discrepancy remain open. A subsequent DMA comparison moves the same four
  pictures 2.21 times faster, but a later completion timeout initially prevented
  FPS and cleanup acceptance. Two subsequent complete runs pass all audits and
  drain and measure about 42–43% higher FPS with DMA. The original binary passes
  too. A later small frame producer reproduced a peer heap check incorrectly
  rejecting owned DMA; the corrected isolation check passed 512 frames, 89
  active-transaction checks and full STOP/drain. The fixed Doom repeat then
  passed 28 frames and 29 full audit pairs, delivering 1.377 FPS with DMA versus
  0.973 with mailbox. The later two-buffer binary build passes 52 frames and
  29 audit pairs at 1.396 FPS with CRC and 2.070 without CRC. DMA stays opt-in
  pending longer interactive acceptance. The later bounded ping-pong integration
  coordinates frame and WAD traffic on DMA1 and delivers 100 browser frames with
  108 full audit pairs, level restart and held-buffer STOP. Its controlled
  comparison improves 3.503 to 3.887 FPS; ordinary play remains on the earlier
  transport pending longer interactive qualification. The later WAD ring cuts
  matched startup from 290.09 to 186.57 seconds with all audits retained, but
  warm restart rises from 2.84 to 4.24 seconds. It remains opt-in while the
  read-ahead policy is refined. Later full-audit profiling observes roughly
  20.6 MB/s in the DMA completion bracket, while byte-copy loops in the WAD
  cache consume about 94 seconds across the bounded loading test. The subsequent aligned word-copy change reduces those copies to about 18
  seconds, startup to 117.57 seconds and warm restart to 2.89 seconds, with
  68 full audit pairs and unchanged ownership checks. Staging and read-ahead
  remain the next loading targets. The subsequent fixed-screen word copy
  improves delivered FPS from 3.815 to 4.517 (+18.39%), with 67 full audit
  pairs and unchanged persistent-screen/DMA ownership. The later release-priority
  work cuts completion-to-HTTP waiting while sustained FPS remains about 4.84.
  The span optimization reaches 5.334 against 4.831 FPS. Specialized C columns
  then reach 6.204 against a fresh 5.330 baseline in four more 520-frame runs.
  Full audits pass; all measured-window images agree, with one unchanged-baseline
  menu transition differing outside that window. One binary can now switch high
  and low detail. Broader interactive/map qualification remains open.
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

The second card, an AcceleRAID 160 with a 100 MHz controller, began a new
investigation. We read its entire stock flash twice through the card's own
READIMAGE command and found a narrow PCI window into local RAM. A guarded
upload and exact restoration worked, but running the uploaded program is a
different promise: the host cannot make this processor forget stale cached
instructions simply by writing new bytes. We looked for a stock cache and
call gate before trying the program.

The stock debug menu seemed promising until its input path came into focus.
The loader tests a UART register at startup, then chooses either real console
callbacks or stubs. The live card chose the stubs: every input is `q`, and
output vanishes. The menu's `e` command really does invalidate data cache,
but there is no host-controlled way to send it in this boot, and its Code
Manager offers memory diagnostics rather than a safe returning call. An
earlier notebook called the key `d`; two indexing mistakes had cancelled and
pointed to the right table word with the wrong label. The corrected trace
names `e`. The new card has not executed our code yet. Its next milestone is
a small, recoverable firmware helper with a clear RAM and cache contract.

The first offline cut found a possible doorway: diagnostic subcommand `0x8f`
currently just says "unsupported," while `0x8e` belongs to the stock memory
mailbox. The loader also carries about seven and a half kilobytes of erased
space into RAM. We placed the already-built eighty-byte probe there in a
throwaway in-memory image and repaired the two known boot checksums; the image
analyzer accepted that structure. Nothing points at the probe. The runtime
dispatch table is compressed. The next test sent one zero-DMA `0x8f` command
through a driver bound only to the new card after a fresh boot. Stock firmware
completed it as unsupported, with zero residual; the captured command was the
exact sixty-four bytes we intended. The old card did nothing. We also wrote a
strict native model of the proposed PING packet and tried malformed variants
against it. That proves a clean doorway and a proposed admission rule, not a
room behind the door: no helper is installed, no new code has run, and boot or
recovery of a patched image remains untested.

We then rehearsed the first wiring change entirely offline. Twenty-eight bytes
in the loader's copied but erased tail could call the original setup routine,
point only the `0x8f` dispatch slot at a new address, and return. For this
rehearsal that new address leads straight back to stock "unsupported." The
known checksums pass, the compressed program stays byte-for-byte the same, and
the changed bytes fit on a short whitelist. It is deliberately a doorbell
that still answers "no": we have a map for routing a command, not yet the
handler, response, boot proof or recovery confidence needed to program it.

The next offline pass put an actual answer behind that door. The Linux GEM
driver publishes all sixty-four command bytes, and the card's firmware copies
all four sixteen-byte chunks into the object its IOCTL dispatcher reads. The
same stock firmware has a normal completion route for zero status, while the
unsupported route we already measured yields host status two. That gave us a
small, testable contract: a versioned, zero-DMA PING with an `I960` signature
and nonzero nonce may return status zero; every other shape still goes to the
old unsupported handler. The i960 implementation fits in 148 bytes of the
copied loader's erased tail. We checked its exact machine code, assembled an
image only in memory, and found that the compressed program stayed identical
while both known checksums passed. Nothing was programmed or run. In
particular, we have not yet proved the boot-time table write survives startup
or that we can recover this particular card if a flash experiment fails. The
nonce is checked, not echoed; a future live success status would still need
careful attribution.

Then we moved the doorbell. The first PING hook wrote the dispatch word soon
after decompression, leaving the loader's own descriptor pass ahead of it. We
found a common return after that pass and replaced its single return
instruction with a branch into the same copied, erased tail. The new hook
writes the table entry and performs the displaced return. The boot block next
enables the data cache—the `dcctl 1` instruction does not invalidate it—and
hands off to the main program. A second in-memory audit passed with fewer
changed bytes. It narrows the interval in which the stock loader could undo
our write. It does not tell us whether the running program later changes the
table, or whether the board can be recovered if valid-checksum code hangs.
The boot block contains a recovery command loop, but having code on paper is
not the same as reaching it from a PC beside a silent card. We left the flash
and both cards alone.

There was one more fact we could get without teaching the card a new command.
The 80303's PCI aperture can look at a selected 4 KiB of its local memory.
We pointed it briefly at the stock dispatch table, read the page, and put the
aperture back. All 4,096 bytes matched the original decompressed firmware,
including the `0x8f` word that still points to "unsupported." The old card
stayed untouched and both PCI devices remained unbound. This gives us a good
baseline for a future changed-image test. It is not that test: a stock page
after boot cannot reveal whether later startup code would overwrite our new
pointer with the stock one.

*For the reproducible version of these last acts, see
[ROM-FETCH-LIVE.md](docs/loader/ROM-FETCH-LIVE.md),
[FIRMWARE-PROGRAMMED.md](docs/firmware/FIRMWARE-PROGRAMMED.md), and
[SOFTWARE-LOADER.md](docs/loader/SOFTWARE-LOADER.md), and
[rtems/README.md](rtems/README.md). The story ends here for now; the
captures don't.*

We followed the boot block's other door. Its UART test writes a scratch
register and only trusts the port if the byte comes back. After that it
looks at one incoming character during reset. `S` leads to a small recovery
program copied from the boot ROM into RAM; `!` leads to a different,
manufacturing path. There is also a status bit in the flash-control register
that forces recovery. That bit was tempting as an SSH shortcut until we traced
the same register through the erase-and-program routine. Changing it to see
what happens would not be a recovery test we could call safe.

The copied recovery program includes a full-flash staging and programming
route. We pinned the branch and copy instructions to the exact 1 MiB stock
dump, and a changed byte made the audit fail. On the board, though, the
similar UART test had previously chosen inert console callbacks. We still
do not know whether a header exists or why that test failed. The new card and
the old one stayed unbound; we sent no command and wrote no flash. A recovery
routine visible in disassembly is an opportunity, not yet a rescue plan. The
next physical experiment is to identify a level-correct serial connection,
catch `S` at power-on, make a harmless recovery read, and return to a stock
image whose full-flash hash matches the saved dump. Only then should the
late PING candidate move from an offline image to a programming trial.

The user had another way back: a team with a flash programmer in the office.
That changed the decision about the new card. We still did not send an
unexamined image. We exported the exact 1 MiB candidate whose 155 changed
bytes and checksums had already been audited, and built two separate host
commands. The first could only stage an image in controller RAM. The second
could ask the stock firmware to program flash, but stayed inert until given
an exact start token after same-boot evidence was checked.

The first bind in an already-used boot met the familiar mailbox status 2. We
started fresh with the stock driver temporarily blacklisted. The stage command
then completed with clean DMA guards. A full read through the firmware's
image path returned every byte of the candidate. We deliberately changed one
byte of a copied readback record; the flash preflight refused it before loading
the programming module. With the real record, the card spent 37 seconds on
its flash command and reported success. The old PG had no driver and received
no command.

The PC did not return after the first reboot, as it had failed to do after
older controller tests. A physical power cycle brought Linux back. The new
card initialized and still called itself firmware 6.00-05. We read its full
flash twice, through two separate guarded transfers after that power cycle.
Both files matched the candidate, and each other, byte for byte. Finally we
sent the small PING envelope to the new `0x8f` handler. It completed with
status zero. Changing just the `I` of its signature to `H` produced the stock
unsupported status 2. That pair is our first live proof that the new card ran
our patched i960 code after boot and retained the strict fallback. It is not
an arbitrary program loader yet. We removed the temporary blacklist after
saving the evidence; the external programmer and the stock dump remain the
fallback if a later patch goes wrong.

The little PING was a doorbell, not a program. It showed that the new card
could enter our copied-loader handler after a cold start, but the host still
could not place instructions in RAM and have the i960 run them. We made the
next image deliberately narrow. It preserved PING and the stock fallback, then
added one more `0x8f` operation. That operation knows an 80-byte program by its
exact bytes, knows where its result belongs, invalidates the card's data and
instruction caches, calls the program, checks four result words, and returns
to the firmware's ordinary completion path. There is no host-provided jump
address hiding in the command.

We first looked at the proposed page through the 80303 aperture. The upper
half of the 8 KiB BAR does not map to the translation base itself; it maps a
page above it. Once that offset was accounted for, the loader's `c000f000`
page matched the flash image and the two planned slots were erased. We staged
the exact 1 MiB candidate, read all of it back through the firmware, and sent
one flash command. It took about 37 seconds and returned status zero. A
software reboot again let the stock Linux driver bind first; swapping drivers
in that warm boot reached mailbox status 2. A temporary blacklist and a
physical power cycle gave our guarded read driver the first bind.

On the fresh boot, two complete flash reads matched the new candidate. The
original PING still succeeded, and a one-byte-bad signature still reached the
stock unsupported result. Then the host saved the entire 4 KiB loader page,
wrote just the fixed result and code slots, read them back, restored the
aperture to its default mapping, and submitted operation 2. The card returned
status zero and the four expected words: `444f4e45`, the nonce `16102671`,
the sum `000001f0`, and its XOR `80114670`. The host captured the page,
restored the slots, compared all 4,096 bytes with the saved page, and released
the command module. It repeated the whole call once, with the same result and
an identical page preimage. Another full flash read after the first call
still matched. The old card remained unbound throughout.

This is the first ordinary, returning execution of host-staged RAM code on the
new card. It is also intentionally a small result. The flashed handler accepts
only those exact 80 bytes. A read-only survey found zero-filled pages farther
up the reported 16 MiB DRAM, but a zero page is not an allocation: stock RAID
firmware may use or repurpose it later. RTEMS needs tens or hundreds of
kilobytes just for its image, and Doom needs an 8 MiB arena. We have the
execution foothold and a reliable aperture; the next act is to establish
ownership, carry a larger validated image across in chunks, and give the new
board its own timer, interrupt, STOP, network and frame-delivery contracts.

We could narrow the memory question without claiming an allocation. Following
the stock image-read command through the firmware led to its own memory
allocator. It counts 32 KiB blocks, records the caller beside each count, and
hands back an address only after finding a contiguous run. We read that table
twice through the same guarded aperture. Both copies agreed: one pool had 38
free blocks in a row, the other 47. That is enough space for a small RTEMS
image if a future helper can request and hold it through the stock allocator.
It is far short of Doom's 8 MiB arena. We still have not asked the allocator
for a block; reading its book is not the same as having our name written in it.

Then we asked the allocator to write our name in its book. A fixed 256 KiB
request succeeded and freed cleanly. The first host checker complained about
two changing bytes just past the allocator's count and owner arrays; it was
watching firmware state outside the grant. We retained the command, restored
its result slot under readback, corrected the comparison to the actual 512
metadata words, and ran the call again. Those words returned to their
preimage. That was permission to try a longer lease, not permission to borrow
arbitrary zero-looking DRAM.

The next helper reserved exactly 512 KiB at `c0710000` with a fixed owner ID.
The reservation survived a completed host command, and a separate command
freed it. We saw all sixteen 32 KiB blocks carry our owner while the lease was
active and watched all sixteen return to free afterward. The host could write
one odd 4 KiB page through the PCI aperture, but the even pages were still
invisible from that window. We gave the card a bounded copying job: the host
staged one page in the last odd page of its own grant, read it back, and asked
the i960 to check its hash before copying it to an indexed payload page. The
first even page worked. So did an independently readable odd page and the
last allowed payload page. A bad staged hash and an attempt to target the
staging page returned the stock rejection status without a copy. The grant,
control words and loader page still came back exactly as they started.

One lease could then hold more than one page. We copied pages 0 and 126 under
the same owner, reloading only the one-shot command companion between copies.
After that we added a command that hashes a contiguous run of owned pages.
Two adjacent pages produced the same 8 KiB digest on the card and host. A
wrong digest and a count beyond the 127-page payload limit were rejected.
The card's digest is FNV: it catches a bad transfer in this bounded experiment,
but it is not a signature against a malicious image. Our host still pins exact
firmware and module identities before a command runs.

The first call from this rented memory was deliberately familiar. We placed
the same 80-byte leaf that had already returned from the loader page at the
start of the grant, with one more page behind it. The new handler checked the
whole two-page digest and every byte of the leaf, invalidated the instruction
cache, and called `c0710000`. The leaf returned the nonce, the sum 496 and its
XOR result. We released the grant, checked all allocator owners and the loader
page, and did it again in a fresh grant. A wrong digest and a one-byte change
to the leaf were rejected before the result slot moved. Full flash reads
before and after still matched the programmed image, and the old PG stayed
unbound. At this point the AcceleRAID can run a known program from memory it
actually owns; it cannot yet run a new RTEMS board build.

Finally we tried a load the size of that future job. Seventy-seven 4 KiB
pages—315,392 bytes—went through the same staging and card-copy path under one
lease, with a host readback and a card result for every page. The card hashed
the whole region before we returned the grant. It took about 6.1 seconds to
upload and 0.1 seconds for the digest in this one run. This is 284 bytes more
than the archived IPv6 RTEMS flat image from the PG, and it leaves 204,800
bytes of payload space for other extent. That arithmetic does not pay for
RTEMS's BSS, stacks, heap, network buffers or the new board support. We have
proved the crossing and the lease; the next act is to link a small AcceleRAID
RTEMS task for this map, measure its real writable footprint, and give it a
bounded clock and STOP before trying the web server or Doom.

The next program was no longer a hand-written leaf. We gave the AcceleRAID
its own RTEMS build, linked for the owned grant instead of transplanting the
PG's image. Its whole flat image, including zero-initialized BSS, was only
57,972 bytes. Fifteen pages carried it, with 112 payload pages still free.
The entry saved the firmware's processor state, ran a real RTEMS worker, and
restored the state before returning. This first clock was deliberately
synchronous: ten calls to RTEMS's clock tick service, no borrowed hardware
interrupt. The worker asked to wake after five ticks. The card's final report
said it woke on tick five, finished, and returned to the stock command path.

We changed the flash helper only enough to admit that one fixed image: exact
owner and address, exact fifteen-page count, embedded whole-image digest and
entry bytes, then instruction-cache handoff. The 1 MiB candidate changed
only the loader cave and checksum words. We staged it, read every byte back,
flashed once, and restarted. Two full post-boot reads matched. On the first
owned upload every page's host readback and card checksum agreed. A wrong
hash and a wrong page count both returned unsupported status without touching
the result. The real RTEMS call returned the eight expected words. We put the
staging page, loader page, aperture and all allocator owner/count words back,
read the entire flash again, and repeated the task under a fresh grant. The
second return and final full flash read matched too; the old PG stayed
unbound. The host saw about 51 milliseconds for each command cycle, dominated
by its polling interval, not a measured RTEMS CPU time.

This is a real RTEMS task on the 100 MHz card, but only a bounded software-clock
one. We have not yet claimed the card's hardware timer or interrupts, a
persistent operating system, a host STOP channel, a network link or Doom's
multi-megabyte arena. The next chapter is to learn those new-board ownership
rules before letting RTEMS run independently or serve a page.

So we listened to the new card's clock before touching it. Intel's 80303
manual gave us a warning: reading either timer mode register clears its
terminal-count status. We built one more fixed firmware command that skipped
those registers entirely. It read the counts, reloads, interrupt mask and
pending state, mappings, the live PRCB pointer, and eight words from the
stock ROM PRCB. It wrote a small report into the saved loader page and
returned. No timer, vector, mask or DMA register was written.

The new image passed the same full staging readback and flash checks, then
two complete reads after a reboot. The first live inventory call returned,
but our host checker again watched two bytes just beyond the allocator owner
arrays. We captured the discrepancy, found all 512 actual owner records
unchanged, restored the loader page, and released the completed command.
Two fresh calls passed with the right metadata boundary. A final full flash
read still matched. The old PG was unbound throughout.

Timer 0's count moved while its reload stayed fixed; the stock firmware was
using it. Timer 1's count and reload were zero, its interrupt was masked,
and no interrupt was pending in these three snapshots. The live PRCB pointer
still matched the boot ROM. That narrows the next experiment, but it does not
give us timer 1: we have not read its mode, checked the live cached vector at `0x04`,
installed an owned interrupt stack, or proved an independent STOP channel.

The parallel driver review supplied the missing stop lesson. Linux's `myrs`
companion holds its direct-command mutex until a card callback returns. Another
ordinary mailbox request could wait behind the very task we wanted to stop.
The driver's own command ring publishes its first word last and drains a
completion ring in interrupt context, useful rules for a future resident
transport, but neither gives our one-shot callback a second command lane. We
chose a sideband word in the saved loader page instead. The host can change
that word through the PCI aperture while the direct command is still open;
the card invalidates its data cache before each read.

We gave the new image one more fixed opcode, preserving all ten earlier ones.
Its record carries a magic, nonce, epoch, READY, STOP and ACK, and its poll loop
has a fixed limit. The offline image audit found changes only in the retained
loader cave and two checksum words. We read all 1 MiB of the existing flash,
staged the candidate, read all of the staged image back, flashed it, and
rebooted. Two complete reads in the new boot matched exactly. The old PG was
unbound throughout.

Then we left the card in a real pending callback. A wrong STOP value did not
end it. The right value returned an ACK with the expected nonce and epoch, and
the stock command completed normally; the host saw about 22 milliseconds for
that cycle, including its own polling. In a second call we sent nothing. The
card exhausted its 20-million-poll budget after 10.26 seconds and returned
stock unsupported status instead of waiting forever. Both calls restored the
saved loader page and PCI aperture; all 512 allocator owner/count records
matched. A final complete flash read still matched, and no test companion
remained. We now have a real independent STOP *channel* on the 100 MHz card,
not yet a STOP supervisor for arbitrary RTEMS tasks. The live cached vector,
timer mode, owned interrupt stack, timer drain and restoration remain the next
hardware gates before autonomous RTEMS can borrow the clock.
