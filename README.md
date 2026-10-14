# 🌐 The Panels Control Center

**The Panels Control Center** is the central, public control plane for products published under **The Panels Hub** (including **The Panels Streaming**).

It centrally manages:
- **Version Lifecycle & Policies**: Enforces minimum supported versions and deprecation blocks.
- **Maintenance State**: Displays planned maintenance messages without banning user accounts.
- **Emergency Kill Switches**: Per-product and global emergency shutdown directives.
- **Update Metadata**: Publishes verified release notes, APK download URLs, and SHA-256 digests.
- **Ed25519 Cryptographic Trust**: All client policies are digitally signed using Ed25519 to prevent tampering, MITM attacks, and unauthorized policy changes.

---

## 📁 Repository Layout

`
panels-control-center/
├── .github/workflows/
│   └── validate_and_deploy.yml         # CI verification of signatures & schemas
├── docs/
│   ├── THE-PANELS-HUB-COMPLETE-GUIDE.md # Complete Beginner's & Operations Guide
│   ├── DAILY-OPERATIONS-CHECKLIST.md   # Quick daily operations & incident response checklist
│   ├── OPERATOR_GUIDE.md               # Step-by-step instructions for blocking/unblocking versions
│   └── SECURITY.md                     # Ed25519 specification & key management rules
├── products/
│   ├── panels-play/
│   │   ├── policy.json                 # Signed version policy & kill switches for Panels Play
│   │   └── update.json                 # Release metadata & APK download link
│   ├── the-panels-streaming/
│   │   ├── policy.json                 # Signed version policy & kill switches
│   │   └── update.json                 # Release metadata & APK download link
│   └── template/
│       ├── policy.json                 # Template for future products
│       └── update.json
├── schema/
│   ├── policy.schema.json              # JSON Schema for policy envelopes
│   └── update.schema.json              # JSON Schema for update metadata
├── scripts/
│   ├── sign_policy.py                  # Offline Ed25519 canonical signing utility
│   └── verify_policy.py                # Ed25519 signature verification utility
└── README.md
`

---

## 📡 Live Endpoints (The Panels Streaming)

- **Policy Endpoint**:
  https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/the-panels-streaming/policy.json
- **Update Metadata Endpoint**:
  https://raw.githubusercontent.com/ThePanelsHub/panels-control-center/main/products/the-panels-streaming/update.json

---

## 🔐 Cryptographic Verification

All client applications embed the Ed25519 public key:
2f029fce662a015a2b13a0e0261eea6fb13aae7ba832e6a4c80f6026ef6b6db7

Policies are signed over canonical JSON bytes using the offline private key.
See [docs/OPERATOR_GUIDE.md](docs/OPERATOR_GUIDE.md) for how to operate version kill switches.
