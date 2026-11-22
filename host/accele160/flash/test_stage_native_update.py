import os
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage_native_update import DEFAULT_PIATVR, MAGIC, NativeStage, TARGET
from prepare_native_update import fnv32


class FakeStage(NativeStage):
    def __init__(self, require_idle=True):
        super().__init__(TARGET, require_idle=require_idle)
        self.piatvr = DEFAULT_PIATVR

    def pci(self, register, value=None):
        if register == "44.l":
            if value is not None:
                self.piatvr = value
            return self.piatvr
        return {"00.w": "1069", "02.w": "0050"}[register]


class NativeStageTests(unittest.TestCase):
    def service(self, backing, sequence=0, state=0, next_chunk=0):
        for word, value in ((0, MAGIC), (1, sequence), (2, sequence),
                            (8, state), (9, next_chunk), (10, 2)):
            backing.seek(4096 + word * 4)
            backing.write(struct.pack("<I", value))
        backing.flush()

    def test_missing_service_restores_aperture_without_bar_write(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            stage = FakeStage()
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with self.assertRaisesRegex(RuntimeError, "UPD1 service absent"):
                    with stage:
                        self.fail("missing service must not enter staging")
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)
            backing.seek(0)
            self.assertEqual(backing.read(8192), bytes(8192))

    def test_acknowledged_error_sequence_can_be_aborted(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing, sequence=7, state=1, next_chunk=3)
            stage = FakeStage(require_idle=False)
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with stage:
                    self.assertEqual(stage.sequence, 7)
                    def acknowledge(index, value):
                        NativeStage.write_word(stage, index, value)
                        if index == 1:
                            NativeStage.write_word(stage, 2, value)
                            NativeStage.write_word(stage, 8, 0)
                            NativeStage.write_word(stage, 9, 0)
                    with mock.patch.object(stage, "write_word", side_effect=acknowledge):
                        self.assertEqual(stage.abort(), (0, 0))
                    self.assertEqual(stage.sequence, 8)
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)

    def test_unacknowledged_command_blocks_abort(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing, sequence=7, state=1)
            backing.seek(4096 + 4)
            backing.write(struct.pack("<I", 8))
            backing.flush()
            stage = FakeStage(require_idle=False)
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with self.assertRaisesRegex(RuntimeError, "pending or its result is uncertain"):
                    with stage:
                        pass
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)

    def test_partial_write_blocks_abort(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing, sequence=7, state=4)
            stage = FakeStage(require_idle=False)
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with stage:
                    with self.assertRaisesRegex(RuntimeError, "partial flash write"):
                        stage.abort()
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)

    def test_abort_recovers_stale_data_mapping(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing, sequence=9, state=1, next_chunk=3)
            stage = FakeStage(require_idle=False)
            stage.piatvr = "c0802000"
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with stage:
                    self.assertEqual(stage.piatvr, "c0800000")
                    def acknowledge(index, value):
                        NativeStage.write_word(stage, index, value)
                        if index == 1:
                            NativeStage.write_word(stage, 2, value)
                            NativeStage.write_word(stage, 8, 0)
                            NativeStage.write_word(stage, 9, 0)
                    with mock.patch.object(stage, "write_word", side_effect=acknowledge):
                        self.assertEqual(stage.abort(), (0, 0))
                    self.assertEqual(stage.sequence, 10)
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)

    def test_data_readback_stops_before_chunk_command(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing)
            stage = FakeStage()
            target = b"A" * 0x100000
            manifest = {"base_sha256": "00" * 32,
                        "target_sha256": hashlib.sha256(target).hexdigest(),
                        "chunks_fnv32": [f"0x{fnv32(target[:4096]):08x}"] * 256}
            real_write = stage.write_word
            def discard_data(index, value):
                if stage.piatvr != "c0802000":
                    real_write(index, value)
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with stage:
                    with mock.patch.object(stage, "command", return_value=(1, 0)) as command:
                        with mock.patch.object(stage, "write_word", side_effect=discard_data):
                            with self.assertRaisesRegex(RuntimeError, "BAR data page differs at chunk 0 byte 0"):
                                stage.stage(target, manifest)
                        command.assert_called_once()
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)

    def test_timeout_leaves_request_uncertain_and_refuses_restart(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing)
            stage = FakeStage()
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with stage:
                    with self.assertRaises(TimeoutError):
                        stage.command(1, 1, timeout=0)
                    self.assertEqual(stage.sequence, 0)
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)
            recovery = FakeStage(require_idle=False)
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with self.assertRaisesRegex(RuntimeError, "pending or its result is uncertain"):
                    with recovery:
                        pass
            self.assertEqual(recovery.piatvr, DEFAULT_PIATVR)

    def test_acknowledged_chunk_error_advances_sequence_then_aborts(self):
        with tempfile.TemporaryFile() as backing:
            backing.truncate(8192)
            self.service(backing, sequence=7, state=1, next_chunk=3)
            stage = FakeStage(require_idle=False)
            with mock.patch.object(os, "open", return_value=os.dup(backing.fileno())):
                with stage:
                    def acknowledge(index, value):
                        NativeStage.write_word(stage, index, value)
                        if index == 1:
                            NativeStage.write_word(stage, 2, value)
                            if stage.read_word(3) == 2:
                                NativeStage.write_word(stage, 7, 4)
                            else:
                                NativeStage.write_word(stage, 7, 0)
                                NativeStage.write_word(stage, 8, 0)
                                NativeStage.write_word(stage, 9, 0)
                    with mock.patch.object(stage, "write_word", side_effect=acknowledge):
                        with self.assertRaisesRegex(RuntimeError, "returned 4"):
                            stage.command(8, 2, 3, 4096, 0)
                        self.assertEqual(stage.sequence, 8)
                        self.assertEqual(stage.abort(), (0, 0))
                        self.assertEqual(stage.sequence, 9)
            self.assertEqual(stage.piatvr, DEFAULT_PIATVR)


if __name__ == "__main__":
    unittest.main()
