"""
Tests for Temporal FCR data loading validation.
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

def main():
    print("="*70)
    print("TEMPORAL FCR VALIDATION")
    print("="*70)
    
    # Check for run folder arg, else default to test_run_v1
    run_name = sys.argv[1] if len(sys.argv) > 1 else "test_run_v1"
    
    # We generated data for 2014-2016 window
    output_dir = Path(f"data_processing/rolling_windows/output/{run_name}/nodes")
    file_2014 = output_dir / "node_features_rw_2014_2016.parquet"
    
    if not file_2014.exists():
        print(f"❌ Expected output file not found: {file_2014}")
        print("   (Pipeline might be still running or failed)")
        return
        
    print(f"✅ Found parquet: {file_2014}")
    try:
        df_raw = pd.read_parquet(file_2014)
        
        print(f"   Shape: {df_raw.shape}")
        
        if "fcr_temporal" in df_raw.columns:
            # Filter for Banks
            if "nodeLabels" in df_raw.columns:
                banks = df_raw[df_raw["nodeLabels"].apply(lambda x: "Bank" in list(x) if x is not None else False)]
                print(f"✅ Found {len(banks)} nodes with 'Bank' label.")
                if "regn_cbr" not in df_raw.columns:
                     print("ℹ️ 'regn_cbr' not in output (expected due to GDS type limit). Using 'nodeLabels'.")
            else:
                banks = df_raw
                print("⚠️ 'nodeLabels' column missing, showing stats for ALL nodes.")

            print("\nSummary Statistics for fcr_temporal (Banks only):")
            print(banks["fcr_temporal"].describe())
            
            non_zero = (banks["fcr_temporal"] > 0).sum()
            print(f"   Non-zero values: {non_zero} / {len(banks)} ({100*non_zero/len(banks):.1f}%)")
        else:
            print("❌ 'fcr_temporal' column MISSING in parquet.")
            print("   Columns found:", df_raw.columns.tolist())
            
        # Check predicted edges
        pred_dir = Path(f"rolling_windows/output/{run_name}/predicted_edges")
        pred_file = pred_dir / "predicted_edges_rw_2014_2016.parquet"
        
        if pred_file.exists():
            print(f"\n✅ Found predicted edges: {pred_file}")
            df_pred = pd.read_parquet(pred_file)
            print(f"   Predicted edges count: {len(df_pred)}")
            print(df_pred.head())
        else:
            print(f"\n⚠️ Predicted edges file not found: {pred_file}")
            print("   (Link Prediction might have been skipped or produced no results)")

    except Exception as e:
        print(f"❌ Error reading parquet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
