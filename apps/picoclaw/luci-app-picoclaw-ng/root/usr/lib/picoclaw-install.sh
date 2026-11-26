#!/bin/sh
# ============================================================
# PicoClaw 后台安装器
#
# 由 /etc/init.d/picoclaw-installer（procd oneshot）启动，
# 参数从 /tmp/picoclaw-install.args 读取（由 LuCI 控制器写入）。
#
# 设计目标：
#   * 下载/校验/替换全部在后台完成，不会触发 uhttpd CGI 超时
#   * 每一步都写入 /tmp/picoclaw-install.status（页面轮询显示）
#   * 完整过程写入 /tmp/picoclaw-install.log（页面可展开查看）
#   * 开启插件操作日志时，同步写入 /etc/picoclaw-luci.log 便于溯源
#
# 本脚本无论成功失败都 exit 0：避免 procd 把一次失败安装反复重启。
# ============================================================

ARGS=/tmp/picoclaw-install.args
STATUS=/tmp/picoclaw-install.status
LOG=/tmp/picoclaw-install.log
AUDIT=/etc/picoclaw-luci.log
AUDIT_MAX=262144
WORK=/tmp/picoclaw-install-work
LOCK=/var/lock/picoclaw-install.lock

# ---------- 0. 读取并校验参数 ----------
[ -f "$ARGS" ] || exit 0
# shellcheck disable=SC1090
. "$ARGS"

echo "$VERSION"  | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$' || exit 0
echo "$ARCH"     | grep -qE '^[A-Za-z0-9_]+$'            || exit 0
echo "$EXPECTED" | grep -qE '^[0-9a-fA-F]{64}$'          || exit 0
case "$URL" in
    https://github.com/sipeed/picoclaw/releases/download/*) ;;
    *) exit 0 ;;
esac

# ---------- 1. 并发保护 ----------
mkdir -p /var/lock 2>/dev/null
if [ -d "$LOCK" ]; then
    OLD_PID=$(cat "$LOCK/pid" 2>/dev/null)
    if [ -n "$OLD_PID" ] && [ -d "/proc/$OLD_PID" ]; then
        exit 0
    fi
    rm -rf "$LOCK"
fi
mkdir "$LOCK" 2>/dev/null || exit 0
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT INT TERM

# ---------- 2. 日志 ----------
DEBUG_LOG=$(uci -q get picoclaw.@picoclaw[0].debug_log 2>/dev/null)
[ "$DEBUG_LOG" = "1" ] || DEBUG_LOG=0

audit() {
    [ "$DEBUG_LOG" = "1" ] || return 0
    if [ -f "$AUDIT" ]; then
        AUDIT_SIZE=$(wc -c < "$AUDIT" 2>/dev/null || echo 0)
        [ "$AUDIT_SIZE" -gt "$AUDIT_MAX" ] && mv -f "$AUDIT" "$AUDIT.1" 2>/dev/null
    fi
    umask 077
    printf '%s [INSTALL] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$AUDIT" 2>/dev/null
}

STEP=""
log() {
    printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$STEP" "$*" >> "$LOG" 2>/dev/null
    audit "$*"
}

# state: running | success | failed
# 额外写入 progress=0..100，页面用于绘制进度条
write_status() {
    _progress=${4:-0}
    case "$_progress" in ''|*[!0-9]*) _progress=0;; esac
    {
        echo "state=$1"
        echo "step=$2"
        echo "message=$3"
        echo "pid=$$"
        echo "progress=$_progress"
        echo "ts=$(date +%s)"
    } > "$STATUS.tmp" 2>/dev/null || return 0
    chmod 600 "$STATUS.tmp" 2>/dev/null
    mv -f "$STATUS.tmp" "$STATUS" 2>/dev/null
}

format_bytes() {
    _b=${1:-0}
    if [ "$_b" -lt 1024 ] 2>/dev/null; then
        echo "${_b} B"
    elif [ "$_b" -lt 1048576 ] 2>/dev/null; then
        echo "$((_b / 1024)) KB"
    elif [ "$_b" -lt 1073741824 ] 2>/dev/null; then
        echo "$((_b / 1048576)) MB"
    else
        echo "$((_b / 1073741824)) GB"
    fi
}

fail() {
    write_status failed "$STEP" "$1"
    log "FAILED: $1"
    logger -t picoclaw-installer "$1" 2>/dev/null
    rm -rf "$WORK"
    rm -f "$ARGS"
    exit 0
}

# ---------- 3. 开始 ----------
: > "$LOG"
STEP=prepare
write_status running "$STEP" "正在准备安装环境" 2
log "installer start pid=$$ version=$VERSION arch=$ARCH"
audit "version=$VERSION arch=$ARCH url=$URL expected=$EXPECTED"

rm -rf "$WORK"
mkdir -p "$WORK" || fail "无法创建临时目录 $WORK"
TGZ="$WORK/picoclaw.tar.gz"

# ---------- 4. 下载（带进度） ----------
STEP=download
write_status running "$STEP" "正在下载 PicoClaw v$VERSION（$ARCH）" 2
log "download begin url=$URL"

if command -v curl >/dev/null 2>&1; then
    DL_TOOL=curl
elif command -v uclient-fetch >/dev/null 2>&1; then
    DL_TOOL=uclient-fetch
elif command -v wget >/dev/null 2>&1; then
    DL_TOOL=wget
else
    DL_TOOL=""
fi
[ -n "$DL_TOOL" ] || fail "系统缺少下载工具（curl / wget / uclient-fetch）"

# 尽量取远端大小用于百分比；取不到就显示已下载字节数
TOTAL_SIZE=""
if [ "$DL_TOOL" = "curl" ]; then
    TOTAL_SIZE=$(curl -fsIL --connect-timeout 10 --max-time 30 "$URL" 2>/dev/null | \
        awk 'BEGIN{IGNORECASE=1} /^content-length:/{gsub("\r","",$2); n=$2} END{if (n ~ /^[0-9]+$/) print n}')
fi
log "remote size=${TOTAL_SIZE:-unknown}"

RC_FILE="$WORK/download.rc"
rm -f "$RC_FILE"
(
    case "$DL_TOOL" in
        curl)         curl -fL --connect-timeout 15 --max-time 600 -o "$TGZ" "$URL" ;;
        uclient-fetch) uclient-fetch -O "$TGZ" "$URL" ;;
        wget)         wget -O "$TGZ" "$URL" ;;
    esac
    echo $? > "$RC_FILE"
) >> "$LOG" 2>&1 &
DL_PID=$!

LAST_PCT=-1
while kill -0 "$DL_PID" 2>/dev/null; do
    SIZE=$(wc -c < "$TGZ" 2>/dev/null | tr -d ' ')
    [ -n "$SIZE" ] || SIZE=0
    if [ -n "$TOTAL_SIZE" ] && [ "$TOTAL_SIZE" -gt 0 ] 2>/dev/null; then
        PCT=$((SIZE * 85 / TOTAL_SIZE))
        [ "$PCT" -ge 85 ] && PCT=84
        MSG="正在下载 PicoClaw v$VERSION（${PCT}%，$(format_bytes "$SIZE") / $(format_bytes "$TOTAL_SIZE")）"
    else
        PCT=0
        MSG="正在下载 PicoClaw v$VERSION（已下载 $(format_bytes "$SIZE")）"
    fi
    if [ "$PCT" != "$LAST_PCT" ]; then
        write_status running "$STEP" "$MSG" "$PCT"
        LAST_PCT=$PCT
    fi
    sleep 1
done
wait "$DL_PID" 2>/dev/null
RC=$(cat "$RC_FILE" 2>/dev/null)
[ -n "$RC" ] || RC=1
rm -f "$RC_FILE"

log "download done exit=$RC"
if [ "$RC" != "0" ]; then
    fail "下载失败（退出码 $RC），请检查网络后重试"
fi

DL_SIZE=$(wc -c < "$TGZ" 2>/dev/null | tr -d ' ')
log "download size=$DL_SIZE"
if [ -z "$DL_SIZE" ] || [ "$DL_SIZE" -lt 5000000 ]; then
    fail "下载文件不完整（$DL_SIZE 字节），请检查网络后重试"
fi

# ---------- 5. 校验 SHA256 ----------
STEP=verify
write_status running "$STEP" "正在校验文件完整性" 88
log "checksum begin expected=$EXPECTED"

HASH=""
if command -v sha256sum >/dev/null 2>&1; then
    HASH=$(sha256sum "$TGZ" 2>/dev/null | awk '{print $1}')
elif command -v busybox >/dev/null 2>&1 && busybox sha256sum "$TGZ" >/dev/null 2>&1; then
    HASH=$(busybox sha256sum "$TGZ" 2>/dev/null | awk '{print $1}')
elif command -v openssl >/dev/null 2>&1; then
    HASH=$(openssl dgst -sha256 "$TGZ" 2>/dev/null | awk '{print $NF}')
fi

if [ -z "$HASH" ]; then
    fail "系统缺少 SHA256 校验工具（sha256sum / openssl）"
fi
HASH=$(echo "$HASH" | tr 'A-F' 'a-f')
EXPECTED_LC=$(echo "$EXPECTED" | tr 'A-F' 'a-f')
log "checksum got=$HASH"
if [ "$HASH" != "$EXPECTED_LC" ]; then
    fail "SHA256 校验失败，文件可能被篡改或下载损坏"
fi

# ---------- 6. 解包并定位二进制 ----------
STEP=verify
write_status running "$STEP" "正在检查安装包结构" 90
EXTRACT="$WORK/extract"
rm -rf "$EXTRACT"
mkdir -p "$EXTRACT" || fail "无法创建解包目录"
if ! tar -xzf "$TGZ" -C "$EXTRACT" >> "$LOG" 2>&1; then
    fail "解压失败，安装包可能已损坏"
fi
CORE_SRC=$(find "$EXTRACT" -type f -name picoclaw 2>/dev/null | head -n 1)
LAUNCHER_SRC=$(find "$EXTRACT" -type f -name picoclaw-launcher 2>/dev/null | head -n 1)
if [ -z "$CORE_SRC" ] || [ -z "$LAUNCHER_SRC" ]; then
    fail "安装包结构不正确（缺少 picoclaw 或 picoclaw-launcher）"
fi
log "found core=$CORE_SRC launcher=$LAUNCHER_SRC"

# ---------- 7. 停止服务、备份、替换 ----------
STEP=install
write_status running "$STEP" "正在安装到 /usr/bin" 92
log "stopping service"
/etc/init.d/picoclaw stop >> "$LOG" 2>&1
killall picoclaw picoclaw-launcher 2>/dev/null
sleep 1

cp -f /usr/bin/picoclaw /usr/bin/picoclaw.bak 2>/dev/null
cp -f /usr/bin/picoclaw-launcher /usr/bin/picoclaw-launcher.bak 2>/dev/null
log "existing binaries backed up"

rollback() {
    for p in /usr/bin/picoclaw /usr/bin/picoclaw-launcher; do
        if [ -f "$p.bak" ]; then
            cp -f "$p.bak" "$p"
        else
            rm -f "$p"
        fi
    done
    chmod 755 /usr/bin/picoclaw /usr/bin/picoclaw-launcher 2>/dev/null
    log "binaries rolled back"
}

cp -f "$CORE_SRC" /usr/bin/picoclaw || { rollback; fail "写入 /usr/bin/picoclaw 失败"; }
cp -f "$LAUNCHER_SRC" /usr/bin/picoclaw-launcher || { rollback; fail "写入 /usr/bin/picoclaw-launcher 失败"; }
chmod 755 /usr/bin/picoclaw /usr/bin/picoclaw-launcher
log "installed to /usr/bin"

# ---------- 8. 版本自检（只认插件固定版本） ----------
STEP=verify
write_status running "$STEP" "正在校验安装后的版本" 95
VOUT=$(HOME=/root /usr/bin/picoclaw version 2>&1 | tr -d '\033' | sed 's/\[[0-9;]*m//g')
if ! printf '%s\n' "$VOUT" | grep -qE "(^|[^0-9.])v?$VERSION([^0-9.]|$)"; then
    log "version self-check failed output=$(printf '%s' "$VOUT" | head -n 1)"
    rollback
    fail "安装后的版本不是 v$VERSION，已回滚"
fi
log "version self-check ok: $VERSION"

# ---------- 8.5 首次配置（gateway 没有 config.json 会直接退出） ----------
if [ ! -f /root/.picoclaw/config.json ]; then
    STEP=install
    write_status running "$STEP" "正在初始化默认配置" 96
    if HOME=/root /usr/bin/picoclaw onboard >> "$LOG" 2>&1; then
        log "onboard ok"
    else
        log "onboard failed (non-fatal, panel can initialize later)"
    fi
else
    log "config exists, skip onboard"
fi
mkdir -p /root/.picoclaw/workspace/skills 2>/dev/null

# ---------- 9. 启动服务 ----------
STEP=start
write_status running "$STEP" "正在启动 PicoClaw 服务" 97
mkdir -p /root/.picoclaw/workspace/skills 2>/dev/null
# 权限模型保持现状：不调整 /root/.picoclaw 的属主与权限
/etc/init.d/picoclaw enable >> "$LOG" 2>&1
/etc/init.d/picoclaw restart >> "$LOG" 2>&1
log "service restarted"

rm -rf "$WORK"
rm -f "$ARGS"

STEP=done
write_status success "$STEP" "安装完成：PicoClaw v$VERSION 已安装并重启服务" 100
log "install complete version=$VERSION"
exit 0
