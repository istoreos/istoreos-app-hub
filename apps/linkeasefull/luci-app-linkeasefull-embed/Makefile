#
# Copyright (C) 2026 iStoreOS
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-linkeasefull-embed
PKG_VERSION:=1.0.0
PKG_RELEASE:=2

PKG_BUILD_PARALLEL:=1
PKG_USE_MIPS16:=0

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=luci
	CATEGORY:=LuCI
	SUBMENU:=3. Applications
	TITLE:=LinkEaseFull LuCI desktop embed
	DEPENDS:=+linkeasefull +luci-base +luci-theme-istorenas +luci-proto-bonding
	PKGARCH:=all
endef

define Package/$(PKG_NAME)/description
  Register OpenWrt LuCI as a LinkEaseFull desktop module and provide embedded-mode assets.
endef

define Package/$(PKG_NAME)/prerm
#!/bin/sh
if [ "$${IPKG_INSTROOT}" = "" ]; then
	if [ "$$(readlink /usr/share/linkeasefull/desktop-apps.d/15-openwrt-luci.json 2>/dev/null)" = "/usr/share/linkeasefull/openwrt-luci/openwrt-luci.json" ]; then
		rm -f /usr/share/linkeasefull/desktop-apps.d/15-openwrt-luci.json
	fi
fi
exit 0
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/usr/share/linkeasefull/openwrt-luci $(1)/usr/share/linkeasefull/desktop-apps.d
	$(INSTALL_DIR) $(1)/www/luci-static/linkeasefull-embed
	$(INSTALL_DIR) $(1)/www/luci-static/resources/protocol
	$(INSTALL_DATA) ./files/openwrt-luci/openwrt-luci.json $(1)/usr/share/linkeasefull/openwrt-luci/openwrt-luci.json
	$(INSTALL_DATA) ./files/openwrt-luci/openwrt.svg $(1)/usr/share/linkeasefull/openwrt-luci/openwrt.svg
	$(INSTALL_DATA) ./files/www/embed.css $(1)/www/luci-static/linkeasefull-embed/embed.css
	$(INSTALL_DATA) ./files/www/embed-prelude.js $(1)/www/luci-static/linkeasefull-embed/embed-prelude.js
	$(INSTALL_DATA) ./files/protocol/directip.js $(1)/www/luci-static/resources/protocol/directip.js
	$(INSTALL_DATA) ./files/protocol/bonding.js $(1)/www/luci-static/resources/protocol/bonding.js
	$(INSTALL_DATA) ./files/protocol/wwan.js $(1)/www/luci-static/resources/protocol/wwan.js
	ln -sf /usr/share/linkeasefull/openwrt-luci/openwrt-luci.json $(1)/usr/share/linkeasefull/desktop-apps.d/15-openwrt-luci.json
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
