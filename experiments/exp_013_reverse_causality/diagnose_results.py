"""
Diagnostic script for exp_013 to investigate suspicious results.

Issues to investigate:
1. R² (within) = 1.00 in panel model (perfect fit - suspicious)
2. survived_to_2015 = 100% (should have some dead banks)
3. survived_status mean = 1.000 (all alive?)
"""

import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
from statsmodels.stats.outliers_influence import variance_inflation_factor

def main():
    print("="*70)
    print("EXP_013 DIAGNOSTIC TESTS")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    loader = QuarterlyWindowDataLoader()
    df = loader.load_with_lags(
        lag_quarters=4,
        start_year=2010,
        end_year=2020
    )
    
    print(f"   Total observations: {len(df):,}")
    print(f"   Unique banks: {df['regn'].nunique():,}")
    
    # Check death_date distribution
    print("\n2. Checking death_date distribution...")
    df['death_date'] = pd.to_datetime(df['death_date'], errors='coerce')
    
    print(f"   Non-null death_date: {df['death_date'].notna().sum():,} ({100*df['death_date'].notna().mean():.1f}%)")
    print(f"   Null death_date (survivors): {df['death_date'].isna().sum():,} ({100*df['death_date'].isna().mean():.1f}%)")
    
    if df['death_date'].notna().any():
        print(f"\n   Death date range: {df['death_date'].min()} to {df['death_date'].max()}")
        print(f"   Banks with death_date: {df[df['death_date'].notna()]['regn'].nunique()}")
    
    # Check observation dates for dead banks
    print("\n3. Checking observation patterns for dead banks...")
    dead_banks = df[df['death_date'].notna()]['regn'].unique()
    print(f"   Dead banks: {len(dead_banks)}")
    
    if len(dead_banks) > 0:
        # Sample a few dead banks
        sample_dead = dead_banks[:5]
        for bank_id in sample_dead:
            bank_data = df[df['regn'] == bank_id].sort_values('DT')
            death = bank_data['death_date'].iloc[0]
            obs_dates = bank_data['DT'].values
            print(f"\n   Bank {bank_id}:")
            print(f"     Death date: {death}")
            print(f"     Observations: {len(obs_dates)}")
            print(f"     Last observation: {obs_dates[-1]}")
            print(f"     Obs after death: {(pd.to_datetime(obs_dates) > death).sum()}")
    
    # Create survival indicators
    print("\n4. Creating survival indicators (with diagnostics)...")
    df['date'] = pd.to_datetime(df['DT'])
    
    cutoff_2015 = pd.Timestamp('2015-12-31')
    cutoff_2020 = pd.Timestamp('2020-12-31')
    
    df['survived_to_2015'] = (
        (df['death_date'].isna()) | (df['death_date'] > cutoff_2015)
    ).astype(int)
    
    df['survived_to_2020'] = (
        (df['death_date'].isna()) | (df['death_date'] > cutoff_2020)
    ).astype(int)
    
    df['survived_status'] = (
        (df['death_date'].isna()) | (df['death_date'] > df['date'])
    ).astype(int)
    
    print(f"   survived_to_2015: {df['survived_to_2015'].sum():,} / {len(df):,} ({100*df['survived_to_2015'].mean():.1f}%)")
    print(f"   survived_to_2020: {df['survived_to_2020'].sum():,} / {len(df):,} ({100*df['survived_to_2020'].mean():.1f}%)")
    print(f"   survived_status:  mean = {df['survived_status'].mean():.4f}, std = {df['survived_status'].std():.4f}")
    
    # THE PROBLEM: Check if we only observe banks BEFORE they die
    print("\n5. **CRITICAL CHECK**: Do we observe banks after death?")
    dead_bank_obs = df[df['death_date'].notna()]
    if len(dead_bank_obs) > 0:
        obs_after_death = (dead_bank_obs['date'] > dead_bank_obs['death_date']).sum()
        print(f"   Observations from dead banks: {len(dead_bank_obs):,}")
        print(f"   Observations AFTER death: {obs_after_death}")
        print(f"   Observations BEFORE death: {len(dead_bank_obs) - obs_after_death}")
        
        if obs_after_death == 0:
            print("\n   ⚠️  ISSUE FOUND: We never observe dead banks AFTER death!")
            print("   This means survived_status is always 1 in the observed data.")
            print("   Dead banks drop out of sample at death → no variation!")
    
    # Check family_connection_ratio distribution
    print("\n6. Checking family_connection_ratio distribution...")
    fcr = df['family_connection_ratio'].dropna()
    print(f"   Mean: {fcr.mean():.4f}")
    print(f"   Std: {fcr.std():.4f}")
    print(f"   Min: {fcr.min():.4f}")
    print(f"   Max: {fcr.max():.4f}")
    print(f"   Non-zero: {(fcr > 0).sum():,} ({100*(fcr > 0).mean():.1f}%)")
    
    # Check within-bank variation in FCR
    print("\n7. Checking within-bank FCR variation...")
    fcr_by_bank = df.groupby('regn')['family_connection_ratio'].agg(['std', 'count'])
    fcr_by_bank = fcr_by_bank[fcr_by_bank['count'] > 1]  # Banks with multiple obs
    
    print(f"   Banks with >1 observation: {len(fcr_by_bank):,}")
    print(f"   Banks with FCR std > 0: {(fcr_by_bank['std'] > 0).sum():,} ({100*(fcr_by_bank['std'] > 0).mean():.1f}%)")
    print(f"   Banks with FCR std = 0 (constant): {(fcr_by_bank['std'] == 0).sum():,} ({100*(fcr_by_bank['std'] == 0).mean():.1f}%)")
    print(f"   Mean within-bank FCR std: {fcr_by_bank['std'].mean():.6f}")
    
    # VIF test for 2015 cross-section
    print("\n8. Running VIF test (2015 cross-section)...")
    df_2015 = df[(df['date'].dt.year == 2015) & (df['date'].dt.quarter == 4)].copy()
    
    predictors = [
        'survived_to_2015', 'camel_roa', 'camel_npl_ratio', 
        'camel_tier1_capital_ratio', 'state_ownership_pct',
        'foreign_ownership_total_pct', 'rw_page_rank_4q_lag', 
        'rw_out_degree_4q_lag'
    ]
    
    df_vif = df_2015[predictors].dropna()
    
    print(f"   Sample size: {len(df_vif)}")
    
    vif_data = pd.DataFrame()
    vif_data["Variable"] = predictors
    vif_data["VIF"] = [variance_inflation_factor(df_vif.values, i) for i in range(len(predictors))]
    
    print("\n   VIF Results:")
    print(vif_data.to_string(index=False))
    print("\n   Note: VIF > 10 indicates severe multicollinearity")
    
    # Correlation matrix
    print("\n9. Correlation matrix (2015 cross-section)...")
    corr = df_vif.corr()
    print("\n   Correlation with survived_to_2015:")
    print(corr['survived_to_2015'].sort_values(ascending=False))
    
    # Save diagnostics
    print("\n10. Saving diagnostic results...")
    
    with open("diagnostics_report.txt", "w") as f:
        f.write("EXP_013 DIAGNOSTIC REPORT\n")
        f.write("="*70 + "\n\n")
        
        f.write("ISSUE: R² = 1.00 in panel model (perfect fit)\n\n")
        
        f.write("ROOT CAUSE ANALYSIS:\n")
        f.write(f"- Dead banks drop out of sample at death\n")
        f.write(f"- We never observe observations AFTER death\n")
        f.write(f"- survived_status is always 1 in observed data\n")
        f.write(f"- Within-bank: FCR variation likely TIME-INVARIANT\n")
        f.write(f"- Bank FE absorbs all FCR variation → perfect fit\n\n")
        
        f.write("SURVIVAL INDICATOR DISTRIBUTION:\n")
        f.write(f"- survived_to_2015: {100*df['survived_to_2015'].mean():.1f}%\n")
        f.write(f"- survived_to_2020: {100*df['survived_to_2020'].mean():.1f}%\n")
        f.write(f"- survived_status:  {100*df['survived_status'].mean():.1f}%\n\n")
        
        f.write("FCR WITHIN-BANK VARIATION:\n")
        f.write(f"- Mean std: {fcr_by_bank['std'].mean():.6f}\n")
        f.write(f"- Constant FCR: {100*(fcr_by_bank['std'] == 0).mean():.1f}% of banks\n\n")
        
        f.write("VIF RESULTS:\n")
        f.write(vif_data.to_string(index=False))
        
    print("   ✅ Saved diagnostics_report.txt")
    
    print("\n" + "="*70)
    print("DIAGNOSIS COMPLETE")
    print("="*70)

if __name__ == '__main__':
    main()
