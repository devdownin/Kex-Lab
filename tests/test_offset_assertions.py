import importlib.util
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    'offset_assertions', Path(__file__).resolve().parents[1] / 'scripts/assert-offsets.py')
offset_assertions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(offset_assertions)


class OffsetAssertionsTest(unittest.TestCase):
    def test_exact_delta_across_multiple_partitions(self):
        self.assertEqual(offset_assertions.new_ranges(
            {0: 2000, 1: 500, 2: 90}, {0: 2003, 1: 504, 2: 90}, 7),
            [(0, 2000, 3), (1, 500, 4)])

    def test_total_backlog_cannot_replace_new_traffic(self):
        with self.assertRaisesRegex(ValueError, 'Produced 0 new records'):
            offset_assertions.new_ranges({0: 2000}, {0: 2000}, 7)

    def test_extra_writers_are_reported_as_unreliable_evidence(self):
        with self.assertRaisesRegex(ValueError, 'expected exactly 7'):
            offset_assertions.new_ranges({0: 100}, {0: 108}, 7)

    def test_changed_partitions_and_rewinds_fail(self):
        for after in [{0: 105, 1: 2}, {0: 99}]:
            with self.assertRaises(ValueError):
                offset_assertions.new_ranges({0: 100}, after, 7)

    def test_offset_rows_are_strictly_validated(self):
        for content in ['', 'other:0:100\n', 'topic:0:no\n',
                        'topic:0:100\ntopic:0:101\n', 'topic:0:-1\n']:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'offsets'
                path.write_text(content)
                with self.assertRaises(ValueError):
                    offset_assertions.offsets(path, 'topic')


class ImagePinsTest(unittest.TestCase):
    def test_previously_floating_images_use_matching_manifest_and_compose_digests(self):
        root = Path(__file__).resolve().parents[1]
        manifest = dict(line.split('=', 1) for line in (root / 'versions.env').read_text().splitlines()
                        if line and not line.startswith('#'))
        for key, compose in [('AUTOTUNE_IMAGE', 'compose.autotune.yml'),
                             ('SPECTRALLM_IMAGE', 'compose.hub.yml'),
                             ('SPECTRALLM_FRONTEND_IMAGE', 'compose.hub.yml'),
                             ('LAG_EXPORTER_IMAGE', 'compose.observability.yml')]:
            image = manifest[key]
            self.assertRegex(image, r'^[\w./-]+@sha256:[a-f0-9]{64}$')
            self.assertIn('${' + key + ':-' + image + '}', (root / compose).read_text())
