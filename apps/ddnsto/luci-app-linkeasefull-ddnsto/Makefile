# SPDX-License-Identifier: Apache-2.0

include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-linkeasefull-ddnsto
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

include $(INCLUDE_DIR)/package.mk

define Package/luci-app-linkeasefull-ddnsto
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=3. Applications
  TITLE:=LinkEaseFull desktop entry for DDNSTO
  DEPENDS:=+linkeasefull +luci-app-linkeasefull-embed +luci-app-ddnsto
  PKGARCH:=all
endef

define Package/luci-app-linkeasefull-ddnsto/description
  Registers the DDNSTO LuCI plugin as a LinkEaseFull desktop web module.
endef

define Package/luci-app-linkeasefull-ddnsto/prerm
#!/bin/sh
if [ "$$(readlink /usr/share/linkeasefull/desktop-apps.d/16-ddnsto.json 2>/dev/null)" = "/usr/share/linkeasefull/ddnsto/ddnsto.json" ]; then
	rm -f /usr/share/linkeasefull/desktop-apps.d/16-ddnsto.json
fi
exit 0
endef

define Build/Compile
endef

define Package/luci-app-linkeasefull-ddnsto/install
	$(INSTALL_DIR) $(1)/usr/share/linkeasefull/ddnsto $(1)/usr/share/linkeasefull/desktop-apps.d
	$(INSTALL_DATA) ./files/ddnsto/ddnsto.json $(1)/usr/share/linkeasefull/ddnsto/ddnsto.json
	$(INSTALL_DATA) ./files/ddnsto/logo.png $(1)/usr/share/linkeasefull/ddnsto/logo.png
	ln -sf /usr/share/linkeasefull/ddnsto/ddnsto.json $(1)/usr/share/linkeasefull/desktop-apps.d/16-ddnsto.json
endef

$(eval $(call BuildPackage,luci-app-linkeasefull-ddnsto))
