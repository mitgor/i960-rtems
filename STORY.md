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
  RTEMS work; the host still relays packets. Exclusive takeover and unrestricted
  preemption remain future work.
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
