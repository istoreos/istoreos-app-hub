module("luci.controller.linkease_auth", package.seeall)

function index()
	local auth = entry({"admin", "services", "linkease_auth", "auth"}, call("linkease_auth"))
	auth.leaf = true
	auth.dependent = false
	auth.sysauth = "root"
	auth.sysauth_authenticator = "htmlauth"

	local auth_finish = entry({"admin", "services", "linkease_auth", "auth_finish"}, call("linkease_auth_finish"))
	auth_finish.leaf = true
	auth_finish.dependent = false
	auth_finish.sysauth = "root"
	auth_finish.sysauth_authenticator = "htmlauth"
end

local function bridge()
	return require("luci.model.linkease.auth").new()
end

function linkease_auth()
	bridge():auth()
end

function linkease_auth_finish()
	bridge():auth_finish()
end
