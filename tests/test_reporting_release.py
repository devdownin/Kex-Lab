import argparse
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


report = load('lab_report', 'lab_report.py')
release = load('prepare_release', 'prepare-release.py')
lag = load('lag_exporter', 'lag-exporter.py')


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.object(report, 'ROOT', self.root).start()
        patch.dict(os.environ, {'KEX_LAB_REPORT_DIR': str(self.root / 'reports'),
                               'COMPOSE_PROJECT_NAME': 'test-project', 'KEX_LAB_TOPIC': 'demo'}).start()
        (self.root / 'VERSION').write_text('0.1.0\n')

    def test_record_keeps_counts_and_no_record_payload(self):
        work = self.root / 'work'; work.mkdir()
        (work / 'before').write_text('demo:0:100\n')
        (work / 'after').write_text('demo:0:104\n')
        (work / 'sample').write_text('sensitive-customer-payload\nnot-json-poison-message\n')
        args = argparse.Namespace(work=work, expected=4, exit_code=0, scenario='dlt', topic='demo')
        with patch.object(report, 'head', return_value='a' * 40), redirect_stdout(io.StringIO()):
            self.assertEqual(report.record(args), 0)
        text = next((self.root / 'reports/assertions').glob('*.json')).read_text()
        entry = json.loads(text)
        self.assertEqual((entry['status'], entry['observedRecords']), ('PASS', 4))
        self.assertTrue(entry['newPoisonRecordVerified'])
        self.assertNotIn('sensitive-customer-payload', text)
        args.exit_code = 1
        with patch.object(report, 'head', return_value=None), redirect_stdout(io.StringIO()):
            report.record(args)
        self.assertIn('FAIL', [json.loads(p.read_text())['status'] for p in (self.root / 'reports/assertions').glob('*.json')])

    def fake_runtime(self, args, health_code=0):
        if args[:2] == ['git', 'rev-parse']:
            value = 'a' * 40
        elif args[:2] == ['git', 'status']:
            value = ''
        elif 'ps' in args:
            value = json.dumps([{'ID': 'container-123', 'Service': 'explorer', 'State': 'running'}])
        elif args[:2] == ['docker', 'inspect']:
            self.assertNotIn('.Config.Env', ' '.join(args))
            value = json.dumps({'imageId': 'sha256:' + '2' * 64,
                                'configuredImage': 'example/explorer:override', 'startedAt': '2026-10-17T00:00:00Z'})
        elif args[:3] == ['docker', 'image', 'inspect']:
            value = json.dumps(['example/explorer@sha256:' + '3' * 64])
        else:
            return subprocess.CompletedProcess(args, health_code, 'UP Explorer\n' if health_code == 0 else 'DOWN Explorer\n', 'DO_NOT_LEAK')
        return subprocess.CompletedProcess(args, 0, value, 'DO_NOT_LEAK')

    def test_report_uses_actual_image_identity_and_marks_absent_assertions(self):
        with patch.object(report, 'command', side_effect=self.fake_runtime), redirect_stdout(io.StringIO()):
            self.assertEqual(report.report(argparse.Namespace(profile='core')), 0)
        data = json.loads((self.root / 'reports/latest.json').read_text())
        self.assertEqual(data['containers'][0]['configuredImage'], 'example/explorer:override')
        self.assertTrue(data['containers'][0]['repoDigests'][0].endswith('3' * 64))
        text = (self.root / 'reports/latest.md').read_text()
        self.assertIn('UNMEASURED', text)
        self.assertNotIn('DO_NOT_LEAK', text)
        self.assertNotIn('Agent', data['interfaces'])

    def test_failed_health_still_writes_report_and_returns_failure(self):
        with patch.object(report, 'command', side_effect=lambda a: self.fake_runtime(a, 1)), redirect_stdout(io.StringIO()):
            self.assertEqual(report.report(argparse.Namespace(profile='core')), 1)
        self.assertEqual(json.loads((self.root / 'reports/latest.json').read_text())['health']['status'], 'FAIL')

    def test_latest_assertions_filter_project_topic_and_time(self):
        directory = self.root / 'reports/assertions'; directory.mkdir(parents=True)
        for i, (project, topic, date, status) in enumerate([
                ('test-project', 'demo', '2026-10-16', 'FAIL'),
                ('test-project', 'demo', '2026-10-17', 'PASS'),
                ('other-project', 'demo', '2026-10-18', 'FAIL'),
                ('test-project', 'other', '2026-10-18', 'FAIL')]):
            (directory / f'{i}.json').write_text(json.dumps({'schemaVersion': 1, 'scenario': 'basic',
                'project': project, 'topic': topic, 'recordedAt': date, 'status': status}))
        entries = report.latest_assertions(self.root / 'reports', 'test-project', 'demo')
        self.assertEqual([entry['status'] for entry in entries], ['PASS'])

    def test_interface_urls_remove_credentials_and_query(self):
        self.assertEqual(report.safe_url('http://user:secret@localhost:8080/path?token=secret#fragment'), 'http://localhost:8080/path')
        self.assertIsNone(report.safe_url('file:///etc/passwd'))

    def test_compose_ps_ndjson_and_empty_output(self):
        self.assertEqual(report.parse_ps(''), [])
        self.assertEqual(report.parse_ps('{"Service":"explorer"}\n{"Service":"agent"}\n'),
                         [{'Service': 'explorer'}, {'Service': 'agent'}])


class LagExporterTest(unittest.TestCase):
    def test_measured_zero_and_critical_lag_are_distinct_from_missing(self):
        measured = lag.metrics({'status': 'UP', 'components': {'kafkaLag': {'details': {'lag': 0}}}})
        self.assertIn('kex_lab_autotune_consumer_lag 0\n', measured)
        missing = lag.metrics({})
        self.assertIn('kex_lab_autotune_probe_success 0\n', missing)
        self.assertNotIn('kex_lab_autotune_consumer_lag', missing)
        for invalid in [True, -1, '0', float('nan'), float('inf')]:
            self.assertNotIn('kex_lab_autotune_consumer_lag', lag.metrics({'components': {'kafkaLag': {'details': {'lag': invalid}}}}))

    def test_503_health_preserves_measured_critical_lag(self):
        payload = {'status': 'DOWN', 'components': {'kafkaLag': {'details': {'lag': 12000}}}}
        error = HTTPError(lag.URL, 503, 'DOWN', {}, io.BytesIO(json.dumps(payload).encode()))
        with patch.object(lag, 'build_opener') as opener:
            opener.return_value.open.side_effect = error
            text = lag.collect()
        self.assertIn('kex_lab_autotune_consumer_lag 12000\n', text)
        self.assertIn('kex_lab_autotune_health_up 0\n', text)


class ReleaseImageReferenceTest(unittest.TestCase):
    def test_only_explicit_tags_or_valid_sha256_digests_are_accepted(self):
        for image in ['example/app:1.2.3', 'example/app@sha256:' + 'a' * 64]:
            self.assertTrue(release.explicit_image(image))
        for image in ['example/app', 'example/app:latest', 'example/app@sha256:bad', 'registry:5000/app']:
            self.assertFalse(release.explicit_image(image))


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.object(release, 'ROOT', self.root).start()
        self.git('init', '-q')
        (self.root / 'VERSION').write_text('0.1.0\n')
        (self.root / '.gitignore').write_text('.env\ndist/\n')
        (self.root / '.env').write_text('SECRET=do-not-package\n')
        keys = ['KAFKA_IMAGE', 'EXPLORER_IMAGE', 'KEX_AGENT_IMAGE', 'AUTOTUNE_IMAGE',
                'SPECTRALLM_IMAGE', 'SPECTRALLM_FRONTEND_IMAGE', 'PROMETHEUS_IMAGE', 'GRAFANA_IMAGE', 'LAG_EXPORTER_IMAGE']
        (self.root / 'versions.env').write_text('\n'.join(key + '=example/component:1.0.0' for key in keys) + '\n')
        notes = self.root / 'docs/releases'; notes.mkdir(parents=True)
        (notes / 'v0.1.0.md').write_text('# Release 0.1.0\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root)

    def test_bundle_is_reproducible_bound_to_commit_and_excludes_credentials(self):
        one, two = self.root / 'dist/one', self.root / 'dist/two'
        with redirect_stdout(io.StringIO()):
            bundle = release.prepare(one, 'v0.1.0'); release.prepare(two, 'v0.1.0')
        self.assertEqual(bundle['gitHead'], self.git('rev-parse', 'HEAD').decode().strip())
        self.assertEqual({p.name: p.read_bytes() for p in one.iterdir()}, {p.name: p.read_bytes() for p in two.iterdir()})
        with tarfile.open(one / 'kex-lab-0.1.0.tar.gz') as archive:
            self.assertNotIn('kex-lab-0.1.0/.env', archive.getnames())
            self.assertIn('kex-lab-0.1.0/VERSION', archive.getnames())
        for line in (one / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ')
            self.assertEqual(digest, hashlib.sha256((one / name).read_bytes()).hexdigest())

    def test_dirty_worktree_and_wrong_tag_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'tag does not match'):
            release.prepare(self.root / 'dist', 'v9.0.0')
        (self.root / 'VERSION').write_text('0.2.0\n')
        with self.assertRaisesRegex(ValueError, 'clean Git worktree'):
            release.prepare(self.root / 'dist')

class ObservabilityApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        with patch.dict(sys.modules, {'lab_report': report}):
            cls.observability = load('check_observability', 'check-observability.py')

    def fake_api(self, base, path, auth=None, missing_lag=False, failed_agent=False):
        from urllib.parse import parse_qs, urlsplit
        if path.startswith('/api/dashboards'):
            return {'dashboard': {'uid': 'kex-lab-operations', 'title': 'Kex Lab', 'panels': [{}] * 9}}
        expression = parse_qs(urlsplit(path).query)['query'][0]
        if expression == 'up':
            rows = [{'metric': {'job': job}, 'value': [0, '0' if failed_agent and job == 'kex-agent' else '1']}
                    for job in ['autotune', 'kex-agent', 'kafka-explorer', 'lab-metrics']]
        elif expression == 'kex_lab_autotune_probe_success':
            rows = [{'metric': {}, 'value': [0, '1']}]
        elif expression == 'kex_lab_autotune_consumer_lag':
            rows = [] if missing_lag else [{'metric': {}, 'value': [0, '7']}]
        else:
            rows = [{'metric': {}, 'value': [0, '25']}]
        return {'status': 'success', 'data': {'resultType': 'vector', 'result': rows}}

    def test_dashboard_targets_and_measured_lag_are_verified(self):
        with patch.object(self.observability, 'fetch', side_effect=self.fake_api):
            result = self.observability.verify('http://prometheus', 'http://grafana', 'admin:private')
        self.assertEqual(result['autoTuneConsumerLag'], 7)
        self.assertEqual(result['autoTuneReceivedCount'], 25)
        self.assertNotIn('private', json.dumps(result))

    def test_missing_lag_is_not_a_zero_lag_success(self):
        with patch.object(self.observability, 'fetch', side_effect=lambda *a: self.fake_api(*a, missing_lag=True)):
            with self.assertRaisesRegex(ValueError, 'lag is not measured'):
                self.observability.verify('http://prometheus', 'http://grafana', 'admin:private')

    def test_failed_authenticated_target_is_a_failure(self):
        with patch.object(self.observability, 'fetch', side_effect=lambda *a: self.fake_api(*a, failed_agent=True)):
            with self.assertRaisesRegex(ValueError, 'not scraping'):
                self.observability.verify('http://prometheus', 'http://grafana', 'admin:private')
