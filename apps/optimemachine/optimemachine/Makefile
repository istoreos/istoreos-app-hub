include $(TOPDIR)/rules.mk
PKG_NAME:=optimemachine
PKG_VERSION:=0.2.0-otm17-rc1
PKG_RELEASE:=1
include ./release.mk
PKG_SOURCE:=optimemachine-$(PKG_VERSION)-$(ARCH).tar.gz
PKG_SOURCE_URL?=https://fw.koolcenter.com/binary/optimemachine/releases/
PKG_HASH:=$(OPTIMEMACHINE_HASH_$(ARCH))
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_PARALLEL:=1
STRIP:=true
RSTRIP:=:
include $(INCLUDE_DIR)/package.mk

define Package/optimemachine
 SECTION:=admin
 CATEGORY:=System
 TITLE:=时光机
 DEPENDS:=@(x86_64||aarch64) +linkspace +linkease-app-entry +block-mount +rpcd +ucode +ucode-mod-fs +ucode-mod-ubus
endef

define Build/Configure
endef
define Build/Compile
endef

define Package/optimemachine/preinst
#!/bin/sh
[ -n "$${IPKG_INSTROOT:-}" ] && exit 0
if [ -x /usr/sbin/optimemachine_bin ] && [ -f /etc/optimemachine/config.json ]; then
 /usr/sbin/optimemachine_bin maintenance-check >/dev/null || exit 1
 if /etc/init.d/optimemachine enabled; then touch /var/run/optimemachine-package-enable; fi
 if [ -S /var/run/optimemachine.sock ]; then touch /var/run/optimemachine-package-restart; /etc/init.d/optimemachine stop || exit 1; fi
 /usr/sbin/optimemachine_bin maintenance-check >/dev/null || { /etc/init.d/optimemachine start; exit 1; }
fi
exit 0
endef
define Package/optimemachine/conffiles
/etc/config/optimemachine
endef

define Package/optimemachine/postinst
#!/bin/sh
root="$${IPKG_INSTROOT:-}"
legacy="$${root}/usr/share/linkeasefull/desktop-apps.d/25-optimemachine.json"
if [ ! -e "$${legacy}" ] && [ ! -L "$${legacy}" ]; then
 mkdir -p "$${legacy%/*}"
 ln -s /usr/share/optimemachine/optimemachine-plugin.json "$${legacy}" || exit $$?
fi
[ -n "$${IPKG_INSTROOT:-}" ] && exit 0
/usr/libexec/optimemachine-package postinst
endef

define Package/optimemachine/prerm
#!/bin/sh
root="$${IPKG_INSTROOT:-}"
if [ -z "$${root}" ]; then /usr/libexec/optimemachine-package prerm || exit 1; fi
for directory in /usr/share/linkease/apps.d /usr/share/linkeasefull/desktop-apps.d; do
 registration="$${root}$${directory}/25-optimemachine.json"
 if [ "$$(readlink "$${registration}" 2>/dev/null)" = /usr/share/optimemachine/optimemachine-plugin.json ]; then rm -f "$${registration}"; fi
done
rmdir "$${root}/usr/share/linkeasefull/desktop-apps.d" 2>/dev/null || true
exit 0
endef

define Package/optimemachine/install
 $(INSTALL_DIR) $(1)/usr/sbin $(1)/usr/bin $(1)/etc/init.d $(1)/etc/config $(1)/usr/libexec $(1)/usr/share/optimemachine/www $(1)/usr/share/rpcd/acl.d $(1)/usr/share/linkease/apps.d
 $(INSTALL_BIN) $(PKG_BUILD_DIR)/optimemachine_bin $(1)/usr/sbin/optimemachine_bin
 $(CP) ./files/* $(1)/
 ln -sf /usr/share/optimemachine/optimemachine-plugin.json $(1)/usr/share/linkease/apps.d/25-optimemachine.json
endef
$(eval $(call BuildPackage,optimemachine))
