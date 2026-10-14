# 📖 The Panels Hub — Complete Beginner's & Operations Guide

Welcome to the central operations, build, and administration guide for **The Panels Hub** and **Panels Play**.
This guide is written in plain English for administrators, operators, and developers who need to manage releases, enforce version policies, maintain security, and restore the project on any computer.

---

## 📑 Table of Contents

1. [A. System Overview](#a-system-overview)
2. [B. First-Time Setup & Machine Restoration](#b-first-time-setup--machine-restoration)
3. [C. Android Release Building & Signing](#c-android-release-building--signing)
4. [D. Key Management & Security Architecture](#d-key-management--security-architecture)
5. [E. Policy Creation and Signing](#e-policy-creation-and-signing)
6. [F. Policy Publication & Transport](#f-policy-publication--transport)
7. [G. Control Center Features](#g-control-center-features)
8. [H. Maintenance and Version Control](#h-maintenance-and-version-control)
9. [I. Failure Recovery](#i-failure-recovery)
10. [J. AuthLX Subscription & Expiry Management](#j-authlx-subscription--expiry-management)
11. [K. Testing and Troubleshooting Reference](#k-testing-and-troubleshooting-reference)
12. [L. Git & GitHub Workflows](#l-git--github-workflows)
13. [M. Backup and Disaster Recovery](#m-backup-and-disaster-recovery)
14. [N. Security Checklist](#n-security-checklist)
15. [O. Checklist Before Deleting Local Project](#o-checklist-before-deleting-local-project)

---

## A. System Overview

The system consists of independent, decoupled layers that communicate securely over HTTPS:

| Component | Repository / Location | Primary Role |
|---|---|---|
| **Panels Play App** | `ThePanelsHub/the-panels-streaming` | Kotlin Multiplatform Android client application (Package ID: `com.thepanelshub.panelsplay`). |
| **Panels Control Center** | `ThePanelsHub/panels-control-center` | Central policy plane for version control, maintenance mode, and emergency kill switches. |
| **AuthLX Licensing API** | `api.authlx.com` | User authentication, hardware lock (HWID) binding, and subscription entitlement enforcement. |
| **Android Release Keystore** | Keystore file: `the-panels-hub-release.jks` | 4096-bit RSA keystore used to sign Android APKs/AABs for production distribution. |
| **Policy Private Key** | `the-panels-hub-policy-private.pem` | Offline Ed25519 private key used by the operator to sign policy updates. **Never shared.** |
| **Policy Public Key** | Pinned in client & published | Ed25519 public key (`5910d52a21...`) embedded in Panels Play to verify policy integrity. |

### Component Relationship Diagram

```text
                  +-----------------------------------+
                  |          Administrator            |
                  +-----------------+-----------------+
                                    |
            +-----------------------+-----------------------+
            | (signs policy)                                | (edits users/plans)
            v                                               v
+-----------------------+                       +-----------------------+
| Panels Control Center |                       |      AuthLX API       |
| GitHub raw JSON repo  |                       |  Authentication & HWID|
+-----------+-----------+                       +-----------+-----------+
            |                                               |
            | HTTPS GET (Ed25519 verified)                  | HTTPS POST (token & session)
            v                                               v
+-----------------------------------------------------------------------+
|                              Panels Play                              |
|                       Android Client Application                      |
+-----------------------------------------------------------------------+
```

---

## B. First-Time Setup & Machine Restoration

If you are cloning this project onto a new PC or setting up from scratch, follow these exact requirements:

### Prerequisites

| Tool | Version Requirement | Notes |
|---|---|---|
| **Operating System** | Windows 10/11, macOS, or Linux | Windows requires PowerShell 5.1+ or 7+. |
| **Java Development Kit (JDK)** | JDK 17 to JDK 21 | Android Studio's bundled JBR (`jbr/`) is recommended. |
| **Android SDK** | Compile SDK 37, Min SDK 24 | Build tools 34.0.0 or 36.0.0. |
| **Python** | Python 3.10 or newer | Required for policy signing and verification scripts. |
| **Git** | 2.30 or newer | Configured with `ThePanelsHub`. |

### Step-by-Step Restoration Commands

```bash
# 1. Clone the Android application repository
git clone https://github.com/ThePanelsHub/the-panels-streaming.git NuvioMobile
cd NuvioMobile
git checkout main

# 2. Clone the Control Center repository in a sibling directory
cd ..
git clone https://github.com/ThePanelsHub/panels-control-center.git panels-control-center
cd panels-control-center
git checkout main
```

### Python Dependencies for Control Center

```bash
cd panels-control-center
pip install cryptography jsonschema
```

---

## C. Android Release Building & Signing

Panels Play uses Gradle with Android Gradle Plugin (AGP) and Kotlin Multiplatform.

### 1. Release Keystore Specifications

- **Keystore File:** `the-panels-hub-release.jks`
- **Keystore Type:** PKCS12 (4096-bit RSA)
- **Key Alias:** `the-panels-hub-release`
- **Certificate DN:** `CN=The Panels Hub, OU=Release, O=The Panels Hub, L=Gorakhpur, ST=Uttar Pradesh, C=IN`
- **Certificate SHA-256 Digest:** `BF:3E:65:D7:D4:8E:9D:A0:E4:5D:59:F5:8E:91:AE:E7:04:96:F7:19:AE:5D:58:22:10:3D:88:56:CC:61:1A:A9`

### 2. Configuring Local Signing Credentials

Open `NuvioMobile/local.properties` (this file is ignored by Git and never committed):

```properties
sdk.dir=C\:\\Users\\<YourUser>\\AppData\\Local\\Android\\Sdk

THE_PANELS_HUB_RELEASE_STORE_FILE=C\:\\Users\\<YourUser>\\Documents\\the-panels-hub-keys\\android\\the-panels-hub-release.jks
THE_PANELS_HUB_RELEASE_STORE_PASSWORD=YourKeystorePassword
THE_PANELS_HUB_RELEASE_KEY_ALIAS=the-panels-hub-release
THE_PANELS_HUB_RELEASE_KEY_PASSWORD=YourKeystorePassword
```

*(Alternatively, you can set environment variables with the same names in your shell or CI system).*

### 3. Release Build Command

```powershell
cd C:\Users\Atharv\StudioProjects\NuvioMobile
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"

# Build signed full release APKs (Universal and per-ABI splits)
.\gradlew.bat :androidApp:assembleFullRelease -PreleaseMinifyEnabled=false --no-daemon
```

### 4. Produced Artifacts & Checksums

After building, artifacts are located in `androidApp\build\outputs\apk\full\release\`:
- `androidApp-full-universal-release.apk`: Universal APK compatible with all Android devices.
- `androidApp-full-arm64-v8a-release.apk`: Optimized for modern 64-bit phones.

### 5. Signature Verification with apksigner

```powershell
$apksigner = Get-ChildItem "C:\Users\Atharv\AppData\Local\Android\Sdk\build-tools" -Filter "apksigner.bat" -Recurse | Select-Object -First 1 -ExpandProperty FullName
& $apksigner verify --verbose --print-certs "androidApp\build\outputs\apk\full\release\androidApp-full-universal-release.apk"
```

Expected output:
```text
Verifies
Verified using v2 scheme (APK Signature Scheme v2): true
Number of signers: 1
Signer #1 certificate DN: CN=The Panels Hub, OU=Release, O=The Panels Hub...
```

---

## D. Key Management & Security Architecture

There are **three distinct cryptographic keys** in this system. They have completely different roles and must **never** be mixed:

| Key Asset | Stored Location | Sensitivity | What Happens If Lost? |
|---|---|---|---|
| **Android Release Keystore** (`.jks`) | Offline in secure backup | **CRITICAL PRIVATE** | Existing users will not be able to install app updates without uninstalling the app first. |
| **Policy Private Key** (`.pem`) | Offline in secure backup | **CRITICAL PRIVATE** | You cannot sign new Control Center policies. (Requires publishing a new app build with rotated public key). |
| **Policy Public Key** (`.pem` / hex) | Embedded in app & GitHub | **PUBLIC** | Intended to be public; safe to commit and display. |

### Rules for Private Key Security

1. **NEVER** commit `the-panels-hub-release.jks` or `the-panels-hub-policy-private.pem` into Git.
2. **NEVER** paste private keys or passwords into chat prompts, pull request descriptions, or issue trackers.
3. Keep an offline, encrypted copy of your keys on a secure external USB drive or hardware vault.

---

## E. Policy Creation and Signing

Policies in Panels Control Center govern version retirement, maintenance directives, and emergency shutdown.

### 1. The Policy Format (`products/panels-play/policy.json`)

```json
{
  "schema_version": "1.0",
  "product_id": "panels-play",
  "policy": {
    "revision": 1,
    "issued_at": "2026-10-14T00:00:00Z",
    "expires_at": "2027-10-14T00:00:00Z",
    "min_version": "1.0.0",
    "blocked_versions": [],
    "maintenance": {
      "enabled": false,
      "message": "Panels Play is undergoing scheduled maintenance."
    },
    "emergency_disabled": false,
    "global_emergency_disabled": false,
    "user_message": null
  },
  "signature": {
    "algorithm": "ed25519",
    "public_key": "5910d52a21f0b0cac77dbf16abf5f1b61c98666308bac0807aa38898765bff50",
    "signature_hex": "..."
  }
}
```

### 2. Signing a Policy Offline

The signing utility `scripts/sign_policy.py` accepts either a path to your `.pem` private key file or a raw hex string:

```bash
cd panels-control-center
python scripts/sign_policy.py products/panels-play/policy.json "C:\path\to\the-panels-hub-policy-private.pem"
```

Expected output:
```text
[+] Policy successfully signed: products/panels-play/policy.json
    Public Key: 5910d52a21f0b0cac77dbf16abf5f1b61c98666308bac0807aa38898765bff50
    Signature:  ...
```

### 3. Verifying the Signature

```bash
python scripts/verify_policy.py products/panels-play/policy.json
```

Expected output:
```text
[+] Signature VALID!
    Product:     panels-play
    Revision:    1
    Min Version: 1.0.0
    Blocked:     []
    Maintenance: False
```

---

## F. Policy Publication & Transport

1. **How It Works:** Panels Play downloads its policy directly from the raw GitHub endpoint:
   `https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/panels-play/policy.json`
2. **Pushing Policy Updates:**
   After signing and verifying locally:
   ```bash
   git add products/panels-play/policy.json products/panels-play/update.json
   git commit -m "chore(policy): update panels-play release metadata"
   git push origin main
   ```
3. **Propagation Delay:** Raw GitHub content has a CDN cache time-to-live (TTL) of approximately **5 minutes**. Clients refresh the policy upon application startup and foreground resume.

---

## G. Control Center Features

| Directive | JSON Property | What It Does | When To Use |
|---|---|---|---|
| **Emergency Shutdown** | `emergency_disabled: true` | Completely locks Panels Play with a prominent barrier message. | Critical security breach or urgent takedown. |
| **Global Emergency** | `global_emergency_disabled: true` | Shuts down all products in the family simultaneously. | Organization-wide incident response. |
| **Maintenance Mode** | `maintenance.enabled: true` | Displays maintenance banner without invalidating user sessions. | Upgrading database, API servers, or debrid bridges. |
| **Minimum Version** | `min_version: "1.0.1"` | Blocks any installed version strictly lower than `1.0.1`. | Retiring older APKs with known bugs or vulnerabilities. |
| **Blocked Versions** | `blocked_versions: ["1.0.0"]` | Blocks specific faulty version codes/strings. | A specific bad build was distributed and must be halted. |

---

## H. Maintenance and Version Control

### How to Block a Specific Version Safely

1. Open `products/panels-play/policy.json`.
2. Increment `revision` (e.g. `1` -> `2`).
3. Add the bad version to `blocked_versions`:
   `"blocked_versions": ["1.0.0"]`
4. Set a helpful `user_message`:
   `"user_message": "Panels Play v1.0.0 has been retired. Please update to v1.0.1."`
5. Run `python scripts/sign_policy.py ...`.
6. Run `python scripts/verify_policy.py ...`.
7. Commit and push to `origin main`.

---

## I. Failure Recovery

| Failure Mode | Client Behavior | Recovery Action |
|---|---|---|
| **GitHub / Network Down** | Panels Play displays a retryable network error without allowing unauthenticated entry. | Check internet connection or GitHub status. |
| **Invalid Signature / Tampered** | Client rejects policy immediately and displays `Untrusted signing key` or `Verification failed`. | Re-sign with authorized private key and push. |
| **Policy Expired (`expires_at` past)** | Client rejects policy as expired. | Update `expires_at` to a future date, re-sign, and push. |
| **Accidental Kill Switch Trigger** | App shows emergency stop screen. | Edit `emergency_disabled: false`, increment revision, re-sign, and push immediately. |
| **Lost Policy Private Key** | Cannot sign future policies. | Generate new key pair, update `TRUSTED_PUBLIC_KEYS` in app, and publish updated APK. |

---

## J. AuthLX Subscription & Expiry Management

AuthLX provides user authentication, licensing, and subscription enforcement:

1. **Authoritative Expiry Synchronization:**
   - When a user logs in, AuthLX returns their token, username, tier, and subscription expiry.
   - Panels Play evaluates both the **date AND time** (comparing UTC millisecond instants).
   - If an administrator extends or shortens the subscription in AuthLX control panel:
     - On app resume, startup, or when viewing the Account screen, Panels Play queries `/verify-session`.
     - An extended date/time updates the local storage, shifts the expiry timer, and reflects on the Account screen (`"Expires: 14 Oct 2026, 2:30 PM"`).
     - A shortened date/time that has elapsed immediately denies protected access and logs the user out.
2. **Session Persistence:**
   - Tokens are stored securely using Android Keystore encryption with synchronous `.commit()` persistence, surviving normal closure, process death, and phone restarts.

---

## K. Testing and Troubleshooting Reference

### Essential Test Commands (Run from `NuvioMobile/`)

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"

# Run all AuthLX authentication, date/time, and expiry regression tests
.\gradlew.bat :composeApp:testAndroidHostTest --tests "com.nuvio.app.core.auth.AuthLxIntegrationTest" --no-daemon

# Run Control Center cryptographic signature and policy tests
.\gradlew.bat :composeApp:testAndroidHostTest --tests "com.thepanels.control.ControlCenterPolicyTest" --no-daemon

# Run the complete test suite (1,662 tests)
.\gradlew.bat :composeApp:testAndroidHostTest --no-daemon

# Verify Android Lint for full release
.\gradlew.bat :androidApp:lintFullRelease --no-daemon
```

---

## L. Git & GitHub Workflows

### Remote Mapping

- **Panels Play (`NuvioMobile`):**
  - Remote: `target` (`https://github.com/ThePanelsHub/the-panels-streaming.git`), Branch: `main`
  - Upstream tracking: `origin` (`https://github.com/NuvioMedia/NuvioMobile.git`), Branch: `cmp-rewrite`
- **Control Center (`panels-control-center`):**
  - Remote: `origin` (`https://github.com/ThePanelsHub/panels-control-center.git`), Branch: `main`

### Routine Check & Push Commands

```bash
git status
git fetch target
git log -3 --oneline
git push target HEAD:main
```

---

## M. Backup and Disaster Recovery

Before removing this project from your PC or reinstalling your operating system, back up these items to an **external USB drive / secure private vault**:

1. **Android Keystore:** `the-panels-hub-release.jks` and its password.
2. **Policy Private Key:** `the-panels-hub-policy-private.pem`.
3. **Policy Public Key:** `the-panels-hub-policy-public.pem`.
4. **Verified Release APK:** Backup copy of `PanelsPlay-v1.0.0-universal-release.apk` and its `release-metadata.txt`.
5. **Credentials Note:** AuthLX App ID (`dfaea25c-95c2-46ab-8b11-e5241c1bab81`).

---

## N. Security Checklist

- [x] Android release keystore stored outside source directories.
- [x] Policy private key stored outside source directories.
- [x] No plaintext passwords or private keys committed to Git.
- [x] `.gitignore` verified to exclude `.jks`, `.pem`, `local.properties`, and build caches.
- [x] Android release APK signed with 4096-bit RSA key and verified with `apksigner`.
- [x] Control Center policies signed with Ed25519 and verified with cryptographic scripts.
- [x] AuthLX expiry validation enforces both date and time precision.
- [x] Full test suite (1,662 tests) passing with zero failures.

---

## O. Checklist Before Deleting Local Project

Before removing the project from this computer:

- [ ] Confirm all commits are pushed to `ThePanelsHub/the-panels-streaming` on GitHub.
- [ ] Confirm all commits are pushed to `ThePanelsHub/panels-control-center` on GitHub.
- [ ] Back up `C:\Users\Atharv\Documents\the-panels-hub-keys\` to an external USB or secure storage.
- [ ] Back up `C:\Users\Atharv\Documents\the-panels-hub-release\` to external storage.
- [ ] Confirm you know the keystore password (`ThePanelsHub...`).
- [ ] Open GitHub in your browser and verify the repositories display the latest commit hashes.
