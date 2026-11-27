local m, s

local istoreenhance_model = require "luci.model.istoreenhance"

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

local gateway_domains, loopback_domains = istoreenhance_model.gateway_domains()

local function readonly_domains_option(name, title, description, domains)
  local option = s:option(TextValue, name, title)
  option.readonly = true
  option.rows = math.max(2, math.min(12, #domains))
  option.description = description
  function option.cfgvalue()
    return table.concat(domains, "\n")
  end
  function option.write()
  end
  return option
end

readonly_domains_option(
  "_gateway_domains",
  translate("Gateway DNS domains"),
  translate("Gateway mode maps these domains to this router. If KSpeeder runs on another machine, configure the gateway DNS to map these domains to that machine instead."),
  gateway_domains
)

readonly_domains_option(
  "_loopback_domains",
  translate("Client loopback domains"),
  translate("These Docker relay domains must keep resolving to 127.0.0.1 on every client. Do not map them to the router or a remote KSpeeder node."),
  loopback_domains
)

return m


