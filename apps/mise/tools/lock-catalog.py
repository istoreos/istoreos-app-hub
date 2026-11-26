#!/usr/bin/env python3
"""Build a reviewable catalog from cached primary-source metadata, never guesses hashes.

Maintainer tool only; the router does not need Python. Obtain the named metadata
from the URLs recorded by this tool before running. No floating release resolves
occur on the router. Catalog availability does not assert device verification.
"""
import argparse
import hashlib
import copy
import json
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cache = args.metadata
    entries, sources = [], {}

    def read(name, url):
        data = (cache / name).read_bytes()
        sources[name] = {'url': url, 'sha256': hashlib.sha256(data).hexdigest()}
        return data.decode()

    def artifact(url, sha, fmt, strip, size=None, component=None):
        assert re.fullmatch('[a-f0-9]{64}', sha), (url, sha)
        result = {'url': url, 'sha256': sha, 'format': fmt, 'strip': strip}
        if size:
            result['bytes'] = size
        if component:
            result['component'] = component
        return result

    def add(tool, version, arch, abi, build, source, artifacts, layout='standard', npm=None):
        entry = {'id': f'{tool}-{version}-{arch}-{abi}-{build}', 'tool': tool,
                 'version': version, 'arch': arch, 'abi': abi, 'build': build,
                 'source': source, 'availability': 'available', 'layout': layout,
                 'artifacts': artifacts, 'artifact_set': digest(artifacts)}
        if tool == 'node':
            entry['npm'] = npm
        entries.append(entry)

    npm_options = json.loads((ROOT / 'apps/mise/mise-runtime/files/npm.json').read_text())['versions']
    for option in npm_options:
        metadata = json.loads(read('npm-' + option['version'] + '.json', option['source']))
        assert metadata['dist']['integrity'] == option['integrity'] and metadata['engines'] == option['engines']
        archive = (cache / ('npm-' + option['version'] + '.tgz')).read_bytes()
        assert hashlib.sha256(archive).hexdigest() == option['artifact']['sha256']

    for version in ['24.22.1', '24.21.0']:
        npm_file = cache / f'node-npm-{version}.json'
        npm_url = f'https://raw.githubusercontent.com/nodejs/node/v{version}/deps/npm/package.json'
        if not npm_file.exists():
            subprocess.run(['curl', '-fsSL', '--connect-timeout', '8', '--max-time', '30',
                            '-o', str(npm_file), npm_url], check=True)
        npm = json.loads(read(npm_file.name, npm_url))['version']
        for abi in ['glibc', 'musl']:
            base = ('https://nodejs.org/dist' if abi == 'glibc' else
                    'https://unofficial-builds.nodejs.org/download/release')
            source = f'{base}/v{version}/SHASUMS256.txt'
            raw = read(('node-' if abi == 'glibc' else 'node-musl-') + version, source)
            hashes = {line.split()[1]: line.split()[0] for line in raw.splitlines() if line.strip()}
            for arch, upstream in [('x86_64', 'x64'), ('aarch64', 'arm64')]:
                filename = f'node-v{version}-linux-{upstream}' + ('-musl' if abi == 'musl' else '') + '.tar.xz'
                assert filename in hashes, filename
                add('node', version, arch, abi, 'upstream1', source,
                    [artifact(f'{base}/v{version}/{filename}', hashes[filename], 'tar.xz', 1)], npm=npm)
                for option in npm_options:
                    if option['version'] != npm:
                        add('node', version, arch, abi, 'upstream1-npm' + option['version'], source,
                            [artifact(f'{base}/v{version}/{filename}', hashes[filename], 'tar.xz', 1), copy.deepcopy(option['artifact'])], npm=option['version'])

    python_sources = [
        ('python-latest', 'https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest',
         ['3.12', '3.13'], 'install_only_stripped'),
        # Hermes v0.23.4 pins this exact first-party Python build. Keep it in
        # the public catalog so applications can bind the same interpreter
        # without letting Hermes PM download a second private Python.
        ('python-hermes-20261021',
         'https://api.github.com/repos/astral-sh/python-build-standalone/releases/tags/20261021',
         ['3.14'], 'install_only'),
    ]
    for metadata_name, python_url, minors, variant in python_sources:
        python = json.loads(read(metadata_name, python_url))
        assets = {a['name']: a for a in python['assets']}
        python_source = 'https://api.github.com/repos/astral-sh/python-build-standalone/releases/tags/' + python['tag_name']
        for minor in minors:
            versions = {m.group(1) for name in assets if (m := re.match(r'^cpython-(' + re.escape(minor) + r'\.\d+)\+', name))}
            version = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
            for arch in ['x86_64', 'aarch64']:
                for abi, upstream in [('glibc', 'gnu'), ('musl', 'musl')]:
                    name = f'cpython-{version}+{python["tag_name"]}-{arch}-unknown-linux-{upstream}-{variant}.tar.gz'
                    a = assets[name]
                    assert a['digest'].startswith('sha256:')
                    add('python', version, arch, abi, python['tag_name'], python_source,
                        [artifact(a['browser_download_url'], a['digest'][7:], 'tar.gz', 1, a['size'])], 'python')

    go_source = 'https://go.dev/dl/?mode=json&include=all'
    go = {x['version']: x for x in json.loads(read('go', go_source))}
    for version in ['1.27.4', '1.26.10']:
        files = {a['arch']: a for a in go['go' + version]['files'] if a['os'] == 'linux' and a['kind'] == 'archive'}
        for arch, upstream in [('x86_64', 'amd64'), ('aarch64', 'arm64')]:
            a = files[upstream]
            add('go', version, arch, 'native', 'upstream1', go_source,
                [artifact('https://dl.google.com/go/' + a['filename'], a['sha256'], 'tar.gz', 1, a['size'])])

    for version in ['1.91.1', '1.90.0']:
        source = f'https://static.rust-lang.org/dist/channel-rust-{version}.toml'
        manifest = tomllib.loads(read('rust-' + version, source))
        for arch in ['x86_64', 'aarch64']:
            for abi, upstream in [('glibc', 'gnu'), ('musl', 'musl')]:
                triple = f'{arch}-unknown-linux-{upstream}'
                artifacts = []
                for component in ['rustc', 'cargo', 'rust-std']:
                    a = manifest['pkg'][component]['target'][triple]
                    assert a['available'], (version, triple, component)
                    artifacts.append(artifact(a['xz_url'], a['xz_hash'], 'tar.xz', 1, component=component))
                add('rust', version, arch, abi, 'minimal1', source, artifacts, 'rust-components')

    zig_source = 'https://ziglang.org/download/index.json'
    zig = json.loads(read('zig', zig_source))
    for version in ['0.17.1', '0.15.2']:
        for arch in ['x86_64', 'aarch64']:
            a = zig[version][arch + '-linux']
            add('zig', version, arch, 'native', 'upstream1', zig_source,
                [artifact(a['tarball'], a['shasum'], 'tar.xz', 1, int(a['size']))], 'zig')

    java_file = ROOT / 'docs/evidence/mise-java-design-20261123/upstream-fixed-artifacts.json'
    java_data = java_file.read_bytes()
    sources['java-baseline'] = {'path': str(java_file.relative_to(ROOT)), 'sha256': hashlib.sha256(java_data).hexdigest()}
    for release in json.loads(java_data):
        for arch, upstream in [('x86_64', 'x64'), ('aarch64', 'aarch64')]:
            a = next(a for a in release['assets'][upstream] if a['name'].endswith('.tar.gz'))
            assert a['digest'].startswith('sha256:')
            add('java', 'temurin-' + release['version'], arch, 'glibc', 'hotspot1', release['source'],
                [artifact(a['url'], a['digest'][7:], 'tar.gz', 1, a['size'])])

    catalog = {'schema_version': 1, 'entries': sorted(entries, key=lambda e: e['id']),
               'sources': sources, 'note': 'Pinned upstream availability only; runtime capability requires device probes.'}
    catalog['revision'] = digest(catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'entries': len(entries), 'revision': catalog['revision'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
