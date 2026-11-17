import struct
import unittest

from observe import check_config, decode, decode_pci_release


class ObserveTest(unittest.TestCase):
    def config(self):
        data = bytearray(0x48)
        struct.pack_into("<2H", data, 0, 0x1069, 0x0050)
        struct.pack_into("<2H", data, 0x2c, 0x1069, 0x0054)
        struct.pack_into("<2I", data, 0x40, 0xffffe000, 0xc0000000)
        return data

    def test_pci_release_record(self):
        # Words as written by the emulator run of the passive release image
        # (config-retry-gate.json, pci0).
        record = decode_pci_release((0x30494350, 0xc, 0x48, 0x3, 0x00501069,
                                     0x00541069, 0x0, 55))
        self.assertTrue(record["config_cycle_retry_was_set_at_reset"])
        self.assertTrue(record["config_cycle_retry_released"])
        self.assertTrue(record["option_rom_hidden"])
        self.assertEqual(record["register_writes"], 55)
        # A board strapped RETRY low would report it rather than assume.
        self.assertFalse(decode_pci_release(
            (0x30494350, 0x18, 0x48, 0x2, 0, 0, 0, 49)
        )["config_cycle_retry_was_set_at_reset"])
        self.assertIsNone(decode_pci_release((0,) * 8))   # image without it
        with self.assertRaises(ValueError):
            decode_pci_release((0x30494350,) * 7)

    def test_exact_identity_and_aperture(self):
        resource = "ee002000 ee003fff 00000200\n"
        record = check_config(self.config(), resource)
        self.assertEqual(record["piatvr"], "c0000000")
        for change in (lambda b: struct.pack_into("<H", b, 2, 0x0010),
                       lambda b: struct.pack_into("<I", b, 0x44, 0xc0800000)):
            data = self.config()
            change(data)
            with self.assertRaises(ValueError):
                check_config(data, resource)

    def test_markers(self):
        words = (0x32544753, 0x2000, 15840, 0x12345678,
                 64, 1, 1, 0x50415353, 0)
        record = decode(words)
        self.assertTrue(record["stage2_entered"])
        self.assertTrue(record["stage2_copy_ok"])
        self.assertEqual(record["rtems_result"], "PASS")
        self.assertIsNone(record["host_startup"])

    def test_host_startup_snapshot(self):
        words = (0x32544753, 0x2000, 15840, 0x12345678,
                 64, 1, 1, 0x50415353, 0,
                 0x30545348, 4, 6, 2, 4, 0xfffffffb, 7)
        sample = decode(words)["host_startup"]
        self.assertTrue(sample["bridge_pci_ready"])
        self.assertTrue(sample["raid_pci_ready"])
        self.assertTrue(sample["boot_doorbell_seen"])
        self.assertEqual(sample["inbound_status"], "0x00000004")
        self.assertEqual(sample["inbound_mask"], "0xfffffffb")

    def test_sequenced_monitor_and_mailbox_pointer(self):
        words = (0x32544753, 0x2000, 16464, 0x12345678,
                 64, 1, 1, 0x50415353, 0,
                 0x30545348, 0x107, 0x107, 3, 7, 0xffffffff, 7,
                 12, 0x9f120, 0, 0x31545348)
        result = decode(words)
        self.assertEqual(result["host_monitor"]["sequence"], 12)
        self.assertEqual(result["host_monitor"]["mailbox_pointer"],
                         "0x000000000009f120")
        changed = list(words)
        changed[16] = 13
        with self.assertRaises(ValueError):
            decode(changed)

    def test_mailbox_ingress_extension(self):
        base = (0x32544753, 0x2000, 16700, 0x12345678,
                64, 1, 1, 0x50415353, 0,
                0x30545348, 0x107, 0x107, 3, 7, 0xffffffff, 7,
                14, 0x9f120, 0, 0x31545348)
        words = base + (0x3058424d, 2, 0x7f, 0x9f3e0, 0x12345678)
        result = decode(words)
        self.assertEqual(result["mailbox_ingress"]["state"], "0x00000002")
        self.assertEqual(result["mailbox_ingress"]["command_id"], 0x7f)
        self.assertEqual(result["mailbox_ingress"]["output_bus_address"],
                         "0x0009f3e0")
        reply = decode(words + (0x304c5052, 2, 0xcf28fbb5))
        self.assertEqual(reply["local_reply"],
                         {"state": "0x00000002", "fnv32": "0xcf28fbb5"})
        dma = decode(words + (0x304c5052, 2, 0xcf28fbb5,
                              0x31414d44, 2))
        self.assertEqual(dma["dma1_reply"], {"state": "0x00000002"})
        two = decode(words + (0x304c5052, 2, 0xcf28fbb5,
                              0x31414d44, 2, 0x32514552, 2, 0x11))
        self.assertEqual(two["request_sequence"],
                         {"limit": 2, "completed_count": 2, "last_ioctl": "0x11"})
        three = decode(words + (0x304c5052, 2, 0xcf28fbb5,
                                0x31414d44, 2, 0x33514552, 3, 0x15))
        self.assertEqual(three["request_sequence"],
                         {"limit": 3, "completed_count": 3, "last_ioctl": "0x15"})
        four = decode(words + (0x304c5052, 2, 0xcf28fbb5,
                               0x31414d44, 2, 0x34514552, 4, 0xd0))
        self.assertEqual(four["request_sequence"],
                         {"limit": 4, "completed_count": 4, "last_ioctl": "0xd0"})
        five = decode(words + (0x304c5052, 2, 0xcf28fbb5,
                               0x31414d44, 2, 0x35514552, 5, 0x2d))
        self.assertEqual(five["request_sequence"],
                         {"limit": 5, "completed_count": 5, "last_ioctl": "0x2d"})


if __name__ == "__main__":
    unittest.main()
