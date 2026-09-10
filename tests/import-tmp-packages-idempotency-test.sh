#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

origin="${tmp_dir}/origin.git"
repo="${tmp_dir}/repo"
source_dir="${tmp_dir}/artifacts"
run_id=12345
branch="zip-${run_id}"

git init -q --bare "${origin}"
git init -q -b main "${repo}"
git -C "${repo}" config user.name test
git -C "${repo}" config user.email test@example.com
git -C "${repo}" remote add origin "${origin}"
git -C "${repo}" commit -q --allow-empty -m initial
git -C "${repo}" push -q -u origin main

git -C "${repo}" switch -q -c "${branch}"
git -C "${repo}" commit -q --allow-empty -m "chore: import OpenWrt artifacts ${run_id}"
git -C "${repo}" push -q origin "${branch}"
git -C "${repo}" switch -q main
git -C "${repo}" branch -q -D "${branch}"
git -C "${repo}" config --unset-all remote.origin.fetch
git -C "${repo}" config --add remote.origin.fetch \
    '+refs/heads/main:refs/remotes/origin/main'
git -C "${repo}" update-ref -d "refs/remotes/origin/${branch}"

mkdir -p "${source_dir}"
touch "${source_dir}/arm64.zip"
printf 'OPENWRT_ACTIONS_RUN_ID=%s\n' "${run_id}" > "${source_dir}/urls.env"

output="$(${root_dir}/tools/import-tmp-packages.sh \
    --source-dir "${source_dir}" \
    --urls-env "${source_dir}/urls.env" \
    --repo-root "${repo}" \
    --run-id "${run_id}" \
    --skip-download \
    --no-push)"
printf '%s\n' "${output}" | grep -F \
    "artifact run ${run_id} is already imported on remote branch ${branch}" >/dev/null
[ "$(git -C "${repo}" rev-parse "refs/heads/${branch}")" = \
    "$(git -C "${repo}" rev-parse "refs/remotes/origin/${branch}")" ]
[ "$(git -C "${repo}" config --get "branch.${branch}.remote")" = origin ]
[ "$(git -C "${repo}" config --get "branch.${branch}.merge")" = "refs/heads/${branch}" ]
[ "$(git -C "${repo}" for-each-ref --format='%(upstream)' "refs/heads/${branch}")" = \
    "refs/remotes/origin/${branch}" ]
[ "$(git -C "${repo}" branch --show-current)" = main ]
[ -z "$(git -C "${repo}" status --short)" ]

collision_run_id=67890
collision_branch="zip-${collision_run_id}"
git -C "${repo}" switch -q -c "${collision_branch}"
git -C "${repo}" commit -q --allow-empty -m "unrelated branch"
git -C "${repo}" push -q origin "${collision_branch}"
git -C "${repo}" switch -q main
git -C "${repo}" branch -q -D "${collision_branch}"

set +e
collision_output="$(${root_dir}/tools/import-tmp-packages.sh \
    --source-dir "${source_dir}" \
    --urls-env "${source_dir}/urls.env" \
    --repo-root "${repo}" \
    --run-id "${collision_run_id}" \
    --skip-download \
    --no-push 2>&1)"
collision_status=$?
set -e

[ "${collision_status}" -ne 0 ]
printf '%s\n' "${collision_output}" | grep -F \
    "error: remote branch ${collision_branch} exists but does not belong to artifact run ${collision_run_id}" >/dev/null
