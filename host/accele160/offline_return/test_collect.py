import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from collect import (EXPECTED_IDS, EXPECTED_KEYS, FLASH_BYTES, ORIGINAL, SPARE,
                     capture_pci_static_files, validate_target, verify_read)
from review_inventory import review


class CollectorGateTests(unittest.TestCase):
    def test_inventory_review_detects_changed_config_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            pci = {}
            metadata = {}
            for bdf in ("0000:37:04.0", SPARE, "0000:37:09.0", ORIGINAL):
                config = bytearray(64)
                for offset, value in ((0, 0x1069), (2, 0x0050),
                                      (0x2c, 0x1069), (0x2e, 0x0054)):
                    config[offset:offset + 2] = value.to_bytes(2, "little")
                config = bytes(config)
                resource = b"0 0 0\n" * 7
                files = {}
                for name, data in (("config", config), ("resource", resource)):
                    path = out / f"pci-{bdf}-{name}{'.bin' if name == 'config' else '.txt'}"
                    path.write_bytes(data)
                    files[name] = {"file": path.name, "bytes": len(data),
                                   "sha256": hashlib.sha256(data).hexdigest()}
                metadata[bdf] = files
                pci[bdf] = dict(zip(EXPECTED_KEYS, EXPECTED_IDS))
                pci[bdf].update(present=True, block_paths=[])
            (out / "inventory.json").write_text(json.dumps({
                "boot_id": "local-test", "pci": pci,
                "pci_static_files": metadata, "readimage_executed": False,
                "commands": [{"output_file": "lspci-all.txt", "exit_code": 0}]}))
            self.assertEqual(review(out)["gate"], "PASS")
            (out / f"pci-{SPARE}-config.bin").write_bytes(b"changed")
            self.assertEqual(review(out)["gate"], "REVIEW_REQUIRED")

    def ebcr_capture(self, out, bridge_config):
        pci, metadata = {}, {}
        for bdf in ("0000:37:04.0", SPARE, "0000:37:09.0", ORIGINAL):
            config = bytearray(bridge_config if bdf.endswith(".0") else bytes(256))
            if not bdf.endswith(".0"):
                for offset, value in ((0, 0x1069), (2, 0x0050),
                                      (0x2c, 0x1069), (0x2e, 0x0054)):
                    config[offset:offset + 2] = value.to_bytes(2, "little")
            files = {}
            for name, data in (("config", bytes(config)), ("resource", b"0 0 0\n" * 7)):
                path = out / f"pci-{bdf}-{name}{'.bin' if name == 'config' else '.txt'}"
                path.write_bytes(data)
                files[name] = {"file": path.name, "bytes": len(data),
                               "sha256": hashlib.sha256(data).hexdigest()}
            metadata[bdf] = files
            pci[bdf] = dict(zip(EXPECTED_KEYS, EXPECTED_IDS))
            pci[bdf].update(present=True, block_paths=[])
        (out / "inventory.json").write_text(json.dumps({
            "boot_id": "local-test", "pci": pci, "pci_static_files": metadata,
            "readimage_executed": False,
            "commands": [{"output_file": "lspci-all.txt", "exit_code": 0}]}))
        return review(out)

    def test_review_decodes_ebcr_from_bridge_config(self):
        def bridge(value, size=256):
            config = bytearray(256)
            config[0x40:0x42] = value.to_bytes(2, "little")
            return bytes(config[:size])
        with tempfile.TemporaryDirectory() as temp:
            result = self.ebcr_capture(Path(temp), bridge(0x0048))
            self.assertEqual(result["gate"], "PASS")
            self.assertTrue(result["ebcr_measured_on_both_bridges"])
            self.assertEqual(result["ebcr"]["0000:37:04.0"],
                             {"available": True, "raw": "0x0048",
                              "config_cycle_retry_set": False,
                              "equals_stock_write_0x0048": True})
        with tempfile.TemporaryDirectory() as temp:
            # Non-root sysfs read: 64 bytes, EBCR not reachable. Not a failure,
            # but the measurement is reported as incomplete.
            result = self.ebcr_capture(Path(temp), bridge(0x0048, 64))
            self.assertEqual(result["gate"], "PASS")
            self.assertFalse(result["ebcr_measured_on_both_bridges"])
            self.assertIn("as root", result["ebcr"]["0000:37:09.0"]["reason"])
        with tempfile.TemporaryDirectory() as temp:
            # Retry still set on a card Linux enumerated contradicts the model.
            result = self.ebcr_capture(Path(temp), bridge(0x004c))
            self.assertEqual(result["gate"], "REVIEW_REQUIRED")
            self.assertTrue(result["ebcr"]["0000:37:04.0"]["config_cycle_retry_set"])

    def test_static_pci_capture_reads_config_and_rom_resource_row(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            device = root / "sys/bus/pci/devices" / SPARE
            device.mkdir(parents=True)
            config = bytearray(range(256))
            config[4:6] = (0x0006).to_bytes(2, "little")
            config[0x30:0x34] = (0x00ef0000).to_bytes(4, "little")
            config = bytes(config)
            (device / "config").write_bytes(config)
            rows = [f"{n:016x} {n:016x} 0000000000000200" for n in range(7)]
            (device / "resource").write_text("\n".join(rows) + "\n")
            out = root / "out"
            out.mkdir()
            result = capture_pci_static_files(root / "sys", SPARE, out)
            self.assertEqual((out / f"pci-{SPARE}-config.bin").read_bytes(), config)
            self.assertEqual(result["config"]["sha256"], hashlib.sha256(config).hexdigest())
            self.assertEqual(result["rom_resource_row"], rows[6])
            self.assertEqual(result["pci_command_now"]["raw"], "0x0006")
            self.assertTrue(result["pci_command_now"]["bus_master_enabled"])
            self.assertFalse(result["expansion_rom_bar_now"]["decode_enabled"])
            self.assertEqual((device / "config").read_bytes(), config)

    def test_target_rejects_changed_driver_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            sysfs = Path(temp)
            param = sysfs / "module/myrsread/parameters/read_bdf"
            param.parent.mkdir(parents=True)
            param.write_text(SPARE + "\n")
            pci = {}
            for bdf, driver in ((SPARE, "myrsread"), (ORIGINAL, None)):
                pci[bdf] = dict(zip(EXPECTED_KEYS, EXPECTED_IDS))
                pci[bdf].update(driver=driver, block_paths=[])
            validate_target({"pci": pci}, sysfs)
            pci[ORIGINAL]["driver"] = "myrsread"
            with self.assertRaisesRegex(RuntimeError, "spare-only"):
                validate_target({"pci": pci}, sysfs)
            pci[ORIGINAL]["driver"] = None
            pci[SPARE]["block_paths"] = ["host0/target0/block/sda"]
            with self.assertRaisesRegex(RuntimeError, "exposes storage"):
                validate_target({"pci": pci}, sysfs)

    def test_read_verifier_checks_bytes_hash_and_status(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            data = bytes(FLASH_BYTES)
            digest = hashlib.sha256(data).hexdigest()
            (directory / "data.bin").write_bytes(data)
            (directory / "result.json").write_text(json.dumps({
                "bytes": FLASH_BYTES, "sha256": digest}))
            status = "done=1 status=0 residual=0 selector=9 length=1048576 guard_changes=0 released=0\n"
            (directory / "status.txt").write_text(status)
            self.assertEqual(verify_read(directory), digest)
            (directory / "status.txt").write_text(status.replace("guard_changes=0", "guard_changes=1"))
            with self.assertRaisesRegex(RuntimeError, "guard_changes"):
                verify_read(directory)


if __name__ == "__main__":
    unittest.main()
