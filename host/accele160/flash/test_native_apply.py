"""Offline host gates for the destructive UPD1 APPLY command."""
import pathlib
import struct
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stage_native_update import NativeStage  # noqa: E402


class FakeStage(NativeStage):
    def __init__(self):
        self.sequence = 7
        self.words = {1: 7, 2: 7, 8: 2, 9: 256, 11: 1}
        self.commands = []

    def map_page(self, value):
        pass

    def read_word(self, index):
        return self.words.get(index, 0)

    def command(self, seq, cmd, **kwargs):
        self.commands.append((seq, cmd, kwargs))
        return 3, 256


class FailedApplyStage(NativeStage):
    def __init__(self):
        self.sequence = 7
        self.words = {1: 7, 2: 7, 7: 9, 12: 5, 13: 0x28, 14: 0xb0000}

    def map_page(self, value):
        pass

    def read_word(self, index):
        return self.words.get(index, 0)

    def write_word(self, index, value):
        self.words[index] = value
        if index == 1:
            self.words[2] = value


class ApplyGateTests(unittest.TestCase):
    def setUp(self):
        self.stage = FakeStage()
        self.manifest = {"base_sha256": "12" * 32, "target_sha256": "34" * 32}
        for start, key in ((128, "base_sha256"), (160, "target_sha256")):
            raw = bytes.fromhex(self.manifest[key])
            for pos in range(0, 32, 4):
                self.stage.words[(start + pos) // 4] = struct.unpack_from("<I", raw, pos)[0]

    def test_exact_sealed_session_issues_one_apply(self):
        self.assertEqual(self.stage.apply(self.manifest), (3, 256))
        self.assertEqual(self.stage.commands, [(8, 5, {"timeout": 900})])

    def test_missing_writer_never_issues_apply(self):
        self.stage.words[11] = 0
        with self.assertRaisesRegex(RuntimeError, "no linked flash writer"):
            self.stage.apply(self.manifest)
        self.assertEqual(self.stage.commands, [])

    def test_wrong_digest_never_issues_apply(self):
        self.stage.words[40] ^= 1
        with self.assertRaisesRegex(RuntimeError, "target_sha256 differs"):
            self.stage.apply(self.manifest)
        self.assertEqual(self.stage.commands, [])

    def test_unsealed_or_pending_never_issues_apply(self):
        for index, value in ((8, 1), (2, 6)):
            original = self.stage.words[index]
            self.stage.words[index] = value
            with self.assertRaises(RuntimeError):
                self.stage.apply(self.manifest)
            self.stage.words[index] = original
        self.assertEqual(self.stage.commands, [])

    def test_failed_apply_reports_chip_diagnostics(self):
        stage = FailedApplyStage()
        with self.assertRaisesRegex(RuntimeError,
                r"APPLY returned 9; writer=5, S3 status=0x28, flash offset=0xb0000"):
            stage.command(8, 5)
        self.assertEqual(stage.sequence, 8)
        self.assertEqual(stage.words[1], 8)


if __name__ == "__main__":
    unittest.main()
