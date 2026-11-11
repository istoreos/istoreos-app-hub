#!/usr/bin/env python3
"""Build inert IPK/APK fixtures for isolated package-manager migration tests.

Includes real manifests, registration links and rendered hooks, never application
binaries, init scripts or UCI defaults. Not an SDK build or a release artifact.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import tarfile
import tempfile


def archive(files, terminate=True):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.PAX_FORMAT) as tar:
        directories = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
        for name in sorted(directories):
            item = tarfile.TarInfo(name + '/')
            item.type = tarfile.DIRTYPE
            item.mode = 0o755
            tar.addfile(item)
        for name, value in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.uid = item.gid = item.mtime = 0
            if isinstance(value, tuple):
                item.type = tarfile.SYMTYPE
                item.linkname = value[0]
                item.mode = 0o777
                tar.addfile(item)
            else:
                item.mode = 0o755 if name.endswith('.sh') or name.startswith('.') or name in ['postinst', 'prerm'] else 0o644
                item.size = len(value)
                tar.addfile(item, io.BytesIO(value))
        end = tar.offset
    # APKv2 control tar continues into the data tar: no end-of-archive blocks.
    # See Alpine abuild's `abuild-tar --cut` before concatenating gzip streams.
    raw = output.getvalue() if terminate else output.getvalue()[:end]
    return gzip.compress(raw, mtime=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    support = runpy.run_path(str(Path(__file__).with_name('test_app_registration.py')))
    root = support['ROOT']
    records = []
    for app, relative, filename in [('fastnet', 'fastnet/fastnet', '17-fastnet.json'),
                                    ('ddnsto', 'ddnsto/luci-app-ddnsto', '16-ddnsto.json')]:
        with tempfile.TemporaryDirectory() as directory:
            stage = support['PackageStage'](relative, Path(directory))
            new_files = {}
            for path in (stage.stage / 'usr/share').rglob('*'):
                name = str(path.relative_to(stage.stage))
                if path.is_symlink():
                    new_files[name] = (str(path.readlink()),)
                elif path.is_file():
                    new_files[name] = path.read_bytes()
            owner = stage.source.name
            hooks = {name: (stage.work / name).read_bytes() for name in ['postinst', 'prerm']}
            meta = 'app-meta-' + app
            source = (root / 'apps' / app / meta / 'Makefile').read_text()
            meta_hook = re.search(r'define Package/' + meta + r'/postinst\n(.*?)\nendef', source, re.S)[1].replace('$$', '$').encode() + b'\n'
            legacy = 'usr/share/linkeasefull/desktop-apps.d/' + filename
            old_meta = {legacy: (support['FIXTURES'] / filename).read_bytes()}
            meta_marker = {'usr/share/registration-test/' + meta: b'inert metadata fixture\n'}
            old_owner = {'usr/share/registration-test/' + owner: b'inert old owner fixture\n'}
            for name, revision, files, scripts in [(owner, 1, old_owner, {}), (meta, 1, old_meta, {}),
                                                    (owner, 2, new_files, hooks), (meta, 2, meta_marker, {'postinst': meta_hook})]:
                for fmt in ['ipk', 'apk']:
                    data = archive(files)
                    version = '1.0-' + ('r' if fmt == 'apk' else '') + str(revision)
                    if fmt == 'ipk':
                        control = f'Package: {name}\nVersion: {version}\nArchitecture: all\nMaintainer: registration-test\nDescription: inert isolated registration migration fixture\n'.encode()
                        package = archive({'debian-binary': b'2.0\n', 'control.tar.gz': archive({'control': control, **scripts}), 'data.tar.gz': data})
                    else:
                        info = f'pkgname = {name}\npkgver = {version}\npkgdesc = inert isolated registration migration fixture\nurl = https://example.invalid/\nbuilddate = 0\npackager = registration-test\nsize = 4096\narch = noarch\nlicense = GPL-2.0\ndatahash = {hashlib.sha256(data).hexdigest()}\n'.encode()
                        control_files = {'.PKGINFO': info}
                        if 'postinst' in scripts:
                            control_files['.post-install'] = control_files['.post-upgrade'] = scripts['postinst']
                        if 'prerm' in scripts:
                            control_files['.pre-deinstall'] = control_files['.pre-upgrade'] = scripts['prerm']
                        package = archive(control_files, terminate=False) + data
                    target = output / f'{name}_{version}.{fmt}'
                    target.write_bytes(package)
                    records.append({'file': target.name, 'sha256': hashlib.sha256(package).hexdigest(),
                                    'application': app, 'format': fmt, 'revision': revision,
                                    'payload': sorted(files), 'hooks': list(scripts)})
    (output / 'fixtures.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps({'packages': len(records), 'output': str(output)}))


if __name__ == '__main__':
    main()
