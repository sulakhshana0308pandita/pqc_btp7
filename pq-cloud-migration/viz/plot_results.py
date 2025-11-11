import pandas as pd
import matplotlib.pyplot as plt

def plot_csv(path: str = "data/results.csv"):
    df = pd.read_csv(path)
    if df.empty:
        print("No results")
        return
    fig, axes = plt.subplots(1, 3, figsize=(15,4))
    df_pq = df[df.method == "Kyber"]
    df_rsa = df[df.method == "RSA"]
    axes[0].bar(["Kyber","RSA"], [df_pq.enc_time.mean() if not df_pq.empty else 0, df_rsa.enc_time.mean() if not df_rsa.empty else 0])
    axes[0].set_title("Avg encryption time")
    axes[1].bar(["Kyber","RSA"], [df_pq.proof_size.mean() if not df_pq.empty else 0, df_rsa.proof_size.mean() if not df_rsa.empty else 0])
    axes[1].set_title("Avg proof size")
    axes[2].scatter(df.input_size, df.compressed_size, c=df.method.map({"Kyber":"blue","RSA":"orange"}), alpha=0.6)
    axes[2].set_title("Compression: input vs compressed")
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_csv()

