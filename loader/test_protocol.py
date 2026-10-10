#!/usr/bin/env python3
"""Self-check for the loader handshake/protocol (hardware-independent).

Models the four MU registers as shared state, runs loader.c's loop logic and
loadctl.c's command() logic against each other, and asserts that a load+go
sequence lands the right words at the right address and dispatches correctly.
If this fails, the protocol design is wrong - before you ever touch the card.
"""
OP_PING, OP_SET_ADDR, OP_WRITE, OP_READ, OP_GO = 1, 2, 3, 4, 5
ST_READY, ST_OK, ST_BADOP = 0x600D, 0x0002, 0x00EE
M32 = 0xFFFFFFFF

class Card:
    """Shared registers + the loader's state; step() = one loader iteration."""
    def __init__(self):
        self.IMR0 = self.IMR1 = self.OMR0 = self.OMR1 = 0
        self.last = 0
        self.dst = 0
        self.mem = {}
        self.jumped = None
        self.OMR0 = (self.last << 16) | ST_READY   # reset: READY

    def step(self):
        if (self.IMR1 >> 16) == self.last:
            return False                            # no new command
        seq, op, arg, st = self.IMR1 >> 16, self.IMR1 & 0xffff, self.IMR0, ST_OK
        if op == OP_PING:       pass
        elif op == OP_SET_ADDR: self.dst = arg
        elif op == OP_WRITE:    self.mem[self.dst] = arg; self.dst = (self.dst + 4) & M32
        elif op == OP_READ:     self.OMR1 = self.mem.get(arg, 0)
        elif op == OP_GO:       self.jumped = arg
        else:                   st = ST_BADOP
        self.last = seq
        self.OMR0 = (self.last << 16) | st
        return True

class Host:
    def __init__(self, card): self.c, self.seq = card, 0
    def command(self, op, arg):                     # mirrors loadctl.c command()
        self.seq = (self.seq + 1) & 0xffff
        self.c.IMR0 = arg & M32                      # arg first
        self.c.IMR1 = (self.seq << 16) | op          # seq commits
        for _ in range(100):                         # "poll" -> let the loader run
            if self.c.step() and (self.c.OMR0 >> 16) == self.seq:
                return self.c.OMR0 & 0xffff
        raise AssertionError("no ack (timeout)")

def test():
    c = Card(); h = Host(c)
    assert c.OMR0 == (0 << 16) | ST_READY, "reset OMR0 should be READY"
    assert h.command(OP_PING, 0) == ST_OK

    # load 3 words to 0x200, like `loadctl load 0x200 FILE`
    words = [0xDEADBEEF, 0x00C0FFEE, 0xBEEF00EE]
    assert h.command(OP_SET_ADDR, 0x200) == ST_OK
    for w in words:
        assert h.command(OP_WRITE, w) == ST_OK
    for i, w in enumerate(words):
        assert c.mem[0x200 + 4 * i] == w, f"word {i} wrong"

    # read-back path
    assert h.command(OP_READ, 0x204) == ST_OK and c.OMR1 == 0x00C0FFEE

    # bad opcode is reported, not silently accepted
    assert h.command(0x1234, 0) == ST_BADOP

    # go dispatches to the right entry
    assert h.command(OP_GO, 0x200) == ST_OK and c.jumped == 0x200

    # robustness: a "restarted" host (seq reset) still gets through (!= compare)
    h.seq = 0
    assert h.command(OP_PING, 0) == ST_OK

    print("protocol self-check: PASS")

if __name__ == "__main__":
    test()
