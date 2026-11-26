#!/bin/sh
set -eu

root="$1"
host="${2:?missing public host}"
ctl="$root/private-control"
sid="$(ubus call session create '{"timeout":300}' | jsonfilter -e '@.ubus_rpc_session')"
test -n "$sid"
printf '%s' "$sid" >"$ctl/gateway.sid"
chmod 0600 "$ctl/gateway.sid"
payload="$(printf '{"ubus_rpc_session":"%s","values":{"username":"root"}}' "$sid")"
ubus call session set "$payload" >/dev/null

outer="linkease_openwrt_sid=$sid"
persist="$(curl -sS -b "$ctl/cookies.txt" -o /dev/null -w '%{http_code}' http://127.0.0.1:13080/)"
launch_url="$(awk '/dsh web:/ {print $3; exit}' "$ctl/web-prefix.log")"
launch="$(curl -sS -D "$ctl/prefix-launch.headers" -c "$ctl/prefix-dsh.cookies" \
  -H "Cookie: $outer" -o /dev/null -w '%{http_code}' "$launch_url")"
root_code="$(curl -sS -b "$ctl/prefix-dsh.cookies" -b "$outer" \
  -o "$ctl/prefix-root.html" -w '%{http_code}' "http://$host/apps/dsh/")"
asset="$(curl -sS -b "$ctl/prefix-dsh.cookies" -b "$outer" \
  -o "$ctl/prefix-asset.js" -w '%{http_code}' \
  "http://$host/apps/dsh/assets/index-Ciz7DZxv.js")"
bare="$(curl -sS -b "$ctl/prefix-dsh.cookies" -b "$outer" \
  -o /dev/null -w '%{http_code}' "http://$host/apps/dsh")"

rm -f "$ctl/prefix-ws.headers"
curl -sS --http1.1 --max-time 2 -b "$ctl/prefix-dsh.cookies" -b "$outer" \
  -D "$ctl/prefix-ws.headers" -o /dev/null \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  "http://$host/apps/dsh/api/remote.mux" >/dev/null 2>&1 || true
ws="$(head -1 "$ctl/prefix-ws.headers" | tr -d '\r')"

printf '%s\n' \
  "COOKIE_PERSIST_AFTER_RESTART=$persist" \
  "PREFIX_LAUNCH=$launch" \
  "PREFIX_ROOT=$root_code ROOT_BYTES=$(wc -c <"$ctl/prefix-root.html")" \
  "PREFIX_ASSET=$asset ASSET_BYTES=$(wc -c <"$ctl/prefix-asset.js")" \
  "BARE_PATH=$bare" \
  "WS_STATUS=$ws"
grep -i '^Set-Cookie:' "$ctl/prefix-launch.headers" \
  | sed -E 's#^([^=]+=)[^;]+#\1REDACTED#'
