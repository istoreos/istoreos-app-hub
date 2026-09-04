#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  github-artifact-redirect-url.sh <archive_download_url>
  github-artifact-redirect-url.sh --repo OWNER/REPO --run-id RUN_ID --artifact NAME

Print the final redirected URL for a GitHub Actions artifact zip without
downloading the artifact body.

Authentication:
  Automatically sources ~/.config/gh-tokens/kspeeder.env when it exists.
  Uses GH_TOKEN, GITHUB_TOKEN, or LINKEASE_GH_TOKEN if set.
  Set KSPEEDER_GH_TOKEN_FILE to override the token file path.

Examples:
  github-artifact-redirect-url.sh \
    https://api.github.com/repos/linkease/openwrt-app-actions/actions/artifacts/9402015059/zip

  github-artifact-redirect-url.sh \
    --repo linkease/openwrt-app-actions \
    --run-id 32356214676 \
    --artifact arm64
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

repo=""
run_id=""
artifact=""
archive_url=""
max_redirs=10

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || die "--repo requires a value"
      repo="$2"
      shift 2
      ;;
    --run-id|--run)
      [[ $# -ge 2 ]] || die "$1 requires a value"
      run_id="$2"
      shift 2
      ;;
    --artifact)
      [[ $# -ge 2 ]] || die "--artifact requires a value"
      artifact="$2"
      shift 2
      ;;
    --max-redirs)
      [[ $# -ge 2 ]] || die "--max-redirs requires a value"
      max_redirs="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      die "unknown option: $1"
      ;;
    *)
      [[ -z "$archive_url" ]] || die "only one archive_download_url can be provided"
      archive_url="$1"
      shift
      ;;
  esac
done

token_file="${KSPEEDER_GH_TOKEN_FILE:-${HOME}/.config/gh-tokens/kspeeder.env}"
if [[ -f "$token_file" ]]; then
  set +x
  # shellcheck source=/dev/null
  source "$token_file"
fi

token="${GH_TOKEN:-${GITHUB_TOKEN:-${LINKEASE_GH_TOKEN:-}}}"

if [[ -n "$archive_url" ]]; then
  [[ -z "$repo" && -z "$run_id" && -z "$artifact" ]] ||
    die "use either archive_download_url or --repo/--run-id/--artifact, not both"
else
  [[ -n "$repo" ]] || die "--repo is required when archive_download_url is not provided"
  [[ -n "$run_id" ]] || die "--run-id is required when archive_download_url is not provided"
  [[ -n "$artifact" ]] || die "--artifact is required when archive_download_url is not provided"
  [[ -n "$token" ]] || die "GH_TOKEN, GITHUB_TOKEN, or LINKEASE_GH_TOKEN is required"

  need_cmd gh
  need_cmd jq

  escaped_artifact="${artifact//\\/\\\\}"
  escaped_artifact="${escaped_artifact//\"/\\\"}"
  artifacts_json="$(GH_TOKEN="$token" gh api "repos/${repo}/actions/runs/${run_id}/artifacts")"
  archive_url="$(
    printf '%s\n' "$artifacts_json" |
      jq -r ".artifacts[] | select(.name == \"${escaped_artifact}\") | .archive_download_url" |
      sed -n '1p'
  )"
  if [[ -z "$archive_url" ]]; then
    available_artifacts="$(
      printf '%s\n' "$artifacts_json" |
        jq -r '[.artifacts[].name] | if length == 0 then "(none)" else join(", ") end'
    )"
    die "artifact not found: ${artifact}; available artifacts for run ${run_id}: ${available_artifacts}"
  fi
fi

need_cmd curl

curl_args=(
  --fail
  --silent
  --show-error
  --head
  --location
  --max-redirs "$max_redirs"
  --output /dev/null
  --write-out '%{url_effective}\n'
)

if [[ -n "$token" ]]; then
  curl_args+=(
    --header "Authorization: Bearer ${token}"
    --header "Accept: application/vnd.github+json"
  )
fi

curl "${curl_args[@]}" "$archive_url"
