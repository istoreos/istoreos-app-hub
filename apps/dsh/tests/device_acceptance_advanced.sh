#!/bin/sh

set -eu

CORE=dsh
GATEWAY=dsh-gateway
RUNTIME=/usr/libexec/istorec/dsh.sh
KEY_FILE=/etc/dsh/admin.key
EXPECTED_IMAGE_AMD64='ghcr.io/runzhliu/deepseek-harness:0.2.3-alpha.2-r1@sha256:7d2ff641998577439b5b662db3d048ea3e60cd86441b91c3cc2d74ab9fcf72f7'
EXPECTED_IMAGE_ARM64='ghcr.io/runzhliu/deepseek-harness:0.2.3-alpha.2-r1@sha256:7b20e5080a8d7f7df2fb5c1f3dddf2bebd76a5cab545392b5e82735cd1197a79'
LAN_HOST=127.0.0.1
temporary=''

fail() {
	printf 'dsh advanced acceptance: %s\n' "$*" >&2
	exit 1
}

cleanup() {
	case "$temporary" in
		/tmp/dsh-advanced-acceptance.*) rm -rf "$temporary" ;;
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
[ -x "$RUNTIME" ] || fail 'missing runtime helper'
[ "$($RUNTIME profile)" = advanced ] || fail 'advanced profile is not active'
[ "$($RUNTIME status)" = running ] || fail 'deployment is not running'
[ "$($RUNTIME health)" = healthy ] || fail 'deployment is not healthy'
[ "$($RUNTIME key-status)" = configured ] || fail 'administrator key is missing'
[ -f "$KEY_FILE" ] && [ ! -L "$KEY_FILE" ] || fail 'administrator key is not a regular file'
[ "$(stat -c '%a %u' "$KEY_FILE")" = '600 0' ] || fail 'administrator key permissions are not 0600/root'

case "$(uname -m)" in
	x86_64|amd64) expected_image="$EXPECTED_IMAGE_AMD64" ;;
	aarch64|arm64) expected_image="$EXPECTED_IMAGE_ARM64" ;;
	*) fail 'unsupported test architecture' ;;
esac
[ "$($RUNTIME image)" = "$expected_image" ] || fail 'advanced image reference drifted'

port="$($RUNTIME port)"
[ "$port" = "$(uci -q get dsh.@main[0].port)" ] || fail 'published and configured ports differ'
[ "$($RUNTIME address)" = 0.0.0.0 ] || fail 'gateway is not listening on all interfaces'
[ "$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$CORE")" = '{}' ] || fail 'core ports are published to the host'
[ "$(docker inspect -f '{{.HostConfig.ReadonlyRootfs}}' "$CORE")" = true ] || fail 'core rootfs is writable'
[ "$(docker inspect -f '{{json .HostConfig.CapDrop}}' "$CORE")" = '["ALL"]' ] || fail 'core cap-drop is not ALL'
[ "$(docker inspect -f '{{.HostConfig.ShmSize}}' "$CORE")" = 1073741824 ] || fail 'core shm size is not 1 GiB'
[ "$(docker inspect -f '{{.HostConfig.ReadonlyRootfs}}' "$GATEWAY")" = true ] || fail 'gateway rootfs is writable'
[ "$(docker inspect -f '{{json .HostConfig.CapDrop}}' "$GATEWAY")" = '["ALL"]' ] || fail 'gateway cap-drop is not ALL'
[ "$(docker inspect -f '{{json .HostConfig.CapAdd}}' "$GATEWAY")" = '["NET_BIND_SERVICE"]' ] || fail 'gateway cap-add is not limited to NET_BIND_SERVICE'
docker inspect -f '{{json .HostConfig.SecurityOpt}}' "$CORE" | grep -q no-new-privileges || fail 'core no-new-privileges is missing'
docker inspect -f '{{json .HostConfig.SecurityOpt}}' "$GATEWAY" | grep -q no-new-privileges || fail 'gateway no-new-privileges is missing'
if docker inspect -f '{{range .Mounts}}{{println .Destination}}{{end}}' "$CORE" | grep -q /var/run/docker.sock; then
	fail 'core has the Docker socket mounted'
fi
docker exec "$GATEWAY" printenv DSH_PASSWORD_HASH >/dev/null || fail 'gateway password hash is missing'
docker exec "$GATEWAY" printenv DSH_LAUNCH_TOKEN >/dev/null || fail 'gateway launch token is missing'

BASE_URL="http://$LAN_HOST:$port"
temporary="$(mktemp -d /tmp/dsh-advanced-acceptance.XXXXXX)"
jar="$temporary/cookies"
headers="$temporary/headers"

unauth="$(curl -sS -D "$headers" -o /dev/null -w '%{http_code}' -H 'Accept: text/html' "$BASE_URL/")"
[ "$unauth" = 401 ] || fail "unauthenticated root status is $unauth"
grep -qi '^Www-Authenticate: Basic.*DSH administrator' "$headers" \
	|| fail 'unauthenticated root does not request the DSH administrator key'
revision="$(docker exec "$CORE" printenv DSH_NOVNC_ASSET_REVISION)"
case "$revision" in ''|*[!A-Za-z0-9._-]*) fail 'invalid noVNC asset revision' ;; esac
desktop_path="/novnc-$revision/vnc.html"
desktop_unauth="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL$desktop_path")"
[ "$desktop_unauth" = 401 ] || fail "unauthenticated noVNC status is $desktop_unauth"

auth="dsh:$(cat "$KEY_FILE")"
exchange="$(curl -sS -u "$auth" -c "$jar" -D "$headers" -o /dev/null -w '%{http_code}' "$BASE_URL/")"
case "$exchange" in 302|303) ;; *) fail "launch-token exchange status is $exchange" ;; esac
grep -qi '^Set-Cookie:' "$headers" || fail 'launch-token exchange did not issue a cookie'

root_status="$(curl -sS -u "$auth" -b "$jar" -o "$temporary/root.html" -w '%{http_code}' "$BASE_URL/")"
[ "$root_status" = 200 ] || fail "authenticated root status is $root_status"
assets="$temporary/assets.txt"
grep -oE '(src|href)="[^"]+"' "$temporary/root.html" |
	sed -e 's/^[^=]*="//' -e 's/"$//' -e 's/&amp;/\&/g' > "$assets"
asset_count=0
while IFS= read -r asset; do
	case "$asset" in
		''|'./') continue ;;
		/*) url="$BASE_URL$asset" ;;
		./*) url="$BASE_URL/${asset#./}" ;;
		*) url="$BASE_URL/$asset" ;;
	esac
	status="$(curl -sS -u "$auth" -b "$jar" --path-as-is -o /dev/null -w '%{http_code}' "$url")"
	[ "$status" = 200 ] || fail "authenticated asset returned $status: $asset"
	asset_count=$((asset_count + 1))
done < "$assets"
[ "$asset_count" -ge 4 ] || fail "only $asset_count page assets were discovered"
desktop_status="$(curl -sS -u "$auth" -b "$jar" -o /dev/null -w '%{http_code}' "$BASE_URL$desktop_path")"
[ "$desktop_status" = 200 ] || fail "authenticated noVNC status is $desktop_status"

websocket_headers="$temporary/websocket.headers"
curl -sS -u "$auth" -b "$jar" --http1.1 --max-time 2 -o /dev/null -D "$websocket_headers" \
	-H 'Connection: Upgrade' -H 'Upgrade: websocket' \
	-H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
	-H "Origin: $BASE_URL" "$BASE_URL/novnc-$revision/websockify" >/dev/null 2>&1 || true
websocket="$(awk 'NR == 1 {print $2}' "$websocket_headers")"
[ "$websocket" = 101 ] || fail "noVNC WebSocket status is $websocket"
unset auth

docker exec "$CORE" node -e "fetch('http://127.0.0.1:9222/json/version').then(r=>{if(!r.ok)process.exit(1)})" \
	|| fail 'Chromium CDP is unavailable'
chromium="$(docker exec "$CORE" chromium-docker --version)"
[ -n "$chromium" ] || fail 'Chromium version is unavailable'

printf 'FINAL_DSH_ADVANCED_ACCEPTANCE=PASS health=healthy port=%s auth=%s root=%s assets=%s novnc_unauth=%s novnc=%s websocket=%s chromium=ready\n' \
	"$port" "$unauth" "$root_status" "$asset_count" "$desktop_unauth" "$desktop_status" "$websocket"
