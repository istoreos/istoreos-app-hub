#!/usr/bin/env bash
set -euo pipefail

if (($# == 0)); then
	printf 'usage: %s ARTIFACT_DIR [ARTIFACT_DIR ...]\n' "$0" >&2
	exit 2
fi

failures=0

fail() {
	printf 'FAIL: %s\n' "$*" >&2
	failures=$((failures + 1))
}

control_of() {
	local ipk=$1
	local member
	local -a inner_tar=(tar -xO --wildcards '*/control')
	if ar t "$ipk" >/dev/null 2>&1; then
		member=$(ar t "$ipk" | awk '/^control\.tar\./ { print; exit }')
		[[ -n "$member" ]] || return 1
	else
		member=$(tar -tf "$ipk" | awk '/control\.tar\./ { print; exit }')
		[[ -n "$member" ]] || return 1
	fi
	case "$member" in
		*.gz) inner_tar=(tar -xzO --wildcards '*/control') ;;
		*.xz) inner_tar=(tar -xJO --wildcards '*/control') ;;
		*.bz2) inner_tar=(tar -xjO --wildcards '*/control') ;;
		*.zst) inner_tar=(tar --zstd -xO --wildcards '*/control') ;;
	esac
	if ar t "$ipk" >/dev/null 2>&1; then
		ar p "$ipk" "$member" | "${inner_tar[@]}" 2>/dev/null
	else
		tar -xOf "$ipk" "$member" | "${inner_tar[@]}" 2>/dev/null
	fi
}

data_list_of() {
	local ipk=$1
	local member
	local -a inner_tar=(tar -t)
	if ar t "$ipk" >/dev/null 2>&1; then
		member=$(ar t "$ipk" | awk '/^data\.tar\./ { print; exit }')
		[[ -n "$member" ]] || return 1
	else
		member=$(tar -tf "$ipk" | awk '/data\.tar\./ { print; exit }')
		[[ -n "$member" ]] || return 1
	fi
	case "$member" in
		*.gz) inner_tar=(tar -tz) ;;
		*.xz) inner_tar=(tar -tJ) ;;
		*.bz2) inner_tar=(tar -tj) ;;
		*.zst) inner_tar=(tar --zstd -t) ;;
	esac
	if ar t "$ipk" >/dev/null 2>&1; then
		ar p "$ipk" "$member" | "${inner_tar[@]}" 2>/dev/null
	else
		tar -xOf "$ipk" "$member" | "${inner_tar[@]}" 2>/dev/null
	fi | sed -e 's#^\./#/#' -e 's#/$##'
}

one_ipk() {
	local root=$1 package=$2
	find "$root" -type f -name "${package}_*.ipk" -print -quit
}

check_control_field() {
	local control=$1 pattern=$2 label=$3
	printf '%s\n' "$control" | grep -Eq "$pattern" || fail "$label"
}

for root in "$@"; do
	[[ -d "$root" ]] || { fail "artifact directory is missing: $root"; continue; }
	common=$(one_ipk "$root" linkease-common-bin)
	linkease=$(one_ipk "$root" linkease)
	[[ -n "$common" ]] || { fail "linkease-common-bin IPK is missing in $root"; continue; }
	[[ -n "$linkease" ]] || { fail "linkease IPK is missing in $root"; continue; }

	common_control=$(control_of "$common")
	linkease_control=$(control_of "$linkease")
	check_control_field "$common_control" '^Package: linkease-common-bin$' "$common: wrong Package"
	check_control_field "$common_control" '^Version: 1\.7\.6~[^-[:space:]]+-r1$' "$common: wrong Version"
	check_control_field "$common_control" '^Replaces: linkease \(<< 1\.7\.6~\)$' "$common: missing versioned Replaces"
	if printf '%s\n' "$common_control" | grep -q '^Conflicts:'; then
		fail "$common: Conflicts must not block the transition"
	fi
	check_control_field "$linkease_control" '^Package: linkease$' "$linkease: wrong Package"
	check_control_field "$linkease_control" '^Version: 1\.7\.6~[^-[:space:]]+-r1$' "$linkease: wrong Version"
	check_control_field "$linkease_control" '^Depends: .*linkease-common-bin \(>=[[:space:]]*1\.7\.6~\)' "$linkease: missing versioned common dependency"

	common_files=$(data_list_of "$common")
	linkease_files=$(data_list_of "$linkease")
	for path in /usr/sbin/heif-converter /usr/sbin/linkease-config.sh /usr/sbin/linkease-media; do
		printf '%s\n' "$common_files" | grep -qx "$path" || fail "$common: does not own $path"
		if printf '%s\n' "$linkease_files" | grep -qx "$path"; then
			fail "$linkease: still owns $path"
		fi
	done

	full=$(one_ipk "$root" linkeasefull)
	if [[ -n "$full" ]]; then
		full_control=$(control_of "$full")
		check_control_field "$full_control" '^Version: 3\.0\.22~[^-[:space:]]+-r2$' "$full: wrong Version"
		check_control_field "$full_control" '^Depends: .*linkease-common-bin \(>=[[:space:]]*1\.7\.6~\)' "$full: missing versioned common dependency"
	fi

	transition=$(one_ipk "$root" linkease-runtime-transition)
	if [[ -n "$transition" ]]; then
		control=$(control_of "$transition")
		check_control_field "$control" '^Version: 1\.7\.6-r1$' "$transition: wrong Version"
		check_control_field "$control" '^Depends: .*linkease \(>=[[:space:]]*1\.7\.6~\)' "$transition: missing versioned LinkEase dependency"
		check_control_field "$control" '^Depends: .*luci-lib-linkeasefile \(>=[[:space:]]*2\.1\.70-r4\)' "$transition: missing versioned LuCI handoff dependency"
	fi

	for spec in 'app-meta-linkease:3\.0\.0-r3' 'app-meta-linkeasefull:3\.0\.22-r3'; do
		IFS=: read -r package version <<<"$spec"
		ipk=$(one_ipk "$root" "$package")
		[[ -n "$ipk" ]] || continue
		control=$(control_of "$ipk")
		check_control_field "$control" "^Version: ${version}$" "$ipk: wrong Version"
		check_control_field "$control" '^Depends: .*linkease-runtime-transition' "$ipk: missing transition dependency"
		if printf '%s\n' "$control" | grep -Eq '^Depends: .*\([<>]?='; then
			fail "$ipk: exposes a version expression to the is-opkg meta hook"
		fi
	done

	luci_library=$(one_ipk "$root" luci-lib-linkeasefile)
	if [[ -n "$luci_library" ]]; then
		control=$(control_of "$luci_library")
		check_control_field "$control" '^Version: 2\.1\.70-r4$' "$luci_library: wrong Version"
		check_control_field "$control" '^Replaces: luci-app-linkease \(<< 2\.1\.70-r4\)$' "$luci_library: missing versioned Replaces"
	fi

	luci_app=$(one_ipk "$root" luci-app-linkease)
	if [[ -n "$luci_app" ]]; then
		control=$(control_of "$luci_app")
		check_control_field "$control" '^Version: 2\.1\.70-r4$' "$luci_app: wrong Version"
		check_control_field "$control" '^Depends: .*luci-lib-linkeasefile \(>= 2\.1\.70-r4\)' "$luci_app: missing versioned library dependency"
	fi

	printf 'PASS: %s\n' "$root"
done

((failures == 0)) || exit 1
