# Post-Quantum Secure Cloud Data Migration Framework

This repository implements an end-to-end prototype demonstrating:
- Kyber (post-quantum KEM) + AES-GCM hybrid encryption (with simulated fallback if pyoqs is not installed)
- Sensitivity-adaptive compression (zlib)
- Compressed batch integrity proof (simulated ZKP via compressed commitments)
- Local "cloud" uploader (filesystem) and optional AWS S3 support
- Benchmarking and simple Flask demo

Quick start (macOS):

1. Create and activate a Python 3.10+ virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. (Optional) Build and install liboqs + pyoqs to use real Kyber. If you skip this, the project uses a safe simulated KEM for demos/tests.

3. Install Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Run a quick smoke test (this uses the simulated KEM if pyoqs is missing):

```bash
python tests/smoke_test.py
```

5. Run the Flask demo:

```bash
python app.py
# then POST a file to http://127.0.0.1:5000/upload using a form field `file` and `sensitivity`
```

Project layout:
- `crypto/` - compression, hybrid (Kyber+AES) implementation, simulated fallback, ZKP simulator
- `cloud/` - uploader (local filesystem + optional S3)
- `bench/` - benchmarking utilities
- `viz/` - plotting helpers
- `tests/` - smoke tests
- `data/` - outputs

Notes:
- The included ZKP is a compressed-batch integrity proof simulator (not a cryptographic ZKP primitive).
- For production use with real PQ KEMs, install and verify `pyoqs` and adjust KEM selection if needed.

