"""Bounded command model for Intel 28F008S3, for offline fault tests only.

This models the 1 MiB x8 array, sixteen 64 KiB erase blocks, command
sequencing, status register, identifiers, and lock bits from Intel document
290598-005. A tick is an abstract WSM completion step, not device time.
Electrical pins, voltage thresholds, suspend/resume, and bus timing are not
modeled. This module is not a flash writer and must not drive hardware.
"""

from dataclasses import dataclass

SIZE = 0x100000
BLOCK = 0x10000
BLOCKS = SIZE // BLOCK
READY = 0x80
ERASE_ERROR = 0x20
PROGRAM_ERROR = 0x10
VPP_ERROR = 0x08
PROTECT_ERROR = 0x02


class UnknownContents(RuntimeError):
    """A reset interrupted an operation, so modeled array data is uncertain."""


@dataclass
class Operation:
    kind: str
    address: int
    value: int = 0
    ticks: int = 1


class S3Flash:
    def __init__(self, image: bytes | None = None):
        if image is not None and len(image) != SIZE:
            raise ValueError("28F008S3 requires exactly 1 MiB")
        self.array = bytearray(image if image is not None else b"\xff" * SIZE)
        self.mode = "array"
        self.status = READY
        self.vpp_enabled = False  # logical permission, not a voltage model
        self.rp_override = False  # models RP# at VHH, not a voltage value
        self.rp_low = False
        self.block_locked = [False] * BLOCKS
        self.master_locked = False
        self.unknown_blocks: set[int] = set()
        self.lock_state_unknown = False
        self.setup: tuple[str, int] | None = None
        self.pending: Operation | None = None

    @staticmethod
    def _address(address: int) -> None:
        if not 0 <= address < SIZE:
            raise ValueError("flash address outside 1 MiB")

    def read(self, address: int) -> int:
        self._address(address)
        if self.rp_low:
            raise RuntimeError("RP# low: outputs disabled")
        if self.mode == "status":
            return self.status
        if self.mode == "id":
            if address == 0:
                return 0x89
            if address == 1:
                return 0xA6  # 8-Mbit 28F008S3
            if address == 3:
                if self.lock_state_unknown:
                    raise UnknownContents("master lock state uncertain")
                return int(self.master_locked)
            if (address & 0xFFFF) == 2:
                if self.lock_state_unknown:
                    raise UnknownContents("block lock state uncertain")
                return int(self.block_locked[address // BLOCK])
            return 0xFF
        if address // BLOCK in self.unknown_blocks:
            raise UnknownContents(f"block {address // BLOCK} interrupted; readback required")
        return self.array[address]

    def _error(self, bits: int) -> None:
        self.setup = None
        self.pending = None
        self.status |= READY | bits
        self.mode = "status"

    def _begin(self, kind: str, address: int, value: int = 0) -> None:
        if self.lock_state_unknown:
            raise UnknownContents("lock state interrupted; reload from independent identification")
        if not self.vpp_enabled:
            # S3 Sections 4.5/4.6 explicitly assign SR.3 and SR.5 to low
            # VPP erase/program attempts; Figure 8 checks SR.3 first.
            self._error(VPP_ERROR | (ERASE_ERROR if kind in ("erase", "program", "clear_locks")
                                     else PROGRAM_ERROR))
            return
        block = address // BLOCK
        if kind in ("erase", "program") and self.block_locked[block] and not self.rp_override:
            self._error(PROTECT_ERROR | (ERASE_ERROR if kind == "erase" else PROGRAM_ERROR))
            return
        if kind in ("lock_block", "clear_locks") and self.master_locked and not self.rp_override:
            self._error(PROTECT_ERROR | (ERASE_ERROR if kind == "clear_locks" else PROGRAM_ERROR))
            return
        if kind == "lock_master" and not self.rp_override:
            self._error(PROTECT_ERROR | PROGRAM_ERROR)
            return
        self.pending = Operation(kind, address, value)
        self.status &= ~READY
        self.mode = "status"

    def write(self, address: int, value: int) -> None:
        self._address(address)
        if not 0 <= value <= 0xFF:
            raise ValueError("flash writes are byte-wide")
        if self.rp_low:
            raise RuntimeError("RP# low: command input disabled")
        if self.pending:
            raise RuntimeError("WSM busy; suspend/resume is outside this model")
        if self.setup:
            kind, setup_address = self.setup
            self.setup = None
            if kind == "erase" and value == 0xD0 and address // BLOCK == setup_address // BLOCK:
                self._begin("erase", address)
            elif kind == "program" and address == setup_address:
                self._begin("program", address, value)
            elif kind == "lock" and value == 0x01 and address // BLOCK == setup_address // BLOCK:
                self._begin("lock_block", address)
            elif kind == "lock" and value == 0xF1:
                self._begin("lock_master", address)
            elif kind == "lock" and value == 0xD0:
                self._begin("clear_locks", address)
            else:
                self._error(ERASE_ERROR | PROGRAM_ERROR)
            return
        if value == 0xFF:
            self.mode = "array"
        elif value == 0x90:
            self.mode = "id"
        elif value == 0x70:
            self.mode = "status"
        elif value == 0x50:
            self.status &= ~(ERASE_ERROR | PROGRAM_ERROR | VPP_ERROR | PROTECT_ERROR)
            self.mode = "status"
        elif value == 0x20:
            self.setup = ("erase", address)
        elif value in (0x40, 0x10):
            self.setup = ("program", address)
        elif value == 0x60:
            self.setup = ("lock", address)
        else:
            raise ValueError(f"unsupported or reserved S3 command 0x{value:02x}")

    def tick(self) -> None:
        """Complete one pending operation; no wall-clock duration is implied."""
        op = self.pending
        if op is None:
            return
        self.pending = None
        block = op.address // BLOCK
        if op.kind == "erase":
            start = block * BLOCK
            self.array[start:start + BLOCK] = b"\xff" * BLOCK
            self.unknown_blocks.discard(block)
        elif op.kind == "program":
            # NOR cells only move 1->0. Requesting 0->1 can report ready with
            # no WSM error, because internal verify only checks programmed 0s.
            self.array[op.address] &= op.value
        elif op.kind == "lock_block":
            self.block_locked[block] = True
        elif op.kind == "lock_master":
            self.master_locked = True
        elif op.kind == "clear_locks":
            self.block_locked = [False] * BLOCKS
            self.lock_state_unknown = False
        else:
            raise AssertionError(op.kind)
        self.status |= READY

    def reset_pin_low(self) -> None:
        """Assert RP# low. An interrupted WSM result is deliberately unknown."""
        if self.pending:
            if self.pending.kind in ("erase", "program"):
                self.unknown_blocks.add(self.pending.address // BLOCK)
            else:
                self.lock_state_unknown = True
        self.pending = None
        self.setup = None
        self.rp_low = True
        self.mode = "array"

    def reset_pin_high(self) -> None:
        self.rp_low = False
        self.mode = "array"
        self.status = READY

    def power_cycle(self) -> None:
        self.reset_pin_low()
        self.reset_pin_high()
