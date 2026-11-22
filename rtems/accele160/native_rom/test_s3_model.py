import unittest

from s3_model import (BLOCK, BLOCKS, ERASE_ERROR, PROGRAM_ERROR,
                      PROTECT_ERROR, READY, SIZE, S3Flash, UnknownContents,
                      VPP_ERROR)


class S3ModelTests(unittest.TestCase):
    def test_array_geometry_and_identifiers(self):
        chip = S3Flash()
        self.assertEqual(len(chip.array), SIZE)
        self.assertEqual(BLOCKS, 16)
        self.assertEqual(chip.read(0x80000), 0xFF)
        chip.write(0, 0x90)
        self.assertEqual((chip.read(0), chip.read(1)), (0x89, 0xA6))
        self.assertEqual(chip.read(0x50002), 0)
        self.assertEqual(chip.read(3), 0)
        chip.write(0, 0xFF)
        self.assertEqual(chip.read(0), 0xFF)

    def test_erase_program_and_readback_catches_zero_to_one(self):
        chip = S3Flash()
        chip.vpp_enabled = True
        address = 0x41000
        chip.write(address, 0x40)
        chip.write(address, 0x00)
        self.assertEqual(chip.read(address), 0)  # status busy
        chip.tick()
        self.assertEqual(chip.read(address), READY)
        chip.write(address, 0xFF)
        self.assertEqual(chip.read(address), 0)
        chip.write(address, 0x10)  # alternate program setup
        chip.write(address, 0xFF)  # cannot change a stored 0 back to 1
        chip.tick()
        self.assertEqual(chip.read(address), READY)  # status alone can look good
        chip.write(address, 0xFF)
        self.assertNotEqual(chip.read(address), 0xFF)  # byte readback detects it
        chip.write(address, 0x20)
        chip.write(address + 1, 0xD0)  # any address in the same block
        self.assertEqual(chip.read(address), 0)
        chip.tick()
        self.assertEqual(chip.read(address), READY)
        chip.write(address, 0xFF)
        self.assertEqual(chip.read(address), 0xFF)

    def test_vpp_and_block_lock_fail_closed(self):
        chip = S3Flash()
        address = 0x50000
        chip.write(address, 0x20)
        chip.write(address, 0xD0)
        self.assertEqual(chip.read(address) & (READY | VPP_ERROR | ERASE_ERROR),
                         READY | VPP_ERROR | ERASE_ERROR)
        chip.write(address, 0x50)
        self.assertEqual(chip.read(address), READY)
        chip.write(address, 0x40)
        chip.write(address, 0)
        self.assertEqual(chip.read(address) & (READY | VPP_ERROR | ERASE_ERROR),
                         READY | VPP_ERROR | ERASE_ERROR)
        chip.write(address, 0x50)
        chip.vpp_enabled = True
        chip.write(address, 0x60)
        chip.write(address, 0x01)
        chip.tick()
        chip.write(address, 0x90)
        self.assertEqual(chip.read(address + 2), 1)
        chip.write(address, 0x20)
        chip.write(address, 0xD0)
        self.assertEqual(chip.read(address) & (PROTECT_ERROR | ERASE_ERROR),
                         PROTECT_ERROR | ERASE_ERROR)
        chip.write(address, 0x50)
        chip.write(address, 0x40)
        chip.write(address, 0)
        self.assertEqual(chip.read(address) & (PROTECT_ERROR | PROGRAM_ERROR),
                         PROTECT_ERROR | PROGRAM_ERROR)
        chip.rp_override = True
        chip.write(address, 0x50)
        chip.write(address, 0x20)
        chip.write(address, 0xD0)
        chip.tick()
        self.assertEqual(chip.read(address), READY)

    def test_master_lock_requires_override_to_clear_blocks(self):
        chip = S3Flash()
        chip.vpp_enabled = True
        chip.write(0x60000, 0x60)
        chip.write(0x60000, 0x01)
        chip.tick()
        chip.write(0, 0x60)
        chip.write(0, 0xF1)
        self.assertEqual(chip.read(0) & (PROTECT_ERROR | PROGRAM_ERROR),
                         PROTECT_ERROR | PROGRAM_ERROR)
        chip.rp_override = True
        chip.write(0, 0x50)
        chip.write(0, 0x60)
        chip.write(0, 0xF1)
        chip.tick()
        chip.write(0, 0x90)
        self.assertEqual(chip.read(3), 1)
        chip.write(0, 0x60)
        chip.write(0, 0xD0)
        chip.tick()
        chip.write(0, 0x90)
        self.assertEqual(chip.read(0x60002), 0)
        self.assertEqual(chip.read(3), 1)  # master lock is not cleared

    def test_bad_erase_sequence_does_not_change_array(self):
        image = bytes([0xAA]) * SIZE
        chip = S3Flash(image)
        chip.vpp_enabled = True
        chip.write(0x40000, 0x20)
        chip.write(0x50000, 0xD0)
        self.assertEqual(chip.read(0) & (ERASE_ERROR | PROGRAM_ERROR),
                         ERASE_ERROR | PROGRAM_ERROR)
        chip.write(0, 0xFF)
        self.assertEqual(chip.read(0x40000), 0xAA)

    def test_power_loss_marks_active_block_uncertain(self):
        chip = S3Flash()
        chip.vpp_enabled = True
        chip.write(0xB1000, 0x20)
        chip.write(0xB1000, 0xD0)
        self.assertEqual(chip.read(0), 0)  # WSM busy
        chip.power_cycle()
        self.assertEqual(chip.status, READY)
        with self.assertRaises(UnknownContents):
            chip.read(0xB0000)
        self.assertEqual(chip.read(0xA0000), 0xFF)
        chip.write(0xB1000, 0x20)
        chip.write(0xB1000, 0xD0)
        chip.tick()  # a full subsequent erase resolves array uncertainty
        chip.write(0, 0xFF)
        self.assertEqual(chip.read(0xB1000), 0xFF)

    def test_power_loss_during_lock_change_blocks_further_writes(self):
        chip = S3Flash()
        chip.vpp_enabled = True
        chip.write(0x70000, 0x60)
        chip.write(0x70000, 0x01)
        chip.power_cycle()
        chip.write(0, 0x90)
        with self.assertRaises(UnknownContents):
            chip.read(0x70002)
        chip.write(0x70000, 0x20)
        with self.assertRaises(UnknownContents):
            chip.write(0x70000, 0xD0)


if __name__ == "__main__":
    unittest.main()
