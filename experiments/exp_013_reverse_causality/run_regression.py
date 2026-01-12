"""
exp_013: Reverse Causality Test - Biennial Cross-Sections

Runs OLS regressions every 2 years (2012-2020) to test whether survival
predicts family_connection_ratio growth over time.
"""

import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS

def load_config(config_path="config_ols.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def create_survival_indicators_for_cutoff(df, cutoff_year):
    """Create survived_to_cutoff indicator for specific year."""
    cutoff_date = pd.Timestamp(f'{cutoff_year}-12-31')
    df['survived_to_cutoff'] = (
        (df['death_date_inferred'].isna()) | (df['death_date_inferred'] > cutoff_date)
    ).astype(int)
    return df

def run_biennial_models(df, config):
    """Run cross-sectional models for each configured year."""
    
    results_list = []
    
    for model_key, model_cfg in config["experiment"]["models"].items():
        if model_cfg['type'] != 'ols':
            continue
            
        year = model_cfg['data_year']
        quarter = model_cfg['data_quarter']
        cutoff_year = model_cfg['cutoff_year']
        predictors = model_cfg['predictors']
        
        print(f"\n{'='*70}")
        print(f"Running: {year}Q{quarter} (survived_to_{cutoff_year})")
        print(f"{'='*70}")
        
        # Create survival indicator for this cutoff
        df_year = create_survival_indicators_for_cutoff(df.copy(), cutoff_year)
        
        # Filter to year/quarter
        df_cross = df_year[
            (df_year['date'].dt.year == year) & 
            (df_year['date'].dt.quarter == quarter)
        ].copy()
        
        print(f"  Observations: {len(df_cross):,}")
        print(f"  Survivors: {df_cross['survived_to_cutoff'].sum():,} ({100*df_cross['survived_to_cutoff'].mean():.1f}%)")
        
        # Prepare data
        available_preds = [p for p in predictors if p in df_cross.columns]
        df_clean = df_cross[['family_connection_ratio'] + available_preds].dropna()
        
        print(f"  After dropna: {len(df_clean):,}")
        
        y = df_clean['family_connection_ratio']
        X = sm.add_constant(df_clean[available_preds])
        
        # Fit OLS
        with mlflow.start_run(run_name=f"{year}"):
            model = OLS(y, X).fit(cov_type='HC3')
            
            # Log params
            mlflow.log_param("year", year)
            mlflow.log_param("cutoff_year", cutoff_year)
            mlflow.log_param("n_obs", int(model.nobs))
            mlflow.log_param("survivor_pct", 100*df_cross['survived_to_cutoff'].mean())
            
            # Log metrics
            mlflow.log_metric("r_squared", model.rsquared)
            mlflow.log_metric("r_squared_adj", model.rsquared_adj)
            
            # Extract survived_to_cutoff coefficient
            if 'survived_to_cutoff' in model.params.index:
                coef = model.params['survived_to_cutoff']
                se = model.bse['survived_to_cutoff']
                pval = model.pvalues['survived_to_cutoff']
                t_stat = model.tvalues['survived_to_cutoff']
                
                mlflow.log_metric("survived_coef", coef)
                mlflow.log_metric("survived_pval", pval)
                
                # Format for stargazer
                sig = ""
                if pval < 0.001:
                    sig = "***"
                elif pval < 0.01:
                    sig = "**"
                elif pval < 0.05:
                    sig = "*"
                elif pval < 0.10:
                    sig = "+"
                
                results_list.append({
                    'year': year,
                    'cutoff_year': cutoff_year,
                    'n_obs': int(model.nobs),
                    'survivor_pct': 100*df_cross['survived_to_cutoff'].mean(),
                    'coef': coef,
                    'se': se,
                    't_stat': t_stat,
                    'pval': pval,
                    'sig': sig,
                    'r_squared': model.rsquared,
                    'formatted': f"{coef:.4f}{sig} ({se:.4f})"
                })
                
                print(f"\n  survived_to_cutoff: {coef:.4f}{sig} (se={se:.4f}, p={pval:.4f})")
                print(f"  R² = {model.rsquared:.4f}")
            
            # Save summary
            with open(f"ols_summary_{year}.txt", "w") as f:
                f.write(str(model.summary()))
            mlflow.log_artifact(f"ols_summary_{year}.txt")
    
    return pd.DataFrame(results_list)

def main():
    print("="*70)
    print("EXP_013: BIENNIAL CROSS-SECTIONS (2012-2020)")
    print("="*70)
    
    config = load_config()
    exp_config = config["experiment"]
    data_config = config["data"]
    
    setup_experiment(exp_config["name"])
    
    print(f"\nExperiment: {exp_config['human_readable_name']}")
    
    # Load data
    print(f"\n1. Loading data...")
    loader = QuarterlyWindowDataLoader()
    df = loader.load_with_lags(
        lag_quarters=data_config['lag_quarters'],
        start_year=data_config['start_year'],
        end_year=data_config['end_year']
    )
    
    # Infer death dates
    print("\n2. Inferring death dates from last observations...")
    df['date'] = pd.to_datetime(df['DT'])
    df['death_date_inferred'] = np.nan
    
    dead_banks = df[df['is_dead'] == True]['regn'].unique()
    print(f"   Dead banks: {len(dead_banks)}")
    
    for bank_id in dead_banks:
        last_obs = df[df['regn'] == bank_id]['date'].max()
        df.loc[df['regn'] == bank_id, 'death_date_inferred'] = last_obs
    
    df['death_date_inferred'] = pd.to_datetime(df['death_date_inferred'])
    
    # Run biennial models
    print("\n3. Running biennial cross-sections...")
    results_df = run_biennial_models(df, config)
    
    # Save aggregated results
    print("\n4. Saving aggregated results...")
    results_df.to_csv("biennial_results.csv", index=False)
    
    # Create stargazer-style table
    stargazer_df = results_df.pivot_table(
        index='year',
        values=['formatted', 'n_obs', 'survivor_pct', 'r_squared'],
        aggfunc='first'
    )
    stargazer_df.to_csv("stargazer_biennial.csv")
    
    print("\n" + "="*70)
    print("Results Summary:")
    print("="*70)
    print(results_df[['year', 'cutoff_year', 'coef', 'pval', 'sig', 'n_obs', 'survivor_pct']].to_string(index=False))
    
    print(f"\n✅ Saved biennial_results.csv and stargazer_biennial.csv")
    print(f"\nMLflow UI: {mlflow.get_tracking_uri()}")

if __name__ == '__main__':
    main()
