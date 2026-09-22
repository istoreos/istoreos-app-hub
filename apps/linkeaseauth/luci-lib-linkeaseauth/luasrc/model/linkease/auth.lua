local M = {}
local Bridge = {}
Bridge.__index = Bridge

local pending_return_cookie = "linkease_openwrt_pending_return"
local bridge_return_cookie = "linkease_openwrt_return"
local pending_return_cookie_path = "/cgi-bin/luci/admin/services/linkease_auth"
local bridge_return_cookie_path = "/cgi-bin/luci/admin/services/linkease_auth/auth"

local function default_dependencies()
	local http = require "luci.http"
	local util = require "luci.util"
	local dispatcher = require "luci.dispatcher"
	return {
		http = http,
		ubus = function(object, method, request) return util.ubus(object, method, request) end,
		lan_ip = function()
			return require("luci.model.uci").cursor():get("network", "lan", "ipaddr") or ""
		end,
		build_url = function(...) return dispatcher.build_url(...) end
	}
end

local function authority_host(authority)
	if not authority or authority == "" then return "" end
	if authority:sub(1, 1) == "[" then return authority:match("^%[([^%]]+)%]") or "" end
	return authority:match("^([^:]+)") or authority
end

local function valid_authority(authority)
	return authority and authority ~= "" and authority:match("^[A-Za-z0-9%._%-%[%]:]+$") ~= nil
end

local function cookie_encode(value)
	return (tostring(value or ""):gsub("([^A-Za-z0-9._~-])", function(char)
		return string.format("%%%02X", char:byte())
	end))
end

local function cookie_decode(value)
	if not value or value == "" then return nil end
	return (value:gsub("%%(%x%x)", function(hex) return string.char(tonumber(hex, 16)) end))
end

local function valid_cookie_value(value)
	return value and value:match("^[A-Za-z0-9._%-_]+$") ~= nil
end

function M.new(dependencies)
	return setmetatable({ dependencies = dependencies or default_dependencies() }, Bridge)
end

function Bridge:request_authority()
	local http = self.dependencies.http
	local forwarded_host = http.getenv("HTTP_X_FORWARDED_HOST") or ""
	local request_host = http.getenv("HTTP_HOST") or ""
	if valid_authority(forwarded_host) then return forwarded_host end
	if valid_authority(request_host) then return request_host end
	return ""
end

function Bridge:request_scheme()
	local http = self.dependencies.http
	if http.getenv("HTTP_X_FORWARDED_PROTO") == "https" or http.getenv("HTTPS") == "on" then return "https" end
	return "http"
end

function Bridge:absolute_luci_url(path)
	if not path or path == "" or path:match("^https?://") then return path end
	local authority = self:request_authority()
	if authority == "" then return path end
	return self:request_scheme() .. "://" .. authority .. path
end

function Bridge:valid_apps_return(value)
	if not value or value == "" then return false end
	local function valid_path(path)
		if path == "/apps" then return true end
		local prefix = path:sub(1, 6)
		return prefix == "/apps/" or prefix == "/apps?" or prefix == "/apps#"
	end
	if value:sub(1, 1) == "/" then return valid_path(value) end

	local _, authority, path = value:match("^(https?://)([^/]+)(/.*)$")
	if not authority or not valid_authority(authority) or not valid_path(path) then return false end
	local candidate = authority_host(authority)
	return candidate ~= "" and (
		candidate == authority_host(self:request_authority())
		or candidate == authority_host(self.dependencies.lan_ip())
	)
end

function Bridge:safe_return_target(value)
	if self:valid_apps_return(value) then return value end
	return "/apps/"
end

function Bridge:retrieve_luci_session()
	local http = self.dependencies.http
	for _, key in ipairs({"sysauth_https", "sysauth_http", "sysauth"}) do
		local sid = http.getcookie(key)
		if sid and sid ~= "" then
			local data = self.dependencies.ubus("session", "get", { ubus_rpc_session = sid })
			if data and type(data.values) == "table" then return sid end
		end
	end
	return nil
end

function Bridge:requested_return_target()
	local http = self.dependencies.http
	return self:safe_return_target(http.formvalue("return") or cookie_decode(http.getcookie(bridge_return_cookie)) or "/apps/")
end

function Bridge:pending_return_target()
	return self:safe_return_target(cookie_decode(self.dependencies.http.getcookie(pending_return_cookie)))
end

function Bridge:auth()
	local http = self.dependencies.http
	local sid = self:retrieve_luci_session()
	local target = self:requested_return_target()
	if valid_cookie_value(sid) then
		http.header("Set-Cookie", bridge_return_cookie .. "=; Path=" .. bridge_return_cookie_path .. "; Max-Age=0; HttpOnly; SameSite=Lax")
		http.header("Set-Cookie", "linkease_openwrt_sid=" .. sid .. "; Path=/apps; HttpOnly; SameSite=Lax")
		http.redirect(target)
		return
	end

	http.header("Set-Cookie", pending_return_cookie .. "=" .. cookie_encode(target) .. "; Path=" .. pending_return_cookie_path .. "; Max-Age=300; HttpOnly; SameSite=Lax")
	local finish = self.dependencies.build_url("admin", "services", "linkease_auth", "auth_finish")
	http.redirect(self:absolute_luci_url(finish))
end

function Bridge:auth_finish()
	local http = self.dependencies.http
	local sid = self:retrieve_luci_session()
	if not valid_cookie_value(sid) then
		http.status(403, "Forbidden")
		return
	end
	local target = self:pending_return_target()
	http.header("Set-Cookie", pending_return_cookie .. "=; Path=" .. pending_return_cookie_path .. "; Max-Age=0; HttpOnly; SameSite=Lax")
	http.header("Set-Cookie", "linkease_openwrt_sid=" .. sid .. "; Path=/apps; HttpOnly; SameSite=Lax")
	http.redirect(target)
end

return M
