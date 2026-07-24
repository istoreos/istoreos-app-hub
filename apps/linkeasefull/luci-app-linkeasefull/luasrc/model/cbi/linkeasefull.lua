local m, s

m = Map("linkeasefull", translate("LinkEase Full"), translate("LinkEase Full provides the local web desktop entry for LinkEase."))

m:section(SimpleSection).template = "linkeasefull_status"

s = m:section(TypedSection, "linkeasefull", translate("Global settings"))
s.addremove = false
s.anonymous = true

s:option(Flag, "enabled", translate("Enable")).rmempty = false
s:option(Value, "port", translate("Port")).rmempty = false

local base = s:option(Value, "base_path", translate("Base Path"))
base.rmempty = false
base.default = "/apps/"

s:option(Value, "data_root_parent", translate("Data Root Parent")).rmempty = true

return m
