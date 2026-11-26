# PicoClaw 应用包（iStore / OpenWrt 布局）

本目录按 `istoreos/istoreos-app-hub` 的 `apps/<id>/` 约定组织，可直接复制进该仓库提交 PR。

```
apps/picoclaw/
  luci-app-picoclaw-ng/ # 插件本体：luasrc/ -> /usr/lib/lua/luci，root/ -> /
  app-meta-picoclaw/    # 软件中心元数据：logo.png + 依赖，不含程序文件
```

- 运行时依赖：PicoClaw 二进制不随包分发，由插件在安装/更新时按 CPU 架构下载并校验 SHA256。
- 目标版本：上游 PicoClaw v0.3.1（见 `luasrc/controller/picoclaw.lua` 中的 `PC_VERSION`）。
- 权限模型：服务以 root 运行，配置位于 `/root/.picoclaw`，本插件不做调整。

## 构建

包源码是标准 OpenWrt 包，可直接在 buildroot / SDK 中编译：

```sh
# 以 iStoreOS 或 OpenWrt SDK 为例
cp -r apps/picoclaw/luci-app-picoclaw-ng package/
cp -r apps/picoclaw/app-meta-picoclaw package/
make package/luci-app-picoclaw-ng/compile V=s
```

本地快速出包仍用仓库根目录的 `scripts/build-ipk.py`（opkg）和 `scripts/build-apk-v3.sh`（apk-tools 3）。

## 提交收录到 iStore

iStore 是策展制，没有自助上传入口。推荐走聚合仓，一次 PR 同时落地源码、包和商店元数据。

1. Fork `istoreos/istoreos-app-hub`，用 “Fetch upstream” 同步 `main`，新建分支如 `add_app_picoclaw`。
2. 复制本目录到 `apps/picoclaw/`，并在根目录 `syncapps.yaml` 的 `apps:` 下加入：

   ```yaml
     picoclaw:
       luci:
         - local: apps/picoclaw/luci-app-picoclaw-ng
           remote: openwrt-app-actions/applications/luci-app-picoclaw-ng
       meta:
         - local: apps/picoclaw/app-meta-picoclaw
           remote: openwrt-app-meta/applications/app-meta-picoclaw
   ```

3. 本地校验映射（不加 `DRY=1` 才真正写入旧仓）：

   ```sh
   make syncapps-app APP=picoclaw DRY=1
   python3 -B tools/tests/test_app_registration.py
   ```

4. 提交 PR。建议同时开 issue 说明插件用途、目标架构和运行时下载行为，便于维护者判断。

### 注意事项

- iStore 官方仓库只覆盖 `x86_64` 与 `aarch64`；其他架构（armv7、mipsle 等）用户需使用本仓库自建的软件源。
- `app-meta-picoclaw` 只负责商店展示与依赖，禁止安装程序文件、应用清单或注册链接；桌面入口如需注册，由 `luci-app-picoclaw-ng` 自己持有 manifest 与 `/usr/share/linkease/apps.d` 软链。
- 当前未注册桌面入口（`apps.d` 清单），因此不依赖 `luci-app-linkeasefull-embed` 等 iStoreOS 专有组件。

## 版本同步

三处版本号必须一致：

| 位置 | 字段 |
| --- | --- |
| `luci-app-picoclaw-ng/Makefile` | `PKG_VERSION` / `PKG_RELEASE` |
| `app-meta-picoclaw/Makefile` | `PKG_VERSION` / `PKG_RELEASE` |
| `scripts/build-ipk.py`、`scripts/build-apk-v3.sh` | `PKG_VERSION` / `PC_VERSION` |
