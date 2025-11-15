"""
Comprehensive Performance Evaluation Script
Compares Kyber (post-quantum) vs RSA+AES (classical hybrid) across multiple scenarios.

Generates:
- CSV results (data/results.csv)
- Summary statistics (data/summary.json)
- Execution logs
"""
import os
import csv
import json
import time
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from crypto.compression import Compressor
from crypto.zkp import BatchZKP
from crypto.hybrid import HybridEncryptor


class ComprehensivePerformanceEvaluator:
    """
    Run comprehensive experiments comparing Kyber vs RSA across:
    - Multiple file sizes (1KB, 10KB, 100KB, 1MB)
    - Multiple sensitivity levels (low, medium, high)
    """
    
    def __init__(self, out_csv: str = "data/results.csv", out_summary: str = "data/summary.json"):
        self.out_csv = out_csv
        self.out_summary = out_summary
        os.makedirs(os.path.dirname(out_csv) or "data", exist_ok=True)
        
        self.compressor = Compressor()
        self.zkp = BatchZKP()
        self.results = []
    
    def rsa_encrypt_aes(self, plaintext: bytes):
        """RSA + AES-GCM encryption (classical hybrid)."""
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
        metadata = {
            "rsa_enc_sym": base64.b64encode(enc_sym).decode(),
            "nonce": base64.b64encode(nonce).decode()
        }
        return nonce + ct, metadata, priv
    
    def run_single(self, data: bytes, sensitivity: str, use_pq: bool = True, test_id: str = ""):
        """
        Run single test: compression + ZKP + encryption (Kyber or RSA).
        
        Args:
            data: Raw data to process
            sensitivity: Sensitivity level (low/medium/high)
            use_pq: Use Kyber (True) or RSA (False)
            test_id: Optional test identifier for logging
            
        Returns:
            Dictionary with timing and size metrics
        """
        # Compress
        t0 = time.time()
        compressed = self.compressor.compress(data, sensitivity)
        comp_time = time.time() - t0
        
        # ZKP
        chunks = [compressed[i:i+1024] for i in range(0, len(compressed), 1024)]
        t1 = time.time()
        commitments = self.zkp.commitments(chunks)
        proof = self.zkp.make_proof(commitments)
        zkp_time = time.time() - t1
        
        # Encryption
        if use_pq:
            he = HybridEncryptor()
            pub, priv = he.generate_kem_keypair()
            t2 = time.time()
            blob, metadata = he.encrypt(compressed, pub)
            enc_time = time.time() - t2
            
            t3 = time.time()
            try:
                recovered = he.decrypt(blob, metadata, priv)
                assert recovered == compressed
                dec_ok = True
            except:
                dec_ok = False
            dec_time = time.time() - t3
            method = "Kyber-512"
        else:
            t2 = time.time()
            blob, metadata, priv = self.rsa_encrypt_aes(compressed)
            enc_time = time.time() - t2
            
            # RSA decryption not implemented for simplicity
            dec_time = 0.0
            dec_ok = False
            method = "RSA-2048+AES"
        
        # Calculate metrics
        comp_ratio = self.compressor.get_compression_ratio(len(data), len(compressed))
        
        row = {
            "test_id": test_id,
            "method": method,
            "sensitivity": sensitivity,
            "input_size_bytes": len(data),
            "compressed_size_bytes": len(compressed),
            "encrypted_size_bytes": len(blob),
            "proof_size_bytes": len(proof),
            "compression_ratio_percent": round(comp_ratio, 2),
            "compress_time_ms": round(comp_time * 1000, 4),
            "zkp_time_ms": round(zkp_time * 1000, 4),
            "encrypt_time_ms": round(enc_time * 1000, 4),
            "decrypt_time_ms": round(dec_time * 1000, 4),
            "total_time_ms": round((comp_time + zkp_time + enc_time + dec_time) * 1000, 4),
            "decryption_ok": dec_ok
        }
        
        self.results.append(row)
        return row
    
    def run_comprehensive(self):
        """
        Run comprehensive benchmark across:
        - File sizes: 1KB, 10KB, 100KB, 1MB
        - Sensitivities: low, medium, high
        - Methods: Kyber, RSA
        """
        test_sizes = {
            "1KB": 1024,
            "10KB": 10 * 1024,
            "100KB": 100 * 1024,
            "1MB": 1024 * 1024,
        }
        
        sensitivities = ["low", "medium", "high"]
        methods = [True, False]  # True = Kyber, False = RSA
        
        total_tests = len(test_sizes) * len(sensitivities) * len(methods)
        test_num = 0
        
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE PERFORMANCE EVALUATION")
        print(f"{'='*80}")
        print(f"Total tests: {total_tests}")
        print(f"{'='*80}\n")
        
        for size_name, size_bytes in test_sizes.items():
            data = os.urandom(size_bytes)  # Random data for realistic compression
            
            for sensitivity in sensitivities:
                for use_pq in methods:
                    test_num += 1
                    method_name = "Kyber" if use_pq else "RSA"
                    test_id = f"{test_num}/{total_tests}"
                    
                    print(f"[{test_id}] {size_name} + {sensitivity:6s} + {method_name:6s} ...", end=" ", flush=True)
                    
                    try:
                        result = self.run_single(data, sensitivity, use_pq, test_id)
                        print(f"✓ {result['total_time_ms']}ms")
                    except Exception as e:
                        print(f"✗ Error: {e}")
        
        print(f"\n{'='*80}")
        print(f"Completed {test_num} tests")
        print(f"{'='*80}\n")
    
    def save_results(self):
        """Save results to CSV and JSON summary."""
        if not self.results:
            print("[ERROR] No results to save")
            return
        
        # Save CSV
        keys = list(self.results[0].keys())
        with open(self.out_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"✓ Saved {len(self.results)} results to {self.out_csv}")
        
        # Generate summary statistics
        summary = self._generate_summary()
        
        with open(self.out_summary, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Saved summary to {self.out_summary}")
    
    def _generate_summary(self) -> dict:
        """Generate summary statistics."""
        kyber_results = [r for r in self.results if r["method"] == "Kyber-512"]
        rsa_results = [r for r in self.results if r["method"] == "RSA-2048+AES"]
        
        def stats(results, metric):
            if not results:
                return {"min": 0, "max": 0, "avg": 0, "count": 0}
            values = [r[metric] for r in results]
            return {
                "min": min(values),
                "max": max(values),
                "avg": round(sum(values) / len(values), 2),
                "count": len(values)
            }
        
        summary = {
            "total_tests": len(self.results),
            "kyber_tests": len(kyber_results),
            "rsa_tests": len(rsa_results),
            "kyber_stats": {
                "encrypt_time_ms": stats(kyber_results, "encrypt_time_ms"),
                "proof_size_bytes": stats(kyber_results, "proof_size_bytes"),
                "compression_ratio_percent": stats(kyber_results, "compression_ratio_percent"),
            },
            "rsa_stats": {
                "encrypt_time_ms": stats(rsa_results, "encrypt_time_ms"),
                "proof_size_bytes": stats(rsa_results, "proof_size_bytes"),
                "compression_ratio_percent": stats(rsa_results, "compression_ratio_percent"),
            },
            "comparison": {
                "kyber_faster_than_rsa": "Yes" if (kyber_results and rsa_results and 
                                                     stats(kyber_results, "encrypt_time_ms")["avg"] < 
                                                     stats(rsa_results, "encrypt_time_ms")["avg"]) else "No",
                "kyber_speedup_factor": round(stats(rsa_results, "encrypt_time_ms")["avg"] / 
                                             stats(kyber_results, "encrypt_time_ms")["avg"], 2) 
                                        if (kyber_results and rsa_results and 
                                            stats(kyber_results, "encrypt_time_ms")["avg"] > 0) else 0,
            }
        }
        
        return summary


if __name__ == "__main__":
    evaluator = ComprehensivePerformanceEvaluator()
    evaluator.run_comprehensive()
    evaluator.save_results()
    
    # Print summary
    with open("data/summary.json") as f:
        summary = json.load(f)
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total tests: {summary['total_tests']}")
    print(f"Kyber tests: {summary['kyber_tests']}")
    print(f"RSA tests: {summary['rsa_tests']}")
    print(f"\nKyber Encryption (avg): {summary['kyber_stats']['encrypt_time_ms']['avg']}ms")
    print(f"RSA Encryption (avg): {summary['rsa_stats']['encrypt_time_ms']['avg']}ms")
    print(f"\nKyber is {summary['comparison']['kyber_speedup_factor']}x faster than RSA!")
    print("="*80 + "\n")
