module("luci.controller.istoreenhance", package.seeall)

function index()
	if not nixio.fs.access("/etc/config/istoreenhance") then return end

	entry({"admin", "services", "istoreenhance"}, cbi("istoreenhance"), _("KSpeeder"), 20).dependent = true
	entry({"admin", "services", "istoreenhance_status"}, call("istoreenhance_status"))
	local open = entry({"admin", "services", "istoreenhance", "open"}, call("istoreenhance_open"))
	open.leaf = true
	open.dependent = false
	open.sysauth = false
end

local function compat()
	local dispatcher = require "luci.dispatcher"
	return require("luci.model.linkease.apps_compat").new({
		http = require "luci.http",
		resolver = require("luci.model.linkease.apps_openwrt").new(),
		auth_url = dispatcher.build_url("admin", "services", "linkease_auth", "auth")
	})
end

local function authority_host(authority)
	if not authority or authority == "" then return "" end
	if authority:sub(1, 1) == "[" then return authority:match("^%[([^%]]+)%]") or "" end
	return authority:match("^([^:]+)") or authority
end

local function url_host(host)
	if host:find(":") and host:sub(1, 1) ~= "[" then return "[" .. host .. "]" end
	return host
end

local function direct_url()
	local http = require "luci.http"
	local uci = require "luci.model.uci".cursor()
	local host = authority_host(http.getenv("HTTP_HOST") or "")
	local port = tonumber(uci:get_first("istoreenhance", "istoreenhance", "adminport")) or 5003
	if host == "" then host = uci:get("network", "lan", "ipaddr") or "127.0.0.1" end
	if port < 1 or port > 65535 or port % 1 ~= 0 then port = 5003 end
	return "http://" .. url_host(host) .. ":" .. tostring(port) .. "/"
end

function istoreenhance_status()
	local sys = require "luci.sys"
	local uci = require "luci.model.uci".cursor()
	compat():legacy_status("kspeeder", {
		running = sys.call("pidof iStoreEnhance >/dev/null") == 0,
		port = uci:get_first("istoreenhance", "istoreenhance", "adminport") or "5003"
	})
end

function istoreenhance_open()
	local http = require "luci.http"
	http.redirect(direct_url())
end
