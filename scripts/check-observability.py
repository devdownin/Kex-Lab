#!/usr/bin/env python3
"""Verify the provisioned dashboard and real Prometheus measurements."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

from lab_report import output_dir, write


def fetch(base, path, auth=None):
    request = Request(base.rstrip('/') + path)
    if auth:
        request.add_header('Authorization', 'Basic ' + base64.b64encode(auth.encode()).decode())
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def values(payload):
    if payload.get('status') != 'success' or payload.get('data', {}).get('resultType') != 'vector':
        raise ValueError('Prometheus did not return a successful vector query.')
    return payload['data']['result']


def verify(prometheus, grafana, auth):
    dashboard = fetch(grafana, '/api/dashboards/uid/kex-lab-operations', auth)['dashboard']
    if dashboard['uid'] != 'kex-lab-operations' or len(dashboard.get('panels', [])) < 8:
        raise ValueError('Grafana dashboard was not provisioned as expected.')
    def query(expression):
        return values(fetch(prometheus, '/api/v1/query?' + urlencode({'query': expression})))
    jobs = {entry['metric']['job']: float(entry['value'][1]) for entry in query('up')}
    expected = {'autotune', 'kex-agent', 'kafka-explorer', 'lab-metrics'}
    if any(jobs.get(job) != 1 for job in expected):
        raise ValueError('Some expected Prometheus targets are not scraping successfully.')
    probe = query('kex_lab_autotune_probe_success')
    lag = query('kex_lab_autotune_consumer_lag')
    traffic = query('app_kafka_events_received_count_total{job="autotune"}')
    if not probe or float(probe[0]['value'][1]) != 1 or not lag:
        raise ValueError('AutoTune lag is not measured.')
    if not traffic or sum(float(entry['value'][1]) for entry in traffic) <= 0:
        raise ValueError('AutoTune traffic counter has not observed the scenario.')
    return {'schemaVersion': 1, 'status': 'PASS', 'generatedAt': datetime.now(timezone.utc).isoformat(),
            'project': os.environ.get('COMPOSE_PROJECT_NAME', 'kex-lab'),
            'dashboardUid': dashboard['uid'], 'dashboardTitle': dashboard['title'],
            'panelCount': len(dashboard['panels']), 'scrapeAvailability': jobs,
            'autoTuneConsumerLag': float(lag[0]['value'][1]),
            'autoTuneReceivedCount': sum(float(entry['value'][1]) for entry in traffic)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=180)
    args = parser.parse_args()
    prometheus = os.environ.get('KEX_LAB_PROMETHEUS_URL', f'http://127.0.0.1:{os.environ.get("PROMETHEUS_PORT", "9090")}')
    grafana = os.environ.get('KEX_LAB_GRAFANA_URL', f'http://127.0.0.1:{os.environ.get("GRAFANA_PORT", "3000")}')
    auth = 'admin:' + os.environ.get('GRAFANA_ADMIN_PASSWORD', 'kex-lab')
    deadline = time.monotonic() + args.timeout
    while True:
        try:
            result = verify(prometheus, grafana, auth)
            write(output_dir() / 'observability.json', json.dumps(result, indent=2) + '\n')
            print('PASS: dashboard provisioned, four targets scraping, measured lag and traffic verified.')
            return 0
        except (OSError, URLError, ValueError, KeyError) as error:
            if time.monotonic() >= deadline:
                write(output_dir() / 'observability.json', json.dumps({'status': 'FAIL', 'error': str(error)}) + '\n')
                parser.exit(1, f'Observability verification failed: {error}\n')
            time.sleep(5)


if __name__ == '__main__':
    raise SystemExit(main())
