# This is free software, licensed under the Apache License, Version 2.0 .
#
# iStore metadata package: store entry, icon and dependencies only.
# Must not install app manifests, app assets or registration links.

include $(TOPDIR)/rules.mk

PKG_VERSION:=3.0.2
PKG_RELEASE:=1
META_TITLE:=PicoClaw 网关
META_TITLE.en:=PicoClaw Gateway
META_DEPENDS:=+luci-app-picoclaw-ng
META_DESCRIPTION:=PicoClaw 的图形管理面板，默认 Gateway 模式，需要时临时打开 Launcher 面板改配置。
META_DESCRIPTION.en:=Lifecycle panel for PicoClaw: Gateway mode by default, Launcher panel on demand.
META_AUTHOR:=Gt841
META_ARCH:=x86_64 aarch64
META_TAGS:=networking service
META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/picoclaw
META_WEBSITE:=https://github.com/Gt841/luci-app-picoclaw-ng

include ../../meta.mk

# call BuildPackage - OpenWrt buildroot signature
