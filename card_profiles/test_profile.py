"""Offline profile contract: no PCI or flash access."""
import unittest
from card_profiles import load, pci_ids, require_workflow


class Profiles(unittest.TestCase):
    def test_exact_identities(self):
        self.assertEqual(pci_ids('dac960pg'), (0x1069, 0x0010, 0x1069, 0x0010))
        self.assertEqual(pci_ids('accele160'), (0x1069, 0x0050, 0x1069, 0x0054))

    def test_cross_card_workflows_rejected(self):
        for name, workflow in [('accele160', 'firmware_romhook'),
                               ('accele160', 'firmware_one_shot'),
                               ('dac960pg', 'firmware_flashimage'),
                               ('dac960pg', 'rtems_accele160'),
                               ('accele160', 'rtems_legacy')]:
            with self.subTest(name=name, workflow=workflow), self.assertRaises(ValueError):
                require_workflow(name, workflow)

    def test_unknown_board_rejected(self):
        with self.assertRaises(ValueError):
            load('other-i960')

    def test_doom_is_shared_but_clock_is_not(self):
        for name in ('dac960pg', 'accele160'):
            self.assertTrue(require_workflow(name, 'doom_i960'))
        self.assertNotEqual(load('dac960pg')['doom']['clock'],
                            load('accele160')['doom']['clock'])


if __name__ == '__main__':
    unittest.main()
