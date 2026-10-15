# 🌐 The Panels Control Center — Master Architecture & Operations Guide

**The Panels Control Center** is the central, public governance plane for **Panels Play** (`com.thepanelshub.panelsplay`).

It provides:
- **Version Lifecycle & Gating**: Enforces minimum allowed versions and blocks vulnerable builds.
- **Maintenance Directives**: Informs users of planned maintenance without invalidating their AuthLX accounts.
- **Emergency Kill Switches**: Instant emergency shutdown of client operations.
- **Release & Distribution Metadata**: Publishes verified APK download links, version codes, and SHA-256 digests.
- **Ed25519 Cryptographic Trust**: All client policies are digitally signed with an offline Ed25519 private key. Panels Play embeds the trusted public key to verify policies mathematically before applying them.

> 🖥️ **Web Dashboard Console**: Open [`index.html`](index.html) in any web browser or visit [**https://ThePanelsHub.github.io/panels-control-center/**](https://ThePanelsHub.github.io/panels-control-center/) to manage policies with a clean visual UI and publish directly via GitHub API (no command line required)!

---

## 📁 Repository Structure

```text
panels-control-center/
├── products/
│   ├── panels-play/
│   │   ├── policy.json         # Live cryptographic policy & kill switch for Panels Play
│   │   └── update.json         # Release metadata, APK download URL, & SHA-256 hash
│   └── template/
│       ├── policy.json         # Clean template for onboarding future products
│       └── update.json
├── schema/
│   ├── policy.schema.json      # Formal JSON Schema validator for policy envelopes
│   └── update.schema.json      # Formal JSON Schema validator for update metadata
├── scripts/
│   ├── sign_policy.py          # Python utility to sign policy.json using PEM or hex key
│   ├── verify_policy.py        # Python utility to verify cryptographic Ed25519 signatures
│   └── nacl-fast.min.js        # Self-contained Ed25519 library used by the Web Console
├── index.html                  # Self-contained Web Console (runs locally or on GitHub Pages)
└── README.md                   # This master documentation file
```

---

## 🔍 Detailed Breakdown: Every File & Its Purpose

### 1. `products/panels-play/policy.json` (Live Policy Envelope)

This is the primary file requested by Panels Play over HTTPS whenever the app starts or returns to the foreground.

- **Live URL:** `https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/panels-play/policy.json`
- **Security:** The entire `policy` object is canonicalized (RFC 8785) and signed with Ed25519. If any character inside `policy` is tampered with, signature verification fails and the client blocks entry.

#### Field-by-Field Reference:

| Field | Type | Example | Description & Client Behavior |
|---|---|---|---|
| `schema_version` | String | `"1.0"` | Policy format version. |
| `product_id` | String | `"panels-play"` | Product identity. Panels Play verifies that this matches its internal ID `panels-play`. |
| `policy.revision` | Integer | `1` | Strictly increasing version number. Prevents replay attacks (the client rejects any policy with a revision number lower than the last accepted revision). |
| `policy.issued_at` | String (ISO-8601) | `"2026-10-14T00:00:00Z"` | UTC timestamp when this policy was created and signed. |
| `policy.expires_at` | String (ISO-8601) | `"2027-10-14T00:00:00Z"` | UTC expiration date. If the current time exceeds this date, Panels Play treats the policy as expired. |
| `policy.min_version` | String (SemVer) | `"1.0.0"` | Minimum required version. If installed client version is `< min_version`, the app displays a version update barrier and blocks streaming. |
| `policy.blocked_versions`| Array of Strings | `["1.0.0-beta"]` | Specific versions to retire. If installed version matches any entry, the app displays a blocked version barrier. |
| `policy.maintenance.enabled` | Boolean | `false` | When `true`, Panels Play displays a maintenance announcement to the user without wiping their session. |
| `policy.maintenance.message` | String | `"Scheduled maintenance..."`| The text displayed on the maintenance banner. |
| `policy.emergency_disabled` | Boolean | `false` | **Product Kill Switch.** When `true`, immediately halts Panels Play with an emergency barrier. |
| `policy.global_emergency_disabled`| Boolean | `false` | **Global Kill Switch.** Shuts down all products in the family. |
| `policy.user_message` | String or `null` | `null` | Optional custom message displayed to users when blocked. |
| `signature.algorithm` | String | `"ed25519"` | Cryptographic algorithm name. |
| `signature.public_key` | String (Hex) | `"5910d52a21..."` | The 32-byte Ed25519 public key corresponding to the signing key. Panels Play checks that this matches its pinned trusted key. |
| `signature.signature_hex` | String (Hex) | `128 hex chars` | The 64-byte Ed25519 signature over canonical JSON bytes of `policy`. |

---

### 2. `products/panels-play/update.json` (Release & Distribution Metadata)

This file tells Panels Play about newly published APK releases, download links, and checksums.

- **Live URL:** `https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/panels-play/update.json`

#### Field-by-Field Reference:

| Field | Type | Example | Description |
|---|---|---|---|
| `product_id` | String | `"panels-play"` | Target product identity. |
| `latest_version` | String | `"1.0.0"` | Latest release version string (matches `MARKETING_VERSION`). |
| `latest_version_code` | Integer | `141` | Latest build code (matches `CURRENT_PROJECT_VERSION`). |
| `min_supported_version` | String | `"1.0.0"` | Minimum supported version. |
| `mandatory` | Boolean | `false` | Whether the update is required before using the app. |
| `release_date` | String (ISO-8601) | `"2026-10-14T00:00:00Z"` | Date of release. |
| `release_notes` | String | `"Official release..."` | Release highlights shown in update prompts. |
| `download_url` | String (URL) | `https://github.com/.../PanelsPlay-v1.0.0-universal-release.apk` | Direct download link to the verified release APK. |
| `apk_sha256` | String (Hex) | `"c8d187053d0657f27ffc39d8ce5304701d76fc7dafb86b14170cfb1198593317"` | Lowercase 64-character SHA-256 digest of the universal release APK for file integrity verification. |

---

### 3. `schema/` (JSON Schema Specifications)

- **`policy.schema.json`**: Formal JSON Schema (Draft-07) defining all validation rules for `policy.json`. Enforces regex formats for hex public keys (64 hex characters), signatures (128 hex characters), timestamps, and required properties.
- **`update.schema.json`**: Formal JSON Schema defining all validation rules for `update.json`.

---

### 4. `scripts/` (Cryptographic Utilities)

- **`scripts/sign_policy.py`**:
  Signs `policy.json` offline.
  - Automatically loads your Ed25519 private key from either a `.pem` file (`the-panels-hub-policy-private.pem`) or a raw 64-character hex string.
  - Canonicalizes the nested `policy` block using RFC 8785 sorting (keys sorted alphabetically, compact separators `','` and `':'`).
  - Generates the 64-byte Ed25519 signature.
  - Writes `signature` into `policy.json`.
  - **Usage:**
    ```bash
    python scripts/sign_policy.py products/panels-play/policy.json "C:\path\to\the-panels-hub-policy-private.pem"
    ```
- **`scripts/verify_policy.py`**:
  Verifies the Ed25519 signature of any policy on disk.
  - **Usage:**
    ```bash
    python scripts/verify_policy.py products/panels-play/policy.json
    ```
- **`scripts/nacl-fast.min.js`**:
  Self-contained, audited TweetNaCl library providing in-browser Ed25519 signing in `index.html`. Allows the Web Console to sign policies 100% offline without sending private keys anywhere.

---

### 5. `index.html` (The Web Console Dashboard)

The **Web Console** is a single-page visual dashboard with zero build steps or dependencies.

#### How It Works:
1. **Direct GitHub Fetch**: Reads the latest `policy.json` and `update.json` from GitHub over HTTPS.
2. **Modular Controls**: Every visual toggle clearly shows which file and field it modifies.
3. **In-Browser Signing**: Uses TweetNaCl to sign the canonical JSON right inside your browser using your `.pem` key file.
4. **Direct GitHub Push**: Uses your GitHub Personal Access Token to commit the updated files directly to `ThePanelsHub/panels-control-center` via the GitHub REST API (`PUT /repos/.../contents`).
5. **No GitHub Actions Needed**: Changes are pushed straight into the repository, live within ~5 minutes.

---

## 🗺️ Modular Dashboard Mapping: Which Feature Modifies What?

| Dashboard Module | Target File | Target JSON Field | What It Controls in Panels Play |
|---|---|---|---|
| **Maintenance Switch** | `products/panels-play/policy.json` | `policy.maintenance.enabled` | Turns maintenance banner ON/OFF. |
| **Maintenance Message** | `products/panels-play/policy.json` | `policy.maintenance.message` | Text notice shown to users during maintenance. |
| **Emergency Kill Switch** | `products/panels-play/policy.json` | `policy.emergency_disabled` | Immediate product shutdown barrier. |
| **Global Emergency Stop** | `products/panels-play/policy.json` | `policy.global_emergency_disabled` | Organization-wide emergency directive. |
| **Minimum Version** | `products/panels-play/policy.json` | `policy.min_version` | Retires builds below this SemVer string. |
| **Blocked Versions Chips**| `products/panels-play/policy.json` | `policy.blocked_versions` | Specific APK versions forbidden to connect. |
| **Policy Expiry** | `products/panels-play/policy.json` | `policy.expires_at` | Absolute deadline before policy renewal is required. |
| **Custom Denial Notice** | `products/panels-play/policy.json` | `policy.user_message` | Custom text shown on blocking barriers. |
| **Release Version Name** | `products/panels-play/update.json` | `latest_version` | Displayed version string in update dialogs. |
| **Release Build Code** | `products/panels-play/update.json` | `latest_version_code` | Android integer version code for update checks. |
| **APK Download Link** | `products/panels-play/update.json` | `download_url` | Direct URL to download the new release APK. |
| **APK SHA-256 Digest** | `products/panels-play/update.json` | `apk_sha256` | Checksum used to verify downloaded APK integrity. |
| **Release Notes** | `products/panels-play/update.json` | `release_notes` | Changelog text displayed to users. |

---

## 🔑 Key Management & Trust Boundaries

There are **two distinct cryptographic key sets**:

```text
+-------------------------------------------------------------------------------+
| 1. Android Release Keystore (.jks)                                           |
|    - Used exclusively to sign Android APKs/AABs.                             |
|    - Keystore: the-panels-hub-release.jks (4096-bit RSA)                     |
|    - Cert SHA-256: BF:3E:65:D7:D4:8E:9D:A0:E4:5D:59:F5:8E:91:AE:E7...        |
|    - NEVER commit or share.                                                  |
+-------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------+
| 2. Policy-Signing Ed25519 Key Pair                                           |
|    - Used exclusively to sign policy.json documents.                         |
|    - Private Key: the-panels-hub-policy-private.pem (Keep offline).           |
|    - Public Key:  5910d52a21f0b0cac77dbf16abf5f1b61c98666308bac0807aa38898...|
|    - Public Key is pinned inside Panels Play client.                         |
+-------------------------------------------------------------------------------+
```

---

## 🛠️ Common Operations Runbook

### Operation 1: Turn On Maintenance Mode
1. Open the [Web Console](https://ThePanelsHub.github.io/panels-control-center/) (or double-click `index.html` locally).
2. Flip the **Maintenance Mode** switch to **ON**.
3. (Optional) Type a message: `"Panels Play is undergoing maintenance until 8:00 PM."`
4. Click **"🚀 Sign & Publish to GitHub"**.
5. Live within ~5 minutes. To turn it off, flip the switch back and click Publish.

### Operation 2: Block a Compromised Version
1. Open the Web Console.
2. In **Blocked Specific Versions**, type the bad version string (e.g. `1.0.0-beta`) and click **"+ Block Version"**.
3. Click **"🚀 Sign & Publish to GitHub"**.

### Operation 3: Publish a New App Version
1. Build the signed release APKs using Gradle in `NuvioMobile/`:
   ```bash
   ./gradlew :androidApp:assembleFullRelease
   ```
2. Run the automated publication utility to copy APKs, calculate hashes, and update metadata:
   ```bash
   python scripts/publish_apks.py androidApp/build/outputs/apk/full/release 1.1.0 142 1.1.0
   ```
3. The APKs are stored directly in the repository at `products/panels-play/apks/` and served via raw GitHub URLs (no GitHub Releases required).
4. Review changes, sign the policy if minimum version was updated:
   ```bash
   python scripts/sign_policy.py products/panels-play/policy.json "C:\path\to\the-panels-hub-policy-private.pem"
   ```
5. Commit and push directly to `origin/main`.
