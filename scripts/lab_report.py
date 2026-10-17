#!/usr/bin/env python3
"""Record non-secret scenario evidence and report the observed Lab runtime."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, urlunsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
OVERLAYS = {
    'core': [], 'ai': [], 'reviews': ['compose.operational-reviews.yml'],
    'demo': ['compose.autotune.yml'],
    'full': ['compose.autotune.yml', 'compose.hub.yml'],
    'observability': ['compose.autotune.yml', 'compose.observability.yml'],
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def command(args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=180)


def head():
    result = command(['git', 'rev-parse', 'HEAD'])
    return result.stdout.strip() if result.returncode == 0 else None


def dirty():
    result = command(['git', 'status', '--porcelain'])
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def output_dir():
    return Path(os.environ.get('KEX_LAB_REPORT_DIR', str(ROOT / 'reports')))


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as handle:
            handle.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_offsets(path):
    if not path.is_file():
        return {}
    rows = {}
    for line in path.read_text().splitlines():
        topic, partition, offset = line.split(':')
        rows[partition] = int(offset)
    return rows


def record(args):
    try:
        before = read_offsets(args.work / 'before')
        after = read_offsets(args.work / 'after')
    except (ValueError, OSError):
        before, after = {}, {}
    measured = bool(before) and before.keys() == after.keys()
    observed = sum(after.values()) - sum(before.values()) if measured else None
    poison = False
    sample = args.work / 'sample'
    if sample.is_file():
        poison = 'not-json-poison-message' in sample.read_text().splitlines()
    passed = (args.exit_code == 0 and observed == args.expected
              and all(after[p] >= before[p] for p in before)
              and (args.scenario != 'dlt' or poison))
    evidence = {
        'schemaVersion': 1, 'recordedAt': now(), 'gitHead': head(), 'worktreeDirty': dirty(),
        'project': os.environ.get('COMPOSE_PROJECT_NAME', 'kex-lab'),
        'topic': args.topic, 'scenario': args.scenario,
        'status': 'PASS' if passed else 'FAIL', 'exitCode': args.exit_code,
        'expectedRecords': args.expected, 'observedRecords': observed,
        'before': before, 'after': after,
        'newPoisonRecordVerified': poison if args.scenario == 'dlt' else None,
    }
    path = output_dir() / 'assertions' / (uuid.uuid4().hex + '.json')
    write(path, json.dumps(evidence, indent=2) + '\n')
    print(f'Assertion evidence: {path}')
    return 0


def parse_ps(text):
    text = text.strip()
    if not text:
        return []
    if text.startswith('['):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def latest_assertions(directory, project, topic):
    latest = {}
    for path in sorted((directory / 'assertions').glob('*.json')):
        try:
            entry = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if (not isinstance(entry, dict) or not isinstance(entry.get('scenario'), str)
                or entry.get('schemaVersion') != 1 or entry.get('project') != project or entry.get('topic') != topic):
            continue
        scenario = entry['scenario']
        if entry.get('recordedAt', '') > latest.get(scenario, {}).get('recordedAt', ''):
            latest[scenario] = entry
    return [latest[key] for key in sorted(latest)]


def safe_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        return None
    hostname = parsed.hostname
    if ':' in hostname:
        hostname = '[' + hostname + ']'
    netloc = hostname + (f':{parsed.port}' if parsed.port else '')
    return urlunsplit((parsed.scheme, netloc, parsed.path, '', ''))


def links(profile):
    entries = [('Explorer', os.environ.get('KEX_LAB_EXPLORER_URL', f'http://127.0.0.1:{os.environ.get("EXPLORER_PORT", "8080")}'))]
    if profile != 'core':
        entries.append(('Agent', os.environ.get('KEX_LAB_AGENT_URL', f'http://127.0.0.1:{os.environ.get("KEX_AGENT_PORT", "8081")}')))
    if profile in {'demo', 'full', 'observability'}:
        entries.append(('AutoTune health', os.environ.get('KEX_LAB_AUTOTUNE_URL', f'http://127.0.0.1:{os.environ.get("AUTOTUNE_PORT", "8082")}') + '/actuator/health'))
    if profile == 'observability':
        entries.extend([('Prometheus', os.environ.get('KEX_LAB_PROMETHEUS_URL', f'http://127.0.0.1:{os.environ.get("PROMETHEUS_PORT", "9090")}')),
                        ('Grafana dashboard', os.environ.get('KEX_LAB_GRAFANA_URL', f'http://127.0.0.1:{os.environ.get("GRAFANA_PORT", "3000")}') + '/d/kex-lab-operations')])
    if profile == 'full':
        entries.append(('Spectra', f'http://127.0.0.1:{os.environ.get("SPECTRA_FRONTEND_PORT", "8084")}'))
    return {name: safe_url(url) for name, url in entries if safe_url(url)}


def markdown(data):
    lines = ['# Kex Lab evaluation report', '', f'- Generated: {data["generatedAt"]}',
             f'- Lab version: {data["labVersion"]}', f'- Git head: {data["gitHead"] or "unavailable"}',
             f'- Worktree modified: {data["worktreeDirty"]}',
             f'- Project: {data["project"]}', f'- Profile: {data["profile"]}',
             f'- Current health: {data["health"]["status"]}', '', '## Interfaces', '']
    lines += [f'- [{name}]({url})' for name, url in data['interfaces'].items()]
    lines += ['', '## Observed containers and images', '',
              '| Service | State | Container image reference | Actual image ID | Registry digests |',
              '|---|---|---|---|---|']
    for item in data['containers']:
        lines.append(f'| {item["service"]} | {item["state"]} | `{item.get("configuredImage", "unavailable")}` | `{item.get("imageId", "unavailable")}` | {", ".join(item.get("repoDigests", [])) or "unavailable"} |')
    if not data['containers']:
        lines.append('| No observed containers | UNMEASURED | unavailable | unavailable | unavailable |')
    lines += ['', '## Latest recorded assertions for this project and topic', '',
              'Recorded assertions are historical evidence; generating this report does not rerun them.', '']
    for item in data['assertions']:
        lines.append(f'- **{item["scenario"]}: {item["status"]}** — expected {item["expectedRecords"]}, observed {item["observedRecords"]}; {item["recordedAt"]}; git `{item.get("gitHead") or "unavailable"}`; source worktree modified: {item.get("worktreeDirty")}')
    if not data['assertions']:
        lines.append('UNMEASURED — no matching scenario assertions have been recorded.')
    lines += ['', '## Current health probes', '', '```text', data['health']['output'].strip(), '```', '']
    if data['collectionErrors']:
        lines += ['## Collection errors', ''] + ['- ' + item for item in data['collectionErrors']] + ['']
    return '\n'.join(lines)


def report(args):
    compose = ['docker', 'compose', '--env-file', 'versions.env', '-f', 'compose.yml']
    for overlay in OVERLAYS[args.profile]:
        compose += ['-f', overlay]
    project = os.environ.get('COMPOSE_PROJECT_NAME', 'kex-lab')
    errors = []
    containers = []
    try:
        result = command(compose + ['ps', '-a', '--format', 'json'])
        if result.returncode != 0:
            errors.append('Unable to list Compose containers.')
        else:
            for item in parse_ps(result.stdout):
                entry = {'service': item['Service'], 'state': item['State'], 'containerId': item['ID']}
                template = '{"imageId":{{json .Image}},"configuredImage":{{json .Config.Image}},"startedAt":{{json .State.StartedAt}}}'
                inspection = command(['docker', 'inspect', '--format', template, item['ID']])
                if inspection.returncode != 0:
                    errors.append('Unable to inspect container for ' + item['Service'])
                else:
                    entry.update(json.loads(inspection.stdout))
                    digests = command(['docker', 'image', 'inspect', '--format', '{{json .RepoDigests}}', entry['imageId']])
                    if digests.returncode == 0:
                        entry['repoDigests'] = json.loads(digests.stdout) or []
                    else:
                        errors.append('Unable to inspect registry digests for ' + item['Service'])
                containers.append(entry)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        errors.append('Runtime collection failed or returned invalid data.')
    try:
        health = command(['sh', 'scripts/health.sh', args.profile])
        health_status = 'PASS' if health.returncode == 0 else 'FAIL'
        health_output = health.stdout
    except (OSError, subprocess.TimeoutExpired):
        health_status, health_output = 'FAIL', 'Health command could not complete.'
    version = ROOT / 'VERSION'
    directory = output_dir()
    assertions = latest_assertions(directory, project, os.environ.get('KEX_LAB_TOPIC', 'demo.app.topic'))
    data = {'schemaVersion': 1, 'generatedAt': now(), 'gitHead': head(), 'worktreeDirty': dirty(),
            'labVersion': version.read_text().strip() if version.is_file() else 'unreleased',
            'project': project, 'profile': args.profile, 'interfaces': links(args.profile),
            'containers': containers, 'assertions': assertions, 'collectionErrors': errors,
            'health': {'status': health_status, 'output': health_output}}
    write(directory / 'latest.json', json.dumps(data, indent=2) + '\n')
    write(directory / 'latest.md', markdown(data))
    print(f'Report written to {directory / "latest.md"} and {directory / "latest.json"}')
    return int(health_status != 'PASS' or bool(errors) or any(item['status'] != 'PASS' for item in assertions))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    capture = sub.add_parser('record')
    capture.add_argument('--scenario', required=True)
    capture.add_argument('--topic', required=True)
    capture.add_argument('--expected', type=int, required=True)
    capture.add_argument('--exit-code', type=int, required=True)
    capture.add_argument('--work', type=Path, required=True)
    capture.set_defaults(func=record)
    render = sub.add_parser('report')
    render.add_argument('--profile', choices=OVERLAYS, default='ai')
    render.set_defaults(func=report)
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
