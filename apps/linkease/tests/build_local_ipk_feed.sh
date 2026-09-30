#!/usr/bin/env bash
set -euo pipefail

if (($# < 2)); then
	printf 'usage: %s OUTPUT_DIR IPK [IPK ...]\n' "$0" >&2
	exit 2
fi

output_dir=$1
shift
mkdir -p "$output_dir"
: >"$output_dir/Packages"

control_of() {
	local ipk=$1 member
	local -a inner_tar=(tar -xO --wildcards '*/control')
	if ar t "$ipk" >/dev/null 2>&1; then
		member=$(ar t "$ipk" | awk '/^control\.tar\./ { print; exit }')
	else
		member=$(tar -tf "$ipk" | awk '/control\.tar\./ { print; exit }')
	fi
	[[ -n "$member" ]]
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

for source_ipk in "$@"; do
	[[ -f "$source_ipk" ]] || {
		printf 'missing IPK: %s\n' "$source_ipk" >&2
		exit 1
	}
	filename=$(basename "$source_ipk")
	target_ipk="$output_dir/$filename"
	if [[ -e "$target_ipk" && "$source_ipk" -ef "$target_ipk" ]]; then
		:
	else
		cp "$source_ipk" "$target_ipk"
	fi
	control_of "$target_ipk" >>"$output_dir/Packages"
	printf 'Filename: %s\n' "$filename" >>"$output_dir/Packages"
	printf 'Size: %s\n' "$(stat -c %s "$target_ipk")" >>"$output_dir/Packages"
	printf 'SHA256sum: %s\n\n' "$(sha256sum "$target_ipk" | awk '{print $1}')" >>"$output_dir/Packages"
done

gzip -9n -c "$output_dir/Packages" >"$output_dir/Packages.gz"
printf 'built local feed with %d packages: %s\n' "$#" "$output_dir"
