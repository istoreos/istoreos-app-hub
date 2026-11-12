#!/usr/bin/env python3
"""Build local, unpublished IPKs by executing runtime recipes' install targets.

This verifies prebuilt packaging without claiming an OpenWrt SDK compilation.
Release archives and release.mk are generated from explicit input binaries.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

HUB = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(files):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.GNU_FORMAT) as target:
        parents = {str(parent) for name, _, _, _ in files for parent in Path(name).parents if str(parent) != "."}
        for name in sorted(parents, key=lambda name: (name.count("/"), name)):
            info = tarfile.TarInfo("./" + name + "/")
            info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, 0
            target.addfile(info)
        for name, data, mode, link in sorted(files):
            info = tarfile.TarInfo("./" + name)
            info.mode, info.uid, info.gid, info.mtime = mode, 0, 0, 0
            if link:
                info.type, info.linkname = tarfile.SYMTYPE, link
                target.addfile(info)
            else:
                info.size = len(data)
                target.addfile(info, io.BytesIO(data))
    return gzip.compress(output.getvalue(), mtime=0)


def files_from(root):
    return [(str(p.relative_to(root)), b"" if p.is_symlink() else p.read_bytes(),
             p.lstat().st_mode & 0o777, os.readlink(p) if p.is_symlink() else "")
            for p in root.rglob("*") if p.is_file() or p.is_symlink()]


def hook(recipe, name, phase):
    match = re.search(r"^define Package/" + re.escape(name) + "/" + phase +
                      r"\n(.*?)^endef", recipe, re.M | re.S)
    return match.group(1).replace("$$", "$") if match else None


def ipk(output, name, version, arch, stage, depends, scripts, conffiles):
    control = (f"Package: {name}\nVersion: {version}\nArchitecture: {arch}\n"
               "Maintainer: LinkEase\nSection: admin\nPriority: optional\n"
               "Description: Device Time Machine candidate\n")
    if depends:
        control += "Depends: " + ", ".join(depends) + "\n"
    controls = [("control", control.encode(), 0o644, "")]
    controls += [(phase, body.encode(), 0o755, "") for phase, body in scripts.items() if body]
    if conffiles:
        controls.append(("conffiles", ("\n".join(conffiles) + "\n").encode(), 0o644, ""))
    payload = archive(files_from(stage))
    body = archive([("debian-binary", b"2.0\n", 0o644, ""),
                    ("control.tar.gz", archive(controls), 0o644, ""),
                    ("data.tar.gz", payload, 0o644, "")])
    path = output / f"{name}_{version}_{arch}.ipk"
    path.write_bytes(body)
    return {"path": str(path), "sha256": sha(path), "depends": depends}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("otm-amd64", "otm-arm64", "linkspace-amd64", "linkspace-arm64", "output", "work"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    output, work = args.output.resolve(), args.work.resolve()
    output.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    releases = {}
    for name, version, prefix, inputs in [
        ("optimemachine", "0.2.0-otm17-rc1", "OPTIMEMACHINE", [args.otm_amd64, args.otm_arm64]),
        ("linkspace", "0.2.0-otm.4", "LINKSPACE", [args.linkspace_amd64, args.linkspace_arm64]),
    ]:
        folder = HUB / "apps" / name / name
        release = []
        for arch, binary in zip(["x86_64", "aarch64"], inputs):
            executable = "optimemachine_bin" if name == "optimemachine" else "linkspace"
            files = [(f"{name}-{version}/{executable}", binary.read_bytes(), 0o755, "")]
            if name == "linkspace":
                descriptor = {"schemaVersion": 1, "path": "/usr/bin/linkspace",
                              "version": version, "sha256": sha(binary)}
                files.append((f"{name}-{version}/dependency.json",
                              (json.dumps(descriptor) + "\n").encode(), 0o644, ""))
            path = output / f"{name}-{version}-{arch}.tar.gz"
            path.write_bytes(archive(files))
            release.append(f"{prefix}_HASH_{arch}:={sha(path)}\n")
            releases[f"{name}/{arch}"] = {"path": str(path), "sha256": sha(path), "binarySHA256": sha(binary)}
        (folder / "release.mk").write_text("# Local candidate archives; not yet published.\n" + "".join(release))

    sdk = work / "packaging-harness"
    (sdk / "include").mkdir(parents=True, exist_ok=True)
    (sdk / "rules.mk").write_text("")
    (sdk / "include/package.mk").write_text("")
    packages = {}
    for name, version, binary in [("linkspace", "0.2.0-otm.4", args.linkspace_amd64),
                                  ("optimemachine", "0.2.0-otm17-rc1", args.otm_amd64)]:
        folder = HUB / "apps" / name / name
        build = sdk / "build" / f"{name}-{version}"
        build.mkdir(parents=True, exist_ok=True)
        shutil.copy2(binary, build / ("optimemachine_bin" if name == "optimemachine" else name))
        if name == "linkspace":
            (build / "dependency.json").write_text(json.dumps({"schemaVersion": 1,
                "path": "/usr/bin/linkspace", "version": version, "sha256": sha(binary)}) + "\n")
        stage = work / f"stage-{name}"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        harness = sdk / f"{name}.mk"
        harness.write_text(f"TOPDIR:={sdk}\nARCH:=x86_64\nBUILD_DIR:={sdk}/build\nINCLUDE_DIR:={sdk}/include\n"
                           "INSTALL_DIR:=install -d -m0755\nINSTALL_BIN:=install -m0755\n"
                           "INSTALL_DATA:=install -m0644\nINSTALL_CONF:=install -m0600\nCP:=cp -a\n"
                           f"include {folder}/Makefile\n.PHONY: stage\nstage:\n"
                           f"\t$(call Package/{name}/install,{stage})\n")
        subprocess.run(["make", "--no-print-directory", "-f", str(harness), "stage"], cwd=folder, check=True)
        recipe = (folder / "Makefile").read_text()
        deps = re.search(r"^ DEPENDS:=(.*)$", recipe, re.M).group(1)
        depends = re.findall(r"\+([a-zA-Z0-9_.-]+)", deps)
        scripts = {p: hook(recipe, name, p) for p in ["preinst", "postinst", "prerm", "postrm"]}
        config = hook(recipe, name, "conffiles") or ""
        packages[name] = ipk(output, name, version + "-1", "x86_64", stage, depends, scripts, config.splitlines())

    for name, version, source, depends in [
        ("luci-app-optimemachine", "0.2.0-r1", HUB / "apps/optimemachine/luci-app-optimemachine/root",
         ["optimemachine", "luci-base", "luci-lib-linkeaseauth", "linkease-app-entry"]),
        ("app-meta-optimemachine", "0.2.0-1", HUB / "apps/optimemachine/app-meta-optimemachine",
         ["optimemachine", "luci-app-optimemachine"]),
    ]:
        stage = work / f"stage-{name}"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        if name.startswith("luci-"):
            shutil.copytree(source, stage, dirs_exist_ok=True)
        else:
            # Exercise the canonical software-center meta.mk in an isolated
            # mirror, since aggregation intentionally does not own apps/meta.mk.
            mirror = sdk / "meta-source/apps/optimemachine" / name
            mirror.mkdir(parents=True, exist_ok=True)
            for item in ["Makefile", "entry.sh", "logo.png"]:
                shutil.copy2(source / item, mirror / item)
            shared = HUB.parent / "openwrt-app-meta/meta.mk"
            shutil.copy2(shared, mirror.parent.parent / "meta.mk")
            harness = sdk / "meta.mk"
            harness.write_text(f"TOPDIR:={sdk}\nINCLUDE_DIR:={sdk}/include\nBUILD_DIR:={sdk}/build\n"
                "INSTALL_DIR:=install -d -m0755\nINSTALL_BIN:=install -m0755\nINSTALL_DATA:=install -m0644\n"
                "empty:=\nspace:=$(empty) $(empty)\ncomma:=,\ndefine newline\n\n\nendef\n"
                f"include {mirror}/Makefile\n.PHONY: stage\nstage:\n"
                f"\t$(call Package/{name}/install,{stage})\n")
            subprocess.run(["make", "--no-print-directory", "-f", str(harness), "stage"], cwd=mirror, check=True)
            json.loads((stage / "usr/lib/opkg/meta/optimemachine.json").read_text())
        packages[name] = ipk(output, name, version, "all", stage, depends, {}, [])
    report = {"schemaVersion": 1, "publiclyPublished": False,
              "runtimeInstallTargetsExecuted": True, "sdkCompilation": False,
              "releases": releases, "packages": packages}
    (output / "packages.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"packages": list(packages), "output": str(output)}))


if __name__ == "__main__":
    main()
