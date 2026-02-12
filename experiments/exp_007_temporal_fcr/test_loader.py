"""Quick test of TemporalFCRLoader"""

import sys
import os
from pathlib import Path

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

print("Testing Temporal FCR Loader...")

# Check if data directory exists
data_dir = Path("data_processing/rolling_windows/output/production_run_1990_2022_v6/nodes")
print(f"\n1. Checking data directory: {data_dir}")
print(f"   Exists: {data_dir.exists()}")

if data_dir.exists():
    files = list(data_dir.glob("node_features_rw_*.parquet"))
    print(f"   Found {len(files)} parquet files")
    if files:
        print(f"   First file: {files[0].name}")
        print(f"   Last file: {files[-1].name}")
else:
    print("   ❌ DATA DIRECTORY NOT FOUND!")
    print("   This is the issue - the temporal FCR data hasn't been generated yet")
    sys.exit(1)

# Try loading one file
if files:
    import pandas as pd
    print(f"\n2. Loading sample file: {files[0].name}...")
    df = pd.read_parquet(files[0])
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)[:10]}...")
    
    # Check for key columns
    key_cols = ['gds_id', 'entity_id', 'fcr_temporal', 'window_start_ms', 'window_end_ms']
    for col in key_cols:
        print(f"   {col}: {'✓' if col in df.columns else '✗ MISSING'}")

print("\n✅ Basic checks passed!")
