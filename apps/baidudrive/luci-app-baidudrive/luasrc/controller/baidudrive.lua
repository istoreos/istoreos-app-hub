local http = require "luci.http"

module("luci.controller.baidudrive", package.seeall)

function index()
	if not nixio.fs.access("/etc/config/baidudrive") then
		return
	end
	local page
	page = entry({"admin", "services", "baidudrive"}, cbi("baidudrive"), _("BaiduDrive"), 100)
	page.dependent = true
	entry({"admin", "services", "baidudrive_status"}, call("baidudrive_status"))
end

function baidudrive_status()
	local sys = require "luci.sys"
	local uci = require "luci.model.uci".cursor()
	local port = uci:get_first("baidudrive", "baidudrive", "port") or "10780"
	local data_dir = uci:get_first("baidudrive", "baidudrive", "data_dir") or ""
	local sdk_log = ""
	if data_dir ~= "" then
		local f = io.open(data_dir .. "/sdk-init.log", "r")
		if f then
			sdk_log = f:read("*all") or ""
			f:close()
		end
	end
	local app_running = (sys.call("pidof baidudrive >/dev/null") == 0)
	local sdk_running = (sys.call("pidof baiduNas >/dev/null") == 0)
	local status = {
		running = app_running and sdk_running,
		app_running = app_running,
		sdk_running = sdk_running,
		sdk_ready = sdk_log:find("register ok", 1, true) and sdk_log:find("quota ok", 1, true) and sdk_log:find("usbIn ok", 1, true) and true or false,
		port = port
	}
	luci.http.prepare_content("application/json")
	luci.http.write_json(status)
end
