# BaiduDrive Native Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `apps/baidudrive` as a full iStoreOS native plugin that packages the Go Web binary, Baidu NAS SDK, P2PClient launcher path, isolated glibc runtime, LuCI config, and app-meta integration.

**Architecture:** `open-drive` remains the upstream release producer and emits a hub-compatible `baidudrive-binary-<version>.tar.gz`. `istoreos-app-hub/apps/baidudrive` consumes that tarball like `linkease` and installs arch-specific runtime files into OpenWrt package paths.

**Tech Stack:** OpenWrt package Makefiles, rc.common/procd shell scripts, LuCI Lua CBI, POSIX shell release tests.

---

### Task Tree

1. Release artifact contract
   - Add an `open-drive` release script and Makefile target that builds `baidudrive-binary-<version>.tar.gz`.
   - The tarball root is `baidudrive-binary-<version>/`.
   - It contains `baidudrive.aarch64`, `baidudrive.x86_64`, `nas_sdk/<arch>/`, and `glibc/<arch>/`.

2. Service package integration
   - Update `istoreos-app-hub/apps/baidudrive/baidudrive/Makefile`.
   - Install `/usr/sbin/baidudrive`.
   - Install `/opt/baidunas-sdk/{baiduNas,P2PClient.bin,libkernel.so}`.
   - Install `/opt/baidunas-glibc`.
   - Create `/opt/baidunas-sdk/P2PClient` as a symlink to `/usr/sbin/baidudrive`.
   - Disable strip for bundled foreign glibc and proprietary SDK files.

3. Runtime service behavior
   - Replace the simple init script with procd-managed `baiduNas`, SDK init loop, and Web service instances.
   - Keep defaults aligned with the verified native release: SDK host `127.0.0.1`, SDK port `8001`, USB path `/mnt`, download path `/`, data dir under iStore config.
   - Require `macid` and `device_type` before starting SDK-dependent processes.

4. LuCI and app-meta config
   - Add UCI defaults for SDK paths and NAS parameters.
   - Expose required fields in LuCI: data dir, port, macid, device type, USB path, download path, quota path, tmp path, log level.
   - Let `app-meta-baidudrive/config.sh` set the iStore data dir and enable flag only.

5. Verification
   - Add shell tests for the hub tarball layout.
   - Add shell tests for hub package declarations.
   - Run the new tests, syntax checks, relevant Go tests, and final `git status`.

