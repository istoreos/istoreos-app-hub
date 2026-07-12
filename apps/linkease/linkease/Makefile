#
# Copyright (C) 2015-2016 OpenWrt.org
# Copyright (C) 2020 jjm2473@gmail.com
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=linkease
PKG_SOURCE_DATE:=3.0.0
PKG_RELEASE:=1

LINKEASE_FULL_ARCH:=
ifeq ($(ARCH),x86_64)
LINKEASE_FULL_ARCH:=x86_64
else ifeq ($(ARCH),aarch64)
LINKEASE_FULL_ARCH:=aarch64
endif

PKG_SOURCE:=linkease-full-binary-$(PKG_SOURCE_DATE).tar.gz
PKG_SOURCE_URL:=https://github.com/linkease/linkease-desktop/releases/download/linkease-full-v$(PKG_SOURCE_DATE)/
PKG_HASH:=6ae7ddbe28ca07e9e2a51476b0ae7ffdef1d1fa3d4f9b48260be700c1fff0833
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-full-binary-$(PKG_SOURCE_DATE)

PKG_BUILD_PARALLEL:=1
PKG_USE_MIPS16:=0

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=net
	CATEGORY:=Network
	SUBMENU:=Web Servers/Proxies
	TITLE:=LinkEase - the file cloud
	DEPENDS:=@(x86_64||aarch64) +ca-bundle
	URL:=https://www.linkease.com/
endef

define Package/$(PKG_NAME)/description
  LinkEase is a file cloud
endef

define Package/$(PKG_NAME)/conffiles
/etc/config/linkease
endef

define Package/$(PKG_NAME)/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	[ -x /usr/bin/linkease-migrate.sh ] && /usr/bin/linkease-migrate.sh
	[ -f /etc/uci-defaults/linkease ] && /etc/uci-defaults/linkease && rm -f /etc/uci-defaults/linkease
	exit 0
fi
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/usr/lib/linkease $(1)/etc/config $(1)/etc/init.d $(1)/etc/uci-defaults
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/linkease-desktop $(1)/usr/bin/linkease-desktop
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/apptunnel-client $(1)/usr/bin/apptunnel-client
	$(INSTALL_BIN) ./files/linkease-config.sh $(1)/usr/bin/linkease-config.sh
	$(INSTALL_BIN) ./files/linkease-migrate.sh $(1)/usr/bin/linkease-migrate.sh
	$(INSTALL_CONF) ./files/linkease.config $(1)/etc/config/linkease
	$(INSTALL_BIN) ./files/linkease.init $(1)/etc/init.d/linkease
	$(INSTALL_BIN) ./files/linkease.uci-default $(1)/etc/uci-defaults/linkease
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
