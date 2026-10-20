#!/usr/bin/env node
/**
 * Panels Control Center — Ed25519 Offline Policy Signing Utility (Node.js)
 * Usage:
 *   node sign_policy.js <path/to/policy.json> [path/to/private.pem]
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

function resolvePrivateKey(keyInput) {
  const trimmed = (keyInput || '').trim();
  if (fs.existsSync(trimmed)) {
    return fs.readFileSync(trimmed, 'utf8');
  }
  const homePath = path.join(process.env.HOME || '', 'keys', 'policy', 'the-panels-hub-policy-private.pem');
  if (fs.existsSync(homePath)) {
    return fs.readFileSync(homePath, 'utf8');
  }
  if (trimmed.startsWith('-----BEGIN')) {
    return trimmed;
  }
  throw new Error('Private key file not found: ' + (keyInput || homePath));
}

function signPolicyFile(policyFilePath, keyInput) {
  const fullPolicyPath = path.resolve(policyFilePath);
  if (!fs.existsSync(fullPolicyPath)) {
    throw new Error(`Policy file not found: ${fullPolicyPath}`);
  }

  const raw = fs.readFileSync(fullPolicyPath, 'utf8');
  const data = JSON.parse(raw);
  if (!data.policy) {
    throw new Error("Invalid policy file: missing 'policy' block");
  }

  const privateKeyPem = resolvePrivateKey(keyInput);
  const canon = canonicalJson(data.policy);
  const canonBuffer = Buffer.from(canon, 'utf8');

  // Sign with Ed25519 private key
  const signatureBuffer = crypto.sign(null, canonBuffer, privateKeyPem);
  const sigHex = signatureBuffer.toString('hex');

  // Derive public key raw hex
  const privKeyObj = crypto.createPrivateKey(privateKeyPem);
  const pubKeyObj = crypto.createPublicKey(privKeyObj);
  const spkiDer = pubKeyObj.export({ type: 'spki', format: 'der' });
  // In SPKI DER for Ed25519 (RFC 8410), prefix is 12 bytes (302a300506032b6570032100) followed by 32-byte raw public key
  const pubRawBytes = spkiDer.subarray(spkiDer.length - 32);
  const pubKeyHex = pubRawBytes.toString('hex');

  // Verify immediately
  const verified = crypto.verify(null, canonBuffer, pubKeyObj, signatureBuffer);
  if (!verified) {
    throw new Error('Self-verification of generated Ed25519 signature failed!');
  }

  data.signature = {
    algorithm: 'ed25519',
    public_key: pubKeyHex,
    signature_hex: sigHex,
  };

  fs.writeFileSync(fullPolicyPath, JSON.stringify(data, null, 2) + '\n', 'utf8');

  console.log(`[+] Policy successfully signed: ${policyFilePath}`);
  console.log(`    Product:     ${data.product_id}`);
  console.log(`    Revision:    ${data.policy.revision}`);
  console.log(`    Min Version: ${data.policy.min_version}`);
  console.log(`    Public Key:  ${pubKeyHex}`);
  console.log(`    Signature:   ${sigHex}`);
  return true;
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node sign_policy.js <policy_file.json> [private_key_path]');
    process.exit(1);
  }

  const policyFile = args[0];
  const keyArg = args[1] || process.env.PANELS_POLICY_SIGNING_KEY;
  try {
    signPolicyFile(policyFile, keyArg);
  } catch (err) {
    console.error('[-] Signing error:', err.message);
    process.exit(1);
  }
}

module.exports = { signPolicyFile, canonicalJson };
