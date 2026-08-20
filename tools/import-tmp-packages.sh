#!/usr/bin/env bash
set -euo pipefail

source_dir="${TARGET_TMP:-/projects/repos/tmp}"
source_dir_set=0
repo_root="${ISTORE_REPO:-}"
urls_env=""
run_id="${OPENWRT_ACTIONS_RUN_ID:-}"
branch_name=""
dry_run=0
skip_download=0
push_branch=1

usage() {
    cat <<'USAGE'
Usage: import-tmp-packages.sh [options] [SOURCE_DIR]

Download arm64.zip and x64.zip from urls.env, import their ipk/apk packages
into an istore-repo branch, commit the changes, and push the branch.

If SOURCE_DIR is omitted, TARGET_TMP is used, falling back to /projects/repos/tmp.

Required environment or options:
  TARGET_TMP     Directory containing urls.env and receiving downloaded zips
  ISTORE_REPO    istore-repo checkout

urls.env variables:
  OPENWRT_ACTIONS_RUN_ID
  ARM64_DOWNLOAD_URL
  X64_DOWNLOAD_URL

Options:
  --source-dir DIR   Directory containing urls.env and downloaded zips.
  --urls-env FILE    Env file to source. Defaults to SOURCE_DIR/urls.env.
  --repo-root DIR    Repository root to receive bin/packages and bin/apks.
  --run-id ID        Override OPENWRT_ACTIONS_RUN_ID.
  --branch NAME      Override branch name. Defaults to zip-RUN_ID.
  --skip-download    Use existing arm64.zip and x64.zip.
  --no-push          Commit locally but do not push.
  --dry-run          Print actions without downloading, writing, committing, or pushing.
  -h, --help         Show this help.
USAGE
}

die() {
    echo "error: $*" >&2
    exit 1
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --source-dir)
            [ "$#" -ge 2 ] || die "missing value for --source-dir"
            [ "${source_dir_set}" -eq 0 ] || die "source directory specified more than once"
            source_dir="$2"
            source_dir_set=1
            shift 2
            ;;
        --urls-env)
            [ "$#" -ge 2 ] || die "missing value for --urls-env"
            urls_env="$2"
            shift 2
            ;;
        --repo-root)
            [ "$#" -ge 2 ] || die "missing value for --repo-root"
            repo_root="$2"
            shift 2
            ;;
        --run-id)
            [ "$#" -ge 2 ] || die "missing value for --run-id"
            run_id="$2"
            shift 2
            ;;
        --branch)
            [ "$#" -ge 2 ] || die "missing value for --branch"
            branch_name="$2"
            shift 2
            ;;
        --skip-download)
            skip_download=1
            shift
            ;;
        --no-push)
            push_branch=0
            shift
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            while [ "$#" -gt 0 ]; do
                [ "${source_dir_set}" -eq 0 ] || die "source directory specified more than once"
                source_dir="$1"
                source_dir_set=1
                shift
            done
            ;;
        -*)
            echo "unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
        *)
            [ "${source_dir_set}" -eq 0 ] || die "source directory specified more than once"
            source_dir="$1"
            source_dir_set=1
            shift
            ;;
    esac
done

require_cmd unzip
require_cmd rsync
require_cmd mktemp
require_cmd git

[ -n "${repo_root}" ] || repo_root="$(git rev-parse --show-toplevel)"
[ -d "${source_dir}" ] || die "source directory not found: ${source_dir}"
[ -d "${repo_root}" ] || die "repo root not found: ${repo_root}"

source_dir="$(cd "${source_dir}" && pwd)"
repo_root="$(cd "${repo_root}" && pwd)"

[ -n "${urls_env}" ] || urls_env="${source_dir}/urls.env"
[ -f "${urls_env}" ] || die "urls env file not found: ${urls_env}"

set +u
# shellcheck source=/dev/null
source "${urls_env}"
set -u

[ -n "${run_id}" ] || run_id="${OPENWRT_ACTIONS_RUN_ID:-}"
[ -n "${run_id}" ] || die "OPENWRT_ACTIONS_RUN_ID is required"
case "${run_id}" in
    *[!0-9]*) die "run id must be numeric: ${run_id}" ;;
esac

[ -n "${branch_name}" ] || branch_name="zip-${run_id}"
case "${branch_name}" in
    *[!A-Za-z0-9._/-]*) die "invalid branch name: ${branch_name}" ;;
esac

arm_zip="${source_dir}/arm64.zip"
x64_zip="${source_dir}/x64.zip"

download_archive() {
    local url="$1"
    local dest="$2"
    local label="$3"

    [ -n "${url}" ] || die "missing ${label} download URL"

    if [ "${dry_run}" -eq 1 ]; then
        echo "download ${label}: ${#url} byte URL -> ${dest}"
        return
    fi

    echo "download ${label}: ${dest}"
    curl --fail --location --retry 3 --retry-delay 2 --output "${dest}.tmp" "${url}"
    mv -f "${dest}.tmp" "${dest}"
}

if [ "${skip_download}" -eq 0 ]; then
    require_cmd curl
    download_archive "${ARM64_DOWNLOAD_URL:-}" "${arm_zip}" "arm64"
    download_archive "${X64_DOWNLOAD_URL:-}" "${x64_zip}" "x64"
fi

if [ "${dry_run}" -eq 0 ]; then
    [ -f "${arm_zip}" ] || die "missing archive: ${arm_zip}"
    [ -f "${x64_zip}" ] || die "missing archive: ${x64_zip}"
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

extract_archive() {
    local archive="$1"
    local target="$2"

    mkdir -p "${target}"
    if [ "${dry_run}" -eq 1 ]; then
        echo "extract ${archive} -> ${target}"
        return
    fi
    unzip -q "${archive}" -d "${target}"
}

sync_dir() {
    local src="$1"
    local dest="$2"
    local label="$3"
    local -a rsync_args=(-a --ignore-existing --itemize-changes)

    if [ "${dry_run}" -eq 1 ]; then
        rsync_args+=(--dry-run)
    fi

    if [ ! -d "${src}" ]; then
        echo "skip ${label}: source directory not found: ${src}"
        return
    fi

    mkdir -p "${dest}"
    echo "sync ${label}: ${src}/ -> ${dest}/"
    rsync "${rsync_args[@]}" "${src}/" "${dest}/"
}

merge_luci_dir() {
    local src="$1"
    local dest="$2"
    local label="$3"

    if [ ! -d "${src}" ]; then
        echo "skip ${label}: source directory not found: ${src}"
        return
    fi

    mkdir -p "${dest}"
    while IFS= read -r -d '' file; do
        local rel="${file#"${src}/"}"
        local target="${dest}/${rel}"

        if [ -e "${target}" ]; then
            if ! cmp -s "${file}" "${target}"; then
                echo "conflicting luci package content: ${rel}" >&2
                echo "  existing: ${target}" >&2
                echo "  incoming: ${file}" >&2
                exit 1
            fi
            continue
        fi

        mkdir -p "$(dirname "${target}")"
        cp -p "${file}" "${target}"
    done < <(find "${src}" -type f -print0)
}

prepare_branch() {
    cd "${repo_root}"

    [ -z "$(git status --short)" ] || die "repo has uncommitted changes"

    echo "prepare branch ${branch_name} from origin/main"
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        die "local branch already exists: ${branch_name}"
    fi
    if git ls-remote --exit-code --heads origin "refs/heads/${branch_name}" >/dev/null 2>&1; then
        die "remote branch already exists: ${branch_name}"
    fi

    git fetch origin main
    git switch main
    git pull --ff-only origin main
    git switch -c "${branch_name}" origin/main
}

finish_branch() {
    cd "${repo_root}"

    git add bin/packages bin/apks
    if git diff --cached --quiet; then
        echo "no package changes to commit"
        return
    fi

    git commit -m "chore: import OpenWrt artifacts ${run_id}"
    if [ "${push_branch}" -eq 1 ]; then
        git push -u origin "${branch_name}"
    else
        echo "skip push: --no-push"
    fi
}

if [ "${dry_run}" -eq 0 ]; then
    prepare_branch
else
    echo "dry-run: skip git branch creation for ${branch_name}"
fi

arm_dir="${tmpdir}/arm64"
x64_dir="${tmpdir}/x64"

extract_archive "${arm_zip}" "${arm_dir}"
extract_archive "${x64_zip}" "${x64_dir}"

all_luci_dir="${tmpdir}/all_nas_luci"
merge_luci_dir "${arm_dir}/ipk/nas_luci" "${all_luci_dir}" "arm64 luci all"
merge_luci_dir "${x64_dir}/ipk/nas_luci" "${all_luci_dir}" "x64 luci all"

all_apk_luci_dir="${tmpdir}/all_apk_nas_luci"
merge_luci_dir "${arm_dir}/apk/nas_luci" "${all_apk_luci_dir}" "arm64 apk luci all"
merge_luci_dir "${x64_dir}/apk/nas_luci" "${all_apk_luci_dir}" "x64 apk luci all"

sync_dir "${all_luci_dir}" "${repo_root}/bin/packages/all/nas_luci" "luci all"
sync_dir "${arm_dir}/ipk/nas" "${repo_root}/bin/packages/aarch64_cortex-a53/nas" "arm64 nas"
sync_dir "${x64_dir}/ipk/nas" "${repo_root}/bin/packages/x86_64/nas" "x64 nas"

sync_dir "${all_apk_luci_dir}" "${repo_root}/bin/apks/all/nas_luci" "apk luci all"
sync_dir "${arm_dir}/apk/nas" "${repo_root}/bin/apks/aarch64_generic/nas" "arm64 apk nas"
sync_dir "${x64_dir}/apk/nas" "${repo_root}/bin/apks/x86_64/nas" "x64 apk nas"

if [ "${dry_run}" -eq 0 ]; then
    finish_branch
else
    echo "dry-run: skip git commit and push"
fi
