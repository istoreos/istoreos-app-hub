#!/bin/sh

set -eu

CONTAINER_NAME="dsh"
ROLLBACK_NAME="dsh-rollback"
STANDARD_IMAGE="ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2@sha256:a447bbfcafce5d05d1e9cc861c9170bb6907ef1e31ed53a40c588bd6e77d5705"
KEY_DIRECTORY="/etc/dsh"
KEY_FILE="$KEY_DIRECTORY/admin.key"

fail() {
	printf 'dsh: %s\n' "$*" >&2
	exit 1
}

uci_get() {
	uci -q get "dsh.@main[0].$1" 2>/dev/null || true
}

resolve_profile() {
	case "${1:-standard}" in
		standard|'') printf '%s\n' "$STANDARD_IMAGE" ;;
		*) fail "unsupported image profile: $1" ;;
	esac
}

validate_port() {
	case "$1" in ''|*[!0-9]*) return 1 ;; esac
	[ "${#1}" -le 5 ] && [ "$1" -ge 1024 ] && [ "$1" -le 65535 ]
}

ensure_admin_key() {
	umask 077
	if [ ! -f "$KEY_FILE" ]; then
		mkdir -p "$KEY_DIRECTORY"
		[ -d "$KEY_DIRECTORY" ] && [ ! -L "$KEY_DIRECTORY" ] || fail "invalid key directory"
		pending="$KEY_FILE.new"
		hexdump -n 32 -e '32/1 "%02x"' /dev/urandom > "$pending"
		[ "$(wc -c < "$pending" | tr -d ' ')" = 64 ] || {
			rm -f "$pending"
			fail "could not generate the DSH administrator key"
		}
		chmod 0600 "$pending"
		mv "$pending" "$KEY_FILE"
	fi
	[ -f "$KEY_FILE" ] && [ ! -L "$KEY_FILE" ] || fail "invalid administrator key file"
	[ "$(stat -c '%u' "$KEY_FILE" 2>/dev/null || true)" = 0 ] || fail "administrator key must be owned by root"
	chmod 0600 "$KEY_FILE"
	key_size="$(wc -c < "$KEY_FILE" | tr -d ' ')"
	case "$key_size" in ''|*[!0-9]*) fail "administrator key size could not be read" ;; esac
	[ "$key_size" -ge 12 ] && [ "$key_size" -le 4096 ] || fail "administrator key must contain 12 to 4096 bytes"
	if LC_ALL=C grep -q '[[:cntrl:]]' "$KEY_FILE"; then
		fail "administrator key must not contain control characters"
	fi
}

validate_storage_path() {
	path="$1"
	case "$path" in
		/mnt/*/*) ;;
		*) return 1 ;;
	esac
	case "$path" in
		*//*|*/../*|*/..|*/./*|*/.|*:*|*,*|*[[:space:]]*) return 1 ;;
	esac
	return 0
}

validate_trusted_hosts() {
	value="$1"
	[ -n "$value" ] || return 0
	[ "$value" = "*" ] && return 0
	case "$value" in
		*[!A-Za-z0-9.,:_%_-]*) return 1 ;;
	esac
	return 0
}

prepare_directory() {
	path="$1"
	created=0
	if [ ! -d "$path" ]; then
		mkdir -p "$path"
		created=1
	fi
	[ -d "$path" ] || fail "not a directory: $path"
	[ ! -L "$path" ] || fail "symbolic-link storage paths are not supported: $path"
	if [ "$created" = "1" ]; then
		chown 1000:1000 "$path"
		chmod 0750 "$path"
	else
		owner="$(stat -c '%u' "$path" 2>/dev/null || true)"
		[ "$owner" = "1000" ] || fail "existing directory must be owned by UID 1000: $path"
	fi
}

timezone() {
	value="$(uci -q get system.@system[0].zonename 2>/dev/null || true)"
	[ -n "$value" ] || value="UTC"
	printf '%s\n' "$(printf '%s' "$value" | tr ' ' '_')"
}

trusted_hosts() {
	extra="$1"
	hostname_value="$(uci -q get system.@system[0].hostname 2>/dev/null || true)"
	value="localhost,127.0.0.1"
	if [ -n "$hostname_value" ]; then
		value="$value,$hostname_value,$hostname_value.lan"
	fi
	if command -v ip >/dev/null 2>&1; then
		for address in $(ip -o -4 addr show scope global 2>/dev/null | awk '{sub(/\/.*/, "", $4); print $4}'); do
			[ -z "$address" ] || value="$value,$address"
		done
	fi
	case "$extra" in
		''|'*') ;;
		*) value="$value,$extra" ;;
	esac
	printf '%s\n' "$value"
}

container_exists() {
	docker container inspect "$1" >/dev/null 2>&1
}

restore_previous() {
	docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
	if container_exists "$ROLLBACK_NAME"; then
		docker rename "$ROLLBACK_NAME" "$CONTAINER_NAME" >/dev/null
		docker start "$CONTAINER_NAME" >/dev/null
	fi
}

wait_healthy() {
	count=0
	while [ "$count" -lt 60 ]; do
		state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || true)"
		case "$state" in
			healthy) return 0 ;;
			unhealthy|exited|dead) return 1 ;;
		esac
		count=$((count + 1))
		sleep 2
	done
	return 1
}

do_install() {
	command -v docker >/dev/null 2>&1 || fail "docker is not installed"
	docker info >/dev/null 2>&1 || fail "docker daemon is not available"

	profile="$(uci_get image_profile)"
	[ -n "$profile" ] || profile="standard"
	image="$(resolve_profile "$profile")"
	port="$(uci_get port)"
	[ -n "$port" ] || port="13080"
	data_path="$(uci_get data_path)"
	workspace_path="$(uci_get workspace_path)"
	extra_hosts="$(uci_get extra_trusted_hosts)"

	validate_port "$port" || fail "port must be between 1024 and 65535"
	validate_storage_path "$data_path" || fail "data path must be a dedicated directory below /mnt"
	validate_storage_path "$workspace_path" || fail "workspace path must be a dedicated directory below /mnt"
	[ "$data_path" != "$workspace_path" ] || fail "data and workspace paths must be different"
	validate_trusted_hosts "$extra_hosts" || fail "extra trusted hosts contain unsupported characters"
	ensure_admin_key

	prepare_directory "$workspace_path"
	prepare_directory "$data_path"

	printf 'Pulling pinned DSH image: %s\n' "$image"
	docker pull "$image"
	admin_key="$(cat "$KEY_FILE")"

	docker rm -f "$ROLLBACK_NAME" >/dev/null 2>&1 || true
	if container_exists "$CONTAINER_NAME"; then
		if ! docker stop -t 20 "$CONTAINER_NAME" >/dev/null; then
			fail "failed to stop the current DSH container"
		fi
		if ! docker rename "$CONTAINER_NAME" "$ROLLBACK_NAME" >/dev/null; then
			docker start "$CONTAINER_NAME" >/dev/null 2>&1 || true
			fail "failed to prepare the current DSH container for rollback"
		fi
	fi

	if ! docker run -d \
		--name "$CONTAINER_NAME" \
		--hostname dsh-workbench \
		--label "io.istore.dsh.profile=$profile" \
		--restart unless-stopped \
		--init \
		--read-only \
		--cap-drop ALL \
		--security-opt no-new-privileges:true \
		--stop-timeout 20 \
		--pids-limit 1024 \
		--publish "$port:3080" \
		--env "DSH_HOME=/home/node/.dsh" \
		--env "DSH_CONTAINER_KEY=$admin_key" \
		--env "DSH_PERMISSION_MODE=danger-full-access" \
		--env "DSH_TELEMETRY_DISABLED=1" \
		--env "DSH_CONTAINER_TRUSTED_HOSTS=$(trusted_hosts "$extra_hosts")" \
		--env "NODE_USE_ENV_PROXY=1" \
		--env "TZ=$(timezone)" \
		--tmpfs /tmp:rw,exec,nosuid,nodev,size=512m,mode=1777 \
		--mount "type=bind,src=$workspace_path,dst=/home/node" \
		--mount "type=bind,src=$data_path,dst=/home/node/.dsh" \
		"$image"; then
		unset admin_key
		restore_previous
		fail "failed to create DSH container; previous container restored"
	fi
	unset admin_key

	if ! wait_healthy; then
		restore_previous
		fail "DSH health check failed; previous container restored (startup logs are not copied because they may contain a launch token)"
	fi

	docker rm -f "$ROLLBACK_NAME" >/dev/null 2>&1 || true
	legacy_index="$data_path/.istoreos/dsh-index.html"
	if [ -f "$legacy_index" ] && [ ! -L "$legacy_index" ]; then
		rm -f "$legacy_index"
		rmdir "$data_path/.istoreos" 2>/dev/null || true
	fi
	printf 'DSH is healthy on the dedicated authenticated port.\n'
}

do_port() {
	bindings="$(docker inspect --format '{{range (index .NetworkSettings.Ports "3080/tcp")}}{{printf "%s %s\n" .HostIp .HostPort}}{{end}}' "$CONTAINER_NAME")" || return 1
	port=""
	while read -r address candidate extra; do
		[ -n "$address$candidate$extra" ] || continue
		[ -z "$extra" ] || return 1
		case "$address" in 0.0.0.0|::) ;; *) return 1 ;; esac
		validate_port "$candidate" || return 1
		[ -z "$port" ] || [ "$port" = "$candidate" ] || return 1
		port="$candidate"
	done <<EOF
$bindings
EOF
	[ -z "$port" ] || printf '%s\n' "$port"
}

do_address() {
	docker inspect --format '{{range (index .NetworkSettings.Ports "3080/tcp")}}{{println .HostIp}}{{end}}' "$CONTAINER_NAME" 2>/dev/null | awk 'NF {print; exit}'
}

do_key_status() {
	if [ -f "$KEY_FILE" ] && [ ! -L "$KEY_FILE" ]; then
		printf 'configured\n'
	else
		printf 'missing\n'
	fi
}

usage() {
	printf '%s\n' \
		"usage: $0 sub-command" \
		"sub-commands: install upgrade rm start stop restart status health port address key-status image profile"
}

ACTION="${1:-}"
case "$ACTION" in
	install|upgrade) do_install ;;
	rm) docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true ;;
	start|stop) docker "$ACTION" "$CONTAINER_NAME" ;;
	restart) do_install ;;
	status) docker inspect --format '{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || true ;;
	health) docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || true ;;
	port) do_port ;;
	address) do_address ;;
	key-status) do_key_status ;;
	image) docker inspect --format '{{.Config.Image}}' "$CONTAINER_NAME" 2>/dev/null || true ;;
	profile) docker inspect --format '{{index .Config.Labels "io.istore.dsh.profile"}}' "$CONTAINER_NAME" 2>/dev/null || true ;;
	*) usage; exit 1 ;;
esac
