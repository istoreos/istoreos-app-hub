#!/usr/bin/env bash
set -euo pipefail

if (($# < 1 || $# > 2)); then
	printf 'usage: %s ASSET_DIR [VERSION]\n' "$0" >&2
	exit 2
fi

asset_dir=$1
version=${2:-1.7.6}
failures=0
checked=0

fail() {
	printf 'FAIL: %s\n' "$*" >&2
	failures=$((failures + 1))
}

check_archive() {
	local family=$1 arch=$2
	shift 2
	local root="${family}-${version}-linux-${arch}"
	local archive="${asset_dir}/${root}.tar.gz"
	local listing member
	local -a roots

	if [[ ! -s "$archive" ]]; then
		fail "missing or empty archive: $archive"
		return
	fi

	listing=$(tar -tzf "$archive") || {
		fail "cannot list archive: $archive"
		return
	}

	if grep -Eq '(^|/)\.\.(/|$)|^/' <<<"$listing"; then
		fail "$archive contains an unsafe path"
	fi

	mapfile -t roots < <(
		printf '%s\n' "$listing" |
			sed 's#^\./##' |
			cut -d/ -f1 |
			sed '/^$/d' |
			sort -u
	)
	if ((${#roots[@]} != 1)) || [[ ${roots[0]:-} != "$root" ]]; then
		fail "$archive: expected sole top-level directory $root, found ${roots[*]:-(none)}"
	fi

	for member in "$@"; do
		if ! grep -Fxq "${root}/${member}" <<<"$listing"; then
			fail "$archive: missing ${root}/${member}"
		fi
	done

	checked=$((checked + 1))
}

for arch in x86_64 aarch64 arm; do
	check_archive linkease-bin "$arch" linkease
	check_archive linkease-common-bin "$arch" heif-converter linkease-media
done

if [[ -f "$asset_dir/SHA256SUMS" ]]; then
	(
		cd "$asset_dir"
		sha256sum -c SHA256SUMS
	) || fail "$asset_dir/SHA256SUMS does not match the release archives"
else
	fail "missing checksum manifest: $asset_dir/SHA256SUMS"
fi

((failures == 0)) || exit 1
printf 'PASS: verified %d LinkEase runtime archives for version %s\n' "$checked" "$version"
