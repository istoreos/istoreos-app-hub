"""Exercise package install recipes and hooks against isolated filesystem roots.

Runtime payloads are inert fixtures. This is packaging/upgrade validation, not an
SDK release build or a test of the application binaries.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path('usr/share/linkease/apps.d')
RETIRED = Path('usr/share/linkeasefull/desktop-apps.d')
FIXTURES = Path(__file__).parent / 'fixtures/legacy-registrations'
CASES = [
    ('kaiplus/kaiplus', 'kaiplus', '00-kaiplus-plugin.json'),
    ('kai/kai', 'kai', '05-kai-plugin.json'),
    ('baidudrive/baidudrive', 'baidudrive', '10-baidudrive-plugin.json'),
    ('dockermanager/dockermanager', 'dockermanager', '20-dockermanager-plugin.json'),
    ('agentflow/agentflow', 'agentflow', '30-agentflow.json'),
    ('istoreenhance/istoreenhance', 'kspeeder', '20-kspeeder.json'),
    ('fastnet/fastnet', 'fastnet', '17-fastnet.json'),
    ('ddnsto/luci-app-ddnsto', 'ddnsto', '16-ddnsto.json'),
    ('linkeasefull/luci-app-linkeasefull-embed', 'openwrt-luci', '15-openwrt-luci.json'),
]


class PackageStage:
    def __init__(self, relative, workspace):
        self.source = ROOT / 'apps' / relative
        self.work = workspace
        self.stage = workspace / 'root'
        self.stage.mkdir()
        self.build = workspace / 'built'
        self.build.mkdir()
        top = workspace / 'sdk'
        for name in ['rules.mk', 'include/package.mk', 'feeds/luci/luci.mk']:
            p = top / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('')
        self.makefile = workspace / 'harness.mk'
        self.makefile.write_text(f'''TOPDIR:={top}
INCLUDE_DIR:={top}/include
BUILD_DIR:={workspace}/build
ARCH:=x86_64
PKG_NAME:={self.source.name}
INSTALL_DIR:=install -d -m0755
INSTALL_BIN:=install -m0755
INSTALL_DATA:=install -m0644
INSTALL_CONF:=install -m0600
CP:=cp -a
LN:=ln -sf
include {self.source}/Makefile
stage:
\t$(call Package/$(PKG_NAME)/install,{self.stage})
hooks:
\t$(file >{workspace}/postinst,$(Package/$(PKG_NAME)/postinst))
\t$(file >{workspace}/prerm,$(Package/$(PKG_NAME)/prerm))
''')
        if self.source.name == 'luci-app-ddnsto':
            shutil.copytree(self.source / 'root', self.stage, symlinks=True, dirs_exist_ok=True)
        else:
            preview = self.make('-n', 'stage')
            # Populate only the fake built-artifact paths used by the real recipe.
            for value in re.findall(re.escape(str(self.build)) + r'''[^\s;"']*''', preview):
                if value.endswith('/.') or value.endswith('/*') or value.endswith('/wwwroot'):
                    directory = Path(value.removesuffix('/.').removesuffix('/*'))
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / 'index.html').write_text('fixture')
                else:
                    p = Path(value)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text('fixture')
            if self.source.name == 'baidudrive':
                (self.build / 'web/dist/baidu-drive.png').write_text('fixture')
            self.make('stage')
        self.make('hooks')

    def make(self, *arguments):
        return subprocess.check_output(
            ['make', '--no-print-directory', '-f', str(self.makefile),
             f'PKG_BUILD_DIR={self.build}', *arguments],
            cwd=self.source, text=True, stderr=subprocess.STDOUT,
        )

    def hook(self, name):
        script = self.work / name
        subprocess.run(['sh', '-n', str(script)], check=True)
        subprocess.run(['sh', str(script)], check=True,
                       env={**os.environ, 'IPKG_INSTROOT': str(self.stage)},
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ApplicationRegistrationTest(unittest.TestCase):
    def stages(self):
        for relative, app, filename in CASES:
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            yield PackageStage(relative, Path(temporary.name)), app, filename

    def test_fresh_install_has_one_owned_manifest_and_no_retired_directory(self):
        ids = set()
        for package, app, filename in self.stages():
            links = list((package.stage / REGISTRY).glob('*.json'))
            self.assertEqual([p.name for p in links], [filename])
            self.assertTrue(links[0].is_symlink())
            target = package.stage / str(links[0].readlink()).lstrip('/')
            manifest = json.loads(target.read_text())
            self.assertEqual(manifest['id'], app)
            self.assertNotIn(app, ids)
            ids.add(app)
            if manifest.get('icon'):
                icon = package.stage / manifest['staticRoot'].lstrip('/') / manifest['icon']
                self.assertTrue(icon.is_file(), str(icon))
            package.hook('postinst')
            self.assertFalse((package.stage / RETIRED).exists())

    def test_upgrade_removes_own_old_link_and_is_idempotent(self):
        for package, _, filename in self.stages():
            old = package.stage / RETIRED / filename
            old.parent.mkdir(parents=True)
            old.symlink_to((package.stage / REGISTRY / filename).readlink())
            package.hook('postinst')
            package.hook('postinst')
            self.assertFalse(old.is_symlink())
            self.assertFalse(old.parent.exists())
            self.assertTrue((package.stage / REGISTRY / filename).is_symlink())

    def test_upgrade_preserves_custom_files_and_other_owners(self):
        for package, _, filename in self.stages():
            old = package.stage / RETIRED / filename
            old.parent.mkdir(parents=True)
            old.write_text('{"custom":true}')
            package.hook('postinst')
            self.assertEqual(old.read_text(), '{"custom":true}')
            old.unlink()
            old.symlink_to('/usr/share/other/registration.json')
            package.hook('postinst')
            self.assertEqual(str(old.readlink()), '/usr/share/other/registration.json')

    def test_exact_old_metadata_files_are_retired_but_modified_files_survive(self):
        for relative, _, filename in [CASES[6], CASES[7]]:
            with self.subTest(package=relative), tempfile.TemporaryDirectory() as directory:
                package = PackageStage(relative, Path(directory))
                old = package.stage / RETIRED / filename
                old.parent.mkdir(parents=True)
                old.write_bytes((FIXTURES / filename).read_bytes())
                package.hook('postinst')
                self.assertFalse(old.exists())
                old.parent.mkdir(parents=True, exist_ok=True)
                old.write_bytes((FIXTURES / filename).read_bytes() + b'\n')
                package.hook('postinst')
                self.assertTrue(old.exists())

    def test_uninstall_removes_only_registration_still_owned_by_the_package(self):
        for package, _, filename in self.stages():
            registration = package.stage / REGISTRY / filename
            package.hook('prerm')
            self.assertFalse(registration.is_symlink())
            registration.symlink_to('/usr/share/replacement/registration.json')
            package.hook('prerm')
            self.assertEqual(str(registration.readlink()), '/usr/share/replacement/registration.json')

    def test_metadata_repositories_do_not_ship_application_registrations(self):
        for base in [ROOT / 'apps']:
            for pkg in base.rglob('app-meta-*'):
                if not pkg.is_dir():
                    continue
                for file in (pkg / 'root').rglob('*'):
                    if file.is_file() or file.is_symlink():
                        self.assertNotIn('apps.d', file.parts, str(file))
                        self.assertNotIn('desktop-apps.d', file.parts, str(file))
                        if file.suffix == '.json' and file.is_file():
                            value = json.loads(file.read_text())
                            self.assertNotIn('desktop', value, str(file))

    def test_luci_owned_ddnsto_keeps_its_existing_launch_contract(self):
        previous = json.loads((FIXTURES / '16-ddnsto.json').read_text())
        source = ROOT / 'apps/ddnsto/luci-app-ddnsto/root/usr/share/ddnsto'
        current = json.loads((source / 'ddnsto-plugin.json').read_text())
        self.assertEqual(current.pop('staticRoot'), '/usr/share/ddnsto/www')
        previous.pop('staticRoot')
        self.assertEqual(current, previous)
        self.assertEqual((source / 'www/logo.png').read_bytes(),
                         (ROOT / 'apps/ddnsto/app-meta-ddnsto/logo.png').read_bytes())


if __name__ == '__main__':
    unittest.main()
