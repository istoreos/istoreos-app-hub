#!/usr/bin/env python3
"""Exercise entry.sh with real target jshn, isolated service fixtures, no service writes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--target', choices=['root@192.168.30.244'], required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
source = (Path(__file__).resolve().parents[1] / 'app-meta-fastnet/entry.sh').read_text()
report = {'result': 'running', 'scriptSha256': hashlib.sha256(source.encode()).hexdigest(), 'cases': []}


def remote(command, data=None):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', a.target, command],
                          input=data, capture_output=True, text=True, timeout=20)


task = remote('umask 077; mktemp -d /tmp/fastnet-entry-test.XXXXXXXX').stdout.strip()
assert re.fullmatch(r'/tmp/fastnet-entry-test\.[A-Za-z0-9]+', task)
quote = shlex.quote


def put(name, content):
    r = remote('cat > ' + quote(task + '/' + name), content)
    assert r.returncode == 0, r.stderr


try:
    binary = task + '/FastNet'
    # Only substitute the binary dependency in the test copy. Production script
    # and /usr/sbin/FastNet are never changed by this harness.
    assert source.count('FASTNET_BIN=/usr/sbin/FastNet') == 1
    put('entry.sh', source.replace('FASTNET_BIN=/usr/sbin/FastNet', 'FASTNET_BIN=' + quote(binary)))
    put('ubus', '#!/bin/sh\n[ "$*" = \'-S call service list {"name":"fastnet"}\' ] || exit 9\n[ "$QS_FASTNET_FAIL" != 1 ] || exit 1\ncat "$QS_FASTNET_STATE"\n')
    put('uci', '#!/bin/sh\nexit 9\n')
    assert remote('chmod 700 ' + quote(task + '/ubus') + ' ' + quote(task + '/uci')).returncode == 0

    def instance(running=True, address='0.0.0.0:3200', command=None):
        return {'running': running, 'command': command or [binary, 'web', '--addr', address, '--no-open', '--token', 'fixture-secret']}

    cases = [
        ('running-default', instance(), True, ':3200'),
        ('effective-custom-port', instance(address='0.0.0.0:4321'), True, ':4321'),
        ('ipv6-wildcard', instance(address='[::]:3200'), True, ':3200'),
        ('stopped-binary-still-present', instance(False), False, None),
        ('loopback-only', instance(address='127.0.0.1:3200'), True, None),
        ('port-zero', instance(address='0.0.0.0:0'), None, None),
        ('port-overflow', instance(address='0.0.0.0:65536'), None, None),
        ('port-invalid', instance(address='0.0.0.0:no'), None, None),
        ('wrong-command', instance(command=['other', 'web', '--addr', ':3200']), None, None),
        ('absent-service', {}, False, None),
        ('undeployed', instance(), False, None),
        ('ubus-failure', instance(), None, None),
        ('invalid-json', '{', None, None),
        ('ambiguous-instances', {'one': instance(), 'two': instance(address=':4321')}, None, None),
    ]
    for name, value, running, web in cases:
        put('FastNet', '#!/bin/sh\nexit 0\n')
        assert remote('chmod 700 ' + quote(binary)).returncode == 0
        if name == 'undeployed':
            assert remote('rm ' + quote(binary)).returncode == 0
        state = '{}' if name == 'absent-service' else value if isinstance(value, str) else json.dumps({'fastnet': {'instances': value if name == 'ambiguous-instances' else {'instance1': value}}})
        put('state.json', state)
        command = 'env PATH=' + quote(task + ':/usr/sbin:/usr/bin:/sbin:/bin') + ' QS_FASTNET_STATE=' + quote(task + '/state.json') + ' QS_FASTNET_FAIL=' + ('1' if name == 'ubus-failure' else '0') + ' /bin/sh ' + quote(task + '/entry.sh') + ' status'
        r = remote(command)
        if running is None:
            assert r.returncode != 0, name
        else:
            assert r.returncode == 0, name + ': ' + r.stderr
            try:
                result = json.loads(r.stdout)
            except ValueError:
                report['parseFailure'] = {'name': name, 'stdout': r.stdout.replace('fixture-secret', '[redacted]'), 'stderr': r.stderr.replace('fixture-secret', '[redacted]')}
                raise
            assert result['app'] == 'fastnet' and result['running'] is running, (name, result)
            assert result['deployed'] is (name != 'undeployed')
            assert result.get('web') == web, (name, result)
            assert result['href'] == '/cgi-bin/luci/admin/services/fastnet'
            assert 'fixture-secret' not in r.stdout
        report['cases'].append({'name': name, 'result': 'passed', 'exitCode': r.returncode})
    report['result'] = 'passed'
except Exception as e:
    report['result'] = 'failed'
    report['failure'] = str(e)
    raise
finally:
    report['temporaryFilesCleaned'] = remote('rm -rf ' + quote(task)).returncode == 0
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
