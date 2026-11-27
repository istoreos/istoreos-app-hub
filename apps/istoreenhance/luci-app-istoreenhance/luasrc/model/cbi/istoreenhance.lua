local m, s

local istoreenhance_model = require "luci.model.istoreenhance"
local uci = require "luci.model.uci".cursor()

m = Map("istoreenhance", translate("KSpeeder"), translate("KSpeeder is a tool to fix network issues for iStore."))

m:section(SimpleSection).template  = "istoreenhance_status"

s=m:section(TypedSection, "istoreenhance", translate("Global settings"))
s.addremove=false
s.anonymous=true

s:option(Flag, "enabled", translate("Enable")).rmempty=false

o = s:option(Flag, "gateway_mode", translate("Gateway mode"))
o.rmempty = false
o.description = translate("Resolve KSpeeder gateway domains to this router's LAN IP through dnsmasq. Enable this only when KSpeeder runs on the router.")

s:option(Value, "adminport", translate("Admin Port")).rmempty=false

s:option(Value, "port", translate("Port")).rmempty=false

o = s:option(Value, "cache", translate("Cache Path").."<b>*</b>")
o.rmempty = false
o.datatype = "string"

local blocks = istoreenhance_model.blocks()
local home = istoreenhance_model.home()

local paths, default_path = istoreenhance_model.find_paths(blocks, home, "Configs")
for _, val in pairs(paths) do
  o:value(val, val)
end
o.default = default_path

local gateway_link = s:option(DummyValue, "_gateway_dns")
gateway_link.template = "istoreenhance_gateway_dns"
gateway_link.adminport = tonumber(uci:get_first("istoreenhance", "istoreenhance", "adminport")) or 5003

return m


