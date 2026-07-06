#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PKG_DIR="$ROOT_DIR/apps/baidudrive/baidudrive"
LUCI_DIR="$ROOT_DIR/apps/baidudrive/luci-app-baidudrive"

grep -F 'PKG_ARCH_BAIDUDRIVE:=$(ARCH)' "$PKG_DIR/Makefile" >/dev/null
grep -F 'DEPENDS:=@(x86_64||aarch64) +curl' "$PKG_DIR/Makefile" >/dev/null
grep -F 'STRIP:=true' "$PKG_DIR/Makefile" >/dev/null
grep -F '$(PKG_BUILD_DIR)/baidudrive.$(PKG_ARCH_BAIDUDRIVE)' "$PKG_DIR/Makefile" >/dev/null
grep -F '$(PKG_BUILD_DIR)/nas_sdk/$(PKG_ARCH_BAIDUDRIVE)/baiduNas' "$PKG_DIR/Makefile" >/dev/null
grep -F '$(PKG_BUILD_DIR)/nas_sdk/$(PKG_ARCH_BAIDUDRIVE)/P2PClient.bin' "$PKG_DIR/Makefile" >/dev/null
grep -F '$(PKG_BUILD_DIR)/glibc/$(PKG_ARCH_BAIDUDRIVE)/.' "$PKG_DIR/Makefile" >/dev/null
grep -F '$(LN) /usr/sbin/baidudrive $(1)/opt/baidunas-sdk/P2PClient' "$PKG_DIR/Makefile" >/dev/null

sh -n "$PKG_DIR/files/baidudrive.init"
grep -F 'procd_open_instance baiduNas' "$PKG_DIR/files/baidudrive.init" >/dev/null
grep -F 'procd_open_instance sdk-init' "$PKG_DIR/files/baidudrive.init" >/dev/null
grep -F 'BAIDU_NAS_MACID="$macid"' "$PKG_DIR/files/baidudrive.init" >/dev/null
grep -F 'BAIDU_NAS_DEVICE_TYPE="$device_type"' "$PKG_DIR/files/baidudrive.init" >/dev/null
grep -F 'procd_set_param command /usr/libexec/baidudrive/sdk-init.sh' "$PKG_DIR/files/baidudrive.init" >/dev/null
grep -F 'storage_root_from_data_dir' "$PKG_DIR/files/baidudrive.init" >/dev/null

sh -n "$PKG_DIR/files/sdk-init.sh"
grep -F 'register' "$PKG_DIR/files/sdk-init.sh" >/dev/null
grep -F 'type=quota' "$PKG_DIR/files/sdk-init.sh" >/dev/null
grep -F 'type=usbIn' "$PKG_DIR/files/sdk-init.sh" >/dev/null
grep -F 'sdk init ready' "$PKG_DIR/files/sdk-init.sh" >/dev/null

grep -F "option 'sdk_dir' '/opt/baidunas-sdk'" "$PKG_DIR/files/baidudrive.config" >/dev/null
! grep -F "option 'glibc_dir'" "$PKG_DIR/files/baidudrive.config" >/dev/null
grep -F "option 'sdk_port' '8001'" "$PKG_DIR/files/baidudrive.config" >/dev/null
grep -F "option 'macid' ''" "$PKG_DIR/files/baidudrive.config" >/dev/null
grep -F "option 'device_type' ''" "$PKG_DIR/files/baidudrive.config" >/dev/null
grep -F "option 'usb_path' ''" "$PKG_DIR/files/baidudrive.config" >/dev/null
grep -F "option 'quota_path' ''" "$PKG_DIR/files/baidudrive.config" >/dev/null
grep -F "option 'download_path' '/'" "$PKG_DIR/files/baidudrive.config" >/dev/null

grep -F 'Value, "data_dir"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
grep -F 'Value, "port"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "host"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "sdk_dir"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "sdk_host"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "sdk_port"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "macid"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "device_type"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "usb_path"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "download_path"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "quota_path"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "tmp_path"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "log_level"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'Value, "glibc_dir"' "$LUCI_DIR/luasrc/model/cbi/baidudrive.lua" >/dev/null
! grep -F 'NAS SDK init' "$LUCI_DIR/luasrc/view/baidudrive/baidudrive_status.htm" >/dev/null
! grep -F 'sdk_ready' "$LUCI_DIR/luasrc/controller/baidudrive.lua" >/dev/null
grep -F -- '--data-urlencode' "$PKG_DIR/files/sdk-init.sh" >/dev/null
