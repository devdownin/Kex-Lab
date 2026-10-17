#!/usr/bin/env python3
"""Render all Lab profiles without starting services or reading the local .env."""
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main():
    env = {**os.environ, 'EXPLORER_MCP_AUTH_TOKEN': 'validation-mcp',
           'KEX_AGENT_API_KEY': 'validation-agent',
           'KEX_TIMESFM_DB_PASSWORD': 'validation-db', 'TIMESFM_TOKEN': 'validation-model'}
    base = ['docker', 'compose', '--env-file', 'versions.env',
            '--env-file', '.env.example', '-f', 'compose.yml']
    profiles = [[], ['compose.autotune.yml'],
                ['compose.autotune.yml', 'compose.observability.yml'],
                ['compose.autotune.yml', 'compose.hub.yml'],
                ['compose.operational-reviews.yml'], ['compose.timesfm.yml']]
    for files in profiles:
        command = base + [arg for file in files for arg in ('-f', file)]
        config = json.loads(subprocess.check_output(
            command + ['config', '--format', 'json'], cwd=ROOT, env=env))
        if files == ['compose.operational-reviews.yml']:
            policy = json.loads(config['services']['explorer']['environment']['SPRING_APPLICATION_JSON'])
            route = policy['explorer']['mcp']['dlq-routes'][0]
            assert route['queue-topic'] == config['services']['kafka-init']['environment']['KEX_LAB_DLT_TOPIC']
        print('PASS Compose:', ', '.join(['compose.yml'] + files))


if __name__ == '__main__':
    main()
