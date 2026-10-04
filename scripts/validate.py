#!/usr/bin/env python3
"""Validate multi-profile configs, firmware identity and per-image packages."""
import json
import pathlib
import re
import sys
from devices import profiles_for, required_packages


def validate_config(path, subtarget, catalog):
    lines = pathlib.Path(path).read_text().splitlines()
    actual = set(lines)
    expected = {
        f"CONFIG_TARGET_DEVICE_airoha_{subtarget}_DEVICE_{profile}=y"
        for profile in profiles_for(catalog, subtarget)
    }
    required = {
        "CONFIG_TARGET_airoha=y", f"CONFIG_TARGET_airoha_{subtarget}=y",
        "CONFIG_TARGET_MULTI_PROFILE=y", "CONFIG_TARGET_PER_DEVICE_ROOTFS=y",
        "CONFIG_TARGET_ROOTFS_SQUASHFS=y", "CONFIG_TARGET_ROOTFS_INITRAMFS=y",
        "CONFIG_JSON_OVERVIEW_IMAGE_INFO=y", "CONFIG_LUCI_LANG_zh_Hans=y",
    } | expected | {f"CONFIG_PACKAGE_{x}=y" for x in required_packages(subtarget)}
    errors = [f"Missing required config: {x}" for x in sorted(required - actual)]
    # fitblk is a hidden symbol. Multi-profile defaults build it as m and the
    # upstream per-device package lists install it into FIT-based rootfs images.
    if not {"CONFIG_PACKAGE_fitblk=y", "CONFIG_PACKAGE_fitblk=m"} & actual:
        errors.append("Missing required config: CONFIG_PACKAGE_fitblk=y or m")
    selected = {
        x for x in lines
        if re.match(r"^CONFIG_TARGET_(?:DEVICE_)?airoha_an758[13]_DEVICE_.+=y$", x)
    }
    if selected != expected:
        errors.append(f"Selected profiles differ from upstream catalog: {sorted(selected ^ expected)}")
    for symbol in ["CONFIG_TARGET_ALL_PROFILES", "CONFIG_PACKAGE_dnsmasq", "CONFIG_PACKAGE_vlmcsd"]:
        if f"{symbol}=y" in actual:
            errors.append(f"Unexpected config: {symbol}=y")
    other = "an7583" if subtarget == "an7581" else "an7581"
    if f"CONFIG_TARGET_airoha_{other}=y" in actual:
        errors.append(f"Wrong additional subtarget selected: {other}")
    return errors


def validate_profile(meta, profile_info, profile, subtarget, packages):
    errors = []
    device = profile.replace("_", ",", 1)
    version = meta.get("version") or {}
    if version.get("board") != profile or version.get("target") != f"airoha/{subtarget}":
        errors.append(f"{profile}: wrong image board/target: {version}")
    if device not in meta.get("supported_devices", []):
        errors.append(f"{profile}: image metadata does not support {device}")
    if set(meta.get("supported_devices", [])) != set(profile_info.get("supported_devices", [])):
        errors.append(f"{profile}: supported_devices differs between image and profiles.json")
    hardware = set(profile_info.get("device_packages", []))
    hardware = {x for x in hardware if not x.startswith("-")} - {
        x[1:] for x in hardware if x.startswith("-")
    }
    required = set(required_packages(subtarget)) | hardware
    errors.extend(f"{profile}: missing rootfs package {x}" for x in sorted(required - set(packages)))
    return errors


def main():
    if len(sys.argv) != 5 or sys.argv[1] != "config":
        print("Usage: validate.py config CONFIG SUBTARGET CATALOG", file=sys.stderr)
        return 2
    catalog = json.loads(pathlib.Path(sys.argv[4]).read_text())
    errors = validate_config(sys.argv[2], sys.argv[3], catalog)
    if errors:
        print("\n".join("ERROR: " + x for x in errors), file=sys.stderr)
        return 1
    print(f"Validated {sys.argv[3]} profiles and all required runtime packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
