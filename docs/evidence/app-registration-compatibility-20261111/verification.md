# 应用注册过渡期兼容验收

目标和任务树见 [实施计划](../../plans/app-registration-compatibility.md)，当前规范见 [应用注册规范](../../architecture/linkease-app-registration.md)。

## 实施结果

- RC01：通过。新目录是标准入口，旧 desktop-apps.d 是过渡期入口；单一清单由实际插件拥有，元包没有恢复 JSON/图标副本/注册链接。
- RC02：通过。9 个应用的实际安装配方及钩子已调整；标准链接随包安装，兼容链接由 postinst 创建，prerm 只删除仍指向自身清单的链接。普通自定义文件、目录和其他目标的软链接受到保护。FastNet/DDNSTO 的已知旧清单以 SHA256 精确识别后替换。
- RC03：通过。桌面、网关和 Lua 新目录优先、旧目录兜底；Go 按 ID 去重，Lua 的单 ID 查询在新目录命中后返回。显式目录配置不追加默认目录。网关先确定新旧优先级再过滤 builtin，避免旧清单绕过新清单的能力约束。
- RC04：部分通过。FastNet/DDNSTO 元包各增加局部 postinst，调用插件提供的幂等修复脚本。opkg 四场景实测通过；APK 隔离测试夹具在三次修正后仍因缺少文件嵌入校验信息被拒绝，未进入注册逻辑测试。已暂停 APK 依赖工作并请求追加一轮，尚不能宣称 APK 完成验收。
- RC05：通过。22 个文件按显式映射同步构建仓库；保留元数据仓库 DDNSTO 较新的 4.2.8 版本。8 个对应产品元包发布号各增加一次。共享 meta.mk/CI、FastNet 清单、controller、前端和测速业务不变。

## 验证

| 检查 | 结果 |
| --- | --- |
| 9 应用安装配方/钩子、幂等、升级、自定义文件、卸载 | 9 项测试通过 |
| FastNet、BaiduDrive、Docker、KSpeeder、Kai、LinkEase 集成包契约 | 39 项测试通过 |
| openwrt-app-meta 元包归属 | 1 项测试通过 |
| Go 桌面注册与网关 | 35 项测试通过 |
| Lua 适配器 | .7、.164 的 Lua 均通过 |
| opkg，192.168.30.7 | FastNet/DDNSTO × 插件先更新/元包先更新，共 4 场景通过 |
| APK 3.0.5，192.168.3.164 | 夹具打包失败，未完成验收 |
| 两台设备真实包数据库 SHA256 | 测试前后相同 |

Go 构建和测试使用 SSD 缓存环境；Unix socket 测试使用 SSD 用户目录下较短的临时路径。测试生成的 go.work.sum 已恢复，不属于产品变更。

包管理测试只安装到 `/tmp/registration-compatibility.*` 下隔离根目录，使用真实清单、注册链接与从配方展开的钩子，未包含业务二进制、init 脚本或 UCI defaults。这是包管理迁移检查，不是 SDK 正式包构建或完整桌面 UI 验收。opkg 显式设置离线 IPKG_INSTROOT；APK 在隔离根目录中执行脚本，不使用 force-no-chroot。

仅更新元包而未安装新版插件，不代表迁移完成；两者更新完成后的最终结果应与升级顺序无关。新桌面源码测试通过不代表新桌面运行版本已经发布或部署。

原始证据： [Go](go-tests.json)、[包契约](package-regression.json)、[opkg](opkg.log)、[APK 暂停点](apk-pending.log)、[同步](sync-result.json)、[范围检查](scope-audit.json)、[结构化结果](verification.json)。按用户指令随本记录进行本地提交；未推送、发布或部署业务服务。

APKv2 测试夹具的控制 tar 截断规则参考 [Alpine abuild](https://github.com/alpinelinux/abuild/blob/master/abuild.in)；当前仍缺少数据文件嵌入校验信息，不能作为正式 APK 构建器使用。
