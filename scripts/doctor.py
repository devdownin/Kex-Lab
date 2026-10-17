#!/usr/bin/env python3
"""Read-only workstation preflight for the lightweight Lab profile."""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess


class Doctor:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.errors = 0
        self.warnings = 0

    def result(self, level, message, action=''):
        print(f'{level:5} {message}', flush=True)
        if action:
            print(f'      Next: {action}', flush=True)
        self.errors += level == 'ERROR'
        self.warnings += level == 'WARN'

    def command(self, args):
        try:
            result = subprocess.run(args, text=True, capture_output=True, timeout=15)
            # Configuration diagnostics can contain private values: never dump stderr.
            if self.verbose:
                print(f'      {args[0]} {args[1]}: exit {result.returncode}', flush=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None

    def resources(self, info):
        try:
            cpus, memory = map(int, info.split())
        except (ValueError, AttributeError):
            self.result('WARN', 'Docker CPU/RAM allocation could not be measured.',
                        'Inspect docker info; allow about 4 CPUs and 8 GiB RAM for demo-lite.')
            return
        for label, actual, minimum, unit in [('CPU', cpus, 4, 'CPUs'),
                                              ('RAM', memory / 1024**3, 8, 'GiB')]:
            self.result('OK' if actual >= minimum else 'WARN',
                        f'Docker {label}: {actual:g} {unit} (recommended: {minimum}).',
                        '' if actual >= minimum else 'Increase Docker resources or expect slower startup.')

    def port(self, variable, default):
        value = os.environ.get(variable, default)
        try:
            port = int(value)
            if not 0 <= port <= 65535:
                raise ValueError
        except ValueError:
            self.result('ERROR', f'{variable} must be between 0 and 65535.',
                        f'Edit {variable} in .env, then rerun make doctor.')
            return
        if port == 0:
            self.result('OK', f'{variable}: Docker will choose an ephemeral port.')
            return
        address = os.environ.get('BIND_ADDR', '127.0.0.1')
        try:
            family = socket.AF_INET6 if ':' in address else socket.AF_INET
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.bind((address, port))
            self.result('OK', f'{variable}: {address}:{port} is available.')
        except OSError:
            self.result('WARN', f'{variable}: {address}:{port} could not be reserved.',
                        f'Run make status. If another service owns this port, change {variable} in .env; '
                        'an existing Lab service may already own it.')

    def run(self):
        print('Kex Lab doctor — lightweight demo preflight (read-only)', flush=True)
        print('Resource values are planning recommendations, not performance guarantees.', flush=True)
        docker = bool(shutil.which('docker'))
        self.result('OK' if docker else 'ERROR', 'Docker CLI available.' if docker else 'Docker CLI missing.',
                    '' if docker else 'Install Docker Engine or Docker Desktop with Compose v2.')
        for tool in ('curl', 'make'):
            found = bool(shutil.which(tool))
            self.result('OK' if found else 'ERROR', f'{tool} {"available" if found else "missing"}.',
                        '' if found else f'Install {tool} with your system package manager.')
        self.result('OK', 'Python 3 available.')
        if docker:
            info = self.command(['docker', 'info', '--format', '{{.NCPU}} {{.MemTotal}}'])
            self.result('OK' if info is not None else 'ERROR',
                        'Docker daemon reachable.' if info is not None else 'Docker daemon unavailable or timed out.',
                        '' if info is not None else 'Start Docker; check docker context show and docker info, then rerun make doctor.')
            if info is not None:
                self.resources(info)
            compose = self.command(['docker', 'compose', 'version']) is not None
            self.result('OK' if compose else 'ERROR', 'Compose v2 available.' if compose else 'Compose v2 unavailable.',
                        '' if compose else 'Install the Docker Compose v2 plugin; verify docker compose version.')
            if compose and Path('.env').is_file():
                valid = self.command(['docker', 'compose', '--env-file', 'versions.env',
                                      '-f', 'compose.yml', '-f', 'compose.autotune.yml', 'config', '-q']) is not None
                self.result('OK' if valid else 'ERROR', 'Demo Compose configuration valid.' if valid else 'Demo Compose configuration invalid.',
                            '' if valid else 'Run docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml config -q locally; correct .env.')
        if not Path('.env').is_file():
            self.result('ERROR', '.env is missing.', 'Run make setup, review .env, then rerun make doctor.')
        else:
            self.result('OK', '.env loaded; exported caller settings take precedence.')
        free = shutil.disk_usage('.').free / 1024**3
        self.result('OK' if free >= 10 else 'WARN', f'Checkout filesystem: {free:.1f} GiB free (recommended: 10).',
                    '' if free >= 10 else 'Free disk space before pulling images; inspect docker system df before removing anything.')
        print('      Docker Desktop/remote daemons: also verify free space on the Docker image filesystem.', flush=True)
        configured_ports = {}
        for variable, default in [('KAFKA_PORT', '9092'), ('EXPLORER_PORT', '8080'),
                                  ('KEX_AGENT_PORT', '8081'), ('AUTOTUNE_PORT', '8082')]:
            self.port(variable, default)
            value = os.environ.get(variable, default)
            if value.isdigit() and int(value) != 0:
                port = int(value)
                if port in configured_ports:
                    self.result('ERROR', f'{variable} and {configured_ports[port]} use the same host port.',
                                f'Choose distinct ports in .env, then rerun make doctor.')
                configured_ports[port] = variable
        for variable, default in [('EXPLORER_MCP_AUTH_TOKEN', 'change-me-local-mcp-token'),
                                  ('KEX_AGENT_API_KEY', 'change-me-local-agent-key')]:
            customized = os.environ.get(variable, '') not in ('', default)
            self.result('OK' if customized else 'WARN', f'{variable}: {"customized" if customized else "default or empty"}.',
                        '' if customized else f'Set {variable} in .env before sharing access. Its value is never printed here.')
        print(f'Doctor result: {self.errors} error(s), {self.warnings} warning(s)', flush=True)
        if self.errors:
            print('Correct the errors above, then rerun make doctor.', flush=True)
        else:
            print('Next: make demo-lite. Warnings do not block the local demo.', flush=True)
        return int(bool(self.errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', action='store_true', help='Show diagnostic command exit codes; never secret values.')
    raise SystemExit(Doctor(parser.parse_args().verbose).run())
