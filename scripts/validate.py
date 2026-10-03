#!/usr/bin/env python3
"""Validate the resolved config and produced firmware before publication."""
import json
import pathlib
import re
import sys

CI_DIR = pathlib.Path(__file__).resolve().parent.parent
BOARD = 'nokia_xg-040g-md-ubi'
DEVICE = 'nokia,xg-040g-md-ubi'
TARGET = 'airoha/an7581'


def required_packages():
    return [x.strip() for x in (CI_DIR / 'config/required-packages.txt').read_text().splitlines()
            if x.strip() and not x.startswith('#')]


def validate_config(path):
    lines = pathlib.Path(path).read_text().splitlines()
    actual = set(lines)
    required = [
        'CONFIG_TARGET_airoha=y', 'CONFIG_TARGET_airoha_an7581=y',
        f'CONFIG_TARGET_airoha_an7581_DEVICE_{BOARD}=y',
        'CONFIG_TARGET_ROOTFS_SQUASHFS=y', 'CONFIG_TARGET_ROOTFS_INITRAMFS=y',
        'CONFIG_LUCI_LANG_zh_Hans=y',
    ] + [f'CONFIG_PACKAGE_{x}=y' for x in required_packages()]
    errors = [f'Missing required config: {x}' for x in required if x not in actual]
    selected = [x for x in lines if re.match(r'^CONFIG_TARGET_(?:DEVICE_)?airoha_an7581_DEVICE_.+=y$', x)]
    expected = [f'CONFIG_TARGET_airoha_an7581_DEVICE_{BOARD}=y']
    if selected != expected:
        errors.append(f'Expected exactly the MD UBI profile; selected: {selected}')
    for symbol in ['CONFIG_TARGET_MULTI_PROFILE', 'CONFIG_TARGET_ALL_PROFILES',
                   'CONFIG_TARGET_PER_DEVICE_ROOTFS', 'CONFIG_PACKAGE_dnsmasq',
                   'CONFIG_PACKAGE_vlmcsd']:
        if f'{symbol}=y' in actual:
            errors.append(f'Unexpected config: {symbol}=y')
    return errors


def validate_images(meta_path, profiles_path, manifest_path):
    meta = json.loads(pathlib.Path(meta_path).read_text())
    version = meta.get('version') or {}
    errors = []
    if DEVICE not in (meta.get('supported_devices') or []):
        errors.append(f'Image metadata does not support {DEVICE}')
    if version.get('board') != BOARD or version.get('target') != TARGET:
        errors.append(f'Wrong board/target in image metadata: {version}')
    profiles = json.loads(pathlib.Path(profiles_path).read_text()).get('profiles') or {}
    if set(profiles) != {BOARD}:
        errors.append(f'Expected only {BOARD} in profiles.json, found {sorted(profiles)}')
    names = [x.get('name', '') for x in (profiles.get(BOARD) or {}).get('images', [])]
    if not any(x.endswith(f'-{BOARD}-squashfs-sysupgrade.itb') for x in names):
        errors.append('profiles.json does not advertise the MD UBI sysupgrade.itb')
    packages = {x.split()[0] for x in pathlib.Path(manifest_path).read_text().splitlines() if x.strip()}
    errors.extend(f'Missing package in rootfs manifest: {x}' for x in required_packages() if x not in packages)
    return errors


def main():
    if len(sys.argv) == 3 and sys.argv[1] == 'config':
        errors = validate_config(sys.argv[2])
    elif len(sys.argv) == 5 and sys.argv[1] == 'images':
        errors = validate_images(*sys.argv[2:])
    else:
        print('Usage: validate.py config CONFIG | images METADATA PROFILES MANIFEST', file=sys.stderr)
        return 2
    if errors:
        print('\n'.join('ERROR: ' + x for x in errors), file=sys.stderr)
        return 1
    print('Validated MD UBI target and all required runtime packages.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
