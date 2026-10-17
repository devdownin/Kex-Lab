#!/usr/bin/env python3
"""Guide the lightweight demo, with bounded log output and live progress."""
import argparse
from collections import deque
import os
import signal
import subprocess
import tempfile
import time

from lab_report import links, safe_url


COMPOSE = ['docker', 'compose', '--env-file', 'versions.env',
           '-f', 'compose.yml', '-f', 'compose.autotune.yml']


def run_step(number, label, command, verbose=False, env=None):
    started = time.monotonic()
    print(f'[{number}/5] {label}', flush=True)
    with tempfile.TemporaryFile(mode='w+') as log:
        process = subprocess.Popen(command, stdout=None if verbose else log,
                                   stderr=None if verbose else subprocess.STDOUT,
                                   env=env, start_new_session=True)
        try:
            while True:
                try:
                    status = process.wait(timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    print(f'      Still working: {label} ({time.monotonic() - started:.0f}s elapsed)', flush=True)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        if status:
            if not verbose:
                log.seek(0)
                # Keep only the last 40 lines in memory, even for a large image pull.
                print(''.join(deque(log, maxlen=40)), end='', flush=True)
            print(f'FAIL [{number}/5] {label} (exit {status}, {time.monotonic() - started:.0f}s).', flush=True)
            print('Next: make doctor; make health PROFILE=demo; rerun make demo-lite ARGS=--verbose.', flush=True)
            return status if status > 0 else 128 - status
    print(f'      PASS ({time.monotonic() - started:.0f}s)', flush=True)
    return 0


def discover_urls():
    for service, port, variable in [('explorer', '8080', 'KEX_LAB_EXPLORER_URL'),
                                    ('agent', '8081', 'KEX_LAB_AGENT_URL'),
                                    ('autotune', '8080', 'KEX_LAB_AUTOTUNE_URL')]:
        if os.environ.get(variable):
            continue
        published = subprocess.check_output(COMPOSE + ['port', service, port], text=True, timeout=15).splitlines()[0]
        host, actual_port = published.rsplit(':', 1)
        if host in ('0.0.0.0', '[::]', '::'):
            host = '127.0.0.1'
        os.environ[variable] = f'http://{host}:{actual_port}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', action='store_true', help='Stream detailed command logs.')
    args = parser.parse_args()
    started = time.monotonic()
    print('Kex Lab — guided lightweight demo', flush=True)
    print('Kafka → AutoTune → Explorer → Agent. No Spectra or model download.', flush=True)
    print('Expected: healthy services and an exact increase in Kafka records; AI reasoning is a separate check.', flush=True)
    commands = [
        ('Check prerequisites', ['sh', 'scripts/doctor.sh'] + (['--verbose'] if args.verbose else [])),
        ('Start Kafka, Explorer, Agent and AutoTune', COMPOSE + ['up', '-d', 'kafka', 'explorer', 'agent', 'autotune']),
        ('Wait for the demo profile', ['sh', 'scripts/wait-ready.sh', '30', '5', 'demo'] + (['--verbose'] if args.verbose else [])),
        ('Inject traffic and verify exact Kafka offsets', ['sh', 'scripts/scenario-assert.sh', 'basic']),
        ('Write the runtime report', ['sh', 'scripts/report.sh', 'demo']),
    ]
    for number, (label, command) in enumerate(commands, 1):
        # Start without seed traffic; only the explicit assertion generates records.
        env = {**os.environ, 'KEX_LAB_MESSAGES': '0', 'KEX_LAB_INJECT_INVALID': 'false'} if number == 2 else None
        if number == 3:
            try:
                discover_urls()
            except (OSError, subprocess.SubprocessError, ValueError, IndexError):
                print('FAIL: published demo ports could not be discovered. Run make status and make demo-lite ARGS=--verbose.', flush=True)
                return 1
        status = run_step(number, label, command, args.verbose or number == 1, env)
        if status:
            return status
    print(f'Lightweight demo ready ({time.monotonic() - started:.0f}s elapsed).', flush=True)
    print(f'PASS: exactly {os.environ.get("KEX_LAB_MESSAGES", "500")} new records verified in {os.environ.get("KEX_LAB_TOPIC", "demo.app.topic")}.', flush=True)
    for name, url in links('demo').items():
        print(f'  {name}: {url}', flush=True)
    print(f'  AutoTune dashboard: {safe_url(os.environ["KEX_LAB_AUTOTUNE_URL"] + "/dashboard")}', flush=True)
    print('Evidence: reports/latest.md and reports/latest.json', flush=True)
    print('Try: open Explorer and inspect the topic; open AutoTune to inspect consumption.', flush=True)
    print('Grafana is optional and has not been started by this command.', flush=True)
    grafana = os.environ.get('KEX_LAB_GRAFANA_URL', f'http://127.0.0.1:{os.environ.get("GRAFANA_PORT", "3000")}')
    print(f'  Next: make observability-up, then open {safe_url(grafana + "/d/kex-lab-operations")}', flush=True)
    print('Agent reasoning requires a configured model provider/API key.', flush=True)
    print('Stop with make demo-lite-down (keeps Kafka data).', flush=True)
    return 0


if __name__ == '__main__':
    def terminate(_signum, _frame):
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, terminate)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nInterrupted. Services and Kafka data are preserved; stop with make demo-lite-down.', flush=True)
        raise SystemExit(130)
