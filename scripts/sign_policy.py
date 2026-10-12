#!/usr/bin/env python3
"""
Panels Control Center — Ed25519 Offline Policy Signing Utility
Usage:
    python sign_policy.py <path/to/policy.json> <private_key_hex_or_env>
"""

import sys
import os
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def canonical_bytes(policy_dict):
    return json.dumps(policy_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')

def sign_file(policy_file_path, private_key_hex):
    with open(policy_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'policy' not in data:
        raise ValueError("Invalid policy file: missing 'policy' block")

    priv = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw if hasattr(serialization, 'PrivateFormat') else serialization.PublicFormat.Raw
    )

    canon = canonical_bytes(data['policy'])
    sig = priv.sign(canon)

    data['signature'] = {
        'algorithm': 'ed25519',
        'public_key': pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex(),
        'signature_hex': sig.hex()
    }

    with open(policy_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"[+] Policy successfully signed: {policy_file_path}")
    print(f"    Public Key: {data['signature']['public_key']}")
    print(f"    Signature:  {data['signature']['signature_hex']}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python sign_policy.py <policy_file.json> [private_key_hex]")
        sys.exit(1)

    file_path = sys.argv[1]
    key_hex = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('PANELS_POLICY_SIGNING_KEY')
    if not key_hex:
        print("Error: Private key must be provided as arg or PANELS_POLICY_SIGNING_KEY env variable.")
        sys.exit(1)

    sign_file(file_path, key_hex.strip())
