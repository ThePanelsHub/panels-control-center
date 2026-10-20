#!/usr/bin/env node
/**
 * Panels Control Center — Ed25519 Policy Verification Utility (Node.js)
 * Usage:
 *   node verify_policy.js <path/to/policy.json>
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function canonicalJson(obj) {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalJson).join(',') + ']';
  }
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => JSON.stringify(k) + ':' + canonicalJson(obj[k])).join(',') + '}';
}

function verifyPolicyFile(policyFilePath) {
  const fullPolicyPath = path.resolve(policyFilePath);
  if (!fs.existsSync(fullPolicyPath)) {
    console.error(`[-] File not found: ${fullPolicyPath}`);
    return false;
  }

  const raw = fs.readFileSync(fullPolicyPath, 'utf8');
  const data = JSON.parse(raw);
  const policy = data.policy;
  const sigInfo = data.signature;

  if (!policy || !sigInfo) {
    console.error('[-] Invalid policy structure: missing policy or signature block');
    return false;
  }

  const pubHex = sigInfo.public_key;
  const sigHex = sigInfo.signature_hex;

  const canon = canonicalJson(policy);
  const canonBuffer = Buffer.from(canon, 'utf8');

  // Wrap raw 32-byte Ed25519 public key in SPKI DER header
  const spkiPrefix = Buffer.from('302a300506032b6570032100', 'hex');
  const pubKeyDer = Buffer.concat([spkiPrefix, Buffer.from(pubHex, 'hex')]);
  const pubKey = crypto.createPublicKey({ key: pubKeyDer, format: 'der', type: 'spki' });

  const valid = crypto.verify(null, canonBuffer, pubKey, Buffer.from(sigHex, 'hex'));

  if (valid) {
    console.log('[+] Signature VALID!');
    console.log(`    Product:     ${data.product_id}`);
    console.log(`    Revision:    ${policy.revision}`);
    console.log(`    Min Version: ${policy.min_version}`);
    console.log(`    Blocked:     ${JSON.stringify(policy.blocked_versions || [])}`);
    console.log(`    Maintenance: ${policy.maintenance?.enabled}`);
    console.log(`    Public Key:  ${pubHex}`);
    return true;
  } else {
    console.error('[-] Signature INVALID!');
    return false;
  }
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node verify_policy.js <path/to/policy.json>');
    process.exit(1);
  }

  const ok = verifyPolicyFile(args[0]);
  if (!ok) {
    process.exit(1);
  }
}

module.exports = { verifyPolicyFile, canonicalJson };
