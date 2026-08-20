from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


class LinkEasePackageContractTest(unittest.TestCase):
    def read_app(self, app, relative):
        return (REPO / "apps" / app / relative).read_text(encoding="utf-8")

    def makefile_installed_files(self, relative):
        paths = set()
        for line in (REPO / relative).read_text(encoding="utf-8").splitlines():
            if "$(INSTALL_BIN)" not in line and "$(INSTALL_CONF)" not in line:
                continue
            matches = re.findall(r"\$\(1\)(/\S+)", line)
            if matches:
                paths.add(matches[-1])
        return paths

    def luci_installed_files(self, relative):
        root = REPO / relative
        paths = set()
        for subdir, prefix in (
            ("htdocs", "/www/"),
            ("luasrc", "/usr/lib/lua/luci/"),
        ):
            base = root / subdir
            if not base.exists():
                continue
            for file in base.rglob("*"):
                if file.is_file():
                    paths.add(prefix + file.relative_to(base).as_posix())
        return paths

    def procd_instance_block(self, text, name=None):
        if name is None:
            pattern = re.compile(
                r"^[ \t]*procd_open_instance\b.*?^[ \t]*procd_close_instance\b",
                re.DOTALL | re.MULTILINE,
            )
        else:
            escaped = re.escape(name)
            pattern = re.compile(
                r"^[ \t]*procd_open_instance\s+(?:['\"]%s['\"]|%s)(?=\s|$|#).*?^[ \t]*procd_close_instance\b"
                % (escaped, escaped),
                re.DOTALL | re.MULTILINE,
            )
        match = pattern.search(text)
        self.assertIsNotNone(match, "missing procd instance block")
        return match.group(0)

    def test_standard_linkease_uses_legacy_runtime_only(self):
        makefile = self.read_app("linkease", "linkease/Makefile")
        common_makefile = self.read_app("linkease-common-bin", "linkease-common-bin/Makefile")
        init = self.read_app("linkease", "linkease/files/linkease.init")
        config = self.read_app("linkease", "linkease/files/linkease.config")
        helper = self.read_app(
            "linkease-common-bin", "linkease-common-bin/files/linkease-config.sh"
        )
        status = self.read_app(
            "linkease", "luci-app-linkease/luasrc/view/linkease_status.htm"
        )
        controller = self.read_app(
            "linkease", "luci-app-linkease/luasrc/controller/linkease.lua"
        )

        self.assertIn("PKG_NAME:=linkease", makefile)
        self.assertIn("PKG_ARCH_LINKEASE:=$(ARCH)", makefile)
        self.assertIn("ARCH_HEXCODE=8664", makefile)
        self.assertIn("ARCH_HEXCODE=aa64", makefile)
        self.assertIn("ARCH_HEXCODE=aa32", makefile)
        self.assertIn("ARCH_HEXCODE=1b0c", makefile)
        self.assertIn("PKG_SOURCE_VERSION:=$(ARCH_HEXCODE)", makefile)
        self.assertIn("PKG_SOURCE:=linkease-bin-$(PKG_SOURCE_DATE)-linux-$(PKG_ARCH_LINKEASE).tar.gz", makefile)
        self.assertIn("PKG_SOURCE_URL:=https://github.com/istoreos/istoreos-app-hub/releases/download/linkease-runtime-v$(PKG_SOURCE_DATE)/", makefile)
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/linkease-bin-$(PKG_SOURCE_DATE)-linux-$(PKG_ARCH_LINKEASE)", makefile)
        self.assertIn("634d3e1a807119badf98ae58f3e6e9815dacc22a5be31080228998ee0de6addd", makefile)
        self.assertIn("92d0c6f9d05a0ba283d03fef2b7f4675eee032c303e959b1e4198e12806510f9", makefile)
        self.assertIn("2a91f404c3eb190a8a828b5e41913595901de54664de518f0430c5544d71a914", makefile)
        self.assertNotIn("PKG_VERSION:=1.7.5", makefile)
        self.assertIn("PKG_SOURCE_DATE:=1.7.5", makefile)
        self.assertIn("DEPENDS:=@(arm||x86_64||aarch64) +linkease-common-bin", makefile)
        self.assertIn("PKGARCH:=all", makefile)
        self.assertNotIn("dl.istoreos.com/binary/LinkEase/LinuxStorage", makefile)
        self.assertNotIn("+linkmount", makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/linkease $(1)/usr/sbin/linkease", makefile)
        self.assertNotIn("$(1)/usr/sbin/heif-converter", makefile)
        self.assertNotIn("$(1)/usr/sbin/linkease-media", makefile)
        self.assertIn("PKG_NAME:=linkease-common-bin", common_makefile)
        self.assertIn("PKG_ARCH_LINKEASE:=$(ARCH)", common_makefile)
        self.assertIn("PKG_SOURCE_VERSION:=$(ARCH_HEXCODE)", common_makefile)
        self.assertIn("PKG_SOURCE:=linkease-common-bin-$(PKG_SOURCE_DATE)-linux-$(PKG_ARCH_LINKEASE).tar.gz", common_makefile)
        self.assertIn("PKG_SOURCE_URL:=https://github.com/istoreos/istoreos-app-hub/releases/download/linkease-runtime-v$(PKG_SOURCE_DATE)/", common_makefile)
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/linkease-common-bin-$(PKG_SOURCE_DATE)-linux-$(PKG_ARCH_LINKEASE)", common_makefile)
        self.assertIn("fffcabac6072feeb460aef0a31d395acf245b78ae2f5af6abd59411a1757935a", common_makefile)
        self.assertIn("1646db48f5a512b96a34971e5af82eacd5a51f32abab2c5e84f277c408a72eb8", common_makefile)
        self.assertIn("61f970245e1ae9783bc58280929e134fb0c94f5fc4e0e9a3deea117846b81e40", common_makefile)
        self.assertNotIn("PKG_VERSION:=1.7.5", common_makefile)
        self.assertIn("PKG_SOURCE_DATE:=1.7.5", common_makefile)
        self.assertIn("PKGARCH:=all", common_makefile)
        self.assertNotIn("linkease-binary-$(PKG_SOURCE_DATE).tar.gz", common_makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/heif-converter $(1)/usr/sbin/heif-converter", common_makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/linkease-media $(1)/usr/sbin/linkease-media", common_makefile)
        self.assertIn("$(INSTALL_BIN) ./files/linkease-config.sh $(1)/usr/sbin/linkease-config.sh", common_makefile)
        self.assertNotIn("$(INSTALL_BIN) ./files/linkease-config.sh $(1)/usr/sbin/linkease-config.sh", makefile)
        self.assertNotIn("$(1)/usr/sbin/linkease\n", common_makefile)
        self.assertNotIn("/etc/config/linkease", common_makefile)
        self.assertNotIn("/etc/init.d/linkease", common_makefile)
        self.assertNotIn("linkease-migrate.sh", makefile)
        self.assertNotIn("linkease-desktop", makefile)
        self.assertNotIn("apptunnel-client", makefile)
        self.assertNotIn("linkease-full", makefile)

        self.assertIn("PROG=/usr/sbin/linkease", init)
        self.assertIn("LOCAL_API=/var/run/linkease.sock", init)
        self.assertIn("linkeasefull_enabled()", init)
        self.assertIn('uci -q get linkeasefull.@linkeasefull[0].enabled', init)
        self.assertIn("please disable linkeasefull before starting linkease", init)
        self.assertNotIn('uci -q set linkeasefull.@linkeasefull[0].enabled="0"', init)
        self.assertNotIn('uci -q set linkeaselite.@linkeaselite[0].enabled="0"', init)
        block = self.procd_instance_block(init)
        self.assertIn('procd_set_param command "$PROG"', block)
        self.assertIn('procd_append_param command --deviceAddr ":$port" --localApi "$LOCAL_API"', block)
        self.assertIn('[ "$allowPublic" = "1" ] && procd_append_param command --allowPublic', block)
        self.assertNotIn("PROG_DESKTOP", init)
        self.assertNotIn("PROG_APPTUNNEL", init)

        self.assertIn("option port '8897'", config)
        self.assertNotIn("desktop_port", config)
        self.assertNotIn("desktop_base_path", config)
        self.assertNotIn("edition", config)
        self.assertIn("Click to open LinkEase", status)
        self.assertIn("Please disable LinkEase Full before starting LinkEase", status)
        self.assertNotIn("Click to open LinkEase Full", status)
        self.assertNotIn("Click to open LinkEase Legacy", status)
        self.assertIn('pidof linkease >/dev/null', controller)
        self.assertIn('conflict = full_enabled', controller)
        self.assertIn('conflict_service = full_enabled and "linkeasefull" or ""', controller)
        self.assertNotIn('pidof linkease-full >/dev/null', controller)
        self.assertNotIn("desktop_running", controller)
        self.assertNotIn("apptunnel_running", controller)
        self.assertNotIn("desktop_port", helper)
        self.assertNotIn("desktop_base_path", helper)
        self.assertNotIn("desktop_url", helper)
        self.assertIn("ensure_linkease_config()", helper)
        self.assertNotIn("sync_linkeasefull_local_home()", helper)
        self.assertIn("uci -q set linkease.@linkease[0].enabled='0'", helper)
        self.assertIn("uci -q set linkease.@linkease[0].port='8897'", helper)
        self.assertIn("uci -q set linkease.@linkease[0].allowPublic='0'", helper)
        self.assertNotIn("linkeasefull.@linkeasefull[0].data_root_parent", helper)
        self.assertIn('uci set "linkease.@linkease[0].local_home=$2"', helper)
        self.assertIn("uci -q set quickstart.main=main", helper)
        self.assertIn('uci set "quickstart.main.main_dir=$ROOT_DIR"', helper)
        self.assertIn("uci commit linkease", helper)

    def test_legacy_luci_file_proxy_uses_shared_unix_socket_only(self):
        backend = self.read_app(
            "linkeasefile", "luci-lib-linkeasefile/luasrc/controller/linkease_file.lua"
        )
        controller = self.read_app(
            "linkease", "luci-app-linkease/luasrc/controller/linkease.lua"
        )
        status = self.read_app(
            "linkease", "luci-app-linkease/luasrc/view/linkease_status.htm"
        )
        full_init = self.read_app("linkeasefull", "linkeasefull/files/linkeasefull.init")

        self.assertIn('local LINKEASE_UNIX = "/var/run/linkease.sock"', backend)
        self.assertNotIn("LINKEASE_FULL_LEGACY_HOST", backend)
        self.assertNotIn("LINKEASE_FULL_LEGACY_PORT", backend)
        self.assertNotIn("connect_linkease_backend()", backend)
        self.assertIn('nixio.socket("unix", "stream")', backend)
        self.assertNotIn('nixio.socket("inet", "stream")', backend)
        self.assertIn("sock:connect(LINKEASE_UNIX)", backend)
        self.assertNotIn("sock:connect(LINKEASE_FULL_LEGACY_HOST, LINKEASE_FULL_LEGACY_PORT)", backend)
        self.assertNotIn('return sock, "tcp"', backend)
        self.assertNotIn("backend_request_uri(backend_kind)", backend)
        self.assertNotIn('local prefix = "/cgi-bin/luci/linkease"', backend)
        self.assertIn('entry({"linkease"}, call("linkease_backend")).leaf=true', backend)
        self.assertIn('entry({"admin", "services", "linkease", "file"}, call("linkease_file_template"))', backend)
        self.assertNotIn("linkease_file_template", controller)
        self.assertNotIn('{"admin", "services", "linkease", "file"}', controller)
        self.assertIn('running = (sys.call("pidof linkease >/dev/null") == 0)', controller)
        self.assertIn("Click to open Files", status)
        self.assertIn("LOCAL_API=/var/run/linkease.sock", full_init)
        self.assertIn('rm -f "$LOCAL_API"', full_init)
        self.assertIn('--localApi "$LOCAL_API"', full_init)

    def test_linkeasefull_is_dependent_full_runtime_package(self):
        makefile = self.read_app("linkeasefull", "linkeasefull/Makefile")
        init = self.read_app("linkeasefull", "linkeasefull/files/linkeasefull.init")
        config = self.read_app("linkeasefull", "linkeasefull/files/linkeasefull.config")
        cbi = self.read_app("linkeasefull", "luci-app-linkeasefull/luasrc/model/cbi/linkeasefull.lua")
        controller = self.read_app(
            "linkeasefull", "luci-app-linkeasefull/luasrc/controller/linkeasefull.lua"
        )
        status = self.read_app(
            "linkeasefull", "luci-app-linkeasefull/luasrc/view/linkeasefull_status.htm"
        )
        meta = self.read_app("linkeasefull", "app-meta-linkeasefull/Makefile")
        defaults = self.read_app("linkeasefull", "linkeasefull/files/linkeasefull.uci-default")
        meta_config = self.read_app("linkeasefull", "app-meta-linkeasefull/config.sh")

        self.assertIn("PKG_NAME:=linkeasefull", makefile)
        self.assertIn("PKG_ARCH_LINKEASE:=$(ARCH)", makefile)
        self.assertNotIn("PKG_VERSION:=3.0.9", makefile)
        self.assertIn("PKG_SOURCE_DATE:=3.0.11", makefile)
        self.assertIn("ARCH_HEXCODE=8664", makefile)
        self.assertIn("ARCH_HEXCODE=aa64", makefile)
        self.assertIn("PKG_SOURCE_VERSION:=$(ARCH_HEXCODE)", makefile)
        self.assertIn("LINKEASE_RUNTIME_ARCH:=amd64", makefile)
        self.assertIn("LINKEASE_RUNTIME_ARCH:=arm64", makefile)
        self.assertIn("PKG_SOURCE:=linkease-runtime-$(PKG_SOURCE_DATE)-linux-$(LINKEASE_RUNTIME_ARCH).tar.gz", makefile)
        self.assertIn("PKG_SOURCE_URL:=https://github.com/istoreos/istoreos-app-hub/releases/download/linkeasefull-runtime-v$(PKG_SOURCE_DATE)/", makefile)
        self.assertIn("PKG_BUILD_DIR:=$(BUILD_DIR)/linkease-runtime-$(PKG_SOURCE_DATE)-linux-$(LINKEASE_RUNTIME_ARCH)", makefile)
        self.assertNotIn("linkease-desktop", makefile)
        self.assertIn("506028ba73983bfba264231bd2276152e1525b5f7dcb023f2256a8471bb856b0", makefile)
        self.assertIn("4dae89c14b3a8d56bae64b751eb67aa4ddf06526aed30aa6e86c9bbe51dde389", makefile)
        self.assertNotIn("TAR_CMD=", makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/linkease-full $(1)/usr/bin/linkease-full", makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/linkremote-agent $(1)/usr/bin/linkremote-agent", makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/hostlink $(1)/usr/bin/hostlink", makefile)
        self.assertIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/linkmount_bin/linkmount_bin $(1)/usr/libexec/linkeasefull/linkmount_bin/linkmount_bin", makefile)
        self.assertIn("$(CP) $(PKG_BUILD_DIR)/linkmount_bin/lib $(1)/usr/libexec/linkeasefull/linkmount_bin/lib", makefile)
        self.assertNotIn("$(PKG_BUILD_DIR)/scripts", makefile)
        self.assertNotIn("/usr/libexec/linkeasefull/scripts", makefile)
        self.assertIn("DEPENDS:=@(x86_64||aarch64) +linkease-common-bin +ca-bundle +cifsmount +kmod-fs-cifs", makefile)
        self.assertNotIn("+linkease +luci-app-linkease", makefile)
        self.assertNotIn("$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/heif-converter $(1)/usr/bin/heif-converter", makefile)
        self.assertNotIn("/etc/config/linkease\n", makefile)
        self.assertNotIn("/etc/init.d/linkease\n", makefile)
        self.assertNotIn("/usr/sbin/linkease", makefile)
        self.assertNotIn("apptunnel-client", makefile)
        self.assertIn("PKGARCH:=all", makefile)

        self.assertIn("PROG=/usr/bin/linkease-full", init)
        self.assertIn("config_load linkeasefull", init)
        self.assertIn("linkease_enabled()", init)
        self.assertIn('uci -q get linkease.@linkease[0].enabled', init)
        self.assertIn("please disable linkease before starting linkeasefull", init)
        self.assertNotIn('uci -q set linkease.@linkease[0].enabled="0"', init)
        self.assertNotIn('uci -q set linkeaselite.@linkeaselite[0].enabled="0"', init)
        self.assertNotIn("SERVER_HOST=", init)
        self.assertIn("LINKEASE_FULL_PORT=19290", init)
        self.assertIn("LINKEASE_BASE_PATH=/apps/", init)
        self.assertIn("LINKEASE_LEGACY_ADDR=0.0.0.0:8897", init)
        self.assertIn("LOCAL_API=/var/run/linkease.sock", init)
        self.assertIn("DATA_ROOT_WAIT_SECONDS=${LINKEASEFULL_DATA_ROOT_WAIT_SECONDS:-60}", init)
        self.assertIn('rm -f "$LOCAL_API"', init)
        self.assertNotIn("SERVER_PORT=", init)
        self.assertNotIn("SERVER_BASE_PATH=", init)
        self.assertNotIn("LINKEASE_AUTH_PROVIDER=", init)
        self.assertNotIn("LINKEASE_EDITION=", init)
        self.assertNotIn("LINKEASE_APPTUNNEL_INTERNAL_ADDR=", init)
        self.assertNotIn("LINKEASE_APPTUNNEL_LEGACY_ADDR=", init)
        self.assertNotIn("LINKEASE_APPTUNNEL_LOCAL_API=", init)
        self.assertIn('--host "0.0.0.0"', init)
        self.assertIn('--port "$LINKEASE_FULL_PORT"', init)
        self.assertIn('--basePath "$LINKEASE_BASE_PATH"', init)
        self.assertIn('--deviceAddr "$LINKEASE_LEGACY_ADDR"', init)
        self.assertIn('--localApi "$LOCAL_API"', init)
        self.assertNotIn("LINKEASE_APPTUNNEL_DATA_DIR=", init)
        self.assertNotIn("APPTUNNEL_MOUNTREMOTE_", init)
        self.assertNotIn("MOUNTREMOTE_ALLOWED_MOUNT_PREFIX=", init)
        self.assertNotIn("LINKEASE_LINKMOUNT_BIN=", init)
        self.assertNotIn("LINKEASE_LINKMOUNT_LIB_DIR=", init)
        self.assertIn("is_allowed_data_root_parent()", init)
        self.assertIn("wait_for_data_root_parent()", init)
        self.assertIn('wait_for_data_root_parent "$data_root_parent"', init)
        self.assertIn("is_persistent_data_root_parent()", init)
        self.assertIn('uci -q get linkease.@linkease[0].local_home', init)
        self.assertNotIn('linkeasefull.@linkeasefull[0].data_root_parent', init)
        self.assertIn("data root is not initialized; starting for first-run setup", init)
        self.assertNotIn("please choose a persistent disk storage path", init)
        self.assertNotIn("data_root_parent=/tmp/linkeasefull", init)
        self.assertNotIn("config_get port", init)
        self.assertNotIn("config_get base_path", init)

        self.assertIn("option enabled '1'", config)
        self.assertNotIn("option port", config)
        self.assertNotIn("option base_path", config)
        self.assertNotIn("option data_root_parent", config)
        self.assertIn('Map("linkeasefull"', cbi)
        self.assertIn("ListValue, \"_local_home\"", cbi)
        self.assertIn('get_first("linkease", "linkease", "local_home")', cbi)
        self.assertIn("Choose a mounted persistent disk", cbi)
        self.assertIn("/tmp and system paths cannot be used", cbi)
        self.assertNotIn("\"base_path\"", cbi)
        self.assertNotIn("translate(\"Port\")", cbi)
        self.assertIn('/etc/config/linkeasefull', controller)
        self.assertIn('pidof linkease-full >/dev/null', controller)
        self.assertIn('conflict = linkease_enabled', controller)
        self.assertIn('conflict_service = linkease_enabled and "linkease" or ""', controller)
        self.assertIn("full_port = 19290", controller)
        self.assertIn("legacy_port = 8897", controller)
        self.assertIn('base_path = "/apps/"', controller)
        self.assertIn('uci:get("network", "lan", "ipaddr")', controller)
        self.assertIn('proxy_prefix_enabled = uhttpd_has_apps_proxy_prefix()', controller)
        self.assertIn('uci:get_list("uhttpd", "main", "proxy_prefix")', controller)
        self.assertIn('mapping == "/apps=http://127.0.0.1:19290"', controller)
        self.assertIn('entry({"admin", "services", "linkeasefull", "auth"}, call("linkeasefull_auth")).leaf = true', controller)
        self.assertLess(
            controller.index('entry({"admin", "services", "linkeasefull", "auth"}, call("linkeasefull_auth")).leaf = true'),
            controller.index('if not nixio.fs.access("/etc/config/linkeasefull") then'),
        )
        self.assertIn('http.getcookie(key)', controller)
        self.assertIn('"sysauth_https", "sysauth_http", "sysauth"', controller)
        self.assertIn('util.ubus("session", "get", { ubus_rpc_session = sid })', controller)
        self.assertIn('"linkease_openwrt_sid=" .. sid .. "; Path=/apps; HttpOnly; SameSite=Lax"', controller)
        self.assertIn("valid_apps_return(value)", controller)
        self.assertIn('path == "/apps"', controller)
        self.assertIn('prefix == "/apps/" or prefix == "/apps?" or prefix == "/apps#"', controller)
        self.assertIn('value:match("^(https?://)([^/]+)(/.*)$")', controller)
        self.assertIn('request_host .. ":19290"', controller)
        self.assertIn('lan_host .. ":19290"', controller)
        self.assertIn("valid_cookie_value(sid)", controller)
        self.assertIn('target = "/apps/"', controller)
        self.assertNotIn("get_first(\"linkeasefull\", \"linkeasefull\", \"port\")", controller)
        self.assertNotIn("get_first(\"linkeasefull\", \"linkeasefull\", \"base_path\")", controller)
        self.assertNotIn("linkease_file_template", controller)
        self.assertNotIn('{"admin", "services", "linkease", "file"}', controller)
        self.assertIn("Open Full Entry", status)
        self.assertIn("Open Standard Entry", status)
        self.assertIn("st.proxy_prefix_enabled", status)
        self.assertIn("Please disable LinkEase before starting LinkEase Full", status)
        self.assertIn('window.location.protocol + "//" + window.location.host + "/apps/"', status)
        self.assertIn('st.lan_ip || window.location.hostname', status)
        self.assertIn("st.full_port || 19290", status)
        self.assertIn("st.legacy_port || 8897", status)
        self.assertIn('"/apps/"', status)
        self.assertNotIn("basePath", status)
        self.assertIn("PKG_VERSION:=3.0.11", meta)
        self.assertIn("META_DEPENDS:=+linkease-common-bin +linkeasefull +luci-app-linkeasefull +luci-lib-linkeasefile +luci-i18n-linkeasefull-zh-cn", meta)
        self.assertNotIn("+linkease +luci-app-linkease", meta)
        self.assertIn("复用独立的易有云文件管理入口", meta)
        self.assertIn("META_LUCI_ENTRY:=/cgi-bin/luci/admin/services/linkeasefull", meta)
        self.assertFalse((REPO / "apps/linkeasefull/luci-app-linkeasefull/htdocs/luci-static/linkeasefile").exists())
        self.assertFalse((REPO / "apps/linkease/luci-app-linkease/htdocs/luci-static/linkeasefile").exists())
        self.assertFalse((REPO / "apps/linkease/luci-app-linkease/luasrc/controller/linkease_backend.lua").exists())
        self.assertTrue((REPO / "apps/linkeasefile/luci-lib-linkeasefile/htdocs/luci-static/linkeasefile").exists())
        self.assertTrue((REPO / "apps/linkeasefile/luci-lib-linkeasefile/luasrc/controller/linkease_file.lua").exists())
        self.assertNotIn("set_default port", defaults)
        self.assertNotIn("set_default base_path", defaults)
        self.assertIn("/etc/init.d/linkeasefull enable", defaults)
        self.assertNotIn("/etc/init.d/linkeasefull restart", defaults)
        self.assertNotIn("/etc/init.d/linkease enable", defaults)
        self.assertNotIn("/etc/init.d/linkease restart", defaults)
        self.assertNotIn("set linkease.@linkease[0].enabled", meta_config)
        self.assertNotIn("commit linkease\n", meta_config)
        self.assertNotIn("/etc/init.d/linkease restart", meta_config)

    def test_linkease_packages_do_not_install_overlapping_paths(self):
        packages = {
            "linkease": (
                self.makefile_installed_files("apps/linkease/linkease/Makefile")
                | self.luci_installed_files("apps/linkease/luci-app-linkease")
            ),
            "linkease-common-bin": self.makefile_installed_files(
                "apps/linkease-common-bin/linkease-common-bin/Makefile"
            ),
            "linkeasefile": self.luci_installed_files(
                "apps/linkeasefile/luci-lib-linkeasefile"
            ),
            "linkeasefull": (
                self.makefile_installed_files("apps/linkeasefull/linkeasefull/Makefile")
                | self.luci_installed_files("apps/linkeasefull/luci-app-linkeasefull")
            ),
        }

        names = sorted(packages)
        for index, left_name in enumerate(names):
            for right_name in names[index + 1 :]:
                with self.subTest(left=left_name, right=right_name):
                    self.assertEqual(
                        set(),
                        packages[left_name] & packages[right_name],
                    )

    def test_syncapps_maps_linkeasefull_slots(self):
        text = (REPO / "syncapps.yaml").read_text(encoding="utf-8")

        self.assertIn("    linkeasefull:", text)
        self.assertIn("local: apps/linkeasefull/linkeasefull", text)
        self.assertIn("remote: nas-packages/network/services/linkeasefull", text)
        self.assertIn("local: apps/linkeasefull/luci-app-linkeasefull", text)
        self.assertIn("remote: nas-packages-luci/luci/luci-app-linkeasefull", text)
        self.assertIn("local: apps/linkeasefull/app-meta-linkeasefull", text)
        self.assertIn("remote: openwrt-app-meta/applications/app-meta-linkeasefull", text)
        self.assertIn("    linkease-common-bin:", text)
        self.assertIn("local: apps/linkease-common-bin/linkease-common-bin", text)
        self.assertIn("remote: nas-packages/network/services/linkease-common-bin", text)
        self.assertIn("    linkeasefile:", text)
        self.assertIn("local: apps/linkeasefile/luci-lib-linkeasefile", text)
        self.assertIn("remote: nas-packages-luci/luci/luci-lib-linkeasefile", text)

    def test_apps_catalog_contains_linkeasefull(self):
        text = (REPO / "docs/apps-catalog.min.md").read_text(encoding="utf-8")
        data = json.loads((REPO / "docs/apps-catalog.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in data}

        self.assertIn("- linkeasefull — 易有云完整版 —", text)
        self.assertIn("linkeasefull", ids)


if __name__ == "__main__":
    unittest.main()
