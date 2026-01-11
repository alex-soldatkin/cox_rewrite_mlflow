"""
Multicollinearity diagnostic for exp_007 features.

Tests VIF (Variance Inflation Factor) and correlation matrix 
to identify problematic feature combinations before Cox modeling.
"""

import os
import sys
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader

def calculate_vif(df, features):
    """Calculate VIF for each feature."""
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features
    vif_data["VIF"] = [variance_inflation_factor(df[features].values, i) 
                       for i in range(len(features))]
    return vif_data.sort_values('VIF', ascending=False)

def main():
    print("="*70)
    print("MULTICOLLINEARITY DIAGNOSTICS")
    print("="*70)
    
    # Load data
    loader = QuarterlyWindowDataLoader()
    df = loader.load_with_lags(lag_quarters=4, start_year=2014, end_year=2020)
    
    # Get available features
    accounting_features = ['total_assets', 'total_equity', 'npl_amount', 
                          'total_loans', 'total_deposits', 'total_liquid_assets']
    
    network_features = ['rw_page_rank_4q_lag', 'rw_out_degree_4q_lag', 
                       'rw_in_degree_4q_lag', 'rw_degree_4q_lag']
    
    # Filter to available
    all_features = [f for f in accounting_features + network_features if f in df.columns]
    
    # Remove missing
    df_test = df[all_features].dropna()
    
    print(f"\n1. Testing {len(all_features)} features on {len(df_test):,} observations")
    print(f"   Features: {all_features}")
    
    # Correlation matrix
    print(f"\n2. Correlation Matrix:")
    corr = df_test[all_features].corr()
    print(corr.round(3))
    
    # Find high correlations
    print(f"\n3. High Correlations (|r| > 0.8):")
    high_corr = []
    for i in range(len(all_features)):
        for j in range(i+1, len(all_features)):
            r = corr.iloc[i, j]
            if abs(r) > 0.8:
                high_corr.append((all_features[i], all_features[j], r))
                print(f"   {all_features[i]} <-> {all_features[j]}: {r:.3f}")
    
    if not high_corr:
        print("   None found")
    
    # VIF
    print(f"\n4. Variance Inflation Factors:")
    try:
        vif = calculate_vif(df_test, all_features)
        print(vif.to_string(index=False))
        
        print(f"\n5. VIF Interpretation:")
        print(f"   VIF < 5: Low multicollinearity")
        print(f"   VIF 5-10: Moderate multicollinearity")
        print(f"   VIF > 10: High multicollinearity (remove feature)")
        
        high_vif = vif[vif['VIF'] > 10]
        if len(high_vif) > 0:
            print(f"\n⚠️  Features with VIF > 10 (should consider removing):")
            for _, row in high_vif.iterrows():
                print(f"   - {row['Feature']}: VIF = {row['VIF']:.2f}")
        else:
            print(f"\n✅ No features with VIF > 10")
            
    except Exception as e:
        print(f"   VIF calculation failed: {e}")
    
    # Recommendations
    print(f"\n6. Recommendations for Cox Model:")
    
    if 'rw_in_degree_4q_lag' in all_features and 'rw_out_degree_4q_lag' in all_features:
        print(f"   • Use out_degree OR degree, not both in/out (they sum to degree)")
    
    if 'total_assets' in all_features and 'total_equity' in all_features:
        corr_val = corr.loc['total_assets', 'total_equity'] if 'total_assets' in corr.index else None
        if corr_val and abs(corr_val) > 0.8:
            print(f"   • total_assets and total_equity highly correlated ({corr_val:.3f})")
            print(f"     Consider using ratios instead (e.g., equity/assets)")
    
    print(f"\n✅ Diagnostic complete")

if __name__ == '__main__':
    main()
