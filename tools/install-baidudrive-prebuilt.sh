#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install the published baidudrive prebuilt runtime to a remote iStoreOS/OpenWrt box.

This does not compile OpenWrt packages. It downloads baidudrive-binary-<version>.tar.gz,
stages the selected architecture payload, overlays the LuCI/init files from this repo,
then copies the payload to the remote host.

Required for remote install:
  DEPLOY_HOST

Optional:
  DEPLOY_USER=root
  DEPLOY_PORT=22
  DEPLOY_ARCH=x86_64
  BAIDUDRIVE_VERSION=0.5.1
  BAIDUDRIVE_ARCH=<x86_64|aarch64>
  BAIDUDRIVE_TARBALL_URL=<url>
  BAIDUDRIVE_INSTALL_DEPS=1
  BAIDUDRIVE_RESTART=1
  DEPLOY_SSH_KEY
  DEPLOY_SSH_OPTS

Examples:
  BAIDUDRIVE_ARCH=x86_64 ./tools/install-baidudrive-prebuilt.sh --dry-run
  DEPLOY_HOST=192.168.30.244 ./tools/install-baidudrive-prebuilt.sh
EOF
}

die() { echo "error: $*" >&2; exit 2; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"; }

PROJECT_ROOT=""
WORK_DIR=""
TARBALL_PATH=""
PAYLOAD_PATH=""

cleanup() {
  set +e
  [[ -n "${WORK_DIR:-}" ]] && rm -rf "$WORK_DIR"
  [[ -n "${TARBALL_PATH:-}" ]] && rm -f "$TARBALL_PATH"
  [[ -n "${PAYLOAD_PATH:-}" ]] && rm -f "$PAYLOAD_PATH"
}

copy_tree_into() {
  local src_dir="$1"
  local dst_dir="$2"
  [[ -d "$src_dir" ]] || return 0
  mkdir -p "$dst_dir"
  tar -C "$src_dir" -cf - . | tar -C "$dst_dir" -xf -
}

copy_file_into() {
  local src_path="$1"
  local dst_path="$2"
  mkdir -p "$(dirname "$dst_path")"
  cp -a "$src_path" "$dst_path"
}

stage_luci() {
  local luci_dir="$PROJECT_ROOT/apps/baidudrive/luci-app-baidudrive"
  local staging_dir="$1"

  copy_tree_into "$luci_dir/luasrc/controller" "$staging_dir/usr/lib/lua/luci/controller"
  copy_tree_into "$luci_dir/luasrc/model" "$staging_dir/usr/lib/lua/luci/model"
  copy_tree_into "$luci_dir/luasrc/view" "$staging_dir/usr/lib/lua/luci/view"
  copy_tree_into "$luci_dir/root" "$staging_dir"
}

stage_runtime() {
  local extracted_root="$1"
  local arch="$2"
  local staging_dir="$3"

  local src_arch="$arch"
  case "$arch" in
    x86_64|aarch64) ;;
    arm64) src_arch="aarch64" ;;
    *) die "unsupported BAIDUDRIVE_ARCH: $arch" ;;
  esac

  local binary="$extracted_root/baidudrive.$src_arch"
  local sdk_dir="$extracted_root/nas_sdk/$src_arch"
  local glibc_dir="$extracted_root/glibc/$src_arch"

  [[ -x "$binary" ]] || die "missing binary: $binary"
  [[ -x "$sdk_dir/baiduNas" ]] || die "missing SDK binary: $sdk_dir/baiduNas"
  [[ -x "$sdk_dir/P2PClient.bin" ]] || die "missing SDK binary: $sdk_dir/P2PClient.bin"
  [[ -f "$sdk_dir/libkernel.so" ]] || die "missing SDK file: $sdk_dir/libkernel.so"
  [[ -d "$glibc_dir" ]] || die "missing glibc dir: $glibc_dir"

  copy_file_into "$binary" "$staging_dir/usr/sbin/baidudrive"
  copy_file_into "$sdk_dir/baiduNas" "$staging_dir/opt/baidunas-sdk/baiduNas"
  copy_file_into "$sdk_dir/P2PClient.bin" "$staging_dir/opt/baidunas-sdk/P2PClient.bin"
  copy_file_into "$sdk_dir/libkernel.so" "$staging_dir/opt/baidunas-sdk/libkernel.so"
  ln -sfn /usr/sbin/baidudrive "$staging_dir/opt/baidunas-sdk/P2PClient"
  copy_tree_into "$glibc_dir" "$staging_dir/opt/baidunas-glibc"

  local pkg_dir="$PROJECT_ROOT/apps/baidudrive/baidudrive"
  copy_file_into "$pkg_dir/files/baidudrive.init" "$staging_dir/etc/init.d/baidudrive"
  copy_file_into "$pkg_dir/files/baidudrive.config" "$staging_dir/etc/config/baidudrive"
  copy_file_into "$pkg_dir/files/baidudrive.uci-default" "$staging_dir/etc/uci-defaults/09-baidudrive"
  copy_file_into "$pkg_dir/files/sdk-init.sh" "$staging_dir/usr/libexec/baidudrive/sdk-init.sh"

  chmod +x \
    "$staging_dir/usr/sbin/baidudrive" \
    "$staging_dir/opt/baidunas-sdk/baiduNas" \
    "$staging_dir/opt/baidunas-sdk/P2PClient.bin" \
    "$staging_dir/etc/init.d/baidudrive" \
    "$staging_dir/etc/uci-defaults/09-baidudrive" \
    "$staging_dir/usr/libexec/baidudrive/sdk-init.sh"
}

main() {
  need_cmd curl
  need_cmd tar

  local dry_run="0"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) dry_run="1"; shift ;;
      -h|--help) usage; exit 0 ;;
      *) die "unknown arg: $1 (use --help)" ;;
    esac
  done

  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
  WORK_DIR="$(mktemp -d)"
  TARBALL_PATH="$(mktemp -t baidudrive-prebuilt.XXXXXX.tar.gz)"
  PAYLOAD_PATH="$(mktemp -t baidudrive-install.XXXXXX.tgz)"
  trap cleanup EXIT

  local version="${BAIDUDRIVE_VERSION:-0.5.1}"
  local arch="${BAIDUDRIVE_ARCH:-${DEPLOY_ARCH:-x86_64}}"
  local url="${BAIDUDRIVE_TARBALL_URL:-https://github.com/linkease/istore-packages/releases/download/prebuilt/baidudrive-binary-${version}.tar.gz}"
  local install_deps="${BAIDUDRIVE_INSTALL_DEPS:-1}"
  local restart_service="${BAIDUDRIVE_RESTART:-1}"

  curl -fsSL "$url" -o "$TARBALL_PATH"
  tar -xzf "$TARBALL_PATH" -C "$WORK_DIR"

  local extracted_root="$WORK_DIR/baidudrive-binary-$version"
  [[ -d "$extracted_root" ]] || die "missing tarball root: baidudrive-binary-$version"

  local staging_dir="$WORK_DIR/staging"
  mkdir -p "$staging_dir"
  stage_runtime "$extracted_root" "$arch" "$staging_dir"
  stage_luci "$staging_dir"

  tar -C "$staging_dir" -czf "$PAYLOAD_PATH" .

  echo "Payload contents:"
  tar -tzf "$PAYLOAD_PATH" | sed 's#^\./##' | sed '/^$/d' | sort

  if [[ "$dry_run" == "1" ]]; then
    echo "Dry-run: not installing."
    return 0
  fi

  need_cmd ssh
  need_cmd scp

  local host="${DEPLOY_HOST:-}"
  local user="${DEPLOY_USER:-root}"
  local port="${DEPLOY_PORT:-22}"
  local ssh_key="${DEPLOY_SSH_KEY:-}"
  local ssh_opts="${DEPLOY_SSH_OPTS:-}"
  [[ -n "$host" ]] || die "DEPLOY_HOST is required"

  local ssh_args=(-p "$port")
  local scp_args=(-P "$port")
  if [[ -n "$ssh_key" ]]; then
    ssh_args+=(-i "$ssh_key")
    scp_args+=(-i "$ssh_key")
  fi
  if [[ -n "$ssh_opts" ]]; then
    # shellcheck disable=SC2206
    ssh_args+=($ssh_opts)
    # shellcheck disable=SC2206
    scp_args+=($ssh_opts)
  fi

  local remote="${user}@${host}"
  local remote_tmp
  remote_tmp="$(ssh "${ssh_args[@]}" "$remote" "mktemp -d /tmp/baidudrive-install.XXXXXX")"
  scp "${scp_args[@]}" "$PAYLOAD_PATH" "${remote}:${remote_tmp}/payload.tgz" >/dev/null

  ssh "${ssh_args[@]}" "$remote" sh -seu <<EOF
cd "$remote_tmp"
if [ "$install_deps" = "1" ] && command -v opkg >/dev/null 2>&1; then
  opkg update || true
  opkg install curl luci-compat rpcd-mod-luci || true
fi
tar -xzf payload.tgz -C /
chmod +x /usr/sbin/baidudrive /opt/baidunas-sdk/baiduNas /opt/baidunas-sdk/P2PClient.bin /etc/init.d/baidudrive /usr/libexec/baidudrive/sdk-init.sh
[ -x /etc/init.d/baidudrive ] && /etc/init.d/baidudrive enable || true
rm -rf /tmp/luci-* /tmp/luci-indexcache || true
if [ "$restart_service" = "1" ]; then
  /etc/init.d/baidudrive restart 2>/dev/null || true
  /etc/init.d/uhttpd reload 2>/dev/null || /etc/init.d/uhttpd restart 2>/dev/null || true
fi
echo "Installed baidudrive prebuilt ${version} (${arch})"
EOF
}

main "$@"
