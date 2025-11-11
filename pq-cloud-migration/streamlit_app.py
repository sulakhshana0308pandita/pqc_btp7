import streamlit as st
import time
import os
from crypto.compression import Compressor
from crypto.hybrid import HybridEncryptor
from crypto.zkp import BatchZKP
from cloud.uploader import CloudUploader

st.set_page_config(page_title="PQ Cloud Migration Demo", layout="wide")

st.title("Post-Quantum Secure Cloud Migration — Demo (Streamlit)")
st.markdown("Upload a file, choose sensitivity, and run the hybrid pipeline (compression → proof → encrypt). Uses a simulated PQ KEM if `pyoqs`/`liboqs` isn't installed.")

uploader = CloudUploader()
compressor = Compressor()
zkp = BatchZKP()

uploaded = st.file_uploader("Choose a file to upload", type=None)
sensitivity = st.selectbox("Sensitivity level", ["low", "medium", "high"], index=1)

if uploaded is not None:
    data = uploaded.read()
    st.info(f"Loaded {uploaded.name} — {len(data)} bytes")

    if st.button("Run pipeline"):
        t0 = time.time()
        compressed = compressor.compress(data, sensitivity)
        t1 = time.time()
        chunks = [compressed[i:i+1024] for i in range(0, len(compressed), 1024)]
        commitments = zkp.commitments(chunks)
        proof = zkp.make_proof(commitments)
        t2 = time.time()

        # Encryption (uses HybridEncryptor; real pyoqs if installed otherwise simulated fallback)
        he = HybridEncryptor()
        pub, priv = he.generate_kem_keypair()
        t3 = time.time()
        enc_blob, metadata = he.encrypt(compressed, pub)
        t4 = time.time()

        # Save to local cloud simulation
        os.makedirs("cloud", exist_ok=True)
        enc_path = os.path.join("cloud", uploaded.name + ".enc")
        proof_path = os.path.join("cloud", uploaded.name + ".proof")
        with open(enc_path, "wb") as f:
            f.write(enc_blob)
        with open(proof_path, "wb") as f:
            f.write(proof)

        # Show results
        st.success("Pipeline finished")
        st.write({
            "timings": {
                "compress": round(t1-t0, 6),
                "proof": round(t2-t1, 6),
                "enc_setup": round(t3-t2, 6),
                "encrypt": round(t4-t3, 6),
            },
            "sizes": {
                "input": len(data),
                "compressed": len(compressed),
                "enc_blob": len(enc_blob),
                "proof": len(proof)
            },
            "metadata": metadata
        })

        st.download_button("Download encrypted file", enc_blob, file_name=uploaded.name + ".enc")
        st.download_button("Download proof", proof, file_name=uploaded.name + ".proof")

        # Verify decrypt and proof on demand
        if st.checkbox("Run verification (decrypt + verify proof) now"):
            try:
                recovered = he.decrypt(enc_blob, metadata, priv)
                ok = (recovered == compressed)
            except Exception as e:
                ok = False
                st.error(f"Decryption failed: {e}")

            proof_ok = zkp.verify(chunks, proof)
            st.write({"decryption_ok": ok, "proof_ok": proof_ok})

        st.write("Files saved to local cloud folder: `cloud/`")
        st.write(enc_path)
        st.write(proof_path)

else:
    st.info("Upload a file to enable the pipeline")

