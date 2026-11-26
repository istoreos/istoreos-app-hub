local http = require "luci.http"

module("luci.controller.dsh", package.seeall)

function index()
	local open = entry({"admin", "services", "dsh", "open"}, call("dsh_open"))
	open.leaf = true
	open.dependent = false
	open.sysauth = false

	if not nixio.fs.access("/etc/config/dsh") then return end
	entry({"admin", "services", "dsh"}, cbi("dsh"), _("DSH"), 101).dependent = true
end

local function compat()
	local dispatcher = require "luci.dispatcher"
	return require("luci.model.linkease.apps_compat").new({
		http = http,
		resolver = require("luci.model.linkease.apps_openwrt").new(),
		auth_url = dispatcher.build_url("admin", "services", "linkease_auth", "auth")
	})
end

function dsh_open()
	compat():open("dsh")
end
