#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  publish-openwrt-artifact-urls.sh RUN_ID

Resolve available arm64 and x64 GitHub Actions artifact redirect URLs for a run, then
write them as environment variables into TARGET_FILE on TARGET_SSH.

Required environment:
  TARGET_SSH    SSH target, for example user@example.com
  TARGET_TMP    Remote temp directory. Default target file is TARGET_TMP/urls.env

Optional environment:
  KSPEEDER_GH_TOKEN_FILE  Defaults to ~/.config/gh-tokens/kspeeder.env
  REPO                    Defaults to linkease/openwrt-app-actions
  TARGET_FILE             Overrides TARGET_TMP/urls.env
  ARM64_ENV_NAME          Defaults to ARM64_DOWNLOAD_URL
  X64_ENV_NAME            Defaults to X64_DOWNLOAD_URL
  RUN_ID_ENV_NAME         Defaults to OPENWRT_ACTIONS_RUN_ID

Options:
  --repo OWNER/REPO
  --target-ssh SSH_TARGET
  --target-tmp DIR
  --target-file PATH
  --dry-run

The token file is sourced automatically when it exists.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

shell_quote() {
  printf '%q' "$1"
}

env_quote() {
  local value="$1"
  value="${value//\'/\'\\\'\'}"
  printf "'%s'" "$value"
}

validate_env_name() {
  local name="$1"
  [[ "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "invalid environment variable name: $name"
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
redirect_script="${script_dir}/github-artifact-redirect-url.sh"

token_file="${KSPEEDER_GH_TOKEN_FILE:-${HOME}/.config/gh-tokens/kspeeder.env}"
if [[ -f "$token_file" ]]; then
  set +x
  # shellcheck source=/dev/null
  source "$token_file"
fi

repo="${REPO:-linkease/openwrt-app-actions}"
target_ssh="${TARGET_SSH:-}"
target_tmp="${TARGET_TMP:-}"
target_file="${TARGET_FILE:-}"
arm64_env_name="${ARM64_ENV_NAME:-ARM64_DOWNLOAD_URL}"
x64_env_name="${X64_ENV_NAME:-X64_DOWNLOAD_URL}"
run_id_env_name="${RUN_ID_ENV_NAME:-OPENWRT_ACTIONS_RUN_ID}"
dry_run=0
run_id=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || die "--repo requires a value"
      repo="$2"
      shift 2
      ;;
    --target-ssh)
      [[ $# -ge 2 ]] || die "--target-ssh requires a value"
      target_ssh="$2"
      shift 2
      ;;
    --target-file)
      [[ $# -ge 2 ]] || die "--target-file requires a value"
      target_file="$2"
      shift 2
      ;;
    --target-tmp)
      [[ $# -ge 2 ]] || die "--target-tmp requires a value"
      target_tmp="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
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
[[ -n "$target_ssh" ]] || die "TARGET_SSH or --target-ssh is required"
if [[ -z "$target_file" ]]; then
  [[ -n "$target_tmp" ]] || die "TARGET_TMP, TARGET_FILE, --target-tmp, or --target-file is required"
  target_file="${target_tmp%/}/urls.env"
fi
[[ -x "$redirect_script" ]] || die "missing executable helper: $redirect_script"

validate_env_name "$arm64_env_name"
validate_env_name "$x64_env_name"
validate_env_name "$run_id_env_name"

need_cmd ssh

resolve_optional_url() {
  local artifact="$1"
  local output

  if output="$("$redirect_script" --repo "$repo" --run-id "$run_id" --artifact "$artifact" 2>&1)"; then
    printf '%s\n' "$output"
    return
  fi

  if [[ "$output" == error:\ artifact\ not\ found:\ "$artifact"* ]]; then
    printf 'warning: skip missing artifact %s for run %s\n' "$artifact" "$run_id" >&2
    return
  fi

  printf '%s\n' "$output" >&2
  return 1
}

arm64_url="$(resolve_optional_url arm64)"
x64_url="$(resolve_optional_url x64)"

[[ -n "$arm64_url" || -n "$x64_url" ]] || die "no supported artifacts found for run ${run_id}"

payload="$(
  printf 'export %s=%s\n' "$run_id_env_name" "$(env_quote "$run_id")"
  if [[ -n "$arm64_url" ]]; then
    printf 'export %s=%s\n' "$arm64_env_name" "$(env_quote "$arm64_url")"
  fi
  if [[ -n "$x64_url" ]]; then
    printf 'export %s=%s\n' "$x64_env_name" "$(env_quote "$x64_url")"
  fi
)"

if [[ "$dry_run" == "1" ]]; then
  printf 'would update %s:%s\n' "$target_ssh" "$target_file"
  printf 'variables: %s %s %s\n' "$run_id_env_name" "$arm64_env_name" "$x64_env_name"
  printf 'arm64_url_length=%s\n' "${#arm64_url}"
  printf 'x64_url_length=%s\n' "${#x64_url}"
  exit 0
fi

target_file_q="$(shell_quote "$target_file")"
var_re="${run_id_env_name}|${arm64_env_name}|${x64_env_name}"
var_re_q="$(shell_quote "$var_re")"

ssh "$target_ssh" "TARGET_FILE=${target_file_q} VAR_RE=${var_re_q} bash -s" <<REMOTE_SCRIPT
set -euo pipefail

target_dir="\$(dirname -- "\$TARGET_FILE")"
mkdir -p -- "\$target_dir"

tmp="\$(mktemp "\${TARGET_FILE}.XXXXXX")"
cleanup() {
  rm -f -- "\$tmp"
}
trap cleanup EXIT

if [[ -f "\$TARGET_FILE" ]]; then
  grep -v -E "^(export[[:space:]]+)?(\$VAR_RE)=" "\$TARGET_FILE" > "\$tmp" || true
fi

cat >> "\$tmp" <<'ENV_PAYLOAD'
$payload
ENV_PAYLOAD

chmod 600 "\$tmp"
mv -- "\$tmp" "\$TARGET_FILE"
trap - EXIT
REMOTE_SCRIPT

printf 'updated %s:%s with %s, %s, %s\n' \
  "$target_ssh" "$target_file" "$run_id_env_name" "$arm64_env_name" "$x64_env_name"
