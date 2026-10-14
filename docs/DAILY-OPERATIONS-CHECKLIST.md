# 📋 Panels Play & Control Center — Daily Operations Checklist

This checklist provides short, copy-pasteable instructions for everyday administration, release publication, and incident response.

---

## 1. Publishing an Ordinary Policy Update

1. Edit `products/panels-play/policy.json` (e.g., change `user_message`, `min_version`, or `maintenance`).
2. Increment `policy.revision` by 1.
3. Sign the policy offline using the private key:
   ```bash
   cd panels-control-center
   python scripts/sign_policy.py products/panels-play/policy.json "C:\Users\Atharv\Documents\the-panels-hub-keys\policy\the-panels-hub-policy-private.pem"
   ```
4. Verify the signature locally:
   ```bash
   python scripts/verify_policy.py products/panels-play/policy.json
   ```
5. Commit and push:
   ```bash
   git add products/panels-play/policy.json
   git commit -m "chore(policy): update panels-play policy to revision X"
   git push origin main
   ```

---

## 2. Verifying a Signed Policy

To verify that any policy file on disk is valid and untampered:

```bash
cd panels-control-center
python scripts/verify_policy.py products/panels-play/policy.json
```

Expected output:
```text
[+] Signature VALID!
    Product:     panels-play
    Revision:    ...
    Min Version: ...
```

---

## 3. Publishing a New App Release

1. Update `iosApp/Configuration/Version.xcconfig` with the new version name (`MARKETING_VERSION`) and version code (`CURRENT_PROJECT_VERSION`).
2. Build the signed release APK in `NuvioMobile/`:
   ```powershell
   cd C:\Users\Atharv\StudioProjects\NuvioMobile
   $env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
   $env:PATH="$env:JAVA_HOME\bin;$env:PATH"
   .\gradlew.bat :androidApp:assembleFullRelease -PreleaseMinifyEnabled=false --no-daemon
   ```
3. Copy the generated universal APK to backup storage:
   ```powershell
   Copy-Item "androidApp\build\outputs\apk\full\release\androidApp-full-universal-release.apk" "C:\Users\Atharv\Documents\the-panels-hub-release\PanelsPlay-universal-release.apk"
   ```
4. Compute the SHA-256 hash:
   ```powershell
   Get-FileHash "C:\Users\Atharv\Documents\the-panels-hub-release\PanelsPlay-universal-release.apk" -Algorithm SHA256
   ```
5. Update `products/panels-play/update.json` in `panels-control-center` with the new version, download URL, and SHA-256 hash.
6. Commit and push both repositories to GitHub.

---

## 4. Verifying a Release Artifact

To verify the cryptographic signature of an APK:

```powershell
$apksigner = Get-ChildItem "C:\Users\Atharv\AppData\Local\Android\Sdk\build-tools" -Filter "apksigner.bat" -Recurse | Select-Object -First 1 -ExpandProperty FullName
& $apksigner verify --verbose --print-certs "path\to\your-release.apk"
```

Confirm that:
- `Verifies: true`
- `Signer #1 certificate DN: CN=The Panels Hub, OU=Release...`
- `SHA-256 digest: bf3e65d7d48e9da0e45d59f58e91aee70496f719ae5d5822103d8856cc611aa9`

---

## 5. Checking That GitHub Contains the Intended Changes

In both `NuvioMobile` and `panels-control-center`:

```bash
git fetch
git status
git log -1 --stat
```

Confirm:
- `Your branch is up to date with '...'`
- `nothing to commit, working tree clean`

---

## 6. Testing Before Publication

Run the test suite in `NuvioMobile/`:

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"

# Run AuthLX tests
.\gradlew.bat :composeApp:testAndroidHostTest --tests "com.nuvio.app.core.auth.AuthLxIntegrationTest" --no-daemon

# Run Control Center tests
.\gradlew.bat :composeApp:testAndroidHostTest --tests "com.thepanels.control.ControlCenterPolicyTest" --no-daemon
```

Ensure all tests report `0 failures`.

---

## 7. Recovering From an Incorrect Policy

If a policy was published with an accidental block or kill switch:

1. Open `products/panels-play/policy.json`.
2. Revert the bad setting (e.g., set `emergency_disabled: false` or empty `blocked_versions: []`).
3. **Increment `revision`** (so clients reject the old replayed revision).
4. Sign the policy:
   ```bash
   python scripts/sign_policy.py products/panels-play/policy.json "C:\Users\Atharv\Documents\the-panels-hub-keys\policy\the-panels-hub-policy-private.pem"
   ```
5. Commit and push to `origin main`.
6. Clients will pick up the updated policy within 5 minutes (or on restart/resume).

---

## 8. Responding to a Compromised or Lost Key

### Policy Signing Key Compromised
1. Generate a new Ed25519 key pair.
2. In `NuvioMobile/composeApp/src/commonMain/kotlin/com/thepanels/control/ControlCenterPolicyRepository.kt`, update `TRUSTED_PUBLIC_KEY` with the new public key hex.
3. Build and publish an updated APK.
4. Sign all future policies using the new private key.

### Android Release Keystore Lost
- Note: Android keystores cannot be recovered if lost.
- If you lose `the-panels-hub-release.jks`, existing installed apps cannot be updated in-place; users will need to uninstall and reinstall the new build signed with a newly generated keystore.

---

## 9. Verifying AuthLX Subscription-Expiry Changes

1. In the AuthLX web control panel, locate a test user.
2. Extend the user's expiration date or time (e.g., to next month).
3. In Panels Play on device:
   - Navigate to **Settings -> Account**.
   - Confirm that the `Expires` line immediately updates to display the new date and time (`d MMM yyyy, h:mm a`).
4. In the AuthLX web control panel, shorten the expiration date/time to a past instant.
5. In Panels Play, resume or reopen the app:
   - Confirm that access is immediately revoked with `"Your subscription has expired. Please renew to continue."`.

---

## 10. Confirming All Changes Are Committed & Pushed

Run this one-liner in each repository:

```bash
git status && git log -1 --format="Latest remote commit: %h (%s)"
```

Confirm that the working tree is clean and the latest commit message matches your last intended update.
