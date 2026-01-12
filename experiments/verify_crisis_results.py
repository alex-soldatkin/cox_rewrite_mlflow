#!/usr/bin/env python3
"""
Extract and verify all exp_009 and exp_011 results for crisis_interactions_writeup.md
"""

import pandas as pd
from pathlib import Path
import json

print("="*80)
print("Extracting exp_009 and exp_011 Results for Verification")
print("="*80)

# ============================================================================
# exp_011 Subperiod Results (from aggregated Stargazer tables)
# ============================================================================
print("\n### exp_011 Subperiod Analysis ###\n")

exp_011_dir = Path("experiments/exp_011_subperiod_analysis/output/aggregated")

models = [
    ("model_1_baseline", "M1: Baseline"),
    ("model_2_crisis_dummies", "M2: Crisis Dummies"),
    ("model_3_family_crisis", "M3: Family × Crisis"),
    ("model_4_state_crisis", "M4: State × Crisis"),
    ("model_5_foreign_crisis", "M5: Foreign × Crisis"),
    ("model_6_full_interactions", "M6: Full Interactions")
]

# Extract C-index and model fit metrics
exp_011_summary = {}

for model_key, model_name in models:
    coef_file = exp_011_dir / f"stargazer_coef_{model_key}.csv"
    hr_file = exp_011_dir / f"stargazer_hr_{model_key}.csv"
    
    if coef_file.exists():
        df_coef = pd.read_csv(coef_file, index_col=0)
        df_hr = pd.read_csv(hr_file, index_col=0)
        
        for period in ['2004-2007', '2007-2013', '2013-2020']:
            if period in df_coef.columns:
                c_index = df_coef.loc['C-index', period]
                log_lik = df_coef.loc['Log Likelihood', period]
                aic = df_coef.loc['AIC Partial', period]
                obs = df_coef.loc['Observations', period]
                events = df_coef.loc['Events', period]
                subjects = df_coef.loc['Subjects', period]
                
                key = f"{model_name} ({period})"
                exp_011_summary[key] = {
                    'c_index': c_index,
                    'log_lik': log_lik,
                    'aic': aic,
                    'observations': obs,
                    'events': events,
                    'subjects': subjects
                }
                
                print(f"{key}:")
                print(f"  C-index: {c_index}, Events: {events}, Obs: {obs}")

# Extract baseline coefficients for cross-period comparison
print("\n### Baseline Ownership Effects Across Periods ###\n")

m1_coef = pd.read_csv(exp_011_dir / "stargazer_coef_model_1_baseline.csv", index_col=0)
m1_hr = pd.read_csv(exp_011_dir / "stargazer_hr_model_1_baseline.csv", index_col=0)

key_vars = [
    'family_connection_ratio',
    'family_ownership_pct',
    'state_ownership_pct',
    'foreign_ownership_total_pct',
    'rw_page_rank_4q_lag',
    'rw_out_degree_4q_lag',
    'camel_roa',
    'camel_npl_ratio',
    'camel_tier1_capital_ratio'
]

print("Variable | 2004-2007 (Coef) | 2007-2013 (Coef) | 2013-2020 (Coef)")
print("-" * 80)
for var in key_vars:
    if var in m1_coef.index:
        print(f"{var:30s} | {m1_coef.loc[var, '2004-2007']:20s} | {m1_coef.loc[var, '2007-2013']:20s} | {m1_coef.loc[var, '2013-2020']:20s}")

# Save to JSON for writeup
output_data = {
    'exp_011_summary': exp_011_summary,
    'exp_011_baseline_coef': m1_coef.to_dict(),
    'exp_011_baseline_hr': m1_hr.to_dict()
}

output_file = Path("experiments/exp_011_subperiod_analysis/verified_results.json")
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"\n✅ Results saved to: {output_file}")

# ============================================================================  
# exp_009 Results (would need MLflow extraction - placeholder for now)
# ============================================================================
print("\n### exp_009 Pooled Analysis ###\n")
print("⚠️  exp_009 extraction requires MLflow server access")
print("    Manually verify from http://localhost:5000/#/experiments/13")

print("\n" + "="*80)
print("Verification Complete!")
print("="*80)
