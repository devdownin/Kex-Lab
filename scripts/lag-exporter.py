#!/usr/bin/env python3
"""Expose only measured AutoTune lag and health from its internal health endpoint."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

URL = 'http://autotune:8080/actuator/health'


def metrics(payload):
    value = payload.get('components', {}).get('kafkaLag', {}).get('details', {}).get('lag')
    measured = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
    lines = ['# HELP kex_lab_autotune_probe_success AutoTune health returned a measured consumer lag.',
             '# TYPE kex_lab_autotune_probe_success gauge',
             f'kex_lab_autotune_probe_success {int(measured)}']
    if measured:
        lines += ['# HELP kex_lab_autotune_consumer_lag Total lag reported by AutoTune for its own consumers, not all Kafka groups.',
                  '# TYPE kex_lab_autotune_consumer_lag gauge',
                  f'kex_lab_autotune_consumer_lag {value}']
    if payload.get('status') in {'UP', 'DOWN', 'WARNING', 'OUT_OF_SERVICE'}:
        lines += ['# HELP kex_lab_autotune_health_up AutoTune overall health status is UP.',
                  '# TYPE kex_lab_autotune_health_up gauge',
                  f'kex_lab_autotune_health_up {int(payload["status"] == "UP")}']
    return '\n'.join(lines) + '\n'


def collect():
    # This fixed Docker-network URL is local; no external destinations are queried.
    opener = build_opener(ProxyHandler({}))
    try:
        response = opener.open(URL, timeout=3)
    except HTTPError as error:
        if error.code != 503:
            raise
        response = error
    with response:
        payload = json.load(response)
    return metrics(payload)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path != '/metrics':
            self.send_error(404)
            return
        try:
            body = collect()
        except (OSError, ValueError, TypeError, AttributeError):
            body = metrics({})
        data = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 9108), Handler).serve_forever()
