#!/bin/sh

set -eu

CONTAINER=dsh
RUNTIME=/usr/libexec/istorec/dsh.sh
KEY_FILE=/etc/dsh/admin.key
EXPECTED_IMAGE='ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2@sha256:a447bbfcafce5d05d1e9cc861c9170bb6907ef1e31ed53a40c588bd6e77d5705'
GATEWAY='http://127.0.0.1:19290'
LAN_HOST='127.0.0.1'
temporary=''

fail() {
	printf 'dsh acceptance: %s\n' "$*" >&2
	exit 1
}

cleanup() {
	case "$temporary" in
		/tmp/dsh-acceptance.*) rm -rf "$temporary" ;;
	esac
}
trap cleanup EXIT

while [ "$#" -gt 0 ]; do
	case "$1" in
		--lan-host)
			[ "$#" -ge 2 ] || fail '--lan-host requires an address'
			LAN_HOST="$2"
			shift 2
			;;
		*) fail "unknown argument: $1" ;;
	esac
done

for command in docker curl awk grep sed mktemp stat uci; do
	command -v "$command" >/dev/null 2>&1 || fail "missing command: $command"
done
[ -x "$RUNTIME" ] || fail "missing runtime helper: $RUNTIME"
[ "$($RUNTIME health)" = healthy ] || fail 'container is not healthy'
port="$($RUNTIME port)"
configured_port="$(uci -q get dsh.@main[0].port)"
[ -n "$port" ] || fail 'published port could not be resolved'
[ "$port" = "$configured_port" ] || fail 'container and UCI ports do not match'
[ "$($RUNTIME address)" = '0.0.0.0' ] || fail 'container is not listening on all interfaces'
[ "$($RUNTIME key-status)" = configured ] || fail 'administrator key is missing'
[ -f "$KEY_FILE" ] && [ ! -L "$KEY_FILE" ] || fail 'administrator key is not a regular file'
[ "$(stat -c '%a %u' "$KEY_FILE")" = '600 0' ] || fail 'administrator key permissions are not 0600/root'
[ "$($RUNTIME image)" = "$EXPECTED_IMAGE" ] || fail 'image reference drifted'
[ "$(docker inspect -f '{{.Config.User}}' "$CONTAINER")" = node ] || fail 'container user is not node'
[ "$(docker inspect -f '{{.HostConfig.ReadonlyRootfs}}' "$CONTAINER")" = true ] || fail 'rootfs is writable'
[ "$(docker inspect -f '{{.HostConfig.Privileged}}' "$CONTAINER")" = false ] || fail 'container is privileged'
[ "$(docker inspect -f '{{json .HostConfig.CapDrop}}' "$CONTAINER")" = '["ALL"]' ] || fail 'cap-drop is not ALL'
docker inspect -f '{{json .HostConfig.SecurityOpt}}' "$CONTAINER" | grep -q 'no-new-privileges' || fail 'no-new-privileges is missing'
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" | grep -q '^DSH_CONTAINER_KEY=.' || fail 'container authentication is disabled'
if docker inspect -f '{{range .Mounts}}{{println .Destination}}{{end}}' "$CONTAINER" | grep -Eq '/var/run/docker.sock|dsh-web-frontend/dist/index.html'; then
	fail 'container has an unsafe or compatibility-only mount'
fi

BASE_URL="http://$LAN_HOST:$port"
temporary="$(mktemp -d /tmp/dsh-acceptance.XXXXXX)"
jar="$temporary/cookies"
headers="$temporary/headers"

unauth="$(curl -sS -D "$headers" -o /dev/null -w '%{http_code}' \
	-H 'Accept: text/html' -H 'Sec-Fetch-Mode: navigate' "$BASE_URL/")"
[ "$unauth" = 303 ] || fail "unauthenticated root status is $unauth, expected 303"
grep -qi '^Location: /_dsh-container/auth/login' "$headers" || fail 'unauthenticated root does not open the DSH login'
grep -qi '^Cache-Control:.*no-store' "$headers" || fail 'unauthenticated root is cacheable'
asset_unauth="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL/auth-bootstrap.js")"
[ "$asset_unauth" = 401 ] || fail "unauthenticated asset status is $asset_unauth, expected 401"

login="$(curl -sS -c "$jar" -D "$headers" -o /dev/null -w '%{http_code}' -X POST \
	--data-urlencode "key@$KEY_FILE" --data-urlencode 'next=/' \
	"$BASE_URL/_dsh-container/auth/login")"
[ "$login" = 303 ] || fail "administrator-key login status is $login, expected 303"
grep -qi '^Set-Cookie: dsh_container_session=' "$headers" || fail 'login did not issue a protected session'

root="$temporary/root.html"
root_status="$(curl -sS -b "$jar" -D "$headers" -o "$root" -w '%{http_code}' "$BASE_URL/")"
[ "$root_status" = 200 ] || fail "authenticated root status is $root_status"
grep -q 'src="/auth-bootstrap.js"' "$root" || fail 'native root HTML no longer contains the expected bootstrap path'
bootstrap="$(curl -sS -b "$jar" -o /dev/null -w '%{http_code}' "$BASE_URL/auth-bootstrap.js")"
[ "$bootstrap" = 200 ] || fail "authenticated root bootstrap status is $bootstrap"

assets="$temporary/assets.txt"
grep -oE '(src|href)="[^"]+"' "$root" |
	sed -e 's/^[^=]*="//' -e 's/"$//' -e 's/&amp;/\&/g' > "$assets"
asset_count=0
while IFS= read -r asset; do
	case "$asset" in
		''|'./') continue ;;
		/*) url="$BASE_URL$asset" ;;
		./*) url="$BASE_URL/${asset#./}" ;;
		*) url="$BASE_URL/$asset" ;;
	esac
	status="$(curl -sS -b "$jar" --path-as-is -o /dev/null -w '%{http_code}' "$url")"
	[ "$status" = 200 ] || fail "asset returned $status: $asset"
	asset_count=$((asset_count + 1))
done < "$assets"
[ "$asset_count" -ge 10 ] || fail "only $asset_count page assets were discovered"

websocket_headers="$temporary/websocket.headers"
curl -sS -b "$jar" --http1.1 --max-time 2 -o /dev/null -D "$websocket_headers" \
	-H 'Connection: Upgrade' -H 'Upgrade: websocket' \
	-H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
	"$BASE_URL/api/remote.mux" >/dev/null 2>&1 || true
websocket="$(awk 'NR == 1 {print $2}' "$websocket_headers")"
[ "$websocket" = 101 ] || fail "WebSocket status is $websocket, expected 101"

launcher_headers="$temporary/launcher.headers"
launcher="$(curl -sS -D "$launcher_headers" -o /dev/null -w '%{http_code}' -H "Host: $LAN_HOST" "$GATEWAY/apps/dsh/")"
[ "$launcher" = 307 ] || fail "launcher status is $launcher, expected 307"
grep -qi "^Location: http://$LAN_HOST:$port/" "$launcher_headers" || fail 'launcher does not target the dedicated root port'
legacy_asset="$(curl -sS -o /dev/null -w '%{http_code}' -H "Host: $LAN_HOST" "$GATEWAY/apps/dsh/auth-bootstrap.js")"
[ "$legacy_asset" = 404 ] || fail "legacy subpath asset status is $legacy_asset, expected 404"

printf 'FINAL_DSH_DEVICE_ACCEPTANCE=PASS health=healthy port=%s auth=%s root=%s bootstrap=%s assets=%s websocket=%s launcher=%s legacy_subpath=%s\n' \
	"$port" "$unauth" "$root_status" "$bootstrap" "$asset_count" "$websocket" "$launcher" "$legacy_asset"
