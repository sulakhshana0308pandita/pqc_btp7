"""Simple smoke test to validate basic pipeline behavior.
This test uses the simulated KEM if pyoqs is missing so it should run in most dev setups.
"""
import sys
import os
# Ensure project root on path
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from crypto.compression import Compressor
from crypto.hybrid import HybridEncryptor
from crypto.zkp import BatchZKP


def run_smoke():
    compressor = Compressor()
    zkp = BatchZKP()
    he = HybridEncryptor()

    data = b"Hello world!\n" * 1000
    print(f"Input size: {len(data)} bytes")

    # Compression
    comp = compressor.compress(data, "low")
    print(f"Compressed size: {len(comp)} bytes")

    # Chunk, commitments, proof
    chunks = [comp[i:i+1024] for i in range(0, len(comp), 1024)]
    commitments = zkp.commitments(chunks)
    proof = zkp.make_proof(commitments)
    print(f"Chunks: {len(chunks)}, Proof size: {len(proof)}")

    # KEM keypair
    pub, priv = he.generate_kem_keypair()
    blob, metadata = he.encrypt(comp, pub)
    print(f"Encrypted blob size: {len(blob)}; metadata keys: {list(metadata.keys())}")

    # Decrypt and verify
    recovered = he.decrypt(blob, metadata, priv)
    assert recovered == comp, "Decrypted data does not match compressed plaintext"
    print("Encryption/decryption roundtrip OK")

    # Verify proof
    ok = zkp.verify(chunks, proof)
    assert ok, "Proof verification failed"
    print("ZKP verification OK")

if __name__ == '__main__':
    run_smoke()
