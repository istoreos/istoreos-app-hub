#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  publish-and-import-openwrt-artifacts.sh RUN_ID

Resolve arm64/x64 artifact redirect URLs for a GitHub Actions run, write them
to TARGET_TMP/urls.env on TARGET_SSH, upload import-tmp-packages.sh to
TARGET_TMP, and execute it on the target server.

Environment:
  KSPEEDER_GH_TOKEN_FILE  Defaults to ~/.config/gh-tokens/kspeeder.env
  TARGET_SSH              SSH target
  TARGET_TMP              Remote temp directory
  ISTORE_REPO             Remote istore-repo checkout

Options:
  --repo OWNER/REPO       Defaults to linkease/openwrt-app-actions
  --dry-run               Resolve URLs and print intended actions without remote writes
  --remote-dry-run        Upload and execute import script with --dry-run
  --no-push               Execute import script with --no-push
  -h, --help              Show this help.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

shell_quote() {
  printf '%q' "$1"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
publish_urls_script="${script_dir}/publish-openwrt-artifact-urls.sh"
import_script="${script_dir}/import-tmp-packages.sh"

token_file="${KSPEEDER_GH_TOKEN_FILE:-${HOME}/.config/gh-tokens/kspeeder.env}"
if [[ -f "$token_file" ]]; then
  set +x
  # shellcheck source=/dev/null
  source "$token_file"
fi

repo="${REPO:-linkease/openwrt-app-actions}"
target_ssh="${TARGET_SSH:-}"
target_tmp="${TARGET_TMP:-}"
istore_repo="${ISTORE_REPO:-}"
dry_run=0
remote_dry_run=0
no_push=0
run_id=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || die "--repo requires a value"
      repo="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --remote-dry-run)
      remote_dry_run=1
      shift
      ;;
    --no-push)
      no_push=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      die "unknown option: $1"
      ;;
    *)
      [[ -z "$run_id" ]] || die "only one RUN_ID can be provided"
      run_id="$1"
      shift
      ;;
  esac
done

[[ -n "$run_id" ]] || die "RUN_ID is required"
case "$run_id" in
  *[!0-9]*) die "RUN_ID must be numeric: $run_id" ;;
esac

[[ -n "$target_ssh" ]] || die "TARGET_SSH is required"
[[ -n "$target_tmp" ]] || die "TARGET_TMP is required"
[[ -n "$istore_repo" ]] || die "ISTORE_REPO is required"
[[ -x "$publish_urls_script" ]] || die "missing executable helper: $publish_urls_script"
[[ -x "$import_script" ]] || die "missing executable helper: $import_script"

need_cmd scp
need_cmd ssh

remote_import="${target_tmp%/}/import-tmp-packages.sh"
remote_urls="${target_tmp%/}/urls.env"

if [[ "$dry_run" == "1" ]]; then
  "$publish_urls_script" --repo "$repo" --target-ssh "$target_ssh" --target-tmp "$target_tmp" --dry-run "$run_id"
  printf 'would upload %s to %s:%s\n' "$import_script" "$target_ssh" "$remote_import"
  printf 'would execute remote import for branch zip-%s\n' "$run_id"
  exit 0
fi

"$publish_urls_script" --repo "$repo" --target-ssh "$target_ssh" --target-tmp "$target_tmp" "$run_id"

ssh "$target_ssh" "mkdir -p -- $(shell_quote "$target_tmp")"
scp "$import_script" "${target_ssh}:${remote_import}"
ssh "$target_ssh" "chmod +x -- $(shell_quote "$remote_import")"

remote_args=(
  "--source-dir" "$target_tmp"
  "--urls-env" "$remote_urls"
  "--repo-root" "$istore_repo"
  "--run-id" "$run_id"
)

if [[ "$remote_dry_run" == "1" ]]; then
  remote_args+=("--dry-run")
fi
if [[ "$no_push" == "1" ]]; then
  remote_args+=("--no-push")
fi

remote_cmd="TARGET_TMP=$(shell_quote "$target_tmp") ISTORE_REPO=$(shell_quote "$istore_repo") $(shell_quote "$remote_import")"
for arg in "${remote_args[@]}"; do
  remote_cmd+=" $(shell_quote "$arg")"
done

ssh "$target_ssh" "$remote_cmd"
