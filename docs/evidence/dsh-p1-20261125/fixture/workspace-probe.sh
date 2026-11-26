#!/bin/sh
set -eu

root="$1"
host="${2:?missing public host}"
phase="${3:?missing phase}"
workspace="$root/workspace"
ctl="$root/private-control"
sid="$(cat "$ctl/gateway.sid")"
outer="linkease_openwrt_sid=$sid"
payload="$(printf '{"type":"client-request","rpcId":"p1-%s","method":"workspace/create","payload":{"args":{"request":{"path":"%s"}}}}' "$phase" "$workspace")"
response="$ctl/workspace-$phase.json"
code="$(curl -sS -b "$ctl/prefix-dsh.cookies" -b "$outer" \
  -H 'Content-Type: application/json' -X POST --data "$payload" \
  -o "$response" -w '%{http_code}' "http://$host/apps/dsh/api/workspace/create")"
ok="$(jsonfilter -i "$response" -e '@.result.ok' 2>/dev/null || true)"
workspace_id="$(jsonfilter -i "$response" -e '@.result.value.workspace.workspaceId' 2>/dev/null || true)"
directory="$(jsonfilter -i "$response" -e '@.result.value.workspace.path' 2>/dev/null || true)"
test "$code" = 200
test "$ok" = true
test -n "$workspace_id"
test "$directory" = "$workspace"
printf '%s' "$workspace_id" >"$ctl/workspace-$phase.id"
chmod 0600 "$response" "$ctl/workspace-$phase.id"
printf 'WORKSPACE_RPC=%s OK=%s DIRECTORY=%s ID_REDACTED\n' "$code" "$ok" "$directory"
