local m, s

m = Map("baidudrive", translate("BaiduDrive"), translate("BaiduDrive provides a Baidu Netdisk Web UI."))
m:section(SimpleSection).template = "baidudrive/baidudrive_status"

s = m:section(TypedSection, "baidudrive", translate("Global settings"))
s.addremove = false
s.anonymous = true

s:option(Flag, "enabled", translate("Enable")).rmempty = false

local baidudrive_model = require "luci.model.baidudrive"
local blocks = baidudrive_model.blocks()
local home = baidudrive_model.home()

local data_dir = s:option(Value, "data_dir", translate("Data directory"))
data_dir.rmempty = false
data_dir.description = translate("Required. BaiduDrive stores its config, session and task data under this directory.")

local paths, default_path = baidudrive_model.find_paths(blocks, home, "Configs")
for _, val in pairs(paths) do
	data_dir:value(val, val)
end
data_dir.default = default_path

local host = s:option(Value, "host", translate("Listen address"))
host.default = "0.0.0.0"
host.rmempty = false

local port = s:option(Value, "port", translate("Listen port"))
port.default = "10780"
port.rmempty = false
port.datatype = "port"
port.description = translate("Port for BaiduDrive HTTP server.")

local sdk_dir = s:option(Value, "sdk_dir", translate("NAS SDK directory"))
sdk_dir.default = "/opt/baidunas-sdk"
sdk_dir.rmempty = false

local sdk_host = s:option(Value, "sdk_host", translate("NAS SDK address"))
sdk_host.default = "127.0.0.1"
sdk_host.rmempty = false

local sdk_port = s:option(Value, "sdk_port", translate("NAS SDK port"))
sdk_port.default = "8001"
sdk_port.rmempty = false
sdk_port.datatype = "port"

local macid = s:option(Value, "macid", translate("Device address"))
macid.rmempty = false
macid.description = translate("Required. Must match the macid used by Baidu NAS SDK device registration.")

local device_type = s:option(Value, "device_type", translate("Device type"))
device_type.rmempty = false
device_type.description = translate("Required. Baidu NAS device type assigned to the application.")

local usb_path = s:option(Value, "usb_path", translate("USB path"))
usb_path.default = "/mnt"
usb_path.rmempty = false

local download_path = s:option(Value, "download_path", translate("Download root"))
download_path.default = "/"
download_path.rmempty = false

local quota_path = s:option(Value, "quota_path", translate("Quota path"))
quota_path.default = "/mnt"
quota_path.rmempty = false

local tmp_path = s:option(Value, "tmp_path", translate("SDK temp directory"))
tmp_path.rmempty = true
tmp_path.description = translate("Optional. Defaults to data directory plus /sdk-tmp.")

local log_level = s:option(Value, "log_level", translate("SDK log level"))
log_level.default = "7"
log_level.rmempty = false

return m
