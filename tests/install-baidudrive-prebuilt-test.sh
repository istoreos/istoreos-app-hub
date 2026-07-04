#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP_DIR=${TMPDIR:-/tmp}/install-baidudrive-prebuilt-test.$$

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

mkdir -p \
  "$TMP_DIR/src/baidudrive-binary-test/nas_sdk/x86_64" \
  "$TMP_DIR/src/baidudrive-binary-test/glibc/x86_64/lib64" \
  "$TMP_DIR/src/baidudrive-binary-test/glibc/x86_64/lib/x86_64-linux-gnu"

printf '#!/bin/sh\n' > "$TMP_DIR/src/baidudrive-binary-test/baidudrive.x86_64"
printf '#!/bin/sh\n' > "$TMP_DIR/src/baidudrive-binary-test/nas_sdk/x86_64/baiduNas"
printf '#!/bin/sh\n' > "$TMP_DIR/src/baidudrive-binary-test/nas_sdk/x86_64/P2PClient.bin"
printf 'kernel\n' > "$TMP_DIR/src/baidudrive-binary-test/nas_sdk/x86_64/libkernel.so"
printf 'loader\n' > "$TMP_DIR/src/baidudrive-binary-test/glibc/x86_64/lib64/ld-linux-x86-64.so.2"
printf 'libc\n' > "$TMP_DIR/src/baidudrive-binary-test/glibc/x86_64/lib/x86_64-linux-gnu/libc.so.6"
chmod +x \
  "$TMP_DIR/src/baidudrive-binary-test/baidudrive.x86_64" \
  "$TMP_DIR/src/baidudrive-binary-test/nas_sdk/x86_64/baiduNas" \
  "$TMP_DIR/src/baidudrive-binary-test/nas_sdk/x86_64/P2PClient.bin"

tar -czf "$TMP_DIR/baidudrive-binary-test.tar.gz" -C "$TMP_DIR/src" baidudrive-binary-test

output=$(
  BAIDUDRIVE_VERSION=test \
  BAIDUDRIVE_ARCH=x86_64 \
  BAIDUDRIVE_TARBALL_URL="file://$TMP_DIR/baidudrive-binary-test.tar.gz" \
  "$ROOT_DIR/tools/install-baidudrive-prebuilt.sh" --dry-run
)

printf '%s\n' "$output" | grep -F 'usr/sbin/baidudrive' >/dev/null
printf '%s\n' "$output" | grep -F 'opt/baidunas-sdk/baiduNas' >/dev/null
printf '%s\n' "$output" | grep -F 'opt/baidunas-sdk/P2PClient' >/dev/null
printf '%s\n' "$output" | grep -F 'opt/baidunas-sdk/P2PClient.bin' >/dev/null
printf '%s\n' "$output" | grep -F 'opt/baidunas-glibc/lib64/ld-linux-x86-64.so.2' >/dev/null
printf '%s\n' "$output" | grep -F 'etc/init.d/baidudrive' >/dev/null
printf '%s\n' "$output" | grep -F 'usr/libexec/baidudrive/sdk-init.sh' >/dev/null
printf '%s\n' "$output" | grep -F 'usr/lib/lua/luci/controller/baidudrive.lua' >/dev/null
