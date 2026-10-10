import pathlib
import shutil
import tempfile
import unittest
from validate_capture import classify

CAPTURE = pathlib.Path(__file__).resolve().parents[2] / 'artifacts/dump-attempt-20261010'


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = pathlib.Path(self.temp.name)
        for name in ['result.txt', 'enquiry-before.bin', 'enquiry-after.bin', 'read-a5.bin', 'read-5a.bin']:
            shutil.copyfile(CAPTURE / name, self.directory / name)

    def tearDown(self):
        self.temp.cleanup()

    def test_live_capture_has_no_host_update(self):
        result = classify(self.directory)
        self.assertEqual(result['outcome'], 'no_host_buffer_update')
        self.assertTrue(result['transport_checks_passed'])
        self.assertFalse(result['physical_flash_backup_verified'])

    def test_stale_identifier_invalidates_transport(self):
        path = self.directory / 'result.txt'
        path.write_text(path.read_text().replace('complete op=21 id=0003', 'complete op=21 id=0002'))
        self.assertFalse(classify(self.directory)['transport_checks_passed'])

    def test_uncertain_dma_never_validates(self):
        path = self.directory / 'result.txt'
        path.write_text(path.read_text().replace('pending=0;', 'pending=1;'))
        self.assertEqual(classify(self.directory)['outcome'], 'unverified_capture')

    def test_matching_bytes_are_not_automatically_a_backup(self):
        for name in ['read-a5.bin', 'read-5a.bin']:
            (self.directory / name).write_bytes(bytes([0xff]) * 512)
        result = classify(self.directory)
        self.assertEqual(result['outcome'], 'repeatable_capture_requires_semantic_and_image_validation')
        self.assertFalse(result['physical_flash_backup_verified'])

    def test_load20_staging_pattern_is_not_firmware(self):
        root = CAPTURE.parent / 'dump-load20-20261010'
        result = classify(root / 'offset0')
        self.assertEqual(result['outcome'], 'repeatable_sentinel_value_not_firmware')
        self.assertTrue(result['command_direction_verified'])
        self.assertFalse(result['source_is_physical_flash_verified'])

    def test_load20_real_transfer_still_needs_image_validation(self):
        root = CAPTURE.parent / 'dump-load20-20261010'
        for directory in ['offset200', 'window200']:
            result = classify(root / directory)
            self.assertTrue(result['transport_checks_passed'])
            self.assertTrue(result['captures_equal'])
            self.assertEqual(result['outcome'],
                             'repeatable_capture_requires_semantic_and_image_validation')
            self.assertFalse(result['physical_flash_backup_verified'])

    def test_short_file_rejected(self):
        (self.directory / 'read-a5.bin').write_bytes(b'a')
        with self.assertRaises(ValueError):
            classify(self.directory)


if __name__ == '__main__':
    unittest.main()
