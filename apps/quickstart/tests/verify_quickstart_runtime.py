#!/usr/bin/env python3
import argparse
import hashlib
import os
import re
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
BACKEND_MAKEFILE = APP_ROOT / "quickstart" / "Makefile"
GO_SECURITY_FLOORS = {(1, 26): 11, (1, 27): 4}
EXPECTED_GO_MODULE = "github.com/istoreos/quickstart/backend/cmd/backend"
RUNTIME_NAMES = ("quickstart.x86_64", "quickstart.aarch64", "quickstart.arm")


def make_value(path: Path, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:=(.*)$", path.read_text(), re.MULTILINE)
    if not match:
        raise RuntimeError(f"{key} is missing from {path}")
    return match.group(1).strip()


def version_is_safe(actual: str) -> bool:
    parts = tuple(int(part) for part in actual.split("."))
    if len(parts) != 3 or parts[0] != 1:
        return False
    branch = parts[:2]
    if branch in GO_SECURITY_FLOORS:
        return parts[2] >= GO_SECURITY_FLOORS[branch]
    return branch > max(GO_SECURITY_FLOORS)


def inspect_binary(binary: Path) -> tuple[str, str]:
    go = os.environ.get("GO", "go")
    result = subprocess.run(
        [go, "version", "-m", str(binary)],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.splitlines()
    version_match = re.search(r": go([0-9]+(?:\.[0-9]+)+)$", lines[0])
    module_line = next((line for line in lines if line.lstrip().startswith("path\t")), "")
    if not version_match or not module_line:
        raise RuntimeError(f"incomplete Go build info in {binary}")
    return version_match.group(1), module_line.strip().split("\t", 1)[1]


def verify_archive(
    archive: Path,
    version: str | None = None,
    check_recipe_hash: bool = True,
) -> None:
    version = version or make_value(BACKEND_MAKEFILE, "PKG_VERSION")
    expected_hash = make_value(BACKEND_MAKEFILE, "PKG_HASH") if check_recipe_hash else None
    actual_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    if expected_hash is not None and actual_hash != expected_hash:
        raise RuntimeError(f"archive SHA256 is {actual_hash}; Makefile expects {expected_hash}")
    print(f"archive_sha256={actual_hash}")

    prefix = f"quickstart-binary-{version}"
    with tarfile.open(archive, "r:gz") as bundle, tempfile.TemporaryDirectory() as directory:
        temp_root = Path(directory)
        manifest_member = bundle.getmember(f"{prefix}/MANIFEST")
        manifest_file = bundle.extractfile(manifest_member)
        if manifest_file is None:
            raise RuntimeError("runtime MANIFEST cannot be read")
        manifest = manifest_file.read().decode()
        manifest_values = dict(
            line.split("=", 1) for line in manifest.splitlines() if "=" in line
        )
        for key in ("version", "go_version", "go_module"):
            if key not in manifest_values:
                raise RuntimeError(f"runtime MANIFEST is missing {key}")
        if manifest_values["version"] != version:
            raise RuntimeError(
                f"runtime MANIFEST version is {manifest_values['version']}; expected {version}"
            )
        manifest_go_version = manifest_values["go_version"].removeprefix("go")
        if not version_is_safe(manifest_go_version):
            raise RuntimeError(
                f"runtime MANIFEST uses unsupported or vulnerable go{manifest_go_version}"
            )
        if manifest_values["go_module"] != EXPECTED_GO_MODULE:
            raise RuntimeError(
                f"runtime MANIFEST module is {manifest_values['go_module']}; expected {EXPECTED_GO_MODULE}"
            )

        for name in RUNTIME_NAMES:
            member = bundle.getmember(f"{prefix}/{name}")
            source = bundle.extractfile(member)
            if source is None:
                raise RuntimeError(f"cannot read {name} from runtime archive")
            binary = temp_root / name
            binary.write_bytes(source.read())
            go_version, module_path = inspect_binary(binary)
            if not version_is_safe(go_version):
                raise RuntimeError(f"{name} uses unsupported or vulnerable go{go_version}")
            if module_path != EXPECTED_GO_MODULE:
                raise RuntimeError(
                    f"{name} module path is {module_path}; expected {EXPECTED_GO_MODULE}"
                )
            if go_version != manifest_go_version:
                raise RuntimeError(
                    f"{name} uses go{go_version}; MANIFEST declares go{manifest_go_version}"
                )
            print(f"verified {name}: go{go_version} {module_path}")


def runtime_url() -> str:
    version = make_value(BACKEND_MAKEFILE, "PKG_VERSION")
    filename = (
        make_value(BACKEND_MAKEFILE, "PKG_SOURCE")
        .replace("$(PKG_NAME)", "quickstart")
        .replace("$(PKG_VERSION)", version)
    )
    base = make_value(BACKEND_MAKEFILE, "PKG_SOURCE_URL").replace(
        "$(PKG_VERSION)", version
    )
    return base + filename


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the Quickstart prebuilt runtime selected by its OpenWrt recipe"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--archive", type=Path, help="path to an already downloaded runtime tarball")
    source.add_argument(
        "--download",
        action="store_true",
        help="download the archive selected by the package recipe",
    )
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="verify an unpublished --archive and print the hash needed by the package recipe",
    )
    args = parser.parse_args()

    if args.archive:
        if args.candidate:
            match = re.fullmatch(r"quickstart-binary-(.+)\.tar\.gz", args.archive.name)
            if not match:
                raise RuntimeError("candidate archive name must be quickstart-binary-VERSION.tar.gz")
            verify_archive(args.archive, version=match.group(1), check_recipe_hash=False)
        else:
            verify_archive(args.archive)
        return

    if args.candidate:
        parser.error("--candidate requires --archive")

    with tempfile.TemporaryDirectory() as directory:
        version = make_value(BACKEND_MAKEFILE, "PKG_VERSION")
        archive = Path(directory) / f"quickstart-binary-{version}.tar.gz"
        url = runtime_url()
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, archive)
        verify_archive(archive)


if __name__ == "__main__":
    main()
