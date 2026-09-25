#!/bin/sh
set -eu

importer="${1:-tools/import-tmp-packages.sh}"
case "$importer" in
    /*) ;;
    *) importer="$(pwd)/${importer#./}" ;;
esac

for command_name in zip unzip rsync; do
    command -v "$command_name" >/dev/null 2>&1 || {
        echo "skip: ${command_name} is required" >&2
        exit 0
    }
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

make_fixture() {
    arch="$1"
    runtime_arch="$2"
    tree="$tmp/fixture-$arch"

    mkdir -p "$tree/ipk/apps" "$tree/ipk/nas" "$tree/ipk/nas_luci"
    mkdir -p "$tree/apk/apps" "$tree/apk/nas" "$tree/apk/nas_luci"

    printf '%s runtime ipk\n' "$arch" >"$tree/ipk/apps/agentflow_1.0-1_${runtime_arch}.ipk"
    printf 'shared luci ipk\n' >"$tree/ipk/apps/luci-app-agentflow_1.0_all.ipk"
    printf '%s runtime apk\n' "$arch" >"$tree/apk/apps/agentflow-1.0-r1.apk"
    printf 'shared luci apk\n' >"$tree/apk/apps/luci-app-agentflow-1.0-r1.apk"

    printf '%s legacy runtime ipk\n' "$arch" >"$tree/ipk/nas/legacy-runtime_1.0-1_all.ipk"
    printf 'shared legacy luci ipk\n' >"$tree/ipk/nas_luci/luci-app-legacy_1.0_all.ipk"
    printf '%s legacy runtime apk\n' "$arch" >"$tree/apk/nas/legacy-runtime-1.0-r1.apk"
    printf 'shared legacy luci apk\n' >"$tree/apk/nas_luci/luci-app-legacy-1.0-r1.apk"

    mkdir -p "$tree/ipk/istore" "$tree/apk/istore"
    printf 'ignored\n' >"$tree/ipk/istore/taskd_1.0_all.ipk"
    printf 'ignored\n' >"$tree/apk/istore/taskd-1.0-r1.apk"

    (cd "$tree" && zip -qr "$tmp/$arch.zip" .)
}

make_fixture arm64 aarch64_cortex-a53
make_fixture x64 x86_64

mkdir -p "$tmp/repo" "$tmp/fake-bin"
cat >"$tmp/fake-bin/git" <<'EOF'
#!/bin/sh
case " $* " in
    *' ls-remote '*) exit 2 ;;
esac
exit 0
EOF
chmod +x "$tmp/fake-bin/git"
printf 'export OPENWRT_ACTIONS_RUN_ID=1\n' >"$tmp/urls.env"

output="$(
    PATH="$tmp/fake-bin:$PATH" "$importer" \
        --source-dir "$tmp" \
        --urls-env "$tmp/urls.env" \
        --repo-root "$tmp/repo" \
        --skip-download \
        --dry-run
)"

assert_output() {
    expected="$1"
    printf '%s\n' "$output" | grep -F -- "$expected" >/dev/null || {
        printf 'failed: missing output: %s\n' "$expected" >&2
        printf '%s\n' "$output" >&2
        exit 1
    }
}

assert_absent() {
    unexpected="$1"
    if printf '%s\n' "$output" | grep -F -- "$unexpected" >/dev/null; then
        printf 'failed: unexpected output: %s\n' "$unexpected" >&2
        printf '%s\n' "$output" >&2
        exit 1
    fi
}

assert_output 'route arm64 ipk apps: luci-app-agentflow_1.0_all.ipk -> all/nas_luci'
assert_output 'route x64 ipk apps: agentflow_1.0-1_x86_64.ipk -> x86_64/nas'
assert_output 'route arm64 apk apps: luci-app-agentflow-1.0-r1.apk -> all/nas_luci'
assert_output 'route x64 apk apps: agentflow-1.0-r1.apk -> x86_64/nas'
assert_output 'sync arm64 nas:'
assert_output 'sync x64 nas:'
assert_output 'sync luci all:'
assert_output 'sync apk luci all:'
assert_absent '/apps/'
assert_absent '/istore/'

legacy_source="$tmp/legacy-source"
mkdir -p "$legacy_source"
for arch in arm64 x64; do
    legacy_tree="$tmp/legacy-$arch"
    mkdir -p "$legacy_tree/ipk" "$legacy_tree/apk"
    cp -R "$tmp/fixture-$arch/ipk/nas" "$tmp/fixture-$arch/ipk/nas_luci" "$legacy_tree/ipk/"
    cp -R "$tmp/fixture-$arch/apk/nas" "$tmp/fixture-$arch/apk/nas_luci" "$legacy_tree/apk/"
    (cd "$legacy_tree" && zip -qr "$legacy_source/$arch.zip" .)
done
printf 'export OPENWRT_ACTIONS_RUN_ID=2\n' >"$legacy_source/urls.env"

output="$(
    PATH="$tmp/fake-bin:$PATH" "$importer" \
        --source-dir "$legacy_source" \
        --urls-env "$legacy_source/urls.env" \
        --repo-root "$tmp/repo" \
        --skip-download \
        --dry-run
)"

assert_output 'sync arm64 nas:'
assert_output 'sync x64 nas:'
assert_output 'sync luci all:'
assert_output 'sync apk luci all:'
assert_absent 'route arm64 ipk apps:'
assert_absent 'route arm64 apk apps:'

echo 'ok: OpenWrt artifact routing supports mixed apps and legacy layouts'
