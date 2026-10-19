# FastNet软件中心动态入口

app-meta0.7.7-r7增加entry.sh及META_UCI=fastnet。构建器依现有entry.sh规则安装/usr/libexec/istoree/fastnet.sh并登记entrysh能力；静态entry/href仍是原LuCI管理页，不替换管理入口。

status只读：可执行文件表示deployed，procd running才表示运行。从正在运行实例的实际`FastNet web --addr`命令读取端口，避免未应用的UCI改动误指向新端口；端口必须1–65535，异常或服务状态读取失败返回非零。停止、未部署、仅loopback监听不发布可直接打开的Web；不读取/输出API token。不通过pid文件或文件存在猜测running。多个运行实例端口不一致视为无法确定，不返回猜测地址。start/stop仅为软件中心原有明确动作入口，status不触发它们。

Quickstart普通应用入口沿统一动态解析规则；首页“测速”是业务入口：确认安装且运行并有有效Web才同窗直达；未安装保留既有确认安装。已安装未运行/旧元数据无动态能力时确认后沿原检查/配置流程，不自动启动、不重复安装；未知/超时明确重试。安装成功后先打开原配置，不声称服务已运行。

当前B快速验证仅更新脚本及本机meta能力标记，不虚构已安装meta包版本升级。包配方、本地构建测试、目标脚本SHA和真实导航证据应分别记录；未推送/发布前远端包不自动获得本能力。
