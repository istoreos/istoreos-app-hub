--wulishui <wulishui@gmail.com> ,20200911
--jjm2473 <jjm2473@gmail.com> ,20210127

local m, s

m = Map("linkease", translate("LinkEase"), translate("LinkEase is an efficient data transfer tool."))

m:section(SimpleSection).template  = "linkease_status"

s=m:section(TypedSection, "linkease", translate("Global settings"))
s.addremove=false
s.anonymous=true

s:option(Flag, "enabled", translate("Enable")).rmempty=false

s:option(Value, "port", translate("Port")).rmempty=false

s:option(Value, "desktop_port", translate("Full UI Port")).rmempty=false

local base = s:option(Value, "desktop_base_path", translate("Full UI Base Path"))
base.rmempty=false
base.default="/apps/"

local edition = s:option(ListValue, "edition", translate("Edition"))
edition:value("full", "Full")
edition:value("standard", "Standard")
edition:value("lite", "Lite")
edition.default="full"

s:option(Flag, "desktop_enabled", translate("Enable Full UI")).rmempty=false
s:option(Flag, "apptunnel_enabled", translate("Enable Remote Access Runtime")).rmempty=false
s:option(Flag, "low_memory_fallback", translate("Low Memory Fallback")).rmempty=false
s:option(Value, "data_root_parent", translate("Data Root Parent")).rmempty=true

s:option(Flag, "allowPublic", translate("AllowPublic"), translate("Allowing access via public IP addresses can lead to insufficient security.")).rmempty=false

return m

