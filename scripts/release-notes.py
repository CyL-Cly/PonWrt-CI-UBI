#!/usr/bin/env python3
"""Require complete device coverage before publishing a multi-device release."""
import hashlib
import json
import re
import os
import pathlib
import sys


def verify_checksums(output, subtarget):
    checked = {}
    for line in (output / f"SHA256SUMS-{subtarget}").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or pathlib.Path(name).name != name:
            raise ValueError("Invalid checksum entry")
        if name in checked:
            raise ValueError("Duplicate checksum entry: " + name)
        with (output / name).open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest:
            raise ValueError("Artifact checksum mismatch: " + name)
        checked[name] = digest
    if not checked:
        raise ValueError("Empty checksum list")
    return checked


def release_notes(output, catalog):
    lines = [
        "# PonWrt — all supported PON devices", "",
        "Source: " + catalog["source_commit"],
        "Requested source ref: " + os.environ.get("SOURCE_REF", "master"),
        "Weekly builds: Sunday 04:17 Asia/Shanghai (GitHub scheduling may be delayed).", "",
        "Each image is device-specific. Match the full model, variant and flash layout.",
        "Back up the device's own calibration/identity data and verify its boot chain before flashing.",
        "The initramfs image is for RAM recovery; sysupgrade images require the matching installed layout.",
        "Native upstream factory/bootloader artifacts, where present, follow that profile's installation procedure.", "",
        "| Target | Profile | Upgrade image |", "| --- | --- | --- |",
    ]
    for subtarget, expected in catalog["targets"].items():
        checked = verify_checksums(output, subtarget)
        summary_name = f"{subtarget}-build-summary.json"
        if summary_name not in checked:
            raise ValueError("Build summary is not checksummed")
        summary = json.loads((output / f"{subtarget}-build-summary.json").read_text())
        if summary["source_commit"] != catalog["source_commit"]:
            raise ValueError(f"{subtarget}: build used a different source commit")
        actual = {x["profile"] for x in summary["profiles"]}
        if summary["target"] != f"airoha/{subtarget}":
            raise ValueError("Wrong summary target")
        if actual != set(expected) or len(summary["profiles"]) != len(expected):
            raise ValueError(f"{subtarget}: incomplete release coverage: {actual ^ set(expected)}")
        for item in summary["profiles"]:
            names = {image["name"] for image in item["images"]}
            if item["sysupgrade"] not in names or not set(item["recovery"]) <= names or not item["recovery"]:
                raise ValueError("Missing advertised upgrade/recovery image")
            for image in item["images"]:
                name = image["name"]
                if checked.get(name) != image["sha256"] or (output / name).stat().st_size != image["size"]:
                    raise ValueError("Artifact differs from validated image: " + name)
            lines.append(f"| {subtarget} | {item['profile']} | {item['sysupgrade']} |")
    lines += [
        "", "Every profile passed image identity, size/hash and per-image installed-package checks.",
        "OpenClash, Lucky, GecoosAC, Samba4, WOL Ultra, Chinese LuCI and the PON tools are included.",
        "Hardware defaults remain profile-specific; NPU firmware is selected for the correct SoC.",
        "Feed/package revisions, actual per-image manifests and SHA256SUMS are included.",
        "These builds have not been tested on every physical device.", "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: release-notes.py OUTPUT CATALOG NOTES")
    catalog = json.loads(pathlib.Path(sys.argv[2]).read_text())
    pathlib.Path(sys.argv[3]).write_text(release_notes(pathlib.Path(sys.argv[1]), catalog))

