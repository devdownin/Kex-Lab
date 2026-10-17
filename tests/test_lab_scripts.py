"""Exercise shell entry points without starting application containers."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class LabScriptsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(REPO / 'scripts', self.root / 'scripts')
        shutil.copy(REPO / 'versions.env', self.root)
        shutil.copy(REPO / '.env.example', self.root / '.env')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        docker = self.bin / 'docker'
        docker.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['CALL_LOG'], 'a') as log:
    log.write(json.dumps({'args': sys.argv[1:], 'messages': os.getenv('KEX_LAB_MESSAGES'), 'topic': os.getenv('KEX_LAB_TOPIC'), 'image': os.getenv('EXPLORER_IMAGE')}) + '\\n')
if 'kafka.tools.GetOffsetShell' in sys.argv:
    print('custom.topic:0:7')
''')
        docker.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(('KEX_', 'EXPLORER_', 'AUTOTUNE_'))}
        self.env.update(PATH=f'{self.bin}:{os.environ["PATH"]}',
                        CALL_LOG=str(self.root / 'calls.jsonl'))

    def run_script(self, name, *args, **settings):
        return subprocess.run(['sh', str(self.root / 'scripts' / name), *args],
                              cwd='/tmp', env={**self.env, **settings},
                              text=True, capture_output=True, timeout=10)

    def calls(self):
        return [json.loads(line) for line in
                (self.root / 'calls.jsonl').read_text().splitlines()]

    def test_scenario_defaults_survive_example_env(self):
        for scenario, expected in [('basic', '500'), ('lag', '10000'),
                                   ('overload', '50000'), ('dlt', '500')]:
            with self.subTest(scenario=scenario):
                result = self.run_script('scenario.sh', scenario)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls()[-1]['messages'], expected)

    def test_caller_settings_override_env_and_manifest(self):
        result = self.run_script('scenario.sh', 'lag', KEX_LAB_MESSAGES='7',
                                 KEX_LAB_TOPIC='custom.topic',
                                 EXPLORER_IMAGE='example/explorer:test')
        self.assertEqual(result.returncode, 0, result.stderr)
        call = self.calls()[-1]
        self.assertEqual(call['messages'], '7')
        self.assertEqual(call['topic'], 'custom.topic')
        self.assertEqual(call['image'], 'example/explorer:test')

    def test_assertion_uses_custom_count_and_topic(self):
        result = self.run_script('scenario-assert.sh', 'lag',
                                 KEX_LAB_MESSAGES='7', KEX_LAB_TOPIC='custom.topic')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('(>= 7)', result.stdout)
        self.assertIn('custom.topic', self.calls()[-1]['args'])

    def test_wait_works_outside_repo_and_propagates_failure(self):
        (self.root / 'scripts' / 'smoke-test.sh').write_text('exit 1\n')
        result = self.run_script('wait-ready.sh', '1', '0')
        self.assertEqual(result.returncode, 1)
        self.assertIn('did not become ready', result.stderr)

    def test_wait_rejects_invalid_arguments(self):
        for args in [('0', '0'), ('bad', '0'), ('1', '-1')]:
            result = self.run_script('wait-ready.sh', *args)
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_quick_demo_stops_when_readiness_fails(self):
        for name in ['doctor.sh', 'hub.sh']:
            (self.root / 'scripts' / name).write_text('exit 0\n')
        (self.root / 'scripts' / 'wait-ready.sh').write_text('exit 1\n')
        result = self.run_script('quick-demo.sh')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('demo is ready', result.stdout)
        self.assertFalse((self.root / 'calls.jsonl').exists())
