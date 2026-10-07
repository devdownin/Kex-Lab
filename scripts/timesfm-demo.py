#!/usr/bin/env python3
"""Real Kafka -> observation journal -> SHADOW forecast -> persisted Kex association.
No imported/synthetic history, activation request, or automatic LLM invocation.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
METRIC_ID = 'kex-lab-timesfm-lag'
GROUP_ID = 'kex-lab-timesfm-worker'
MODEL_ID = 'google/timesfm-2.5-200m-pytorch'
MODEL_REVISION = '1d952420fba87f3c6dee4f240de0f1a0fbc790e3'
PROCESS_ID = 'kex-lab-timesfm-orders'
COMPOSE = ['docker', 'compose', '--env-file', str(ROOT / '.env'), '--env-file', str(ROOT / '.env.timesfm'),
           '-p', 'kex-lab-timesfm', '-f', str(ROOT / 'compose.yml'), '-f', str(ROOT / 'compose.timesfm.yml')]


def request(base, path, method='GET', body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        # Do not dump transport headers, credentials, or unbounded server payloads.
        raise RuntimeError(f'{method} {path}: HTTP {exc.code}') from None


def metric_config(topic):
    if not re.fullmatch(r'[a-zA-Z0-9._-]+', topic):
        raise ValueError('Use a valid Kafka topic name')
    return {'id': METRIC_ID, 'name': 'Lab retard temporel commandes', 'type': 'GAUGE',
            'description': 'Retard temporel mesuré du groupe dédié de laboratoire.',
            'templateType': 'CONSUMER_TIME_LAG', 'executionMode': 'TEMPLATE_BOUNDED_SCAN',
            'templateParams': {'topic': topic, 'group': GROUP_ID, 'aggregation': 'MAX'}}



def validate_observation(observation):
    if (not re.fullmatch(r'[a-f0-9]{64}', observation.get('seriesId', ''))
            or not re.fullmatch(r'[a-f0-9]{64}', observation.get('definitionVersion', ''))
            or observation.get('metricId') != METRIC_ID or observation.get('component') != 'value'
            or observation.get('clusterId') != 'kex-lab-timesfm' or observation.get('unit') != 'milliseconds'
            or observation.get('semanticKind') != 'GAUGE' or observation.get('qualityState') != 'OBSERVED'):
        raise ValueError('Observation provenance/semantics are not admissible for this Lab series')
    return observation


def pilot_config(observation, topic):
    observation = validate_observation(observation)
    series = {'series-id': observation['seriesId'], 'metric-id': METRIC_ID, 'environment': 'lab',
              'definition-version': observation['definitionVersion'], 'unit': 'milliseconds',
              'topics': [topic], 'groups': [GROUP_ID],
              'profile': {'step-millis': 1000, 'context-points': 512, 'transformation': 'GAUGE_LAST'},
              'horizon': 60, 'season-length': 60, 'minimum-coverage': 0.8, 'minimum-evaluated-points': 60}
    return {'explorer': {'forecasting': {'pilot': {'enabled': True, 'interval': '1m', 'retention': '1d',
                                                 'max-series': 1, 'series': [series]}}}}


def complete(read):
    return (isinstance(read, dict) and not read.get('unavailable') and not read.get('truncated')
            and read.get('coverage', {}).get('complete') is True)


def ready_shadow(detail, series_id, instant):
    read = detail.get('forecast', {})
    if not complete(read) or read.get('data', {}).get('measured') is not True:
        return False
    value = read['data'].get('value', {})
    forecast = value.get('forecast') or {}
    points = forecast.get('points') or []
    return (value.get('state') == 'READY' and value.get('strategy') == 'TIMESFM'
            and value.get('visibility') == 'SHADOW' and forecast.get('seriesId') == series_id
            and forecast.get('modelId') == MODEL_ID and forecast.get('modelRevision') == MODEL_REVISION
            and bool(points) and isinstance(points[-1].get('at'), (int, float)) and points[-1]['at'] > instant
            and all(isinstance(p.get(k), (int, float)) and math.isfinite(p[k]) for p in points for k in ['central', 'q10', 'q50', 'q90']))


def assert_and_associate(agent, token, expected_id):
    catalog = request(agent, '/api/agent/forecasts/metrics', token=token)
    if not complete(catalog):
        return False
    metric = next((m for m in catalog['data'] if m.get('seriesId') == expected_id and m.get('environment') == 'lab'), None)
    if not metric or metric.get('sources', {}).get('complete') is not True:
        return False
    detail = request(agent, f'/api/agent/forecasts/series/{expected_id}', token=token)
    if not ready_shadow(detail, expected_id, time.time() * 1000):
        return False
    definitions = request(agent, '/api/agent/supervision/processes/definitions', token=token)
    existing = next((p for p in definitions if p['id'] == PROCESS_ID), None)
    if existing and existing.get('name') != 'Commandes — démonstration TimesFM':
        raise ValueError('Existing process identity belongs to another scenario; do not replace its associations')
    if not existing:
        request(agent, '/api/agent/supervision/processes', 'POST',
                {'id': PROCESS_ID, 'name': 'Commandes — démonstration TimesFM',
                 'description': 'Processus de laboratoire ; aucune activation TimesFM.',
                 'hint': 'topics [' + ', '.join(metric['sources']['topics']) + '], consumer group ' + GROUP_ID}, token)
    association = {'seriesId': expected_id, 'environment': 'lab'}
    saved = request(agent, f'/api/agent/forecasts/processes/{PROCESS_ID}/associations', 'PUT',
                    {'associations': [association]}, token)
    if saved.get('associations') != [association]:
        raise RuntimeError('The exact process association was not persisted')
    summary = request(agent, f'/api/agent/forecasts/processes/{PROCESS_ID}', token=token)
    if summary.get('unavailable') or not summary.get('forecasts'):
        raise RuntimeError('Process forecast summary is unavailable')
    record = detail['forecast']['data']['value']
    report = {'seriesId': expected_id, 'environment': 'lab', 'processId': PROCESS_ID,
              'state': record['state'], 'visibility': record['visibility'], 'strategy': record['strategy'],
              'generatedAt': record['generatedAt'], 'lastForecastAt': record['forecast']['points'][-1]['at'],
              'modelId': record['forecast']['modelId'], 'modelRevision': record['forecast']['modelRevision'],
              'quality': detail.get('quality'), 'verifiedAt': int(time.time() * 1000)}
    (ROOT / '.timesfm' / 'result.json').write_text(json.dumps(report, indent=2))
    print('PASS: real persisted SHADOW TimesFM result, quantiles and exact process association. See .timesfm/result.json.')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['enroll', 'run', 'check'])
    parser.add_argument('--seconds', type=int, default=900)
    args = parser.parse_args()
    if not 540 <= args.seconds <= 3600:
        parser.error('--seconds must be between 540 and 3600 (512 real one-second buckets)')
    explorer = os.environ.get('EXPLORER_URL', 'http://127.0.0.1:' + os.environ.get('EXPLORER_PORT', '8080'))
    agent = os.environ.get('KEX_AGENT_URL', 'http://127.0.0.1:' + os.environ.get('KEX_AGENT_PORT', '8081'))
    topic = os.environ.get('KEX_LAB_TOPIC', 'demo.app.topic')
    token = os.environ.get('KEX_AGENT_API_KEY')
    if not token:
        raise ValueError('Export your Lab .env before invoking this script')
    if args.action == 'enroll':
        # Initialize commits on every partition of an inactive, dedicated Lab group. This
        # operates solely on the isolated scenario broker; it is not a production remediation.
        subprocess.run(COMPOSE + ['exec', '-T', 'kafka', '/opt/kafka/bin/kafka-consumer-groups.sh',
                                  '--bootstrap-server', 'kafka:29092', '--group', GROUP_ID, '--topic', topic,
                                  '--reset-offsets', '--to-earliest', '--execute'], check=True)
        proposed = metric_config(topic)
        existing = next((m for m in request(explorer, '/api/metrics') if m['id'] == METRIC_ID), None)
        if existing and any(existing.get(k) != proposed.get(k) for k in ['type', 'templateType', 'executionMode', 'templateParams']):
            raise ValueError('An existing Lab metric has different semantics; do not overwrite it')
        if not existing:
            request(explorer, '/api/metrics', 'POST', proposed)
        for _ in range(10):
            request(explorer, f'/api/metrics/{METRIC_ID}/refresh', 'POST')
            time.sleep(1)
        sql = "SELECT payload FROM kex_metric_observation_v1 WHERE payload::jsonb->>'metricId'='kex-lab-timesfm-lag' AND payload::jsonb->>'component'='value' ORDER BY observed_at DESC LIMIT 1"
        raw = subprocess.check_output(COMPOSE + ['exec', '-T', 'history-db', 'psql', '-U', 'kex_history', '-d', 'kex_history', '-At', '-c', sql], text=True)
        observation = validate_observation(json.loads(raw))
        (ROOT / '.timesfm' / 'pilot.yml').write_text(json.dumps(pilot_config(observation, topic), indent=2))
        (ROOT / '.timesfm' / 'series.json').write_text(json.dumps({'seriesId': observation['seriesId'], 'definitionVersion': observation['definitionVersion']}))
        print('Enrolled observed identity in the local pilot configuration. Run scripts/timesfm.sh reload, then run this collector.')
        return
    series_id = json.loads((ROOT / '.timesfm' / 'series.json').read_text())['seriesId']
    if not re.fullmatch(r'[a-f0-9]{64}', series_id):
        raise ValueError('Invalid enrolled series identity')
    if args.action == 'check':
        if not assert_and_associate(agent, token, series_id):
            raise RuntimeError('No current READY/TIMESFM/SHADOW result with complete coverage. Keep collecting; inspect warming-up/fallback reasons.')
        return
    producer = subprocess.Popen(COMPOSE + ['exec', '-T', 'kafka', '/opt/kafka/bin/kafka-console-producer.sh',
                               '--bootstrap-server', 'kafka:29092', '--topic', topic], stdin=subprocess.PIPE, text=True)
    deadline = time.monotonic() + args.seconds
    next_check = time.monotonic() + 540
    sequence = 0
    try:
        while time.monotonic() < deadline:
            if producer.poll() is not None:
                raise RuntimeError('Kafka producer stopped unexpectedly')
            producer.stdin.write(json.dumps({'eventType': 'TIMESFM_LAB', 'sequence': sequence}) + '\n')
            producer.stdin.flush()
            request(explorer, f'/api/metrics/{METRIC_ID}/refresh', 'POST')
            if time.monotonic() >= next_check:
                print('Checking real forecast readiness and quality...', flush=True)
                if assert_and_associate(agent, token, series_id):
                    return
                next_check = time.monotonic() + 15
            sequence += 1
            time.sleep(0.5)
        raise RuntimeError('Deadline reached without an admissible forecast. No observations or quality were fabricated; extend collection and inspect diagnostics.')
    finally:
        producer.stdin.close()
        try:
            producer.wait(timeout=15)
        except subprocess.TimeoutExpired:
            producer.terminate()
            producer.wait(timeout=10)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, urllib.error.URLError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
