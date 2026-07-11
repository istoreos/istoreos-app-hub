module("luci.controller.linkease", package.seeall)

function index()
	if not nixio.fs.access("/etc/config/linkease") then
		return
	end

	entry({"admin", "services", "linkease"}, cbi("linkease"), _("LinkEase"), 20).dependent = true

	entry({"admin", "services", "linkease_status"}, call("linkease_status"))

	entry({"admin", "services", "linkease", "file"}, call("linkease_file_template")).leaf = true

end

function linkease_status()
	local sys  = require "luci.sys"
	local uci  = require "luci.model.uci".cursor()
	local port = tonumber(uci:get_first("linkease", "linkease", "port"))
	local desktop_port = tonumber(uci:get_first("linkease", "linkease", "desktop_port"))
	local desktop_base_path = uci:get_first("linkease", "linkease", "desktop_base_path") or "/apps/"
	local edition = uci:get_first("linkease", "linkease", "edition") or "full"

	if desktop_base_path == "" then
		desktop_base_path = "/apps/"
	elseif desktop_base_path:sub(1, 1) ~= "/" then
		desktop_base_path = "/" .. desktop_base_path
	end
	if desktop_base_path:sub(-1) ~= "/" then
		desktop_base_path = desktop_base_path .. "/"
	end

	local desktop_running = (sys.call("pidof linkease-desktop >/dev/null") == 0)

	local status = {
		running = desktop_running,
		desktop_running = desktop_running,
		apptunnel_running = (sys.call("pidof apptunnel-client >/dev/null") == 0),
		port = (port or 8897),
		desktop_port = (desktop_port or 19290),
		desktop_base_path = desktop_base_path,
		edition = edition
	}

	luci.http.prepare_content("application/json")
	luci.http.write_json(status)
end

function get_params(name)
    local data = {
        prefix=luci.dispatcher.build_url(unpack({"admin", "services", "linkease", name})),
    }
    return data
end

function linkease_file_template()
    luci.template.render("linkease/file", get_params("file"))
end
