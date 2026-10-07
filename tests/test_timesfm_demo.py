"""Contract checks at the real HTTP and persisted-journal boundaries; no model execution."""
import copy
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('timesfm_demo', Path(__file__).resolve().parents[1] / 'scripts/timesfm-demo.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
SERIES_ID = 'a' * 64


def envelope(data):
    return {'data': data, 'coverage': {'complete': True}, 'truncated': False, 'unavailable': None}


def detail():
    return {'forecast': envelope({'measured': True, 'value': {'state': 'READY', 'strategy': 'TIMESFM',
        'visibility': 'SHADOW', 'generatedAt': int(time.time() * 1000), 'forecast': {
            'seriesId': SERIES_ID, 'modelId': demo.MODEL_ID, 'modelRevision': demo.MODEL_REVISION,
            'points': [{'at': time.time() * 1000 + 60000, 'central': 12, 'q10': 10, 'q50': 12, 'q90': 14}]}}}),
        'quality': envelope({'measured': False, 'reason': 'Insufficient realised points'})}


class TimesfmContractTest(unittest.TestCase):
    def test_journal_rejects_limited_scope_or_wrong_semantics_without_enrollment(self):
        observation = {'seriesId': SERIES_ID, 'definitionVersion': 'b' * 64, 'metricId': demo.METRIC_ID,
                       'component': 'value', 'clusterId': 'kex-lab-timesfm', 'unit': 'milliseconds',
                       'semanticKind': 'GAUGE', 'qualityState': 'OBSERVED'}
        config = demo.pilot_config(observation, 'demo.app.topic')
        self.assertEqual(config['explorer']['forecasting']['pilot']['series'][0]['groups'], [demo.GROUP_ID])
        for key, value in [('qualityState', 'LIMITED_SCOPE'), ('unit', 'UNKNOWN'), ('metricId', 'other'),
                           ('definitionVersion', 'invented'), ('seriesId', 'invented')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                demo.pilot_config({**observation, key: value}, 'demo.app.topic')

    def test_rejects_fallback_expired_incomplete_unmeasured_and_different_model_results(self):
        valid = detail()
        self.assertTrue(demo.ready_shadow(valid, SERIES_ID, time.time() * 1000))
        variants = []
        for key, value in [('visibility', 'ACTIVE'), ('state', 'DEGRADED'), ('strategy', 'LAST_VALUE')]:
            read = copy.deepcopy(valid)
            read['forecast']['data']['value'][key] = value
            variants.append(read)
        expired = copy.deepcopy(valid)
        expired['forecast']['data']['value']['forecast']['points'][0]['at'] = 0
        variants.append(expired)
        incomplete = copy.deepcopy(valid)
        incomplete['forecast']['coverage']['complete'] = False
        variants.append(incomplete)
        unmeasured = {'forecast': envelope({'measured': False})}
        variants.append(unmeasured)
        wrong_model = copy.deepcopy(valid)
        wrong_model['forecast']['data']['value']['forecast']['modelRevision'] = 'unapproved'
        variants.append(wrong_model)
        for read in variants:
            self.assertFalse(demo.ready_shadow(read, SERIES_ID, time.time() * 1000))

    def test_http_scenario_persists_exact_association_and_does_not_activate_or_invoke_llm(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                calls.append(('GET', self.path, None))
                if self.path.endswith('/metrics'):
                    body = envelope([{'seriesId': SERIES_ID, 'environment': 'lab',
                                      'sources': {'complete': True, 'topics': ['demo.app.topic']}}])
                elif self.path.endswith('/definitions'):
                    body = []
                elif '/series/' in self.path:
                    body = detail()
                else:
                    body = {'processId': demo.PROCESS_ID, 'forecasts': [{'association': {'seriesId': SERIES_ID, 'environment': 'lab'}}]}
                self.send(body)
            def do_POST(self):
                data = self.body()
                calls.append(('POST', self.path, data))
                self.send(data)
            def do_PUT(self):
                data = self.body()
                calls.append(('PUT', self.path, data))
                self.send({'associations': data['associations']})
            def body(self):
                return json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            def send(self, body):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary, patch.object(demo, 'ROOT', Path(temporary)):
                (Path(temporary) / '.timesfm').mkdir()
                self.assertTrue(demo.assert_and_associate(f'http://127.0.0.1:{server.server_port}', 'test-token', SERIES_ID))
                report = json.loads((Path(temporary) / '.timesfm/result.json').read_text())
                self.assertEqual(report['visibility'], 'SHADOW')
                self.assertFalse(report['quality']['data']['measured'])
            writes = [call for call in calls if call[0] == 'PUT']
            self.assertEqual(writes, [('PUT', f'/api/agent/forecasts/processes/{demo.PROCESS_ID}/associations',
                                       {'associations': [{'seriesId': SERIES_ID, 'environment': 'lab'}]})])
            self.assertFalse(any('/activation' in path or '/chat' in path for _, path, _ in calls))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
