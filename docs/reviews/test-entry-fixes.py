#!/usr/bin/env python3
"""Execute source entry/provider scripts with isolated dependencies on target ash/jshn.

Only creates/removes one private /tmp directory. Never invokes real ubus, Docker,
UCI, init scripts, binaries or package managers. Reports contain no service secrets.
"""
import argparse
import atexit
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
DOCKER = {'oneapi': ('oneapi', 3000), 'openwebui': ('openwebui', 8080),
          'pve': ('pve', 8006), 'codeserver': ('codeserver', 8443),
          'ubuntu': ('ubuntu2', 3001), 'jellyfin': ('jellyfin', 8096),
          'uptimekuma': ('uptimekuma', 3001), 'webvirtcloud': ('webvirtcloud', 80),
          'dpanel': ('dpanel', 8080)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['root@192.168.30.244'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', help='limit follow-up verification to one app')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve previous evidence')
    report = {'result': 'running', 'scope': 'isolated target ash/jshn, no real services',
              'sourceHashes': {}, 'cases': [], 'temporaryFilesCleaned': False}

    def remote(command, data=None):
        return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                               args.target, command], input=data, capture_output=True, timeout=90)

    task = remote('umask 077; mktemp -d /tmp/app-entry-regression.XXXXXXXX')
    assert task.returncode == 0, task.stderr.decode()
    task = task.stdout.decode().strip()
    assert re.fullmatch(r'/tmp/app-entry-regression\.[a-zA-Z0-9]+', task)

    def cleanup():
        # Also runs if fixture preparation fails before upload/execution.
        if not report['temporaryFilesCleaned']:
            try:
                report['temporaryFilesCleaned'] = remote('rm -rf ' + shlex.quote(task)).returncode == 0
            except subprocess.SubprocessError:
                report['temporaryFilesCleaned'] = False
        if report['result'] == 'running':
            report['result'] = 'failed'
            report['failure'] = 'fixture setup or execution did not finish'
        if not report['temporaryFilesCleaned']:
            report['remainingTemporaryDirectory'] = task
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    atexit.register(cleanup)
    files, cases = {}, []

    def source(path):
        body = (ROOT / path).read_text()
        report['sourceHashes'][path] = hashlib.sha256(body.encode()).hexdigest()
        return body

    def add(app, name, *, env=None, action='status', expected=None, error=False,
            commands=None, state=None):
        number = len(cases)
        if state is not None:
            files[f'state-{number}'] = state if isinstance(state, str) else json.dumps(state)
            env = {**(env or {}), 'ENTRY_STATE': f'{task}/state-{number}'}
        cases.append({'app': app, 'name': name, 'env': env or {}, 'action': action,
                      'expected': expected or {}, 'error': error, 'commands': commands})

    files['docker'] = '''#!/bin/sh
case "$1" in
ps)
    [ "$ENTRY_FAIL" != status ] || exit 17
    [ "$*" = "ps --all -f name=^/$ENTRY_CONTAINER\u0024 --format {{.State}}" ] || exit 91
    printf '%s\\n' "$ENTRY_STATUS";;
inspect)
    [ "$ENTRY_FAIL" != port ] || exit 18
    [ "$4" = "$ENTRY_CONTAINER" ] || exit 92
    case "$3" in
        *NetworkMode*) printf '%s\\n' "${ENTRY_MODE:-bridge}";;
        *"\\\"$ENTRY_INTERNAL/tcp\\\""*) printf '%s\\n' "$ENTRY_BINDINGS";;
        *) exit 93;;
    esac;;
start|stop) echo "$1" >> "$ENTRY_ACTIONS"; exit "${ENTRY_ACTION_EXIT:-0}";;
*) exit 94;;
esac
'''
    files['ubus'] = '''#!/bin/sh
[ "$ENTRY_FAIL" != ubus ] || exit 19
cat "$ENTRY_STATE"
'''
    files['uci'] = '#!/bin/sh\nexit 95\n'
    files['pidof'] = '#!/bin/sh\nexit 95\n'
    files['init'] = '#!/bin/sh\necho "$1" >> "$ENTRY_ACTIONS"\nexit "${ENTRY_ACTION_EXIT:-0}"\n'
    files['vmease'] = '#!/bin/sh\necho "vmease:$1" >> "$ENTRY_ACTIONS"\nexit 0\n'
    for app, (container, internal) in DOCKER.items():
        provider = f'apps/{container}/luci-app-{container}/root/usr/libexec/istorec/{container}.sh'
        body = source(provider).replace('/etc/init.d/vmease', task + '/vmease')
        assert '{{printf "%s %s\\n" .HostIp .HostPort}}' in body, 'Docker template must emit newlines'
        files[container + '-provider'] = body
        entry = source(f'apps/{app}/app-meta-{app}/entry.sh')
        entry = re.sub(r'^ISTOREC_SCRIPT=.*$', f'ISTOREC_SCRIPT={task}/{container}-provider', entry, flags=re.M)
        entry = re.sub(r'^\[ -f /usr/libexec/istorec/jellyfin.sh \].*$', '', entry, flags=re.M)
        files[app + '-entry'] = entry
        env = {'ENTRY_CONTAINER': container, 'ENTRY_INTERNAL': str(internal), 'ENTRY_STATUS': 'running',
               'ENTRY_BINDINGS': '0.0.0.0 43210\n:: 43210'}
        add(app, 'actual-port-dual-stack', env=env, expected={'running': True, 'deployed': True,
            'port': '43210', 'web': ':43210', 'protocol': 'https' if app == 'ubuntu' else 'http'})
        for name, changes, error, expected in [
            ('status-error', {'ENTRY_FAIL': 'status'}, True, {}),
            ('port-error', {'ENTRY_FAIL': 'port'}, True, {}),
            ('stopped', {'ENTRY_STATUS': 'exited'}, False, {'running': False, 'deployed': True, 'web': None}),
            ('undeployed', {'ENTRY_STATUS': ''}, False, {'running': False, 'deployed': False, 'web': None}),
            ('no-published-port', {'ENTRY_BINDINGS': ''}, False, {'running': True, 'web': None}),
            ('loopback-only', {'ENTRY_BINDINGS': '127.0.0.1 43210\n::1 43210'}, False, {'running': True, 'web': None}),
            ('ipv6-only', {'ENTRY_BINDINGS': ':: 43211'}, False, {'port': '43211', 'web': ':43211'}),
            ('ambiguous-ports', {'ENTRY_BINDINGS': '0.0.0.0 43210\n:: 43211'}, True, {}),
            ('invalid-port', {'ENTRY_BINDINGS': '0.0.0.0 65536'}, True, {}),
        ]:
            add(app, name, env={**env, **changes}, error=error, expected=expected)
        for action, status, commands, error, extra in [
            ('start', 'running', [], False, {}), ('stop', 'exited', [], False, {}),
            ('start', '', [], True, {}), ('start', 'exited', ['start'], False, {}),
            ('stop', 'running', ['stop'], False, {}),
            ('start', 'exited', ['start'], True, {'ENTRY_ACTION_EXIT': '23'}),
            ('stop', 'running', [], True, {'ENTRY_FAIL': 'status'}),
        ]:
            if app in ['pve', 'webvirtcloud'] and commands == ['start']:
                commands = ['vmease:start', 'start']
            add(app, action + '-' + status + '-' + str(extra), env={**env, 'ENTRY_STATUS': status, **extra},
                action=action, commands=commands, error=error)
        if app == 'jellyfin':
            add(app, 'host-network-default', env={**env, 'ENTRY_MODE': 'host', 'ENTRY_BINDINGS': ''},
                expected={'running': True, 'port': '8096', 'web': ':8096'})

    # Native fixtures are appended below; all state is synthetic, not read from services.
    native_cases(files, add, source, task)
    if args.only:
        cases = [case for case in cases if case['app'] == args.only]
        assert cases, 'unknown app filter'
    quote = shlex.quote
    runner = ['#!/bin/sh', 'umask 077', 'cd ' + quote(task), 'chmod 700 ./*', 'mkdir out']
    for number, case in enumerate(cases):
        base_env = {'PATH': task + ':/usr/sbin:/usr/bin:/sbin:/bin', 'ENTRY_ACTIONS': task + f'/out/{number}.actions',
                    'ENTRY_FAIL': '', 'ENTRY_ACTION_EXIT': '0'}
        env = {**base_env, **case['env']}
        runner.extend([': > out/' + str(number) + '.actions',
                       'env ' + ' '.join(key + '=' + quote(value) for key, value in env.items()) +
                       ' /bin/sh ' + quote(task + '/' + case['app'] + '-entry') + ' ' + quote(case['action']) +
                       ' router.example > out/' + str(number) + '.stdout 2> out/' + str(number) + '.stderr',
                       'echo $? > out/' + str(number) + '.exit'])
    files['run'] = '\n'.join(runner) + '\n'
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as tar:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o700
            tar.addfile(info, io.BytesIO(data))
    try:
        upload = remote('tar -xf - -C ' + quote(task), archive.getvalue())
        assert upload.returncode == 0, upload.stderr.decode()
        run = remote('/bin/sh ' + quote(task + '/run'))
        assert run.returncode == 0, run.stderr.decode()
        result = remote('tar -cf - -C ' + quote(task + '/out') + ' .')
        assert result.returncode == 0
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tar:
            def read(number, extension):
                return tar.extractfile(f'./{number}.{extension}').read().decode()
            for number, case in enumerate(cases):
                code = int(read(number, 'exit'))
                stdout = read(number, 'stdout')
                failures = []
                if bool(code) != case['error']:
                    failures.append('unexpected-exit-' + str(code))
                if case['error'] and stdout.strip():
                    failures.append('error-must-not-produce-status-json')
                if not case['error'] and case['action'] == 'status':
                    try:
                        actual = json.loads(stdout)
                        for key, value in case['expected'].items():
                            if actual.get(key) != value:
                                failures.append('mismatch-' + key)
                        if actual.get('app') != case['app']:
                            failures.append('mismatch-app')
                    except ValueError:
                        failures.append('invalid-json')
                if case['commands'] is not None and read(number, 'actions').splitlines() != case['commands']:
                    failures.append('unexpected-service-actions')
                report['cases'].append({'app': case['app'], 'name': case['name'], 'exitCode': code,
                                        'result': 'failed' if failures else 'passed', 'failures': failures})
        report['result'] = 'failed' if any(c['result'] == 'failed' for c in report['cases']) else 'passed'
    finally:
        cleanup()
    print(json.dumps({'result': report['result'], 'cases': len(report['cases']),
                      'failed': sum(c['result'] == 'failed' for c in report['cases']),
                      'temporaryFilesCleaned': report['temporaryFilesCleaned']}))
    return int(report['result'] != 'passed' or not report['temporaryFilesCleaned'])


def native_cases(files, add, source, task):
    commands = {
        'baidudrive': ['/usr/sbin/baidudrive', '--host', '0.0.0.0', '--port', '43210', '--data', '/fixture'],
        'agentflow': ['/usr/sbin/agentflow'],
        'kai': ['/usr/sbin/kai_bin', '-a', '0.0.0.0', '-p', '43210'],
        'istoreenhance': ['/usr/sbin/iStoreEnhance', '--localAddr', ':5443', '--adminAddr', ':43210', '--cachePath', '/fixture'],
        'dockermanager': ['/usr/sbin/docker-manager'],
        'openclawmgr': ['/fixture/node/bin/node', '/fixture/global/lib/node_modules/openclaw/openclaw.mjs',
                       'gateway', 'run', '--port', '43210', '--bind', 'lan', '--auth', 'token', '--token', 'fixture+secret/#'],
        'fastnet': [task + '/FastNet', 'web', '--addr', '0.0.0.0:43210', '--no-open'],
    }
    instances = {'baidudrive': 'baidudrive', 'agentflow': 'instance1', 'kai': 'kai_bin',
                 'istoreenhance': 'instance1', 'dockermanager': 'docker-manager',
                 'openclawmgr': 'gateway', 'fastnet': 'instance1'}
    environments = {
        'agentflow': {'AGENT_FLOW_HOST': '0.0.0.0', 'AGENT_FLOW_PORT': '43210'},
        'dockermanager': {'DOCKER_MANAGER_LISTEN_MODE': 'tcp', 'DOCKER_MANAGER_ADDR': '0.0.0.0:43210',
                          'DOCKER_MANAGER_BASE_PATH': '/apps/dockermanager/'},
        'openclawmgr': {'OPENCLAW_CONFIG_PATH': task + '/openclaw.json'},
    }
    files['openclaw.json'] = json.dumps({'gateway': {'controlUi': {'basePath': '/custom/'}}})
    files['FastNet'] = '#!/bin/sh\nexit 0\n'
    for app, command in commands.items():
        body = source(f'apps/{app}/app-meta-{app}/entry.sh')
        # Dependency substitution applies only to the private test copy.
        body = body.replace('/etc/init.d/' + app, '${ENTRY_INIT_FIXTURE:-' + task + '/init}')
        if app == 'fastnet':
            body = body.replace('FASTNET_BIN=/usr/sbin/FastNet', 'FASTNET_BIN=' + task + '/FastNet')
        if app == 'istoreenhance':
            body = body.replace('ISTOREENHANCE_BIN=/usr/sbin/iStoreEnhance', 'ISTOREENHANCE_BIN=' + task + '/FastNet')
        if app == 'openclawmgr':
            # Runtime presence and explicit actions use the existing provider;
            # the Web target is independently read from procd and its config.
            files['claw-provider'] = '''#!/bin/sh
case "$1" in
status) [ "$ENTRY_FAIL" != claw ] || exit 17; printf '%s\\n' "${ENTRY_CLAW_STATUS-running}";;
start|stop) echo "provider:$1" >> "$ENTRY_ACTIONS"; exit "${ENTRY_ACTION_EXIT:-0}";;
*) exit 9;;
esac
'''
            body = re.sub(r'^ISTOREC_SCRIPT=.*$', 'ISTOREC_SCRIPT=' + task + '/claw-provider', body, flags=re.M)
        files[app + '-entry'] = body
        instance = {'running': True, 'command': command, 'env': environments.get(app, {})}

        def state(value=None, extra=None):
            return {app: {'instances': {instances[app]: value or instance, **(extra or {})}}}

        path = {'agentflow': '/apps/agentflow/', 'kai': '/apps/kai/', 'dockermanager': '/apps/dockermanager/',
                'openclawmgr': '/custom/#token=%66%69%78%74%75%72%65%2B%73%65%63%72%65%74%2F%23'}.get(app, '')
        add(app, 'effective-runtime-port', state=state(), expected={'running': True, 'deployed': True,
            'port': '43210', 'web': ':43210' + path, 'docker': False,
            'href': '/cgi-bin/luci/admin/services/' + app})
        add(app, 'stopped', state=state({**instance, 'running': False}),
            expected={'running': False, 'deployed': True, 'web': None})
        add(app, 'absent-service', state={}, expected={'running': False, 'web': None})
        add(app, 'ubus-error', state=state(), env={'ENTRY_FAIL': 'ubus'}, error=True)
        add(app, 'malformed-service-json', state='{', error=True)
        if app != 'fastnet':
            add(app, 'invalid-running-type', state=state({**instance, 'running': 'true'}), error=True)
        add(app, 'wrong-web-command', state=state({**instance, 'command': ['/wrong/binary']}), error=True)
        if app != 'fastnet':
            add(app, 'undeployed', state={}, env={'ENTRY_INIT_FIXTURE': task + '/absent'},
                expected={'running': False, 'deployed': False, 'web': None})
        for action in ['start', 'stop']:
            add(app, action + '-failure', action=action, env={'ENTRY_ACTION_EXIT': '23'},
                commands=[('provider:' if app == 'openclawmgr' else '') + action], error=True)
        if app in ['baidudrive', 'kai']:
            other = 'baiduNas' if app == 'baidudrive' else 'kai_session'
            add(app, 'dependency-only', state=state({**instance, 'running': False},
                {other: {'running': True, 'command': ['/fixture/helper']}}), expected={'running': False, 'web': None})
        if app in ['agentflow', 'istoreenhance', 'fastnet']:
            second = json.loads(json.dumps(instance))
            if app == 'fastnet':
                second['command'][3] = '0.0.0.0:43211'
            add(app, 'ambiguous-instances', state=state(extra={'second': second}), error=True)
        if app == 'dockermanager':
            add(app, 'unix-listener', state=state({**instance, 'env': {
                **instance['env'], 'DOCKER_MANAGER_LISTEN_MODE': 'unix'}}),
                expected={'running': True, 'web': '/cgi-bin/luci/admin/services/linkease_apps/open?id=dockermanager', 'port': None})
            add(app, 'loopback-only', state=state({**instance, 'env': {
                **instance['env'], 'DOCKER_MANAGER_ADDR': '127.0.0.1:43210'}}), expected={'running': True, 'web': None})
        if app == 'openclawmgr':
            add(app, 'runtime-not-downloaded', state=state({**instance, 'running': False}),
                env={'ENTRY_CLAW_STATUS': ''}, expected={'running': False, 'deployed': False, 'web': None})
            add(app, 'runtime-inspection-error', state=state({**instance, 'running': False}),
                env={'ENTRY_FAIL': 'claw'}, error=True)
            loopback = command.copy()
            loopback[7] = 'loopback'
            add(app, 'loopback-only', state=state({**instance, 'command': loopback}), expected={'running': True, 'web': None})
            for name, config, web, error in [
                ('default-base-path', {}, ':43210/#token=%66%69%78%74%75%72%65%2B%73%65%63%72%65%74%2F%23', False),
                ('unsafe-base-path', {'gateway': {'controlUi': {'basePath': '//other.example/'}}}, None, True),
                ('parent-base-path', {'gateway': {'controlUi': {'basePath': '..'}}}, None, True),
                ('wrong-base-path-type', {'gateway': {'controlUi': {'basePath': False}}}, None, True),
                ('invalid-config', '{', None, True),
            ]:
                filename = 'claw-config-' + name
                files[filename] = config if isinstance(config, str) else json.dumps(config)
                value = {**instance, 'env': {'OPENCLAW_CONFIG_PATH': task + '/' + filename}}
                add(app, name, state=state(value), expected={'web': web}, error=error)


if __name__ == '__main__':
    raise SystemExit(main())
