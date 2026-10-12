# 🔒 Cryptographic Policy Security & Key Management

## 1. Cryptographic Standard: Ed25519 (RFC 8032)
- All client policies are signed using standard Ed25519 digital signatures.
- **Public Key (32 bytes)**:
  `2f029fce662a015a2b13a0e0261eea6fb13aae7ba832e6a4c80f6026ef6b6db7`
- Embedded in the Android client application as the trusted root of authority.
- Clients will reject any policy that has:
  - An invalid signature.
  - A tampered payload (even 1 bit change).
  - An expired timestamp (`expires_at < now`).
  - A mismatched `product_id`.
  - A downgraded `revision` number (replay attack protection).

## 2. Private Key Protection
- The private signing key (`6ffe4b5...`) is strictly an offline secret.
- **NEVER** commit the private key to this repository or embed it into an APK.
- If using GitHub Actions for automated signing, store the private key as a GitHub Actions secret: `PANELS_POLICY_SIGNING_KEY` with branch protection requiring maintainer approval on `main`.

## 3. Canonicalization Rules
- Before signing or verifying, the `policy` JSON object is serialized canonically:
  - JSON keys sorted in ascending lexicographical order.
  - Compact separators: `,` between items, `:` between keys and values (no whitespace).
  - UTF-8 byte encoding.
- This guarantees byte-for-byte consistency across Python, Kotlin, and JVM runtimes.
