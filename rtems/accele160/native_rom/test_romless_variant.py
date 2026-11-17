import unittest
from pathlib import Path

from romless_variant import build, ROM_OFFSET


CANDIDATE = (Path(__file__).resolve().parents[3] /
             'artifacts/current/accele160-spare-rom-20261025/native-rom-spare-prototype.bin')
SECOND_CANDIDATE = (Path(__file__).resolve().parents[3] /
                    'artifacts/current/accele160-second-spare-20261026/native-rom-second-spare.bin')


class RomlessVariantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = CANDIDATE.read_bytes()

    def test_only_x86_signature_changes(self):
        output, receipt = build(self.candidate)
        self.assertEqual(output[:ROM_OFFSET], self.candidate[:ROM_OFFSET])
        self.assertEqual(output[ROM_OFFSET], 0)
        self.assertEqual(output[ROM_OFFSET + 1:], self.candidate[ROM_OFFSET + 1:])
        self.assertFalse(receipt['safe_to_flash'])

    def test_rejects_unpinned_input(self):
        changed = bytearray(self.candidate)
        changed[0x100] ^= 1
        with self.assertRaisesRegex(ValueError, 'exact saved spare'):
            build(bytes(changed))

    def test_second_spare_only_x86_signature_changes(self):
        candidate = SECOND_CANDIDATE.read_bytes()
        output, receipt = build(candidate)
        self.assertEqual(output[:ROM_OFFSET], candidate[:ROM_OFFSET])
        self.assertEqual(output[ROM_OFFSET], 0)
        self.assertEqual(output[ROM_OFFSET + 1:], candidate[ROM_OFFSET + 1:])
        self.assertEqual(receipt['source_card'], 'second-spare')


if __name__ == '__main__':
    unittest.main()
