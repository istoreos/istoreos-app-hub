# LinkEase 应用注册规范

状态：current。应用注册目录、包归属和升级规则的唯一规范；应用访问与认证见 [Apps 集成](linkease-apps-integration.md)。

## 标准入口与唯一归属

所有 builtin、iframe、module 类型统一注册到 `/usr/share/linkease/apps.d`。类型差异通过清单能力判断，不通过不同目录判断。过渡期保留 `/usr/share/linkeasefull/desktop-apps.d` 兼容入口；两个入口指向插件持有的同一份清单，不复制 JSON。不增加 `/usr/share/linkeasefull/apps.d`。

| 包 | 职责 |
| --- | --- |
| 有独立 Web/运行服务的应用包 | 持有 `/usr/share/<id>/<id>-plugin.json`，安装标准链接，维护旧桌面兼容链接 |
| 只有 LuCI 页面的 `luci-app-*` | 持有清单、应用图标及新旧入口；不另建 companion 包 |
| `app-meta-*` | 软件中心元数据、软件中心图标、依赖；不得安装应用清单、应用资产副本或注册链接 |
| 桌面、网关、Lua 解析器 | 新目录优先、旧目录兜底、按应用 ID 去重；builtin 在桌面中解析，独立网关按能力忽略 |

软件中心 logo.png 是元数据图标，仍由 app-meta 拥有。供桌面页面独立使用的图标由实际插件包提供，不能链接到只有安装 app-meta 才存在的文件。

## 现有包的归属

| ID | 唯一所属包 | 登记文件 |
| --- | --- | --- |
| fastnet | fastnet | 17-fastnet.json |
| ddnsto | luci-app-ddnsto | 16-ddnsto.json |
| kspeeder | istoreenhance | 20-kspeeder.json |
| dockermanager | dockermanager | 20-dockermanager-plugin.json |
| baidudrive | baidudrive | 10-baidudrive-plugin.json |
| kaiplus | kaiplus | 00-kaiplus-plugin.json |
| kai | kai | 05-kai-plugin.json |
| agentflow | agentflow | 30-agentflow.json |
| openwrt-luci | luci-app-linkeasefull-embed | 15-openwrt-luci.json |

FastNet 的首页卡片另有 Quickstart ABI 注册；其职责是卡片资源/尺寸/接口，不是完整应用注册，不在本规范中合并为同一份协议。

## 安装示例

独立应用 Makefile：

```makefile
$(INSTALL_DIR) $(1)/usr/share/example $(1)/usr/share/linkease/apps.d
$(INSTALL_DATA) ./files/example-plugin.json $(1)/usr/share/example/example-plugin.json
ln -sf /usr/share/example/example-plugin.json $(1)/usr/share/linkease/apps.d/20-example.json
```

LuCI-only 可用 `luci-app-example/root/usr/share/example/example-plugin.json`、`root/usr/share/example/www/logo.png` 及 `root/usr/share/linkease/apps.d/20-example.json`；最后一个必须是指向设备绝对路径的软链接。

过渡期由拥有清单的插件在 postinst 中创建兼容软链接，目标与标准链接完全相同。兼容链接不放入包文件清单，避免与尚未升级的历史元包发生文件归属冲突；卸载由插件钩子精确清理。不对共享旧目录建立整体软链接，以免影响其他插件和自定义文件。

DDNSTO 的清单和图标位于 `/usr/share/ddnsto`；其独立 LuCI URL、LuciContainer 及内容隔离参数不变。LinkEaseFull 自有 OpenWrt 静态资源仍可位于其产品目录；本规范不删除其产品资源。

## 升级与卸载

- 安装、升级和重装补齐缺失的兼容入口，已有正确链接保持不变。对历史 app-meta 普通清单，只有 SHA256 匹配已知原文件才替换为插件清单的链接；用户修改的普通文件、目录和其他链接（含失效链接）必须保留。
- 使用 `IPKG_INSTROOT` 支持离线根目录；不自动启动应用、不修改网络配置。
- 卸载只删除仍指向自己的登记；旧目录只能用 rmdir 尝试移除空目录，禁止递归清空共享目录。
- 迁出 app-meta 后不恢复其旧 root 文件。FastNet/DDNSTO 的历史元包曾拥有旧 JSON，升级回收旧文件可能删除插件先前创建的链接，因此仅这两个元包增加局部 postinst，调用插件自带的 register-desktop.sh 修复入口；脚本和清单仍只由插件安装。两者更新完成后，结果不依赖升级顺序。只有元包更新且尚未安装新版插件，不代表迁移完成。
- 元包保留原有 `META_DEPENDS:=+包名` 普通依赖，不新增最低版本约束，不改共享 meta.mk 或元数据 CI。普通依赖不保证升级全部已装插件，不能把只升级元包描述为设备迁移完成。
- 默认读取器按新目录、旧目录顺序查找，同一 ID 优先采用新目录的有效清单。显式目录配置只读取指定目录，不自动追加系统路径。兼容退出需等插件与桌面升级稳定后另行决策，本轮不删除旧入口。
- 每个本轮修改的包和对应产品元包发布号只增加一次；既有待提交更新在原值上继续保留。
- 配方变更与已发布二进制分别验收。桌面/网关源码默认目录变更需进入后续运行版本发布，不得把源码检查写成已部署。

## 两种仓库布局

聚合源码以 `istoreos-app-hub/apps/<id>` 为准，按 syncapps.yaml 的显式映射同步实际构建仓库。`openwrt-app-meta/applications/app-meta-*` 同样不得持有应用登记。本次迁移只同步任务文件；旧清单删除必须显式传播，不执行全仓 rsync --delete。

聚合仓库检查命令：`python3 -B tools/tests/test_app_registration.py`。测试涵盖实际安装配方、链接目标、重复 ID、历史清单升级、自定义文件保留与卸载钩子保护，复用聚合仓库已有检查工作流。元数据仓库检查命令：`python3 -B tests/test_application_registration.py`，验证禁止元包重复登记。元数据仓库保留原有共享 meta.mk 和 CI，不新增工作流；上述元数据检查按需手动执行。
