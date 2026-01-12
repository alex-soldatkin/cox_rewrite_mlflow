#!/usr/bin/env python3
"""
Aggregate exp_011 Stargazer tables across periods for cross-period comparison.
"""

import pandas as pd
from pathlib import Path

# Model keys matching run_subperiods.py
MODELS = [
    ('model_1_baseline', 'M1: Baseline'),
    ('model_2_crisis_dummies', 'M2: Crisis Dummies'),
    ('model_3_family_crisis', 'M3: Family × Crisis'),
    ('model_4_state_crisis', 'M4: State × Crisis'),
    ('model_5_foreign_crisis', 'M5: Foreign × Crisis'),
    ('model_6_full_interactions', 'M6: Full Interactions')
]

PERIODS = [
    ('2004_2007', '2004-2007'),
    ('2007_2013', '2007-2013'),
    ('2013_2020', '2013-2020')
]

def aggregate_stargazer(model_key, model_name, table_type='coef'):
    """
    Aggregate Stargazer tables for one model across all three periods.
    
    Args:
        model_key: Model file key (e.g., 'model_1_baseline')
        model_name: Model display name (e.g., 'M1: Baseline')
        table_type: Either 'coef' or 'hr'
    """
    dfs = {}
    
    for period_slug, period_label in PERIODS:
        filepath = Path('output') / period_slug / f'stargazer_{table_type}_{model_key}.csv'
        
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0)
            # Rename column to period label
            df.columns = [period_label]
            dfs[period_label] = df
        else:
            print(f"  ⚠️  Missing: {filepath}")
    
    if not dfs:
        print(f"  ❌ No data for {model_name} ({table_type})")
        return None
    
    # Combine side-by-side
    combined = pd.concat(dfs.values(), axis=1)
    
    # Reindex to ensure same variables across periods (fill missing with empty)
    # Get union of all variables
    all_vars = set()
    for df in dfs.values():
        all_vars.update(df.index)
    
    combined = combined.reindex(sorted(all_vars))
    combined = combined.fillna('')
    
    return combined

def main():
    print("="*80)
    print("Aggregating exp_011 Stargazer Tables Across Periods")  
    print("="*80)
    
    output_dir = Path('output/aggregated')
    output_dir.mkdir(exist_ok=True)
    
    for model_key, model_name in MODELS:
        print(f"\n{model_name}")
        
        # Aggregate coefficient tables
        coef_table = aggregate_stargazer(model_key, model_name, 'coef')
        if coef_table is not None:
            coef_path = output_dir / f'stargazer_coef_{model_key}.csv'
            coef_table.to_csv(coef_path)
            print(f"  ✅ Coef table: {coef_path}")
        
        # Aggregate HR tables
        hr_table = aggregate_stargazer(model_key, model_name, 'hr')
        if hr_table is not None:
            hr_path = output_dir / f'stargazer_hr_{model_key}.csv'
            hr_table.to_csv(hr_path)
            print(f"  ✅ HR table: {hr_path}")
    
    print(f"\n{'='*80}")
    print("Aggregation Complete!")
    print(f"{'='*80}")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Files created: {len(list(output_dir.glob('*.csv')))}")

if __name__ == '__main__':
    main()
