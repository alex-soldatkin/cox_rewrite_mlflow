"""
Simple test script for exp_007 data loading (no MLflow dependency).

Validates that quarterly lagged data can be loaded and prepared for Cox analysis.
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader

def main():
    print("="*70)
    print("EXP_007: LAGGED NETWORK DATA VALIDATION")
    print("="*70)
    
    # Load data with 4-quarter lag
    print("\n1. Loading data with 4-quarter lag...")
    loader = QuarterlyWindowDataLoader()
    df = loader.load_with_lags(lag_quarters=4, start_year=2014, end_year=2020)
    
    print(f"\n✅ Data loaded successfully!")
    print(f"   Total observations: {len(df):,}")
    print(f"   Unique banks: {df['regn'].nunique()}")
    print(f"   Date range: {df['DT'].min()} to {df['DT'].max()}")
    
    # Check lagged network columns
    print(f"\n2. Checking lagged network features...")
    lagged_cols = [c for c in df.columns if 'lag' in c and 'rw_' in c]
    print(f"   Found {len(lagged_cols)} lagged network features:")
    for col in lagged_cols:
        non_null = df[col].notna().sum()
        pct = 100 * non_null / len(df)
        print(f"     - {col}: {non_null:,} non-null ({pct:.1f}%)")
    
    # Show sample
    print(f"\n3. Sample data:")
    display_cols = ['regn', 'DT', 'quarter', 'total_assets'] + lagged_cols[:3]
    print(df[display_cols].head(10))
    
    # Summary stats
    print(f"\n4. Summary statistics for lagged network features:")
    print(df[lagged_cols].describe())
    
    print(f"\n✅ VALIDATION COMPLETE")
    print(f"\nNext steps:")
    print(f"  1. Start MLflow server: mlflow server --host 127.0.0.1 --port 5000")
    print(f"  2. Run full Cox models: uv run python run_cox.py")

if __name__ == '__main__':
    main()
