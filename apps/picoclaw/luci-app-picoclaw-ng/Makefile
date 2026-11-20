# SPDX-License-Identifier: MIT
#
# LuCI app for PicoClaw (Gateway / Launcher).
# Layout follows the iStoreOS app-hub convention: apps/<id>/<package>/.
# The directory name must stay equal to PKG_NAME (luci.mk derives it from CURDIR).

include $(TOPDIR)/rules.mk

PKG_VERSION:=3.0.2
PKG_RELEASE:=1
PKG_MAINTAINER:=Gt841 <Gt841@users.noreply.github.com>
PKG_LICENSE:=MIT

LUCI_TITLE:=LuCI app for PicoClaw (Gateway / Launcher)
LUCI_DESCRIPTION:=Lifecycle panel for PicoClaw with arch-aware core install
LUCI_PKGARCH:=all

define Package/luci-app-picoclaw-ng/conffiles
/etc/config/picoclaw
endef

# Post-install (cache flush, rpcd reload) comes from luci.mk defaults.

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
