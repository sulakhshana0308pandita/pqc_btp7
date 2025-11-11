import os
import csv
import time
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from crypto.compression import Compressor
from crypto.zkp import BatchZKP
from crypto.hybrid import HybridEncryptor

class PerformanceEvaluator:
    """
    Run experiments for PQ KEM (Kyber) vs RSA+AES (classical hybrid).
    Call run_single for test cases; results appended to CSV.
    """
    def __init__(self, out_csv: str = "data/results.csv"):
        self.out_csv = out_csv
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        self.compressor = Compressor()
        self.zkp = BatchZKP()

    def rsa_encrypt_aes(self, plaintext: bytes):
        priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub = priv.public_key()
        sym = AESGCM.generate_key(bit_length=256)
        enc_sym = pub.encrypt(
            sym,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(),
                         label=None)
        )
        aesgcm = AESGCM(sym)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        metadata = {"rsa_enc_sym": base64.b64encode(enc_sym).decode(), "nonce": base64.b64encode(nonce).decode()}
        return nonce + ct, metadata, priv

    def run_single(self, data: bytes, sensitivity: str, use_pq: bool = True):
        compressed = self.compressor.compress(data, sensitivity)
        chunks = [compressed[i:i+1024] for i in range(0, len(compressed), 1024)]
        commitments = self.zkp.commitments(chunks)
        proof = self.zkp.make_proof(commitments)

        if use_pq:
            he = HybridEncryptor()
            pub, priv = he.generate_kem_keypair()
            t0 = time.time()
            blob, metadata = he.encrypt(compressed, pub)
            enc_time = time.time() - t0
            t1 = time.time()
            _ = he.decrypt(blob, metadata, priv)
            dec_time = time.time() - t1
            method = "Kyber"
        else:
            t0 = time.time()
            blob, metadata, priv = self.rsa_encrypt_aes(compressed)
            enc_time = time.time() - t0
            dec_time = 0.0
            method = "RSA"

        row = {
            "method": method,
            "sensitivity": sensitivity,
            "input_size": len(data),
            "compressed_size": len(compressed),
            "enc_blob_size": len(blob),
            "proof_size": len(proof),
            "enc_time": enc_time,
            "dec_time": dec_time
        }
        write_header = not Path(self.out_csv).exists()
        with open(self.out_csv, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                w.writeheader()
            w.writerow(row)
        return row

if __name__ == "__main__":
    pe = PerformanceEvaluator()
    sample = b"A" * 10_000
    print(pe.run_single(sample, "low", use_pq=True))
    print(pe.run_single(sample, "low", use_pq=False))

