#!/usr/bin/env bash

set -uo pipefail

target=${1:-root@192.168.30.244}
minimum_version=1.7.6~

ssh -o BatchMode=yes -o ConnectTimeout=8 "$target" 'sh -s' -- "$minimum_version" <<'REMOTE'
minimum_version=$1
failed=0

package_version() {
	opkg status "$1" 2>/dev/null | sed -n 's/^Version: //p' | head -n 1
}

assert_minimum_version() {
	package=$1
	version=$(package_version "$package")
	if [ -z "$version" ]; then
		echo "RED: $package is not installed"
		failed=1
		return
	fi
	if opkg compare-versions "$version" '>=' "$minimum_version"; then
		echo "OK: $package $version >= $minimum_version"
	else
		echo "RED: $package $version < $minimum_version"
		failed=1
	fi
}

assert_exclusive_owner() {
	path=$1
	common_files=$(opkg files linkease-common-bin 2>/dev/null || true)
	linkease_files=$(opkg files linkease 2>/dev/null || true)
	if ! printf '%s\n' "$common_files" | grep -Fqx "$path"; then
		echo "RED: $path is absent from the linkease-common-bin file list"
		failed=1
		return
	fi
	if printf '%s\n' "$linkease_files" | grep -Fqx "$path"; then
		echo "RED: $path is still listed by linkease"
		failed=1
		return
	fi
	echo "OK: $path is owned exclusively by linkease-common-bin"
}

assert_minimum_version linkease
assert_minimum_version linkease-common-bin

common_control=$(cat /usr/lib/opkg/info/linkease-common-bin.control 2>/dev/null || true)
if printf '%s\n' "$common_control" | grep -Fqx 'Replaces: linkease (<< 1.7.6~)'; then
	echo 'OK: linkease-common-bin declares the legacy package replacement boundary'
else
	echo 'RED: linkease-common-bin lacks Replaces: linkease (<< 1.7.6~)'
	failed=1
fi

assert_exclusive_owner /usr/sbin/heif-converter
assert_exclusive_owner /usr/sbin/linkease-config.sh
assert_exclusive_owner /usr/sbin/linkease-media

exit "$failed"
REMOTE
