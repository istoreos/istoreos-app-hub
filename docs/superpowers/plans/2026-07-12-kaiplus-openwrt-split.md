# KaiPlus OpenWrt Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make KaiPlus an independent OpenWrt/iStore plugin on `http://<router-ip>:8189/apps/kaiplus/` while LinkEase Desktop only reverse proxies the standalone service at `/apps/kaiplus/`.

**Architecture:** KaiPlus owns its process, UCI config, LuCI page, app-meta entry, and standalone URL. LinkEase no longer packages or starts an embedded KaiPlus runtime; it disables embedded runtime startup and only sets `KAIPLUS_PROXY_TARGET` when `/etc/init.d/kaiplus` exists.

**Tech Stack:** OpenWrt package Makefiles, `/etc/rc.common` shell init scripts, LuCI Lua MVC, iStore app-meta shell scripts, Python `unittest` contract tests.

## Global Constraints

- Work from `/projects/workspace-linkease-ubuntu/openwrt-apps/istoreos-app-hub`.
- Use `rtk` before shell commands in this repository.
- Do not add a package dependency from `linkease` to `kaiplus` or from `kaiplus` to `linkease`.
- KaiPlus standalone URL must be `http://<router-ip>:8189/apps/kaiplus/`.
- LinkEase Desktop proxy URL must remain `http://<router-ip>:<linkease-desktop-port>/apps/kaiplus/`.
- KaiPlus base path must be `/apps/kaiplus/`.
- LinkEase must not install `/usr/lib/linkease/kaiplus`.
- LinkEase must not start an embedded KaiPlus runtime.
- Do not remove user data directories.

---

## File Structure

- `apps/kaiplus/tests/test_kaiplus_openwrt_contract.py`: new contract tests for standalone KaiPlus defaults, init args, app-meta config, app-meta entry, and LuCI open URL data.
- `apps/kaiplus/kaiplus/files/kaiplus.config`: standalone default UCI values.
- `apps/kaiplus/kaiplus/files/kaiplus.init`: procd launch config for standalone KaiPlus, including `--base-path`.
- `apps/kaiplus/app-meta-kaiplus/config.sh`: iStore install-time UCI defaults.
- `apps/kaiplus/app-meta-kaiplus/entry.sh`: iStore app open/status data.
- `apps/kaiplus/luci-app-kaiplus/luasrc/controller/kaiplus.lua`: status JSON includes `base_path`.
- `apps/kaiplus/luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm`: open button uses port and base path.
- `apps/linkease/tests/test_linkease_full_contract.py`: update contract from embedded KaiPlus to standalone proxy.
- `apps/linkease/linkease/Makefile`: stop packaging embedded KaiPlus directory.
- `apps/linkease/linkease/files/linkease.init`: disable embedded runtime and set proxy target only when standalone KaiPlus exists.

---

### Task 1: KaiPlus Standalone Contract Tests

**Files:**
- Create: `apps/kaiplus/tests/test_kaiplus_openwrt_contract.py`

**Interfaces:**
- Consumes: existing KaiPlus package files under `apps/kaiplus`.
- Produces: failing tests that define the standalone `8189` and `/apps/kaiplus/` contract.

- [ ] **Step 1: Create the failing KaiPlus contract test**

Create `apps/kaiplus/tests/test_kaiplus_openwrt_contract.py` with this exact content:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KaiPlusOpenWrtContractTest(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_config_defaults_to_standalone_url_contract(self):
        text = self.read("kaiplus/files/kaiplus.config")

        self.assertIn("option 'enabled' '0'", text)
        self.assertIn("option 'port' '8189'", text)
        self.assertIn("option 'base_path' '/apps/kaiplus/'", text)
        self.assertIn("option 'system_role' 'istoreos'", text)

    def test_init_reads_base_path_and_passes_it_to_kaiplus_web(self):
        text = self.read("kaiplus/files/kaiplus.init")

        self.assertIn('config_get port "$1" port "8189"', text)
        self.assertIn('config_get base_path "$1" base_path "/apps/kaiplus/"', text)
        self.assertIn('procd_append_param command --base-path "$base_path"', text)
        self.assertIn('procd_append_param command --addr "0.0.0.0:$port"', text)
        self.assertNotIn('port "8198"', text)

    def test_app_meta_config_writes_standalone_port_and_base_path(self):
        text = self.read("app-meta-kaiplus/config.sh")

        self.assertIn('set kaiplus.@kaiplus[0].port="8189"', text)
        self.assertIn('set kaiplus.@kaiplus[0].base_path="/apps/kaiplus/"', text)
        self.assertNotIn('port="8198"', text)

    def test_app_meta_entry_reports_base_path_href(self):
        text = self.read("app-meta-kaiplus/entry.sh")

        self.assertIn('base_path="$(uci get kaiplus.@kaiplus[0].base_path 2>/dev/null)"', text)
        self.assertIn('local basepath=${base_path:-/apps/kaiplus/}', text)
        self.assertIn('json_add_string "href" "http://$host:${portsec}${basepath}"', text)
        self.assertNotIn('http://$host:${portsec}/"', text)

    def test_luci_status_exposes_base_path_and_open_button_uses_it(self):
        controller = self.read("luci-app-kaiplus/luasrc/controller/kaiplus.lua")
        status_view = self.read("luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm")

        self.assertIn('local base_path = uci:get_first("kaiplus", "kaiplus", "base_path", "/apps/kaiplus/")', controller)
        self.assertRegex(controller, re.compile(r"base_path\s*=\s*base_path"))
        self.assertIn('st.base_path || "/apps/kaiplus/"', status_view)
        self.assertIn("window.location.hostname + ':' + st.port + basePath", status_view)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
rtk python3 -m unittest discover apps/kaiplus/tests
```

Expected: FAIL because `apps/kaiplus/tests` is new and the package still uses port `8198`, does not write/read `base_path`, and LuCI does not expose `base_path`.

- [ ] **Step 3: Commit the failing test**

```bash
rtk git add apps/kaiplus/tests/test_kaiplus_openwrt_contract.py
rtk git commit -m "test: define kaiplus standalone openwrt contract"
```

---

### Task 2: KaiPlus Standalone Runtime Implementation

**Files:**
- Modify: `apps/kaiplus/kaiplus/files/kaiplus.config`
- Modify: `apps/kaiplus/kaiplus/files/kaiplus.init`
- Modify: `apps/kaiplus/app-meta-kaiplus/config.sh`
- Modify: `apps/kaiplus/app-meta-kaiplus/entry.sh`
- Modify: `apps/kaiplus/luci-app-kaiplus/luasrc/controller/kaiplus.lua`
- Modify: `apps/kaiplus/luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm`
- Test: `apps/kaiplus/tests/test_kaiplus_openwrt_contract.py`

**Interfaces:**
- Consumes: Task 1 tests.
- Produces: standalone KaiPlus launch contract: UCI `port`, UCI `base_path`, procd `--base-path`, app-meta `href`, and LuCI open URL.

- [ ] **Step 1: Update KaiPlus UCI defaults**

Change `apps/kaiplus/kaiplus/files/kaiplus.config` to:

```sh
config kaiplus
	option 'enabled' '0'
	option 'data_dir' ''
	option 'port' '8189'
	option 'base_path' '/apps/kaiplus/'
	option 'system_role' 'istoreos'
```

- [ ] **Step 2: Update KaiPlus init config reads**

In `apps/kaiplus/kaiplus/files/kaiplus.init`, update `get_config()` to this exact block:

```sh
get_config() {
	config_get_bool enabled "$1" enabled 1
	config_get data_dir "$1" data_dir ""
	config_get port "$1" port "8189"
	config_get base_path "$1" base_path "/apps/kaiplus/"
	config_get system_role "$1" system_role "istoreos"
}
```

- [ ] **Step 3: Pass KaiPlus base path during service startup**

In `apps/kaiplus/kaiplus/files/kaiplus.init`, after the existing line:

```sh
procd_append_param command --defaults-dir /usr/share/kaiplus/defaults
```

insert:

```sh
procd_append_param command --base-path "$base_path"
```

The command block must contain:

```sh
procd_set_param command /usr/sbin/kaiplus_bin kaiplus-web
procd_append_param command --addr "0.0.0.0:$port"
procd_append_param command --data-dir "$data_dir"
procd_append_param command --static-dir /usr/share/kaiplus/www
procd_append_param command --defaults-dir /usr/share/kaiplus/defaults
procd_append_param command --base-path "$base_path"
procd_append_param command --system-role "$system_role"
```

- [ ] **Step 4: Update app-meta install config**

In `apps/kaiplus/app-meta-kaiplus/config.sh`, change the UCI batch to include `8189` and `base_path`:

```sh
uci -q batch <<-EOF >/dev/null || exit 1
	set kaiplus.@kaiplus[0].enabled=$ENABLED
	set kaiplus.@kaiplus[0].data_dir="$ISTORE_CONF_DIR/KAIPlus"
	set kaiplus.@kaiplus[0].port="8189"
	set kaiplus.@kaiplus[0].base_path="/apps/kaiplus/"
	set kaiplus.@kaiplus[0].system_role="istoreos"
	commit kaiplus
EOF
```

- [ ] **Step 5: Update app-meta entry href**

In `apps/kaiplus/app-meta-kaiplus/entry.sh`, replace the `port` handling at the start of `status()` with:

```sh
	local port
	port="$(uci get kaiplus.@kaiplus[0].port 2>/dev/null)"
	local portsec=${port:-8189}
	local base_path
	base_path="$(uci get kaiplus.@kaiplus[0].base_path 2>/dev/null)"
	local basepath=${base_path:-/apps/kaiplus/}
	case "$basepath" in
		/*) ;;
		*) basepath="/$basepath" ;;
	esac
	case "$basepath" in
		*/) ;;
		*) basepath="$basepath/" ;;
	esac
```

Then replace the running `href` line with:

```sh
		json_add_string "href" "http://$host:${portsec}${basepath}"
```

- [ ] **Step 6: Update LuCI status JSON**

In `apps/kaiplus/luci-app-kaiplus/luasrc/controller/kaiplus.lua`, update `kaiplus_status()` to:

```lua
function kaiplus_status()
	local sys = require "luci.sys"
	local uci = require "luci.model.uci".cursor()
	local port = uci:get_first("kaiplus", "kaiplus", "port", "8189")
	local base_path = uci:get_first("kaiplus", "kaiplus", "base_path", "/apps/kaiplus/")
	local status = {
		running = (sys.call("pidof kaiplus_bin >/dev/null") == 0),
		port = port,
		base_path = base_path
	}
	luci.http.prepare_content("application/json")
	luci.http.write_json(status)
end
```

- [ ] **Step 7: Update LuCI open button**

In `apps/kaiplus/luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm`, replace the running branch with:

```javascript
		if (st.running) {
			var basePath = st.base_path || "/apps/kaiplus/";
			if (basePath.charAt(0) !== "/") {
				basePath = "/" + basePath;
			}
			if (basePath.charAt(basePath.length - 1) !== "/") {
				basePath = basePath + "/";
			}
			el.innerHTML = '<br/><em style=\"color:green\"><%:The KaiPlus service is running.%></em>'
				+ "<br/><br/><input class=\"btn cbi-button cbi-button-apply\" type=\"button\" value=\" <%:Click to open KaiPlus%> \" onclick=\"window.open('http://' + window.location.hostname + ':' + st.port + basePath)\"/>";
		}
```

- [ ] **Step 8: Run KaiPlus tests**

Run:

```bash
rtk python3 -m unittest discover apps/kaiplus/tests
```

Expected: PASS.

- [ ] **Step 9: Commit KaiPlus implementation**

```bash
rtk git add \
  apps/kaiplus/kaiplus/files/kaiplus.config \
  apps/kaiplus/kaiplus/files/kaiplus.init \
  apps/kaiplus/app-meta-kaiplus/config.sh \
  apps/kaiplus/app-meta-kaiplus/entry.sh \
  apps/kaiplus/luci-app-kaiplus/luasrc/controller/kaiplus.lua \
  apps/kaiplus/luci-app-kaiplus/luasrc/view/kaiplus/kaiplus_status.htm
rtk git commit -m "feat: run kaiplus as standalone openwrt app"
```

---

### Task 3: LinkEase Decoupling Contract Tests

**Files:**
- Modify: `apps/linkease/tests/test_linkease_full_contract.py`

**Interfaces:**
- Consumes: existing LinkEase full package contract test helpers.
- Produces: failing tests that require LinkEase to stop packaging embedded KaiPlus and only proxy the standalone plugin.

- [ ] **Step 1: Update package install test**

In `apps/linkease/tests/test_linkease_full_contract.py`, replace this assertion:

```python
self.assertIn("$(CP) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/kaiplus $(1)/usr/lib/linkease/", text)
```

with:

```python
self.assertNotIn("$(CP) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/kaiplus $(1)/usr/lib/linkease/", text)
self.assertNotIn("/usr/lib/linkease/kaiplus", text)
```

- [ ] **Step 2: Add desktop KaiPlus decoupling assertions**

In `test_init_starts_desktop_and_apptunnel_instances`, after:

```python
self.assertIn("SERVER_BASE_PATH=$desktop_base_path", desktop)
```

insert:

```python
        self.assertIn("KAIPLUS_ENABLED=0", desktop)
        self.assertNotIn("KAIPLUS_BIN=", desktop)
        self.assertNotIn("KAIPLUS_STATIC_DIR=", desktop)
        self.assertNotIn("KAIPLUS_DEFAULTS_DIR=", desktop)
        self.assertNotIn("KAIPLUS_HOME=", desktop)
        self.assertNotIn("KAIPLUS_ADDR=", desktop)
        self.assertIn("KAIPLUS_PROXY_TARGET=http://127.0.0.1:$kaiplus_port", desktop)
```

- [ ] **Step 3: Add standalone proxy helper assertions**

Add this test method after `test_init_starts_desktop_and_apptunnel_instances`:

```python
    def test_init_configures_kaiplus_proxy_from_standalone_plugin(self):
        text = self.read("linkease/files/linkease.init")

        self.assertIn("resolve_kaiplus_proxy_target()", text)
        self.assertIn("[ -x /etc/init.d/kaiplus ] || return 0", text)
        self.assertIn('kaiplus_port="$(uci -q get kaiplus.@kaiplus[0].port || true)"', text)
        self.assertIn('[ -n "$kaiplus_port" ] || kaiplus_port=8189', text)
        self.assertIn('KAIPLUS_PROXY_TARGET="http://127.0.0.1:$kaiplus_port"', text)
        self.assertNotIn("127.0.0.1:19291", text)
```

- [ ] **Step 4: Run LinkEase tests to verify they fail**

Run:

```bash
rtk python3 -m unittest discover apps/linkease/tests
```

Expected: FAIL because `Makefile` still copies KaiPlus and `linkease.init` still sets embedded KaiPlus env vars.

- [ ] **Step 5: Commit failing LinkEase tests**

```bash
rtk git add apps/linkease/tests/test_linkease_full_contract.py
rtk git commit -m "test: define linkease standalone kaiplus proxy contract"
```

---

### Task 4: LinkEase Package Decoupling Implementation

**Files:**
- Modify: `apps/linkease/linkease/Makefile`
- Modify: `apps/linkease/linkease/files/linkease.init`
- Test: `apps/linkease/tests/test_linkease_full_contract.py`

**Interfaces:**
- Consumes: Task 3 tests and KaiPlus UCI `kaiplus.@kaiplus[0].port`.
- Produces: LinkEase full package that does not install or start embedded KaiPlus and proxies standalone KaiPlus when installed.

- [ ] **Step 1: Stop packaging embedded KaiPlus**

In `apps/linkease/linkease/Makefile`, remove this line from `Package/$(PKG_NAME)/install`:

```make
	$(CP) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/kaiplus $(1)/usr/lib/linkease/
```

Keep these lines:

```make
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/linkease-desktop $(1)/usr/bin/linkease-desktop
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/$(LINKEASE_FULL_ARCH)/apptunnel-client $(1)/usr/bin/apptunnel-client
```

- [ ] **Step 2: Add standalone KaiPlus proxy helper**

In `apps/linkease/linkease/files/linkease.init`, after `resolve_data_root_parent()` and before `read_config()`, insert:

```sh
resolve_kaiplus_proxy_target() {
	KAIPLUS_PROXY_TARGET=""
	kaiplus_port=""

	[ -x /etc/init.d/kaiplus ] || return 0

	kaiplus_port="$(uci -q get kaiplus.@kaiplus[0].port || true)"
	[ -n "$kaiplus_port" ] || kaiplus_port=8189
	KAIPLUS_PROXY_TARGET="http://127.0.0.1:$kaiplus_port"
}
```

- [ ] **Step 3: Call proxy helper from config read**

At the end of `read_config()` in `apps/linkease/linkease/files/linkease.init`, after:

```sh
	recycle_root="$data_root/recycle"
```

insert:

```sh
	resolve_kaiplus_proxy_target
```

- [ ] **Step 4: Remove embedded KaiPlus data directory creation**

In `start_desktop()`, replace:

```sh
	mkdir -p "$data_root" "$recycle_root" "$data_root/user" "$data_root/system" "$data_root/tmp" "$data_root/kaiplus"
```

with:

```sh
	mkdir -p "$data_root" "$recycle_root" "$data_root/user" "$data_root/system" "$data_root/tmp"
```

- [ ] **Step 5: Replace embedded KaiPlus env vars**

In `start_desktop()`, remove these lines:

```sh
	procd_set_param env "KAIPLUS_ENABLED=1"
	procd_set_param env "KAIPLUS_BIN=$APP_DIR/kaiplus/bin/kaiplus_bin"
	procd_set_param env "KAIPLUS_STATIC_DIR=$APP_DIR/kaiplus/www"
	procd_set_param env "KAIPLUS_DEFAULTS_DIR=$APP_DIR/kaiplus/defaults"
	procd_set_param env "KAIPLUS_HOME=$data_root/kaiplus"
	procd_set_param env "KAIPLUS_SYSTEM_ROLE=istoreos"
	procd_set_param env "KAIPLUS_BASE_PATH=${desktop_base_path}kaiplus/"
	procd_set_param env "KAIPLUS_ADDR=127.0.0.1:19291"
	procd_set_param env "KAIPLUS_PROXY_TARGET=http://127.0.0.1:19291"
```

Insert this block in their place:

```sh
	procd_set_param env "KAIPLUS_ENABLED=0"
	if [ -n "$KAIPLUS_PROXY_TARGET" ]; then
		procd_set_param env "KAIPLUS_PROXY_TARGET=$KAIPLUS_PROXY_TARGET"
	fi
```

- [ ] **Step 6: Run LinkEase tests**

Run:

```bash
rtk python3 -m unittest discover apps/linkease/tests
```

Expected: PASS.

- [ ] **Step 7: Commit LinkEase implementation**

```bash
rtk git add apps/linkease/linkease/Makefile apps/linkease/linkease/files/linkease.init
rtk git commit -m "feat: decouple linkease from embedded kaiplus"
```

---

### Task 5: Final Verification

**Files:**
- Read: `apps/kaiplus/tests/test_kaiplus_openwrt_contract.py`
- Read: `apps/linkease/tests/test_linkease_full_contract.py`
- Read: `apps/kaiplus/kaiplus/files/kaiplus.init`
- Read: `apps/linkease/linkease/files/linkease.init`

**Interfaces:**
- Consumes: Task 1 through Task 4 completed changes.
- Produces: verified OpenWrt package split ready for review.

- [ ] **Step 1: Run KaiPlus contract tests**

Run:

```bash
rtk python3 -m unittest discover apps/kaiplus/tests
```

Expected: PASS.

- [ ] **Step 2: Run LinkEase contract tests**

Run:

```bash
rtk python3 -m unittest discover apps/linkease/tests
```

Expected: PASS.

- [ ] **Step 3: Check for remaining embedded KaiPlus packaging**

Run:

```bash
rtk rg -n "PKG_BUILD_DIR.*/kaiplus|/usr/lib/linkease/kaiplus|KAIPLUS_BIN=|KAIPLUS_STATIC_DIR=|KAIPLUS_DEFAULTS_DIR=|KAIPLUS_HOME=|127\\.0\\.0\\.1:19291" apps/linkease/linkease
```

Expected: no matches.

- [ ] **Step 4: Check standalone KaiPlus URL contract**

Run:

```bash
rtk rg -n "8189|/apps/kaiplus/|--base-path|KAIPLUS_PROXY_TARGET" apps/kaiplus apps/linkease/linkease
```

Expected: matches show KaiPlus defaults and LinkEase proxy target logic. No `8198` default should remain in `apps/kaiplus`.

- [ ] **Step 5: Check git state**

Run:

```bash
rtk git status --short --branch
```

Expected: clean worktree, branch ahead by the plan/spec and implementation commits.
