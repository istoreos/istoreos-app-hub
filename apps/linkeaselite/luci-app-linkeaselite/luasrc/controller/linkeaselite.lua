module("luci.controller.linkeaselite", package.seeall)

function index()
	if not nixio.fs.access("/etc/config/linkeaselite") then
		return
	end

	entry({"admin", "services", "linkeaselite"}, cbi("linkeaselite"), _("LinkEaseLite"), 20).dependent = true
	entry({"admin", "services", "linkeaselite_status"}, call("linkeaselite_status"))
	entry({"admin", "services", "linkeaselite", "file"}, call("linkeaselite_file_template")).leaf = true
end

function linkeaselite_status()
	local sys  = require "luci.sys"
	local uci  = require "luci.model.uci".cursor()
	local port = tonumber(uci:get_first("linkeaselite", "linkeaselite", "port"))

	local status = {
		running = (sys.call("pidof linkease-lite >/dev/null") == 0),
		port = (port or 8897)
	}

	luci.http.prepare_content("application/json")
	luci.http.write_json(status)
end

function get_params(name)
	local data = {
		prefix = luci.dispatcher.build_url(unpack({"admin", "services", "linkeaselite", name})),
	}
	return data
end

function linkeaselite_file_template()
	luci.template.render("linkeaselite/file", get_params("file"))
end
