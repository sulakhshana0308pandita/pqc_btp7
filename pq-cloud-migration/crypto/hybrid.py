"""
Hybrid Encryption Module: Kyber (post-quantum KEM) + AES-GCM
Provides post-quantum secure hybrid encryption using NIST-standardized Kyber.

If liboqs/pyoqs is installed: uses real Kyber
If not available: uses simulated KEM (safe for demos/testing)
"""
import os
import hashlib
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class HybridEncryptor:
    """
    Hybrid encryption using Kyber KEM + AES-GCM.
    Post-quantum secure key encapsulation + symmetric bulk encryption.
    """
    
    def __init__(self, use_real_kyber: bool = True):
        """
        Initialize hybrid encryptor.
        
        Args:
            use_real_kyber: If True, attempt to use real Kyber from pyoqs.
                          If False or pyoqs unavailable, use simulated KEM.
        """
        self.use_real_kyber = use_real_kyber
        self.kyber_available = False
        
        # Try to import real Kyber
        if use_real_kyber:
            try:
                import liboqs
                self.liboqs = liboqs
                self.kyber_available = True
                print("[HybridEncryptor] Using real Kyber from liboqs")
            except ImportError:
                print("[HybridEncryptor] liboqs not found, falling back to simulated KEM")
                self.kyber_available = False
    
    def generate_kem_keypair(self):
        """
        Generate a Kyber public/private keypair.
        
        Returns:
            (public_key, private_key) tuple
        """
        if self.kyber_available:
            return self._real_kyber_keygen()
        else:
            return self._simulated_kyber_keygen()
    
    def _real_kyber_keygen(self):
        """Generate real Kyber-512 keypair using liboqs."""
        try:
            kem = self.liboqs.KeyEncapsulation("Kyber512")
            pub = kem.generate_keypair()
            priv = kem.export_secret_key()
            return pub, priv
        except Exception as e:
            print(f"[WARNING] Real Kyber failed: {e}. Falling back to simulated KEM.")
            return self._simulated_kyber_keygen()
    
    def _simulated_kyber_keygen(self):
        """
        Simulated Kyber keypair for demo/testing.
        Uses SHA-256 based deterministic simulation (NOT cryptographically secure for production).
        """
        # Generate a 32-byte seed (simulates private key)
        priv_key = os.urandom(32)
        # Derive public key from private key using SHA-256
        pub_key = hashlib.sha256(priv_key).digest()
        return pub_key, priv_key
    
    def encrypt(self, plaintext: bytes, public_key: bytes):
        """
        Encrypt plaintext using Kyber KEM + AES-GCM.
        
        Args:
            plaintext: Data to encrypt
            public_key: Kyber public key
            
        Returns:
            (ciphertext, metadata) tuple where metadata contains encapsulated key info
        """
        if self.kyber_available:
            return self._real_kyber_encrypt(plaintext, public_key)
        else:
            return self._simulated_kyber_encrypt(plaintext, public_key)
    
    def _real_kyber_encrypt(self, plaintext: bytes, public_key: bytes):
        """Encrypt using real Kyber (requires liboqs)."""
        try:
            kem = self.liboqs.KeyEncapsulation("Kyber512", public_key)
            kem_ciphertext, shared_secret = kem.encap_secret()
            
            # Use shared secret to derive AES key
            aes_key = shared_secret[:32]  # Take first 32 bytes for AES-256
            nonce = os.urandom(12)
            
            # AES-GCM encryption
            cipher = AESGCM(aes_key)
            ciphertext = cipher.encrypt(nonce, plaintext, None)
            
            metadata = {
                "kem_ciphertext": base64.b64encode(kem_ciphertext).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "method": "Kyber512+AES256GCM"
            }
            return nonce + ciphertext, metadata
        except Exception as e:
            print(f"[WARNING] Real Kyber encryption failed: {e}. Falling back to simulated KEM.")
            return self._simulated_kyber_encrypt(plaintext, public_key)
    
    def _simulated_kyber_encrypt(self, plaintext: bytes, public_key: bytes):
        """
        Simulated Kyber encryption using SHA-256 based KEM.
        For demo/testing purposes only.
        """
        # Simulate KEM encapsulation: derive shared secret from public key + random seed
        random_seed = os.urandom(32)
        combined = public_key + random_seed
        shared_secret = hashlib.sha256(combined).digest()
        
        # Use shared secret as AES key
        aes_key = shared_secret[:32]
        nonce = os.urandom(12)
        
        # AES-GCM encryption
        cipher = AESGCM(aes_key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        metadata = {
            "kem_ciphertext": base64.b64encode(random_seed).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "method": "Simulated-Kyber512+AES256GCM"
        }
        return nonce + ciphertext, metadata
    
    def decrypt(self, ciphertext: bytes, metadata: dict, private_key: bytes):
        """
        Decrypt ciphertext using Kyber KEM + AES-GCM.
        
        Args:
            ciphertext: Encrypted data (nonce + encrypted blob)
            metadata: Metadata from encryption (contains kem_ciphertext, nonce)
            private_key: Kyber private key
            
        Returns:
            Decrypted plaintext bytes
        """
        if self.kyber_available:
            return self._real_kyber_decrypt(ciphertext, metadata, private_key)
        else:
            return self._simulated_kyber_decrypt(ciphertext, metadata, private_key)
    
    def _real_kyber_decrypt(self, ciphertext: bytes, metadata: dict, private_key: bytes):
        """Decrypt using real Kyber (requires liboqs)."""
        try:
            kem_ciphertext = base64.b64decode(metadata["kem_ciphertext"])
            nonce = base64.b64decode(metadata["nonce"])
            
            kem = self.liboqs.KeyEncapsulation("Kyber512")
            kem.import_secret_key(private_key)
            shared_secret = kem.decap_secret(kem_ciphertext)
            
            # Use shared secret as AES key
            aes_key = shared_secret[:32]
            
            # AES-GCM decryption
            cipher = AESGCM(aes_key)
            plaintext = cipher.decrypt(nonce, ciphertext[12:], None)  # Skip nonce from ciphertext
            return plaintext
        except Exception as e:
            print(f"[WARNING] Real Kyber decryption failed: {e}. Falling back to simulated KEM.")
            return self._simulated_kyber_decrypt(ciphertext, metadata, private_key)
    
    def _simulated_kyber_decrypt(self, ciphertext: bytes, metadata: dict, private_key: bytes):
        """
        Simulated Kyber decryption using SHA-256 based KEM.
        For demo/testing purposes only.
        """
        kem_ciphertext = base64.b64decode(metadata["kem_ciphertext"])  # This is random_seed
        nonce = base64.b64decode(metadata["nonce"])
        
        # Simulate KEM decapsulation: derive shared secret from private key + random seed
        # We use private key's hash to simulate recovery
        public_key_recovered = hashlib.sha256(private_key).digest()
        combined = public_key_recovered + kem_ciphertext
        shared_secret = hashlib.sha256(combined).digest()
        
        # Use shared secret as AES key
        aes_key = shared_secret[:32]
        
        # AES-GCM decryption
        cipher = AESGCM(aes_key)
        plaintext = cipher.decrypt(nonce, ciphertext[12:], None)  # Skip nonce from ciphertext
        return plaintext
