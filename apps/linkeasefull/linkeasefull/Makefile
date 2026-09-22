#
# Copyright (C) 2026 iStoreOS
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk

PKG_ARCH_LINKEASE:=$(ARCH)

PKG_NAME:=linkeasefull
# use PKG_SOURCE_DATE instead of PKG_VERSION for compitable
PKG_SOURCE_DATE:=3.0.20
PKG_RELEASE:=2

ARCH_HEXCODE:=
ifeq ($(ARCH),x86_64)
ARCH_HEXCODE=8664
LINKEASE_RUNTIME_ARCH:=amd64
PKG_HASH:=f1456c06e3fd5dcdf7fa728fdf102ab4169c0e8ed9308ddae8a9b9faee278dea
else ifeq ($(ARCH),aarch64)
ARCH_HEXCODE=aa64
LINKEASE_RUNTIME_ARCH:=arm64
PKG_HASH:=d3c268aced92425289f968477b5f4d81e6295a10ad39f15773f5eba451f1b5f6
endif

PKG_SOURCE_VERSION:=$(ARCH_HEXCODE)
PKG_SOURCE:=linkease-runtime-$(PKG_SOURCE_DATE)-linux-$(LINKEASE_RUNTIME_ARCH).tar.gz
PKG_SOURCE_URL:=https://github.com/istoreos/istoreos-app-hub/releases/download/linkeasefull-runtime-v$(PKG_SOURCE_DATE)/
PKG_BUILD_DIR:=$(BUILD_DIR)/linkease-runtime-$(PKG_SOURCE_DATE)-linux-$(LINKEASE_RUNTIME_ARCH)

PKG_BUILD_PARALLEL:=1
PKG_USE_MIPS16:=0

include $(INCLUDE_DIR)/package.mk

define Package/linkease-app-entry
	SECTION:=net
	CATEGORY:=Network
	SUBMENU:=Web Servers/Proxies
	TITLE:=LinkEase application entry arbiter and fallback gateway
	DEPENDS:=@(x86_64||aarch64) +ca-bundle +luci-lib-linkeaseauth
	PKGARCH:=all
	URL:=https://www.linkease.com/
endef

define Package/linkease-app-entry/description
  Owns the shared /apps listener, launches LinkEaseFull directly when healthy,
  and runs the manifest-driven fallback gateway only when LinkEaseFull is not available.
endef

define Package/linkease-app-entry/conffiles
/etc/config/linkease_app_entry
endef

define Package/linkease-app-entry/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	[ -f /etc/uci-defaults/linkease-app-entry ] && /etc/uci-defaults/linkease-app-entry && rm -f /etc/uci-defaults/linkease-app-entry
fi
exit 0
endef

define Package/$(PKG_NAME)
	SECTION:=net
	CATEGORY:=Network
	SUBMENU:=Web Servers/Proxies
	TITLE:=LinkEase Full - the local web desktop
	DEPENDS:=@(x86_64||aarch64) +linkease-app-entry +linkease-common-bin +ca-bundle +cifsmount +kmod-fs-cifs
	PKGARCH:=all
	URL:=https://www.linkease.com/
endef

define Package/$(PKG_NAME)/description
  LinkEase Full provides the local web desktop entry for LinkEase and reuses the shared LinkEase file entry.
endef

define Package/$(PKG_NAME)/conffiles
/etc/config/linkeasefull
endef

define Package/$(PKG_NAME)/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	[ -f /etc/uci-defaults/linkeasefull ] && /etc/uci-defaults/linkeasefull && rm -f /etc/uci-defaults/linkeasefull
	exit 0
fi
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/usr/libexec/linkeasefull/linkmount_bin $(1)/etc/config $(1)/etc/init.d $(1)/etc/uci-defaults
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/linkease-full $(1)/usr/bin/linkease-full
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/linkremote-agent $(1)/usr/bin/linkremote-agent
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/hostlink $(1)/usr/bin/hostlink
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/linkmount_bin/linkmount_bin $(1)/usr/libexec/linkeasefull/linkmount_bin/linkmount_bin
	$(CP) $(PKG_BUILD_DIR)/linkmount_bin/lib $(1)/usr/libexec/linkeasefull/linkmount_bin/lib
	$(CP) $(PKG_BUILD_DIR)/linkmount_bin/ver.json $(1)/usr/libexec/linkeasefull/linkmount_bin/ver.json
	$(INSTALL_CONF) ./files/linkeasefull.config $(1)/etc/config/linkeasefull
	$(INSTALL_BIN) ./files/linkeasefull.init $(1)/etc/init.d/linkeasefull
	$(INSTALL_BIN) ./files/linkeasefull.uci-default $(1)/etc/uci-defaults/linkeasefull
endef

define Package/linkease-app-entry/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/etc/config $(1)/etc/init.d $(1)/etc/uci-defaults
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/linkease-app-entryd $(1)/usr/sbin/linkease-app-entryd
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/linkease-app-gateway $(1)/usr/sbin/linkease-app-gateway
	$(INSTALL_CONF) ./files/linkease-app-entry.config $(1)/etc/config/linkease_app_entry
	$(INSTALL_BIN) ./files/linkease-app-entry.init $(1)/etc/init.d/linkease-app-entry
	$(INSTALL_BIN) ./files/linkease-app-entry.uci-default $(1)/etc/uci-defaults/linkease-app-entry
endef

$(eval $(call BuildPackage,linkease-app-entry))
$(eval $(call BuildPackage,$(PKG_NAME)))
