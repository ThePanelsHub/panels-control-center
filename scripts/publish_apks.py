#!/usr/bin/env python3
"""
Panels Control Center — Artifact Publication Utility
Automates copying built APKs, verifying SHA-256 hashes, and updating update.json.

Usage:
    python scripts/publish_apks.py <path_to_apk_directory> <version_name> <version_code> [min_supported_version]
"""

import sys
import os
import hashlib
import json
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_DIR = os.path.join(REPO_ROOT, "products", "panels-play")
APKS_DIR = os.path.join(PRODUCTS_DIR, "apks")
UPDATE_JSON = os.path.join(PRODUCTS_DIR, "update.json")

ABI_MAPPING = {
    "arm64-v8a": ("androidApp-full-arm64-v8a-release.apk", "PanelsPlay-v{version}-arm64-v8a.apk"),
    "armeabi-v7a": ("androidApp-full-armeabi-v7a-release.apk", "PanelsPlay-v{version}-armeabi-v7a.apk"),
    "x86_64": ("androidApp-full-x86_64-release.apk", "PanelsPlay-v{version}-x86_64.apk"),
    "x86": ("androidApp-full-x86-release.apk", "PanelsPlay-v{version}-x86.apk"),
}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def publish_apks(source_dir, version_name, version_code, min_version=None):
    os.makedirs(APKS_DIR, exist_ok=True)
    artifacts = []
    primary_download_url = None
    primary_sha256 = None

    print(f"[*] Publishing Panels Play v{version_name} (code {version_code}) artifacts...")

    for abi, (source_name, target_pattern) in ABI_MAPPING.items():
        src_path = os.path.join(source_dir, source_name)
        if not os.path.exists(src_path):
            candidates = [f for f in os.listdir(source_dir) if abi in f and f.endswith(".apk")]
            if candidates:
                src_path = os.path.join(source_dir, candidates[0])
            else:
                print(f"[-] Warning: No APK found for ABI {abi} in {source_dir}")
                continue

        target_name = target_pattern.format(version=version_name)
        dst_path = os.path.join(APKS_DIR, target_name)
        shutil.copy2(src_path, dst_path)

        file_size = os.path.getsize(dst_path)
        sha256 = compute_sha256(dst_path)
        raw_url = f"https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/panels-play/apks/{target_name}"

        artifacts.append({
            "abi": abi,
            "download_url": raw_url,
            "apk_sha256": sha256,
            "file_size_bytes": file_size,
            "min_sdk": 26,
        })

        if abi == "arm64-v8a" or primary_download_url is None:
            primary_download_url = raw_url
            primary_sha256 = sha256

        print(f"    [+] {abi}: {target_name} ({file_size:,} bytes)")
        print(f"        SHA-256: {sha256}")

    if not artifacts:
        print("[-] Error: No valid APK artifacts were published.")
        sys.exit(1)

    with open(UPDATE_JSON, "r", encoding="utf-8") as f:
        update_data = json.load(f)

    update_data["latest_version"] = version_name
    update_data["latest_version_code"] = int(version_code)
    if min_version:
        update_data["min_supported_version"] = min_version
    update_data["download_url"] = primary_download_url
    update_data["apk_sha256"] = primary_sha256
    update_data["artifacts"] = artifacts

    with open(UPDATE_JSON, "w", encoding="utf-8") as f:
        json.dump(update_data, f, indent=2)

    print(f"[+] Successfully updated {UPDATE_JSON}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python publish_apks.py <apk_directory> <version_name> <version_code> [min_version]")
        sys.exit(1)

    min_v = sys.argv[4] if len(sys.argv) > 4 else None
    publish_apks(sys.argv[1], sys.argv[2], sys.argv[3], min_v)
