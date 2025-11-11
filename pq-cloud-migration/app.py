from flask import Flask, request, jsonify
import time
import os
from crypto.compression import Compressor
from crypto.hybrid import HybridEncryptor
from crypto.zkp import BatchZKP
from cloud.uploader import CloudUploader

app = Flask(__name__)
compressor = Compressor()
zkp = BatchZKP()
uploader = CloudUploader()  # or CloudUploader(bucket_name="my-bucket")

try:
    he = HybridEncryptor()
except Exception:
    he = None

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    sensitivity = request.form.get('sensitivity', 'medium')
    if not f:
        return jsonify({"error": "no file"}), 400
    data = f.read()
    t0 = time.time()
    compressed = compressor.compress(data, sensitivity)
    t1 = time.time()
    chunks = [compressed[i:i+1024] for i in range(0, len(compressed), 1024)]
    proof = zkp.make_proof(zkp.commitments(chunks))
    t2 = time.time()
    if he:
        pub, priv = he.generate_kem_keypair()
        enc_blob, metadata = he.encrypt(compressed, pub)
    else:
        enc_blob, metadata = compressed, {}
    t3 = time.time()
    os.makedirs('cloud', exist_ok=True)
    enc_path = uploader.upload_local(os.path.join('cloud', f.filename + '.enc'), enc_blob)
    proof_path = uploader.upload_local(os.path.join('cloud', f.filename + '.proof'), proof)
    return jsonify({
        "timings": {"compress": t1-t0, "proof": t2-t1, "encrypt": t3-t2},
        "sizes": {"input": len(data), "compressed": len(compressed), "enc": len(enc_blob), "proof": len(proof)},
        "paths": {"enc": enc_path, "proof": proof_path},
        "metadata": metadata
    })

if __name__ == '__main__':
    os.makedirs('cloud', exist_ok=True)
    app.run(debug=True, port=5000)

