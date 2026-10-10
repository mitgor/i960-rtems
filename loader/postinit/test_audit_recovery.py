import unittest
from pathlib import Path
from audit_recovery import audit

ROOT = Path(__file__).resolve().parents[2] / 'artifacts'


class RecoveryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = (ROOT/'private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
        cls.package = (ROOT/'postinit-update-20261010/experimental-firmware.img').read_bytes()

    def test_monitor_lies_wholly_in_preserved_bootblock(self):
        monitor, report = audit(self.stock, self.package)
        candidate = (ROOT/'postinit-preflight-20261010/experimental-full-rom.bin').read_bytes()
        self.assertEqual(monitor, candidate[0x7d600:])
        self.assertEqual(len(monitor), 0x2a00)
        # Vendor/device ID initialization, including device 0x11.
        self.assertEqual(monitor[0x128:0x13c].hex(),
                         '0030a88c691000000010ad8a111eb05c0220b58a')
        self.assertFalse(report['flash_ready'])
        self.assertFalse(report['vendor_acceptance_verified'])

    def test_reject_damaged_donor(self):
        with self.assertRaises(ValueError):
            audit(self.stock[:-1], self.package)

    def test_reject_wrong_type_adapter_and_length(self):
        for offset, value in ((13, 1), (0x58, 0x20), (8, 1), (0, 0)):
            with self.subTest(offset=offset):
                data = bytearray(self.package); data[offset] = value
                with self.assertRaises(ValueError):
                    audit(self.stock, bytes(data))

    def test_zero_adapter_uses_vendor_default(self):
        data = bytearray(self.package); data[0x58:0x5a] = b'\0\0'
        _, report = audit(self.stock, bytes(data))
        self.assertTrue(report['partial_vendor_checks']['normal_and_recovery_adapter_comparison'])
