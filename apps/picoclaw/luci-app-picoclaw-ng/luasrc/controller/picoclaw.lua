module("luci.controller.picoclaw", package.seeall)

-- ============================================================
-- PicoClaw LuCI 模块（v3，重写版）
--
-- 设计原则：
--   * 页面只做“生命周期管理”，模型/通道配置交给临时打开的 Launcher 面板
--   * 所有耗时操作走后台安装器，页面轮询状态 JSON，不阻塞 CGI
--   * 上游二进制按 CPU 架构选择；自动检测失败时允许手动指定
--   * 权限模型保持现状：服务以 root 运行，配置在 /root/.picoclaw
-- ============================================================

local http = require "luci.http"
local sys = require "luci.sys"
local nixio = require "nixio"
local template = require "luci.template"
local dispatcher = require "luci.dispatcher"
local uci = require "luci.model.uci".cursor()

PC_VERSION = "0.3.1"
PC_DEFAULT_PORT = 18800
PC_DEFAULT_MODE = "gateway"
PC_PANEL_FLAG = "/tmp/picoclaw-panel"
PC_RUNTIME_LOG = "/var/log/picoclaw.log"
PC_OPLOG = "/etc/picoclaw-luci.log"
PC_OPLOG_MAX = 262144
PC_INSTALL_STATUS = "/tmp/picoclaw-install.status"
PC_INSTALL_LOG = "/tmp/picoclaw-install.log"
PC_INSTALL_ARGS = "/tmp/picoclaw-install.args"
PC_INSTALL_SCRIPT = "/usr/lib/picoclaw-install.sh"
PC_INSTALL_INIT = "/etc/init.d/picoclaw-installer"
PC_CONFIG_DIR = "/root/.picoclaw"
PC_SKILLS_SRC = "/usr/lib/lua/luci/picoclaw-skills"
PC_SKILLS_ALT = "/usr/share/picoclaw/skills"

-- 上游 release 资产（0.3.1）。id 直接拼进下载文件名，
-- label 是给用户看的 CPU 说明，用于自动检测失败时手动选择。
PC_ASSETS = {
    { id = "Linux_arm64",   label = "ARM64 / aarch64（主流 ARMv8 路由器）" },
    { id = "Linux_armv7",   label = "ARMv7（armv7l / armv8l，Cortex-A7/A53 32 位）" },
    { id = "Linux_armv6",   label = "ARMv6（armv6l / ARM1176）" },
    { id = "Linux_x86_64",  label = "x86_64（软路由 / 虚拟机）" },
    { id = "Linux_mipsle",  label = "MIPS little-endian（mipsel 24kc 等）" },
    { id = "Linux_riscv64", label = "RISC-V 64（riscv64）" },
    { id = "Linux_loong64", label = "LoongArch 64（loongarch64）" },
    { id = "Linux_s390x",   label = "s390x（IBM Z）" },
}

PC_SHA256 = {
    ["Linux_x86_64"]  = "86f0fe84aa55279352edbe13adfca484a03bcf189e2030b25e34628089069c3f",
    ["Linux_arm64"]   = "e78ab0de05d000698ff8b32458e71cb3134e52e9eaf540e3323a72e9914de060",
    ["Linux_armv6"]   = "28c9789be079986bd8b6cea7c82b9c9bda819b58860db0502598149a36407bc8",
    ["Linux_armv7"]   = "1472e9913d800cc5bf7193e736d85007968dabb58973d0cdac02c7232dcf9b0b",
    ["Linux_loong64"] = "e944f1a08710117100aa1db825170eb515094912c2cf214415fbb667c2e0fafc",
    ["Linux_mipsle"]  = "5be2f72018a9663eb673a08a9db5fb6f4626ab1f7430be975b1dbb0efdcf05b2",
    ["Linux_riscv64"] = "5124e553c8fb6f90cd57f7478a37409d2d98531cb028ca6ead6cc6867650d58a",
    ["Linux_s390x"]   = "a7154c210384abc67270ae3435e68a92e3e80b6d93db3051f9122fc3f0ffc111",
}

local function trim(s)
    return (tostring(s or ""):gsub("^%s+", ""):gsub("%s+$", ""))
end

local function shq(s)
    return "'" .. tostring(s or ""):gsub("'", "'\\''") .. "'"
end

local function read_file(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local c = f:read("*a")
    f:close()
    return c
end

function html_escape(s)
    s = tostring(s or "")
    s = s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;")
    s = s:gsub('"', "&quot;"):gsub("'", "&#39;")
    return s
end

local function json_escape(s)
    s = tostring(s or "")
    s = s:gsub("\\", "\\\\"):gsub('"', '\\"')
    s = s:gsub("\r", "\\r"):gsub("\n", "\\n"):gsub("\t", "\\t")
    s = s:gsub("[%z\1-\31]", " ")
    return s
end

local function jstr(s)
    return '"' .. json_escape(s) .. '"'
end

-- ============================================================
-- 操作日志（默认关闭，UCI debug_log=1 才写）
-- ============================================================

function oplog_enabled()
    return uci:get("picoclaw", "main", "debug_log") == "1"
end

function oplog(level, fmt, ...)
    if not oplog_enabled() then return end
    local ok, msg = pcall(string.format, fmt, ...)
    if not ok then msg = tostring(fmt) end
    msg = tostring(msg):gsub("[\r\n\t]+", " "):gsub("://[^/%s@]+:[^/%s@]+@", "://***@")
    if #msg > 300 then msg = msg:sub(1, 300) .. "..." end
    local st = nixio.fs.stat(PC_OPLOG)
    if st and st.size and st.size >= PC_OPLOG_MAX then
        os.remove(PC_OPLOG .. ".1")
        os.rename(PC_OPLOG, PC_OPLOG .. ".1")
    end
    local existed = nixio.fs.access(PC_OPLOG)
    local f = io.open(PC_OPLOG, "a")
    if not f then return end
    if not existed then pcall(nixio.fs.chmod, PC_OPLOG, 384) end
    f:write(os.date("%Y-%m-%d %H:%M:%S"), " [", tostring(level), "] ", msg, "\n")
    f:close()
end

-- ============================================================
-- 配置读写
-- ============================================================

function ensure_config()
    if uci:get("picoclaw", "main") then return end
    uci:section("picoclaw", "picoclaw", "main", {
        mode = PC_DEFAULT_MODE,
        launcher_port = tostring(PC_DEFAULT_PORT),
        launcher_public = "1",
        asset = "",
        debug_log = "0",
    })
    uci:commit("picoclaw")
end

function get_settings()
    ensure_config()
    local mode = uci:get("picoclaw", "main", "mode") or PC_DEFAULT_MODE
    if mode ~= "gateway" and mode ~= "launcher" then mode = PC_DEFAULT_MODE end
    local port = tonumber(uci:get("picoclaw", "main", "launcher_port") or "")
    if not port or port < 1 or port > 65535 then port = PC_DEFAULT_PORT end
    local public = uci:get("picoclaw", "main", "launcher_public")
    if public == nil then public = "1" end
    local asset = uci:get("picoclaw", "main", "asset") or ""
    if asset ~= "" and not PC_SHA256[asset] then asset = "" end
    return {
        mode = mode,
        launcher_port = port,
        launcher_public = (public == "1" or public == "true"),
        asset = asset,
        debug_log = uci:get("picoclaw", "main", "debug_log") == "1",
    }
end

function save_settings(mode, port, public, asset, debug_log)
    ensure_config()
    if mode ~= "gateway" and mode ~= "launcher" then mode = PC_DEFAULT_MODE end
    port = tonumber(port) or PC_DEFAULT_PORT
    if port < 1 or port > 65535 then port = PC_DEFAULT_PORT end
    if asset and asset ~= "" and not PC_SHA256[asset] then asset = "" end
    uci:set("picoclaw", "main", "mode", mode)
    uci:set("picoclaw", "main", "launcher_port", tostring(port))
    uci:set("picoclaw", "main", "launcher_public", public and "1" or "0")
    uci:set("picoclaw", "main", "asset", asset or "")
    uci:set("picoclaw", "main", "debug_log", debug_log and "1" or "0")
    uci:commit("picoclaw")
end

-- ============================================================
-- 架构检测与资产选择
-- ============================================================

local function get_distrib_arch()
    local c = read_file("/etc/openwrt_release") or ""
    return (c:match("DISTRIB_ARCH%s*=%s*['\"]([^'\"]+)['\"]") or ""):lower()
end

local function get_cpu_arch()
    local c = read_file("/proc/cpuinfo") or ""
    return (c:match("CPU architecture%s*:%s*([%w%.]+)") or ""):lower()
end

function detect_arch()
    local raw = trim(sys.exec("uname -m 2>/dev/null") or "")
    local distrib = get_distrib_arch()
    local cpu = get_cpu_arch()
    local u = raw:lower()
    local d = distrib
    local asset = nil

    -- 优先用 uname，再结合 DISTRIB_ARCH 区分 mips/mipsel、armv6/armv7
    if u == "aarch64" or u == "arm64" or d:find("aarch64", 1, true) then
        asset = "Linux_arm64"
    elseif u == "x86_64" or u == "amd64" or d:find("x86_64", 1, true) then
        asset = "Linux_x86_64"
    elseif u == "riscv64" or d:find("riscv64", 1, true) then
        asset = "Linux_riscv64"
    elseif u == "loongarch64" or u == "loong64" or d:find("loongarch64", 1, true) then
        asset = "Linux_loong64"
    elseif u == "s390x" or d:find("s390x", 1, true) then
        asset = "Linux_s390x"
    elseif u == "armv6l" or u == "armv6" or u == "armv5tel" or d:find("arm1176", 1, true) then
        asset = "Linux_armv6"
    elseif u == "armv7l" or u == "armv7" or u == "armv8l" or d:find("arm_", 1, true) or d:find("armv7", 1, true) then
        asset = "Linux_armv7"
    elseif u == "mipsel" or u == "mipsle" or d:find("mipsel", 1, true) then
        asset = "Linux_mipsle"
    elseif u == "mips" then
        -- 大端 MIPS：上游没有对应资产
        asset = nil
    elseif u == "mips64" or u == "mips64el" then
        asset = nil
    end

    return {
        raw = raw ~= "" and raw or "unknown",
        distrib = distrib ~= "" and distrib or "-",
        cpu = cpu ~= "" and cpu or "-",
        asset = asset or "",
        supported = asset ~= nil,
    }
end

function selected_asset(settings, arch)
    if settings.asset ~= "" then return settings.asset, "manual" end
    if arch.asset ~= "" then return arch.asset, "auto" end
    return "", "none"
end

-- ============================================================
-- 服务 / 进程 / 版本
-- ============================================================

function is_installed()
    return nixio.fs.access("/usr/bin/picoclaw") and nixio.fs.access("/usr/bin/picoclaw-launcher")
end

-- BusyBox 的 comm 只保留 15 字符，picoclaw-launcher 会被截断，所以读 cmdline。
function find_pid()
    if not nixio.fs.access("/proc") then return "", "" end
    for pid in nixio.fs.dir("/proc") do
        if tostring(pid):match("^%d+$") then
            local cmd = read_file("/proc/" .. pid .. "/cmdline") or ""
            local first = cmd:match("^([^%z]*)") or ""
            local base = first:match("([^/]+)$")
            if base == "picoclaw" or base == "picoclaw-launcher" then
                return tostring(pid), base
            end
        end
    end
    return "", ""
end

local function read_panel()
    local active = nixio.fs.access(PC_PANEL_FLAG)
    local public = "1"
    local port = nil
    if active then
        local lines = {}
        local f = io.open(PC_PANEL_FLAG, "r")
        if f then
            for line in f:lines() do lines[#lines + 1] = trim(line) end
            f:close()
        end
        if lines[1] ~= nil and lines[1] ~= "" then public = lines[1] end
        local p = tonumber(lines[2] or "")
        if p and p >= 1 and p <= 65535 then port = p end
    end
    return { active = active, public = (public ~= "0"), port = port }
end

-- 第一行 public，第二行可选的临时端口（备用面板使用）。
local function write_panel(public, port)
    local f = io.open(PC_PANEL_FLAG, "w")
    if not f then return false end
    f:write(public and "1" or "0", "\n")
    f:write(port and tostring(port) or "", "\n")
    f:close()
    pcall(nixio.fs.chmod, PC_PANEL_FLAG, 384)
    return true
end

local function clear_panel()
    os.remove(PC_PANEL_FLAG)
end

local function get_lan_ip()
    local ip = trim(sys.exec("ip -4 addr show br-lan 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -1") or "")
    if ip == "" then ip = trim(sys.exec("uci -q get network.lan.ipaddr 2>/dev/null") or "") end
    if ip == "" or ip == "0.0.0.0" then ip = "127.0.0.1" end
    return ip
end

local function service_autostart()
    return trim(sys.exec("ls /etc/rc.d/S??picoclaw 2>/dev/null") or "") ~= ""
end

-- 运行日志 tail（由 init 脚本重定向 stdout/stderr 生成）
function log_tail(n)
    n = tonumber(n) or 40
    if n < 1 then n = 1 end
    if n > 300 then n = 300 end
    if not nixio.fs.access(PC_RUNTIME_LOG) then return "" end
    return sys.exec("tail -n " .. tostring(n) .. " " .. PC_RUNTIME_LOG .. " 2>/dev/null") or ""
end

local _version_cache = nil

function get_local_version()
    if not is_installed() then return "" end
    local st = nixio.fs.stat("/usr/bin/picoclaw")
    local mtime = (st and st.mtime) or 0
    if _version_cache and _version_cache.mtime == mtime then return _version_cache.version end
    local out = sys.exec("HOME=/root /usr/bin/picoclaw version 2>/dev/null | head -n 5") or ""
    out = out:gsub("\27%[[0-9;]*m", "")
    local v = out:match("([0-9]+%.[0-9]+%.[0-9]+)") or ""
    _version_cache = { mtime = mtime, version = v }
    return v
end

local _latest_cache = nil

local function cached_latest()
    if _latest_cache then return _latest_cache end
    local c = read_file("/tmp/picoclaw-latest.cache") or ""
    local ts = tonumber(c:match("ts=(%d+)"))
    local v = c:match("version=([%w%.%-]+)")
    if ts and v and (os.time() - ts) < 3600 then
        _latest_cache = v
        return v
    end
    return ""
end

local function fetch_latest(force)
    if not force then
        local c = cached_latest()
        if c ~= "" then return c end
    end
    local tool = trim(sys.exec("command -v curl 2>/dev/null") or "")
    local cmd
    if tool ~= "" then
        cmd = "curl -fsSL --max-time 8 https://api.github.com/repos/sipeed/picoclaw/releases/latest 2>/dev/null"
    else
        local uf = trim(sys.exec("command -v uclient-fetch 2>/dev/null") or "")
        if uf ~= "" then
            cmd = "uclient-fetch -q -O - --timeout=8 https://api.github.com/repos/sipeed/picoclaw/releases/latest 2>/dev/null"
        else
            local wg = trim(sys.exec("command -v wget 2>/dev/null") or "")
            if wg ~= "" then
                cmd = "wget -q -O - --timeout=8 https://api.github.com/repos/sipeed/picoclaw/releases/latest 2>/dev/null"
            end
        end
    end
    if not cmd then return "" end
    local body = sys.exec(cmd) or ""
    local v = body:match('"tag_name"%s*:%s*"v?([%w%.%-]+)"') or ""
    if v ~= "" then
        _latest_cache = v
        local f = io.open("/tmp/picoclaw-latest.cache", "w")
        if f then
            f:write("ts=", tostring(os.time()), "\nversion=", v, "\n")
            f:close()
            pcall(nixio.fs.chmod, "/tmp/picoclaw-latest.cache", 384)
        end
    end
    return v
end

local function gateway_port()
    local c = read_file(PC_CONFIG_DIR .. "/config.json") or ""
    local p = tonumber(c:match('"gateway"%s*:%s*{[^}]-"port"%s*:%s*(%d+)') or "")
        or tonumber(c:match('"port"%s*:%s*(%d+)'))
    return p
end

-- ============================================================
-- 后台安装状态
-- ============================================================

function read_install_status()
    local st = {}
    local f = io.open(PC_INSTALL_STATUS, "r")
    if f then
        for line in f:lines() do
            local k, v = line:match("^([%w_]+)=(.*)$")
            if k then st[k] = v end
        end
        f:close()
    end
    if st.state == "running" then
        local pid = tonumber(st.pid) or 0
        local ts = tonumber(st.ts) or 0
        if pid > 0 then
            if not nixio.fs.access("/proc/" .. tostring(pid)) then
                st.state = "failed"
                st.message = "安装进程已退出，请查看日志后重试"
            end
        elseif os.time() - ts > 30 then
            st.state = "failed"
            st.message = "安装进程未能启动，请重试"
        end
    end
    return st
end

function write_install_status(state, step, message, pid, progress)
    local f = io.open(PC_INSTALL_STATUS, "w")
    if not f then return false end
    f:write("state=", tostring(state or ""), "\n")
    f:write("step=", tostring(step or ""), "\n")
    f:write("message=", tostring(message or ""):gsub("[\r\n]+", " "), "\n")
    f:write("pid=", tostring(pid or 0), "\n")
    f:write("progress=", tostring(tonumber(progress) or 0), "\n")
    f:write("ts=", tostring(os.time()), "\n")
    f:close()
    pcall(nixio.fs.chmod, PC_INSTALL_STATUS, 384)
    return true
end

function start_background_install(asset)
    if not nixio.fs.access(PC_INSTALL_SCRIPT) or not nixio.fs.access(PC_INSTALL_INIT) then
        return false, "安装组件缺失（请重新安装插件）"
    end
    local sha = PC_SHA256[asset]
    if not sha then return false, "未知的架构资产：" .. tostring(asset) end
    local url = string.format(
        "https://github.com/sipeed/picoclaw/releases/download/v%s/picoclaw_%s.tar.gz",
        PC_VERSION, asset)

    local f = io.open(PC_INSTALL_ARGS, "w")
    if not f then return false, "无法写入安装参数" end
    f:write("VERSION=", shq(PC_VERSION), "\n")
    f:write("ARCH=", shq(asset), "\n")
    f:write("EXPECTED=", shq(sha), "\n")
    f:write("URL=", shq(url), "\n")
    f:close()
    pcall(nixio.fs.chmod, PC_INSTALL_ARGS, 384)

    os.remove(PC_INSTALL_STATUS)
    os.remove(PC_INSTALL_LOG)
    write_install_status("running", "starting", "正在启动安装进程", 0)
    oplog("INSTALL", "requested version=%s asset=%s", PC_VERSION, asset)
    sys.exec(PC_INSTALL_INIT .. " start >/dev/null 2>&1")
    return true
end

-- ============================================================
-- 状态组装
-- ============================================================

function build_status()
    local settings = get_settings()
    local arch = detect_arch()
    local panel = read_panel()
    local installed = is_installed()
    local pid, pname = find_pid()
    local running = pid ~= ""
    local mode = panel.active and "launcher" or settings.mode
    local asset, asset_src = selected_asset(settings, arch)
    local ip = get_lan_ip()
    local panel_port = panel.port or settings.launcher_port
    local listen_port = nil

    if mode == "launcher" then
        listen_port = panel_port
    else
        listen_port = gateway_port()
    end

    local url = ""
    if mode == "launcher" then
        local host = panel.active and panel.public and ip or "127.0.0.1"
        if not panel.active then host = settings.launcher_public and ip or "127.0.0.1" end
        url = "http://" .. host .. ":" .. tostring(panel_port)
    end

    local mem_kb = 0
    if running then
        local st = read_file("/proc/" .. pid .. "/status") or ""
        mem_kb = tonumber(st:match("VmRSS:%s*(%d+)")) or 0
    end

    return {
        installed = installed,
        running = running,
        pid = pid,
        proc = pname,
        mode = mode,
        default_mode = settings.mode,
        panel_active = panel.active,
        panel_public = panel.public,
        panel_port = panel_port,
        launcher_port = settings.launcher_port,
        launcher_public = settings.launcher_public,
        listen_port = listen_port,
        url = url,
        memory_kb = mem_kb,
        autostart = service_autostart(),
        version = get_local_version(),
        supported = PC_VERSION,
        latest = cached_latest(),
        arch = arch,
        asset = asset,
        asset_src = asset_src,
    }
end

local function status_json()
    local s = build_status()
    local inst = read_install_status()
    local parts = {
        '"ok":true',
        '"installed":' .. (s.installed and "true" or "false"),
        '"running":' .. (s.running and "true" or "false"),
        '"pid":' .. jstr(s.pid),
        '"mode":' .. jstr(s.mode),
        '"default_mode":' .. jstr(s.default_mode),
        '"panel_active":' .. (s.panel_active and "true" or "false"),
        '"panel_public":' .. (s.panel_public and "true" or "false"),
        '"panel_port":' .. tostring(s.panel_port),
        '"launcher_port":' .. tostring(s.launcher_port),
        '"launcher_public":' .. (s.launcher_public and "true" or "false"),
        '"listen_port":' .. (s.listen_port and tostring(s.listen_port) or "null"),
        '"url":' .. jstr(s.url),
        '"memory_kb":' .. tostring(s.memory_kb or 0),
        '"autostart":' .. (s.autostart and "true" or "false"),
        '"version":' .. jstr(s.version),
        '"supported":' .. jstr(s.supported),
        '"latest":' .. jstr(s.latest),
        '"arch_raw":' .. jstr(s.arch.raw),
        '"arch_distrib":' .. jstr(s.arch.distrib),
        '"arch_cpu":' .. jstr(s.arch.cpu),
        '"asset":' .. jstr(s.asset),
        '"asset_detected":' .. jstr(s.arch.asset),
        '"asset_src":' .. jstr(s.asset_src),
        '"install_state":' .. jstr(inst.state or ""),
        '"install_step":' .. jstr(inst.step or ""),
        '"install_message":' .. jstr(inst.message or ""),
        '"install_progress":' .. tostring(tonumber(inst.progress) or 0),
    }
    return "{" .. table.concat(parts, ",") .. "}"
end

local function reply_json(ok, message, extra)
    http.prepare_content("application/json")
    local parts = { '"ok":' .. (ok and "true" or "false"), '"message":' .. jstr(message or "") }
    if extra then
        for k, v in pairs(extra) do
            if type(v) == "boolean" then
                parts[#parts + 1] = '"' .. k .. '":' .. (v and "true" or "false")
            elseif type(v) == "number" then
                parts[#parts + 1] = '"' .. k .. '":' .. tostring(v)
            else
                parts[#parts + 1] = '"' .. k .. '":' .. jstr(v)
            end
        end
    end
    http.write("{" .. table.concat(parts, ",") .. "}")
end

-- ============================================================
-- 数据导出
-- ============================================================

local function do_export(kind)
    local map = {
        config = { "config.json", "picoclaw-config" },
        skills = { "workspace/skills", "picoclaw-skills" },
        memory = { "workspace/memory", "picoclaw-memory" },
        all = { ".", "picoclaw-data" },
    }
    local item = map[kind or ""]
    if not item then
        http.status(400, "Bad Request")
        http.write("unknown export kind")
        return
    end
    if not nixio.fs.access(PC_CONFIG_DIR) then
        http.status(404, "Not Found")
        http.write("config directory not found")
        return
    end

    os.execute("mkdir -p /tmp/picoclaw-export")
    local filename = item[2] .. "-" .. os.date("%Y%m%d-%H%M%S") .. ".tar.gz"
    local out = "/tmp/picoclaw-export/" .. filename
    local rc = os.execute(string.format("tar -czf %s -C %s %s 2>/dev/null",
        shq(out), shq(PC_CONFIG_DIR), shq(item[1])))
    local st = nixio.fs.stat(out)
    if (rc ~= 0 and rc ~= true) or not st then
        os.remove(out)
        http.status(500, "Internal Server Error")
        http.write("export failed: tar error")
        return
    end

    http.header("Content-Type", "application/gzip")
    http.header("Content-Disposition", 'attachment; filename="' .. filename .. '"')
    http.header("Content-Length", tostring(st.size or 0))
    local f = io.open(out, "rb")
    if f then
        while true do
            local chunk = f:read(65536)
            if not chunk or #chunk == 0 then break end
            http.write(chunk)
        end
        f:close()
    end
    os.remove(out)
    oplog("EXPORT", "kind=%s size=%s", kind, tostring(st.size))
end

-- ============================================================
-- 动作处理
-- ============================================================

local function restart_service()
    sys.exec("/etc/init.d/picoclaw stop >/dev/null 2>&1; " ..
             "killall picoclaw picoclaw-launcher 2>/dev/null; " ..
             "sleep 1; /etc/init.d/picoclaw start >/dev/null 2>&1")
end

local function handle_api()
    local op = http.formvalue("do") or ""
    local settings = get_settings()
    local arch = detect_arch()
    local asset

    if op == "start" then
        oplog("SERVICE", "start")
        if not is_installed() then return reply_json(false, "请先安装 PicoClaw") end
        sys.exec("/etc/init.d/picoclaw start >/dev/null 2>&1")
        return reply_json(true, "已发送启动命令")

    elseif op == "stop" then
        oplog("SERVICE", "stop")
        clear_panel()
        sys.exec("/etc/init.d/picoclaw stop >/dev/null 2>&1; killall picoclaw picoclaw-launcher 2>/dev/null")
        return reply_json(true, "服务已停止")

    elseif op == "restart" then
        oplog("SERVICE", "restart")
        restart_service()
        return reply_json(true, "服务已重启")

    elseif op == "open_panel" then
        asset = selected_asset(settings, arch)
        oplog("PANEL", "open public=%s asset=%s", settings.launcher_public and "1" or "0", asset)
        if not is_installed() then return reply_json(false, "请先安装 PicoClaw") end
        if not write_panel(settings.launcher_public, nil) then
            return reply_json(false, "无法写入面板标记")
        end
        restart_service()
        local host = settings.launcher_public and get_lan_ip() or "127.0.0.1"
        return reply_json(true, "网页面板已启动", {
            url = "http://" .. host .. ":" .. tostring(settings.launcher_port),
        })

    elseif op == "open_panel_backup" then
        oplog("PANEL", "open backup port")
        if not is_installed() then return reply_json(false, "请先安装 PicoClaw") end
        -- Launcher v0.3.1 只支持面板密码，不再支持 token；备用面板改用备用端口，
        -- 便于主端口被占用或浏览器缓存异常时仍能进入同一套密码认证。
        local base = tonumber(settings.launcher_port) or PC_DEFAULT_PORT
        local alt = base + 1000
        if alt > 65535 then alt = base - 1000 end
        if alt < 1 then alt = 18801 end
        if not write_panel(true, alt) then
            return reply_json(false, "无法写入面板标记")
        end
        restart_service()
        local url = "http://" .. get_lan_ip() .. ":" .. tostring(alt)
        return reply_json(true, "备用面板已启动，使用 Launcher 面板密码登录", { url = url, port = alt })

    elseif op == "close_panel" then
        oplog("PANEL", "close")
        clear_panel()
        restart_service()
        return reply_json(true, "已关闭网页面板，恢复默认模式")

    elseif op == "autostart_on" then
        oplog("SERVICE", "autostart on")
        sys.exec("/etc/init.d/picoclaw enable >/dev/null 2>&1")
        return reply_json(true, "已设置开机自启")

    elseif op == "autostart_off" then
        oplog("SERVICE", "autostart off")
        sys.exec("/etc/init.d/picoclaw disable >/dev/null 2>&1")
        return reply_json(true, "已取消开机自启")

    elseif op == "install" or op == "update" then
        local ist = read_install_status()
        if ist.state == "running" then
            return reply_json(false, "安装/更新正在进行中")
        end
        if not is_installed() and op == "update" then
            return reply_json(false, "尚未安装，请使用安装按钮")
        end
        asset = http.formvalue("asset") or ""
        if asset == "" then asset = selected_asset(settings, arch) end
        if asset == "" or not PC_SHA256[asset] then
            return reply_json(false, "无法确定 CPU 架构，请在页面上手动选择对应资产")
        end
        local ok, err = start_background_install(asset)
        if not ok then return reply_json(false, err) end
        return reply_json(true, "已开始后台安装：" .. asset)

    elseif op == "uninstall" then
        oplog("SERVICE", "uninstall core")
        clear_panel()
        sys.exec("/etc/init.d/picoclaw disable >/dev/null 2>&1; " ..
                 "/etc/init.d/picoclaw stop >/dev/null 2>&1; " ..
                 "killall picoclaw picoclaw-launcher 2>/dev/null")
        os.remove("/usr/bin/picoclaw")
        os.remove("/usr/bin/picoclaw-launcher")
        os.remove("/usr/bin/picoclaw.bak")
        os.remove("/usr/bin/picoclaw-launcher.bak")
        return reply_json(true, "已卸载核心程序，配置目录保留")

    elseif op == "save_panel" then
        local port = http.formvalue("launcher_port") or PC_DEFAULT_PORT
        local public = http.formvalue("launcher_public") == "1"
        save_settings(settings.mode, port, public, settings.asset, settings.debug_log)
        clear_panel()
        oplog("SETTINGS", "panel port=%s public=%s",
              tostring(port), public and "1" or "0")
        restart_service()
        return reply_json(true, "面板参数已保存，服务已重启")

    elseif op == "debug_log" then
        local dbg = http.formvalue("value") == "1"
        save_settings(settings.mode, settings.launcher_port, settings.launcher_public,
                      settings.asset, dbg)
        oplog("SETTINGS", "debug_log=%s", dbg and "1" or "0")
        return reply_json(true, dbg and "诊断日志已开启" or "诊断日志已关闭")

    elseif op == "check_update" then
        local latest = fetch_latest(true)
        return reply_json(true, latest ~= "" and ("上游最新版本：" .. latest) or "无法获取上游版本", {
            latest = latest,
        })

    elseif op == "install_skills" then
        local src = nixio.fs.access(PC_SKILLS_SRC) and PC_SKILLS_SRC or
                    (nixio.fs.access(PC_SKILLS_ALT) and PC_SKILLS_ALT or nil)
        if not src then return reply_json(false, "未找到内置技能包") end
        os.execute("mkdir -p " .. shq(PC_CONFIG_DIR .. "/workspace/skills"))
        local rc = os.execute("cp -R " .. shq(src) .. "/. " .. shq(PC_CONFIG_DIR .. "/workspace/skills") .. " 2>/dev/null")
        if rc ~= 0 and rc ~= true then
            return reply_json(false, "技能包安装失败")
        end
        oplog("SKILLS", "installed from %s", src)
        return reply_json(true, "OpenWrt 技能包已安装到 workspace/skills")

    elseif op == "clear_log" then
        local f = io.open(PC_RUNTIME_LOG, "w")
        if f then f:close() end
        return reply_json(true, "运行日志已清空")
    end

    return reply_json(false, "未知操作：" .. tostring(op))
end

-- ============================================================
-- 入口
-- ============================================================

function index()
    entry({"admin", "services", "picoclaw"},
          call("action_main"), "PicoClaw", 60).dependent = false
end

function action_main()
    local action = http.formvalue("action") or ""

    if action == "api_status" then
        http.prepare_content("application/json")
        http.write(status_json())
        return
    end

    if action == "api_log" then
        http.prepare_content("application/json")
        http.write('{"ok":true,"log":' .. jstr(log_tail(http.formvalue("lines") or 60)) .. '}')
        return
    end

    if action == "api_action" then
        handle_api()
        return
    end

    if action == "export" then
        do_export(http.formvalue("kind"))
        return
    end

    local st = build_status()
    local inst = read_install_status()
    local install_log = ""
    if inst.state ~= "" and nixio.fs.access(PC_INSTALL_LOG) then
        install_log = sys.exec("tail -n 80 " .. PC_INSTALL_LOG .. " 2>/dev/null") or ""
    end

    local scope = {
        csrf_token = dispatcher.context.authsession or "",
        action_url = dispatcher.build_url("admin", "services", "picoclaw"),
        st = st,
        inst = inst,
        install_log = html_escape(install_log),
        logs = html_escape(log_tail(60)),
        esc = html_escape,
        settings = get_settings(),
        arch = st.arch,
        assets = PC_ASSETS,
        pc_version = PC_VERSION,
        runtime = _VERSION or "",
        config_dir = PC_CONFIG_DIR,
        runtime_log = PC_RUNTIME_LOG,
    }
    template.render("picoclaw/main", scope)
end
