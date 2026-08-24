module("luci.controller.linkeasefull", package.seeall)

function index()
	entry({"admin", "services", "linkeasefull_status"}, call("linkeasefull_status"))
	local auth = entry({"admin", "services", "linkeasefull", "auth"}, call("linkeasefull_auth"))
	auth.leaf = true
	auth.dependent = false
	auth.sysauth = "root"
	auth.sysauth_authenticator = "htmlauth"
	local auth_finish = entry({"admin", "services", "linkeasefull", "auth_finish"}, call("linkeasefull_auth_finish"))
	auth_finish.leaf = true
	auth_finish.dependent = false
	auth_finish.sysauth = "root"
	auth_finish.sysauth_authenticator = "htmlauth"

	if not nixio.fs.access("/etc/config/linkeasefull") then
		return
	end

	entry({"admin", "services", "linkeasefull"}, cbi("linkeasefull"), _("LinkEase Full"), 21).dependent = true
end

local function uhttpd_has_apps_proxy_prefix()
	local uci = require "luci.model.uci".cursor()
	local mappings = uci:get_list("uhttpd", "main", "proxy_prefix") or {}

	for _, mapping in ipairs(mappings) do
		if mapping == "/apps=http://127.0.0.1:19290" then
			return true
		end
	end
	return false
end

function linkeasefull_status()
	local sys  = require "luci.sys"
	local uci  = require "luci.model.uci".cursor()

	local status = {
		running = (sys.call("pidof linkease-full >/dev/null") == 0),
		full_port = 19290,
		legacy_port = 8897,
		base_path = "/apps/",
		lan_ip = uci:get("network", "lan", "ipaddr") or "",
		proxy_prefix_enabled = uhttpd_has_apps_proxy_prefix(),
		conflict = false,
		conflict_service = ""
	}

	luci.http.prepare_content("application/json")
	luci.http.write_json(status)
end

local function cookie_encode(value)
	return tostring(value or ""):gsub("([^A-Za-z0-9._~-])", function(char)
		return string.format("%%%02X", char:byte())
	end)
end

local function linkease_auth_url(name)
	local dispatcher = require "luci.dispatcher"
	return dispatcher.build_url("admin", "services", "linkease_auth", name)
end

function linkeasefull_auth()
	local http = require "luci.http"
	local target = http.formvalue("return") or "/apps/"
	http.redirect(linkease_auth_url("auth") .. "?return=" .. cookie_encode(target))
end

function linkeasefull_auth_finish()
	local http = require "luci.http"
	http.redirect(linkease_auth_url("auth_finish"))
end
