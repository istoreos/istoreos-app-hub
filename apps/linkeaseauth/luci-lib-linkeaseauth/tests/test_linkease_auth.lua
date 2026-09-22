local source_root = assert(os.getenv("LINKEASE_AUTH_SOURCE_ROOT"), "LINKEASE_AUTH_SOURCE_ROOT is required")
package.path = source_root .. "/?.lua;" .. package.path

local function equal(actual, expected, message)
	if actual ~= expected then
		error((message or "values differ") .. ": got " .. tostring(actual) .. ", want " .. tostring(expected), 2)
	end
end

local function has_header(headers, pattern)
	for _, header in ipairs(headers) do
		if header[1] == "Set-Cookie" and header[2]:match(pattern) then return true end
	end
	return false
end

local function scenario(options)
	options = options or {}
	local headers = {}
	local result = {}
	local cookies = options.cookies or {}
	local environment = options.environment or { HTTP_HOST = "192.168.30.7:10000" }
	local forms = options.forms or {}

	package.loaded["luci.model.linkease.auth"] = nil
	local auth = require "luci.model.linkease.auth"
	local bridge = auth.new({
		http = {
			getcookie = function(name) return cookies[name] end,
			getenv = function(name) return environment[name] end,
			formvalue = function(name) return forms[name] end,
			header = function(name, value) headers[#headers + 1] = { name, value } end,
			redirect = function(value) result.redirect = value end,
			status = function(code, message) result.status = code; result.message = message end
		},
		ubus = function(object, method, request)
			if object == "session" and method == "get" and request.ubus_rpc_session == options.valid_sid then
				return { values = { username = "root" } }
			end
			return nil
		end,
		lan_ip = function() return "192.168.30.7" end,
		build_url = function()
			return "/cgi-bin/luci/admin/services/linkease_auth/auth_finish"
		end
	})
	return bridge, result, headers
end

local bridge, result, headers = scenario({
	cookies = { sysauth = "valid-session" },
	valid_sid = "valid-session",
	forms = { ["return"] = "/apps/dockermanager/" }
})
bridge:auth()
equal(result.redirect, "/apps/dockermanager/")
equal(has_header(headers, "linkease_openwrt_sid=valid%-session"), true)
equal(has_header(headers, "linkease_openwrt_sid=.*Path=/apps"), true)

bridge, result, headers = scenario({ forms = { ["return"] = "/apps/kaiplus/" } })
bridge:auth()
equal(result.redirect, "http://192.168.30.7:10000/cgi-bin/luci/admin/services/linkease_auth/auth_finish")
equal(headers[1][2]:match("linkease_openwrt_pending_return=") ~= nil, true)

bridge, result = scenario({
	cookies = { sysauth = "valid-session" },
	valid_sid = "valid-session",
	forms = { ["return"] = "http://192.168.30.7:8192/apps/dockermanager/" }
})
bridge:auth()
equal(result.redirect, "http://192.168.30.7:8192/apps/dockermanager/")

bridge, result = scenario({
	cookies = { sysauth = "valid-session" },
	valid_sid = "valid-session",
	forms = { ["return"] = "http://evil.example/apps/dockermanager/" }
})
bridge:auth()
equal(result.redirect, "/apps/")

bridge, result = scenario({
	cookies = { sysauth = "valid-session" },
	valid_sid = "valid-session",
	forms = { ["return"] = "http://192.168.30.7:8192@evil.example/apps/dockermanager/" }
})
bridge:auth()
equal(result.redirect, "/apps/")

bridge, result = scenario()
bridge:auth_finish()
equal(result.status, 403)

print("linkease auth bridge tests passed")
