# 🛡️ The Panels Control Center — Operator Guide

This guide describes how to manage version policies, emergency kill switches, maintenance mode, and updates across all current and future products under **The Panels Hub**.

---

## 📍 Live Endpoints & URL Structure

For **The Panels Streaming**:
- **Signed Policy Endpoint**:
  ```
  https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/the-panels-streaming/policy.json
  ```
- **Update Metadata Endpoint**:
  ```
  https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/the-panels-streaming/update.json
  ```

---

## ⚙️ How to Operate Kill Switches & Policies

All policies are signed with **Ed25519**. Whenever you edit `products/<product-id>/policy.json`, you must:
1. Edit the desired fields in `policy`.
2. Increment the `revision` number.
3. Re-sign the file using `python scripts/sign_policy.py products/<product-id>/policy.json <private_key_hex>`.
4. Commit and push to `main`.

### 1. Blocking Version 1.0.0
In `products/the-panels-streaming/policy.json`:
```json
{
  "policy": {
    "revision": 2,
    "min_version": "1.0.0",
    "blocked_versions": ["1.0.0"],
    "user_message": "Version 1.0.0 is deprecated. Please update to continue streaming."
  }
}
```
*Run:* `python scripts/sign_policy.py products/the-panels-streaming/policy.json <KEY>`

### 2. Requiring Version 2.0.0 (Enforcing Minimum Allowed Version)
To allow `2.0.0+` and block all previous versions (e.g., `1.0.0`, `1.5.0`):
```json
{
  "policy": {
    "revision": 3,
    "min_version": "2.0.0",
    "blocked_versions": [],
    "user_message": "A mandatory update (v2.0.0) is required to access The Panels Streaming."
  }
}
```
*Run:* `python scripts/sign_policy.py products/the-panels-streaming/policy.json <KEY>`

### 3. Enabling Maintenance Mode (Without Blocking Accounts)
To put the app into temporary maintenance:
```json
{
  "policy": {
    "revision": 4,
    "maintenance": {
      "enabled": true,
      "message": "The Panels Streaming is undergoing scheduled system upgrades. Service will resume at 04:00 UTC."
    }
  }
}
```
*Run:* `python scripts/sign_policy.py products/the-panels-streaming/policy.json <KEY>`

### 4. Restoring Normal Service (Unblocking)
To restore service:
```json
{
  "policy": {
    "revision": 5,
    "min_version": "1.0.0",
    "blocked_versions": [],
    "maintenance": {
      "enabled": false,
      "message": ""
    },
    "emergency_disabled": false,
    "user_message": null
  }
}
```
*Run:* `python scripts/sign_policy.py products/the-panels-streaming/policy.json <KEY>`

### 5. Emergency Kill Switches
- **Per-Product Kill Switch**: Set `"emergency_disabled": true` in that product's `policy.json`. Only affects that product.
- **Global Emergency Kill Switch**: Set `"global_emergency_disabled": true`. When verified by clients, all products reading this directive will halt client execution.
