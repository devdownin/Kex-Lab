#!/usr/bin/env python3
"""Build a deterministic release bundle from an exact clean Git commit."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def explicit_image(reference):
    if '@' in reference:
        image, digest = reference.rsplit('@', 1)
        return bool(image and re.fullmatch(r'sha256:[a-f0-9]{64}', digest))
    image, separator, tag = reference.rpartition(':')
    return bool(image and separator and tag != 'latest'
                and re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', tag))


def prepare(output, tag=None):
    if git('status', '--porcelain', '--untracked-files=normal').strip():
        raise ValueError('Release preparation requires a clean Git worktree; commit the reviewed changes first.')
    version = git('show', 'HEAD:VERSION').decode().strip()
    if not re.fullmatch(r'(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)', version):
        raise ValueError('VERSION must contain a stable semantic version.')
    if tag is not None and tag != 'v' + version:
        raise ValueError('Release tag does not match VERSION.')
    sha = git('rev-parse', 'HEAD').decode().strip()
    manifest = git('show', 'HEAD:versions.env').decode()
    values = dict(line.split('=', 1) for line in manifest.splitlines() if line and not line.startswith('#'))
    images = {key: value for key, value in values.items() if key.endswith('_IMAGE')}
    required = {'KAFKA_IMAGE', 'EXPLORER_IMAGE', 'KEX_AGENT_IMAGE', 'AUTOTUNE_IMAGE',
                'SPECTRALLM_IMAGE', 'SPECTRALLM_FRONTEND_IMAGE', 'PROMETHEUS_IMAGE',
                'GRAFANA_IMAGE', 'LAG_EXPORTER_IMAGE'}
    if not required <= images.keys() or any(not explicit_image(value) for value in images.values()):
        raise ValueError('The release manifest must contain explicit, non-latest image references.')
    tracked = git('ls-tree', '-r', '--name-only', 'HEAD').decode().splitlines()
    forbidden = ('.env', '.env.timesfm')
    if any(path in forbidden or (Path(path).name.startswith('.env') and Path(path).name != '.env.example') or path.startswith(('reports/', '.components/', '.timesfm/', 'dist/')) for path in tracked):
        raise ValueError('Generated reports, credentials or local component artifacts must not enter a release.')
    notes = git('show', f'HEAD:docs/releases/v{version}.md').decode()
    bundle = {'schemaVersion': 1, 'version': version, 'gitHead': sha,
              'commitDate': git('show', '-s', '--format=%cI', 'HEAD').decode().strip(),
              'images': images}
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'kex-lab-{version}.tar.gz'
    tar = git('archive', '--format=tar', f'--prefix=kex-lab-{version}/', 'HEAD')
    with archive.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            compressed.write(tar)
    files = {archive.name: archive.read_bytes(), 'versions.env': manifest.encode(),
             'bundle.json': (json.dumps(bundle, indent=2, sort_keys=True) + '\n').encode(),
             'release-notes.md': (notes + f'\nValidated source commit: `{sha}`\n\n## Exact image set\n\n```text\n{manifest}```\n').encode()}
    for name, content in files.items():
        (output / name).write_bytes(content)
    checksums = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(files.items()))
    (output / 'SHA256SUMS').write_text(checksums)
    print(f'Prepared Kex Lab {version} from {sha} in {output}')
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--tag')
    args = parser.parse_args()
    try:
        prepare(args.output, args.tag)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Release preparation failed: {error}\n')


if __name__ == '__main__':
    main()
