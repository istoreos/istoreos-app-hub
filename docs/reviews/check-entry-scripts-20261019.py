#!/usr/bin/env python3
"""Read-only source review probes. All execution uses temporary dependency stubs.

Never runs a real Docker, init script, ubus or UCI command. Findings are observations,
not a release acceptance or a test that should stay red after fixes.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

if len(sys.argv) > 1 and sys.argv[1] == '--json':
    output = Path(os.environ['ENTRY_REVIEW_JSON'])
    value = json.loads(output.read_text())
    mode, key, item = sys.argv[2:5]
    value[key] = item if mode == 'string' else item == '1'
    output.write_text(json.dumps(value))
    raise SystemExit

ROOT = Path(__file__).resolve().parents[2]
IDS = ['baidudrive', 'oneapi', 'istorepanel', 'openwebui', 'pve', 'istoredup', 'agentflow',
       'openclawmgr', 'codeserver', 'ubuntu', 'istoreenhance', 'dockermanager', 'jellyfin',
       'uptimekuma', 'webvirtcloud', 'dpanel', 'kai', 'fastnet']
report = {'snapshot': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'scope': 'local isolated stubs only; no device or service commands', 'files': [], 'probes': []}
with tempfile.TemporaryDirectory(prefix='entry-review-') as directory:
    temp = Path(directory)
    helper = shlex.quote(sys.executable) + ' ' + shlex.quote(str(Path(__file__).resolve()))
    shim = temp / 'jshn.sh'
    shim.write_text('json_init(){ echo "{}" > "$ENTRY_REVIEW_JSON"; }\n'
                    'json_add_string(){ ' + helper + ' --json string "$1" "$2"; }\n'
                    'json_add_boolean(){ ' + helper + ' --json boolean "$1" "$2"; }\n'
                    'json_dump(){ cat "$ENTRY_REVIEW_JSON"; }\njson_cleanup(){ :; }\n')
    provider = temp / 'provider'
    provider.write_text('#!/bin/sh\ncase "$1" in\n'
                        'status) [ "$ENTRY_REVIEW_FAIL" != 1 ] || exit 17; printf "%s\\n" "$ENTRY_REVIEW_STATUS";;\n'
                        'port) printf "%s\\n" "$ENTRY_REVIEW_PORT";;\n'
                        'token) printf "%s\\n" fixture-token;;\n'
                        'start|stop) printf "%s\\n" "$1" >> "$ENTRY_REVIEW_ACTIONS";;\n'
                        '*) exit 9;;\nesac\n')
    provider.chmod(0o700)
    env = dict(os.environ, ENTRY_REVIEW_JSON=str(temp / 'json'), ENTRY_REVIEW_ACTIONS=str(temp / 'actions'),
               ENTRY_REVIEW_STATUS='running', ENTRY_REVIEW_PORT='43210', ENTRY_REVIEW_FAIL='0')
    copies = {}
    for app in IDS:
        source = ROOT / 'apps' / app / ('app-meta-' + app) / 'entry.sh'
        body = source.read_text()
        syntax = subprocess.run(['/bin/sh', '-n', str(source)], capture_output=True, text=True)
        meta = source.with_name('Makefile').read_text()
        bad_test = bool(re.search(r'"running"\]', body))
        report['files'].append({'app': app, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                'shSyntaxExitCode': syntax.returncode, 'missingTestBracketSpace': bad_test,
                                'hasMETA_UCI': bool(re.search(r'^META_UCI\s*[:?]?=', meta, re.M))})
        if 'ISTOREC_SCRIPT=' not in body:
            continue
        body = re.sub(r'^ISTOREC_SCRIPT=.*$', 'ISTOREC_SCRIPT=' + shlex.quote(str(provider)), body, count=1, flags=re.M)
        body = re.sub(r'^\[ -f /usr/libexec/istorec/jellyfin.sh \].*$', '', body, flags=re.M)
        body = body.replace('. /usr/share/libubox/jshn.sh', '. ' + shlex.quote(str(shim)))
        copy = temp / (app + '.sh')
        copy.write_text(body)
        copies[app] = copy
        # Failed status must not look like confirmed undeployed state.
        result = subprocess.run(['/bin/sh', str(copy), 'status', 'router.example'],
                                env={**env, 'ENTRY_REVIEW_FAIL': '1'}, capture_output=True, text=True)
        data = json.loads(result.stdout)
        report['probes'].append({'app': app, 'case': 'provider-status-fails', 'exitCode': result.returncode,
                                 'running': data.get('running'), 'deployed': data.get('deployed'),
                                 'issueReproduced': result.returncode == 0 and data.get('deployed') is False})
        if bad_test:
            for action, state in [('start', 'running'), ('stop', 'stopped')]:
                (temp / 'actions').write_text('')
                result = subprocess.run(['/bin/sh', str(copy), action], env={**env, 'ENTRY_REVIEW_STATUS': state}, capture_output=True, text=True)
                actions = (temp / 'actions').read_text().splitlines()
                report['probes'].append({'app': app, 'case': action + '-when-' + state, 'exitCode': result.returncode,
                                         'stubActions': actions, 'stderr': result.stderr.strip(),
                                         'issueReproduced': actions == [action] and ']' in result.stderr})
    # Compare href scheme with protocol used by Quickstart.
    result = subprocess.run(['/bin/sh', str(copies['ubuntu']), 'status', 'router.example'], env=env, capture_output=True, text=True)
    data = json.loads(result.stdout)
    report['probes'].append({'app': 'ubuntu', 'case': 'scheme-disagreement', 'href': data['href'],
                             'protocol': data['protocol'], 'issueReproduced': data['href'].startswith('https:') and data['protocol'] == 'http'})
    result = subprocess.run(['/bin/sh', str(copies['openclawmgr']), 'status', 'router.example'], env=env, capture_output=True, text=True)
    data = json.loads(result.stdout)
    report['probes'].append({'app': 'openclawmgr', 'case': 'web-vs-href-token',
                             'webHasToken': '#token=' in data['web'], 'hrefHasToken': '#token=' in data['href'],
                             'issueReproduced': '#token=' in data['href'] and '#token=' not in data['web']})
    docker = temp / 'docker'
    docker.write_text('#!/bin/sh\n[ "$1" = ps ] || exit 9\nprintf "%s\\n" "$*" >> "$ENTRY_REVIEW_ACTIONS"\n'
                      'case "$*" in\n*"name=^/htreader$"*) [ "$ENTRY_REVIEW_HTREADER" = 1 ] && echo "0.0.0.0:49060->9060/tcp";;\n'
                      '*"name=^/oneapi$"*) echo "0.0.0.0:43000->3000/tcp";;\n'
                      '*"name=^/openwebui$"*) echo "0.0.0.0:43080->8080/tcp";;\n'
                      '*"name=^/uptimekuma$"*) echo "0.0.0.0:43001->3001/tcp";;\n*) exit 9;;\nesac\n')
    docker.chmod(0o700)
    for app, expected in [('oneapi', '43000'), ('openwebui', '43080'), ('uptimekuma', '43001')]:
        source = ROOT / 'apps' / app / ('luci-app-' + app) / 'root/usr/libexec/istorec' / (app + '.sh')
        for other in ['0', '1']:
            (temp / 'actions').write_text('')
            result = subprocess.run(['/bin/sh', str(source), 'port'], env={**env, 'PATH': str(temp) + ':' + os.environ['PATH'], 'ENTRY_REVIEW_HTREADER': other}, capture_output=True, text=True)
            report['probes'].append({'app': app, 'case': 'actual-provider-port-with-htreader-' + other,
                                     'expectedPort': expected, 'actualPort': result.stdout.strip(),
                                     'stubDockerQueries': (temp / 'actions').read_text().splitlines(),
                                     'issueReproduced': result.stdout.strip() != expected})
report['temporaryFilesCleaned'] = not temp.exists()
destination = ROOT / 'docs/reviews/app-entry-scripts-20261019.json'
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'files': len(report['files']), 'syntaxPassed': sum(f['shSyntaxExitCode'] == 0 for f in report['files']),
                  'badTestFiles': [f['app'] for f in report['files'] if f['missingTestBracketSpace']],
                  'missingUCI': [f['app'] for f in report['files'] if not f['hasMETA_UCI']],
                  'probes': len(report['probes']), 'issuesReproduced': sum(p['issueReproduced'] for p in report['probes']),
                  'temporaryFilesCleaned': report['temporaryFilesCleaned']}))
