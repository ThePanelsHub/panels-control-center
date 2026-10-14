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

def load_private_key(key_input):
    key_str = key_input.strip()
    if os.path.exists(key_str):
        with open(key_str, 'rb') as f:
            content = f.read()
        if b'BEGIN' in content:
            return serialization.load_pem_private_key(content, password=None)
        else:
            return ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(content.decode().strip()))
    return ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key_str))

def sign_file(policy_file_path, private_key_input):
    with open(policy_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'policy' not in data:
        raise ValueError("Invalid policy file: missing 'policy' block")

    priv = load_private_key(private_key_input)
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    canon = canonical_bytes(data['policy'])
    sig = priv.sign(canon)

    data['signature'] = {
        'algorithm': 'ed25519',
        'public_key': pub_bytes.hex(),
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
