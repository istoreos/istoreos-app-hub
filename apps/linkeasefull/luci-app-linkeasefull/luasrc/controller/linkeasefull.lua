module("luci.controller.linkeasefull", package.seeall)

function index()
	if not nixio.fs.access("/etc/config/linkeasefull") then
		return
	end

	entry({"admin", "services", "linkeasefull"}, cbi("linkeasefull"), _("LinkEase Full"), 21).dependent = true
	entry({"admin", "services", "linkeasefull_status"}, call("linkeasefull_status"))
end

function linkeasefull_status()
	local sys  = require "luci.sys"
	local uci  = require "luci.model.uci".cursor()
	local port = tonumber(uci:get_first("linkeasefull", "linkeasefull", "port"))
	local base_path = uci:get_first("linkeasefull", "linkeasefull", "base_path") or "/apps/"

	if base_path == "" then
		base_path = "/apps/"
	elseif base_path:sub(1, 1) ~= "/" then
		base_path = "/" .. base_path
	end
	if base_path:sub(-1) ~= "/" then
		base_path = base_path .. "/"
	end

	local status = {
		running = (sys.call("pidof linkease-full >/dev/null") == 0),
		port = (port or 19290),
		base_path = base_path
	}

	luci.http.prepare_content("application/json")
	luci.http.write_json(status)
end
