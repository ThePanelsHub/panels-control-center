#!/usr/bin/env python3
"""
Panels Control Center — Ed25519 Policy Verification Utility
Usage:
    python verify_policy.py <path/to/policy.json>
"""

import sys
import json
from cryptography.hazmat.primitives.asymmetric import ed25519

def verify_file(policy_file_path):
    with open(policy_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    policy = data['policy']
    sig_info = data['signature']

    pub_hex = sig_info['public_key']
    sig_hex = sig_info['signature_hex']

    pub = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
    canon = json.dumps(policy, sort_keys=True, separators=(',', ':')).encode('utf-8')

    try:
        pub.verify(bytes.fromhex(sig_hex), canon)
        print("[+] Signature VALID!")
        print(f"    Product:     {data.get('product_id')}")
        print(f"    Revision:    {policy.get('revision')}")
        print(f"    Min Version: {policy.get('min_version')}")
        print(f"    Blocked:     {policy.get('blocked_versions')}")
        print(f"    Maintenance: {policy.get('maintenance', {}).get('enabled')}")
        return True
    except Exception as e:
        print("[-] Signature INVALID:", e)
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python verify_policy.py <policy_file.json>")
        sys.exit(1)
    if not verify_file(sys.argv[1]):
        sys.exit(1)
