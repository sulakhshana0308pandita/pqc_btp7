"""
Visualization Module
Generates charts and graphs comparing Kyber vs RSA performance.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path


def plot_csv(path: str = "data/results.csv", output_dir: str = "data"):
    """
    Generate comprehensive comparison charts.
    
    Charts generated:
    1. Encryption time comparison (Kyber vs RSA)
    2. Proof size comparison
    3. Compression ratio by sensitivity
    4. File size vs encrypted size
    5. Total time breakdown
    """
    df = pd.read_csv(path)
    if df.empty:
        print("[ERROR] No results found in CSV")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract method groups
    df_kyber = df[df.method == "Kyber-512"]
    df_rsa = df[df.method == "RSA-2048+AES"]
    
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)
    
    # Figure 1: Encryption Time Comparison
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Post-Quantum vs Classical Hybrid Encryption: Performance Analysis", fontsize=16, fontweight='bold')
    
    # 1.1: Average encryption time by sensitivity
    sensitivities = ["low", "medium", "high"]
    kyber_times = []
    rsa_times = []
    
    for sens in sensitivities:
        kyber_sens = df_kyber[df_kyber.sensitivity == sens]
        rsa_sens = df_rsa[df_rsa.sensitivity == sens]
        kyber_times.append(kyber_sens['encrypt_time_ms'].mean() if not kyber_sens.empty else 0)
        rsa_times.append(rsa_sens['encrypt_time_ms'].mean() if not rsa_sens.empty else 0)
    
    x = range(len(sensitivities))
    width = 0.35
    axes[0, 0].bar([i - width/2 for i in x], kyber_times, width, label='Kyber-512', color='#2ecc71')
    axes[0, 0].bar([i + width/2 for i in x], rsa_times, width, label='RSA-2048+AES', color='#e74c3c')
    axes[0, 0].set_xlabel('Data Sensitivity Level')
    axes[0, 0].set_ylabel('Encryption Time (ms)')
    axes[0, 0].set_title('Encryption Time by Sensitivity')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(sensitivities)
    axes[0, 0].legend()
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # 1.2: Encryption time by file size
    sizes = sorted(df['input_size_bytes'].unique())
    kyber_size_times = []
    rsa_size_times = []
    
    for size in sizes:
        kyber_size = df_kyber[df_kyber.input_size_bytes == size]
        rsa_size = df_rsa[df_rsa.input_size_bytes == size]
        kyber_size_times.append(kyber_size['encrypt_time_ms'].mean() if not kyber_size.empty else 0)
        rsa_size_times.append(rsa_size['encrypt_time_ms'].mean() if not rsa_size.empty else 0)
    
    size_labels = [f"{int(s/1024)}KB" if s < 1024*1024 else f"{int(s/(1024*1024))}MB" for s in sizes]
    x2 = range(len(sizes))
    axes[0, 1].plot(x2, kyber_size_times, marker='o', label='Kyber-512', color='#2ecc71', linewidth=2, markersize=8)
    axes[0, 1].plot(x2, rsa_size_times, marker='s', label='RSA-2048+AES', color='#e74c3c', linewidth=2, markersize=8)
    axes[0, 1].set_xlabel('Input File Size')
    axes[0, 1].set_ylabel('Encryption Time (ms)')
    axes[0, 1].set_title('Encryption Time Scalability')
    axes[0, 1].set_xticks(x2)
    axes[0, 1].set_xticklabels(size_labels)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 1.3: Proof size comparison
    kyber_proof = df_kyber['proof_size_bytes'].mean()
    rsa_proof = df_rsa['proof_size_bytes'].mean()
    
    colors = ['#2ecc71', '#e74c3c']
    bars = axes[1, 0].bar(['Kyber-512', 'RSA-2048+AES'], [kyber_proof, rsa_proof], color=colors)
    axes[1, 0].set_ylabel('Average Proof Size (bytes)')
    axes[1, 0].set_title('ZKP Proof Size Comparison')
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)} B',
                       ha='center', va='bottom', fontweight='bold')
    
    # 1.4: Compression ratio
    comp_ratios_kyber = df_kyber.groupby('sensitivity')['compression_ratio_percent'].mean()
    comp_ratios_rsa = df_rsa.groupby('sensitivity')['compression_ratio_percent'].mean()
    
    sensitivities_available = list(comp_ratios_kyber.index) if not comp_ratios_kyber.empty else list(comp_ratios_rsa.index)
    x3 = range(len(sensitivities_available))
    
    kyber_comp = [comp_ratios_kyber.get(s, 0) for s in sensitivities_available]
    rsa_comp = [comp_ratios_rsa.get(s, 0) for s in sensitivities_available]
    
    axes[1, 1].bar([i - width/2 for i in x3], kyber_comp, width, label='Kyber-512', color='#2ecc71')
    axes[1, 1].bar([i + width/2 for i in x3], rsa_comp, width, label='RSA-2048+AES', color='#e74c3c')
    axes[1, 1].set_xlabel('Data Sensitivity Level')
    axes[1, 1].set_ylabel('Compression Ratio (%)')
    axes[1, 1].set_title('Compression Efficiency by Sensitivity')
    axes[1, 1].set_xticks(x3)
    axes[1, 1].set_xticklabels(sensitivities_available)
    axes[1, 1].legend()
    axes[1, 1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    chart1_path = os.path.join(output_dir, "comparison_analysis.png")
    plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {chart1_path}")
    plt.close()
    
    # Figure 2: Speedup & Efficiency
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Kyber Post-Quantum Advantages", fontsize=14, fontweight='bold')
    
    # 2.1: Speedup factor (log scale)
    speedup_factors = []
    for sens in sensitivities:
        kyber_t = df_kyber[df_kyber.sensitivity == sens]['encrypt_time_ms'].mean()
        rsa_t = df_rsa[df_rsa.sensitivity == sens]['encrypt_time_ms'].mean()
        if kyber_t > 0:
            speedup_factors.append(rsa_t / kyber_t)
        else:
            speedup_factors.append(1)
    
    axes[0].bar(sensitivities, speedup_factors, color=['#27ae60', '#229954', '#1e8449'])
    axes[0].set_ylabel('Speedup Factor (RSA time / Kyber time)')
    axes[0].set_xlabel('Data Sensitivity Level')
    axes[0].set_title('Kyber Speedup over RSA')
    axes[0].set_yscale('log')
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (sens, speedup) in enumerate(zip(sensitivities, speedup_factors)):
        axes[0].text(i, speedup, f'{speedup:.1f}x', ha='center', va='bottom', fontweight='bold')
    
    # 2.2: Total time breakdown for 100KB file
    size_100k = 100 * 1024
    df_100k_kyber = df_kyber[df_kyber.input_size_bytes == size_100k]
    df_100k_rsa = df_rsa[df_rsa.input_size_bytes == size_100k]
    
    if not df_100k_kyber.empty and not df_100k_rsa.empty:
        kyber_breakdown = {
            'Compression': df_100k_kyber['compress_time_ms'].mean(),
            'ZKP': df_100k_kyber['zkp_time_ms'].mean(),
            'Encryption': df_100k_kyber['encrypt_time_ms'].mean(),
        }
        rsa_breakdown = {
            'Compression': df_100k_rsa['compress_time_ms'].mean(),
            'ZKP': df_100k_rsa['zkp_time_ms'].mean(),
            'Encryption': df_100k_rsa['encrypt_time_ms'].mean(),
        }
        
        x_pos = [0, 1]
        kyber_vals = list(kyber_breakdown.values())
        rsa_vals = list(rsa_breakdown.values())
        
        axes[1].bar(x_pos, [sum(kyber_vals), sum(rsa_vals)], color=['#2ecc71', '#e74c3c'], alpha=0.3, label='Total')
        
        bottom_kyber = 0
        bottom_rsa = 0
        colors_breakdown = ['#3498db', '#e67e22', '#9b59b6']
        
        for i, (stage, color) in enumerate(zip(kyber_breakdown.keys(), colors_breakdown)):
            axes[1].bar(0, kyber_breakdown[stage], bottom=bottom_kyber, label=stage, color=color, width=0.6)
            axes[1].bar(1, rsa_breakdown[stage], bottom=bottom_rsa, color=color, width=0.6)
            bottom_kyber += kyber_breakdown[stage]
            bottom_rsa += rsa_breakdown[stage]
        
        axes[1].set_ylabel('Time (ms)')
        axes[1].set_title('Pipeline Time Breakdown (100KB file)')
        axes[1].set_xticks(x_pos)
        axes[1].set_xticklabels(['Kyber-512', 'RSA-2048+AES'])
        axes[1].legend(loc='upper right')
        axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    chart2_path = os.path.join(output_dir, "kyber_advantages.png")
    plt.savefig(chart2_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {chart2_path}")
    plt.close()
    
    # Figure 3: Security vs Performance Trade-off
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # X: Average encryption time, Y: Proof size, Size: File size
    scatter_kyber = ax.scatter(df_kyber['encrypt_time_ms'], df_kyber['proof_size_bytes'], 
                              s=df_kyber['input_size_bytes']/1000,  # Size proportional to file size
                              alpha=0.6, color='#2ecc71', label='Kyber-512', edgecolors='darkgreen', linewidth=2)
    scatter_rsa = ax.scatter(df_rsa['encrypt_time_ms'], df_rsa['proof_size_bytes'], 
                            s=df_rsa['input_size_bytes']/1000,
                            alpha=0.6, color='#e74c3c', label='RSA-2048+AES', edgecolors='darkred', linewidth=2)
    
    ax.set_xlabel('Encryption Time (ms)', fontsize=12)
    ax.set_ylabel('Proof Size (bytes)', fontsize=12)
    ax.set_title('Security vs Performance Trade-off\n(Bubble size = File size)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Add size legend
    sizes_legend = [1, 10, 100, 1024]
    for size in sizes_legend:
        ax.scatter([], [], s=size*10, c='gray', alpha=0.6, edgecolors='black', linewidth=1.5,
                  label=f'{size}KB')
    ax.legend(fontsize=10, loc='center left')
    
    plt.tight_layout()
    chart3_path = os.path.join(output_dir, "security_performance_tradeoff.png")
    plt.savefig(chart3_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {chart3_path}")
    plt.close()
    
    print("="*80 + "\n")


if __name__ == '__main__':
    plot_csv()

