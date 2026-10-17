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
        docker.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['CALL_LOG'], 'a') as log:
    log.write(json.dumps({'tool': 'docker', 'args': args, 'project': os.getenv('COMPOSE_PROJECT_NAME'), 'ports': [os.getenv(k) for k in ['KAFKA_PORT', 'EXPLORER_PORT', 'KEX_AGENT_PORT', 'AUTOTUNE_PORT']], 'messages': os.getenv('KEX_LAB_MESSAGES'), 'topic': os.getenv('KEX_LAB_TOPIC'), 'image': os.getenv('EXPLORER_IMAGE')}) + '\\n')
state = Path(os.environ['CALL_LOG'] + '.offset')
count = int(state.read_text()) if state.exists() else 2000
if 'run' in args and 'traffic' in args:
    if os.getenv('FAIL_TRAFFIC'): sys.exit(1)
    if not os.getenv('NO_PRODUCE'):
        count += int(os.environ.get('KEX_LAB_MESSAGES', '500'))
        count += os.environ.get('KEX_LAB_INJECT_INVALID') == 'true'
        state.write_text(str(count))
if 'kafka-get-offsets.sh' in ' '.join(args):
    if os.getenv('FAIL_OFFSETS'): sys.exit(1)
    topic = os.getenv('KEX_LAB_TOPIC', 'demo.app.topic')
    if os.getenv('MULTI_PARTITION'):
        print(topic + ':0:' + str(2000 + max(0, count - 2001)))
        print(topic + ':1:' + str(2000 + int(count > 2000)))
    else:
        print(topic + ':0:' + str(count))
if 'kafka-console-consumer.sh' in ' '.join(args):
    partition = args[args.index('--partition') + 1]
    valid = os.getenv('MISSING_POISON') or (os.getenv('MULTI_PARTITION') and partition == '0')
    print('valid-json' if valid else 'not-json-poison-message')
    sys.stdin.read()  # Interactive docker exec can drain the caller's loop input.
if 'port' in args:
    print('127.0.0.1:18080')
if 'ps' in args and '-q' in args:
    if args[-1] != os.getenv('MISSING_SERVICE'): print(args[-1])
if args and args[0] == 'inspect':
    print('running unhealthy' if args[-1] == os.getenv('UNHEALTHY_SERVICE') else 'running healthy')
""")
        docker.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(('KEX_', 'EXPLORER_', 'AUTOTUNE_', 'COMPOSE_'))}
        curl = self.bin / 'curl'
        curl.write_text("""#!/usr/bin/env python3
import json, os, sys
with open(os.environ['CALL_LOG'], 'a') as log:
    log.write(json.dumps({'tool': 'curl', 'args': sys.argv[1:]}) + '\\n')
if os.getenv('HTTP_FAIL'): sys.exit(22)
print('{"status":"DOWN"}' if os.getenv('HTTP_DOWN') else '{"status":"UP"}')
""")
        curl.chmod(0o755)
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
        self.assertIn('exactly 7 new records', result.stdout)
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

    def test_old_records_cannot_satisfy_scenario_assertion(self):
        result = self.run_script('scenario-assert.sh', 'basic', NO_PRODUCE='1')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Produced 0 new records', result.stderr)

    def test_failed_offset_command_cannot_pass(self):
        result = self.run_script('scenario-assert.sh', 'basic', FAIL_OFFSETS='1')
        self.assertNotEqual(result.returncode, 0)

    def test_dlt_reads_only_new_records(self):
        result = self.run_script('scenario-assert.sh', 'dlt', KEX_LAB_MESSAGES='3')
        self.assertEqual(result.returncode, 0, result.stderr)
        consumer = next(c['args'] for c in self.calls()
                        if 'kafka-console-consumer.sh' in ' '.join(c['args']))
        self.assertEqual(consumer[consumer.index('--offset') + 1], '2000')
        self.assertEqual(consumer[consumer.index('--max-messages') + 1], '4')
        self.assertNotIn('--from-beginning', consumer)

    def test_dlt_requires_a_new_poison_record(self):
        result = self.run_script('scenario-assert.sh', 'dlt', MISSING_POISON='1')
        self.assertEqual(result.returncode, 1)
        self.assertIn('no new poison', result.stderr)

    def test_integration_isolates_every_docker_call_and_cleans_up(self):
        result = self.run_script('integration-smoke.sh', COMPOSE_PROJECT_NAME='kex-lab')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = [c for c in self.calls() if c['tool'] == 'docker']
        projects = {c['project'] for c in calls}
        self.assertEqual(len(projects), 1)
        project = projects.pop()
        self.assertTrue(project.startswith('kex-lab-test-'))
        self.assertNotEqual(project, 'kex-lab')
        self.assertTrue(all(c['ports'] == ['0'] * 4 for c in calls))
        self.assertIn('down', calls[-1]['args'])
        self.assertIn('-v', calls[-1]['args'])

    def test_failed_integration_preserves_error_and_cleans_own_project(self):
        result = self.run_script('integration-smoke.sh', FAIL_TRAFFIC='1')
        self.assertNotEqual(result.returncode, 0)
        calls = [c for c in self.calls() if c['tool'] == 'docker']
        self.assertIn('down', calls[-1]['args'])
        self.assertTrue(all(c['project'].startswith('kex-lab-test-') for c in calls))

    def test_health_core_does_not_probe_optional_services(self):
        result = self.run_script('health.sh', 'core', MISSING_SERVICE='agent')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        self.assertFalse(any(c['args'][-1] == 'agent' for c in calls))
        self.assertFalse(any(':8081' in c['args'][-1] for c in calls))

    def test_health_profile_requires_expected_services(self):
        for profile, service in [('ai', 'agent'), ('reviews', 'agent'),
                                 ('demo', 'autotune'), ('full', 'spectra-api'),
                                 ('observability', 'grafana')]:
            with self.subTest(profile=profile):
                result = self.run_script('health.sh', profile, MISSING_SERVICE=service)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f'DOWN  {service} container', result.stdout)

    def test_health_rejects_unhealthy_and_http_down(self):
        for settings in [{'UNHEALTHY_SERVICE': 'explorer'}, {'HTTP_DOWN': '1'},
                         {'HTTP_FAIL': '1'}]:
            result = self.run_script('health.sh', 'core', **settings)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_health_rejects_unknown_profile(self):
        result = self.run_script('health.sh', 'typo')
        self.assertEqual(result.returncode, 2)

    def test_wait_rejects_unknown_profile_without_retrying(self):
        result = self.run_script('wait-ready.sh', '30', '5', 'typo')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Waiting for', result.stdout)

    def test_dlt_checks_later_partitions_when_docker_reads_stdin(self):
        result = self.run_script('scenario-assert.sh', 'dlt', KEX_LAB_MESSAGES='3',
                                 MULTI_PARTITION='1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        consumers = [c for c in self.calls()
                     if 'kafka-console-consumer.sh' in ' '.join(c['args'])]
        self.assertEqual(len(consumers), 2)

    def test_lightweight_demo_starts_only_core_and_autotune_and_reports_evidence(self):
        result = self.run_script('demo-lite.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = [c for c in self.calls() if c['tool'] == 'docker']
        self.assertTrue(any('up' in c['args'] and 'autotune' in c['args'] for c in calls))
        self.assertFalse(any('spectra' in ' '.join(c['args']) or 'compose.hub.yml' in c['args'] for c in calls))
        data = json.loads((self.root / 'reports/latest.json').read_text())
        self.assertEqual(data['profile'], 'demo')
        self.assertEqual(data['assertions'][0]['status'], 'PASS')

    def test_lightweight_demo_stops_if_no_new_traffic_is_observed(self):
        result = self.run_script('demo-lite.sh', NO_PRODUCE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Lightweight demo ready', result.stdout)
        evidence = [json.loads(path.read_text()) for path in (self.root / 'reports/assertions').glob('*.json')]
        self.assertEqual([entry['status'] for entry in evidence], ['FAIL'])
