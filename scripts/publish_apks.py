#!/usr/bin/env python3
"""
Panels Control Center — Artifact Publication Utility
Automates copying built APKs, verifying APK signatures (v2/v3) against the official
release certificate, verifying package metadata, calculating SHA-256 hashes, and updating update.json.

Usage:
    python scripts/publish_apks.py <path_to_apk_directory> <version_name> <version_code> [min_supported_version]
"""

import sys
import os
import hashlib
import json
import shutil
import struct
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_DIR = os.path.join(REPO_ROOT, "products", "panels-play")
APKS_DIR = os.path.join(PRODUCTS_DIR, "apks")
UPDATE_JSON = os.path.join(PRODUCTS_DIR, "update.json")

EXPECTED_PACKAGE_NAME = "com.thepanelshub.panelsplay"
EXPECTED_RELEASE_CERT_SHA256 = "bf3e65d7d48e9da0e45d59f58e91aee70496f719ae5d5822103d8856cc611aa9"

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

def extract_certs_from_apk_signing_block(apk_path):
    """
    Direct binary parsing of the APK Signing Block (magic 'APK Sig Block 42')
    extracting SHA-256 digests of all X.509 DER certificates.
    """
    try:
        with open(apk_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            search_len = min(size, 65535 + 22)
            f.seek(size - search_len)
            data = f.read(search_len)
            eocd_idx = data.rfind(b"\x50\x4b\x05\x06")
            if eocd_idx == -1:
                return []
            eocd_pos = size - search_len + eocd_idx
            f.seek(eocd_pos + 16)
            cd_offset = struct.unpack("<I", f.read(4))[0]
            if cd_offset < 24:
                return []
            f.seek(cd_offset - 24)
            sig_header = f.read(24)
            block_size, magic = struct.unpack("<Q16s", sig_header)
            if magic != b"APK Sig Block 42" or block_size < 32:
                return []
            block_start = cd_offset - block_size - 8
            if block_start < 0:
                return []
            f.seek(block_start)
            block_data = f.read(block_size)

            certs = set()
            i = 8
            while i < len(block_data) - 4:
                if block_data[i] == 0x30 and block_data[i + 1] == 0x82:
                    seq_len = (block_data[i + 2] << 8) | block_data[i + 3]
                    total_len = 4 + seq_len
                    if 500 <= total_len <= 8192 and i + total_len <= len(block_data):
                        der = block_data[i : i + total_len]
                        certs.add(hashlib.sha256(der).hexdigest().lower())
                i += 1
            return list(certs)
    except Exception:
        return []

def verify_apk_signatures(apk_path):
    """
    Verifies that the APK is signed and that the certificate matches the expected release key.
    Uses apksigner if available, falling back to direct APK Signing Block verification.
    """
    certs = []
    # 1. Try apksigner CLI
    apksigner_cmd = shutil.which("apksigner")
    if apksigner_cmd:
        try:
            res = subprocess.run(
                [apksigner_cmd, "verify", "--verbose", "--print-certs", apk_path],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "certificate sha-256 digest:" in line.lower():
                        digest = line.split(":")[-1].strip().lower().replace(" ", "")
                        certs.append(digest)
            else:
                return False, f"apksigner verification failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            pass

    # 2. Extract directly from APK Signing Block
    direct_certs = extract_certs_from_apk_signing_block(apk_path)
    all_certs = list(set(certs + direct_certs))

    if not all_certs:
        return False, "APK is unsigned or contains no valid signing certificates"

    if any(c == EXPECTED_RELEASE_CERT_SHA256 for c in all_certs):
        return True, "Valid release signature"

    return False, f"Certificate SHA-256 mismatch: found {all_certs}, expected {EXPECTED_RELEASE_CERT_SHA256}"

def verify_apk_badging(apk_path, expected_version_name, expected_version_code):
    """
    Optionally inspects package name, version name, and version code via aapt/aapt2.
    """
    aapt_cmd = shutil.which("aapt") or shutil.which("aapt2")
    if not aapt_cmd:
        return True, "aapt not installed; skipping badging check"

    try:
        res = subprocess.run([aapt_cmd, "dump", "badging", apk_path], capture_output=True, text=True)
        if res.returncode != 0:
            return False, f"aapt dump badging failed: {res.stderr.strip()}"

        stdout = res.stdout
        if f"name='{EXPECTED_PACKAGE_NAME}'" not in stdout:
            return False, f"Package name mismatch: expected {EXPECTED_PACKAGE_NAME}"
        if f"versionName='{expected_version_name}'" not in stdout:
            return False, f"versionName mismatch: expected {expected_version_name}"
        if f"versionCode='{expected_version_code}'" not in stdout:
            return False, f"versionCode mismatch: expected {expected_version_code}"
        return True, "Badging verified"
    except Exception as e:
        return False, f"Error running badging verification: {e}"

def publish_apks(source_dir, version_name, version_code, min_version=None):
    os.makedirs(APKS_DIR, exist_ok=True)
    artifacts = []
    primary_download_url = None
    primary_sha256 = None

    print(f"[*] Publishing Panels Play v{version_name} (code {version_code}) artifacts...")

    for abi, (source_name, target_pattern) in ABI_MAPPING.items():
        src_path = os.path.join(source_dir, source_name)
        if not os.path.exists(src_path):
            candidates = [
                f for f in os.listdir(source_dir)
                if abi in f and f.endswith(".apk") and not f.endswith("-unsigned.apk")
            ]
            if candidates:
                src_path = os.path.join(source_dir, candidates[0])
            else:
                print(f"[-] Error: No valid signed APK found for ABI {abi} in {source_dir}")
                sys.exit(1)

        # 1. Reject unsigned APK names
        if "-unsigned" in os.path.basename(src_path):
            print(f"[-] Error: Refusing to publish unsigned artifact: {src_path}")
            sys.exit(1)

        # 2. Verify Android release signature
        is_signed, sign_msg = verify_apk_signatures(src_path)
        if not is_signed:
            print(f"[-] Error: Signature verification failed for {src_path}: {sign_msg}")
            sys.exit(1)
        print(f"    [+] Signature verified for {abi}: {sign_msg}")

        # 3. Verify Badging
        badge_ok, badge_msg = verify_apk_badging(src_path, version_name, version_code)
        if not badge_ok:
            print(f"[-] Error: Badging verification failed for {src_path}: {badge_msg}")
            sys.exit(1)
        print(f"    [+] Badging verified for {abi}: {badge_msg}")

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
