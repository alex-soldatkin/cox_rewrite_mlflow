"""
Experiment 010: Mechanism Testing
Tests the three transaction cost mechanisms:
1. Political Embeddedness (Proxy: Regional Stratification)
2. Tax Optimization (Proxy: Stake Fragmentation index)
3. Internal Capital Markets (Proxy: Family Company Count)

Usage:
    uv run python experiments/exp_010_mechanism_testing/run_cox_mechanisms.py
"""

import os
import sys
import pandas as pd
import numpy as np
from lifelines import CoxTimeVaryingFitter
from sklearn.preprocessing import StandardScaler
from lifelines.utils import concordance_index
from visualisations.cox_stargazer_new import create_single_column_stargazer, create_single_column_stargazer_hr
import mlflow
from dotenv import load_dotenv
import yaml

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(project_root)

from mlflow_utils.mechanism_data_loader import MechanismDataLoader

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config_cox.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def prepare_cox_data(df):
    """
    Standardize and prepare data for Cox analysis.
    """
    print(f"\nPreparing Cox data for {len(df)} observations...")
    df_cox = df.copy()
    
    # 1. Date Conversion
    df_cox['start'] = df_cox.groupby('regn')['DT'].rank(method='first') - 1
    df_cox['stop'] = df_cox['start'] + 1
    
    # 2. Scaling
    scaler = StandardScaler()
    num_cols = [
        'family_connection_ratio', 'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio',
        'rw_out_degree_4q_lag', 'rw_page_rank_4q_lag',
        'state_ownership_pct', 'foreign_ownership_total_pct',
        'stake_fragmentation_index', 'family_company_count', 'epu_index',
        'group_total_capital', 'group_sector_count'
    ]
    
    # Ensure all columns exist
    cols_to_scale = [c for c in num_cols if c in df_cox.columns]
    print(f"  Scaling features: {cols_to_scale}")
    df_cox[cols_to_scale] = scaler.fit_transform(df_cox[cols_to_scale].fillna(0))
    
    # 3. Categorical encoding for region and sector (for strata)
    if 'bank_region' in df_cox.columns:
        df_cox['region_id'] = pd.factorize(df_cox['bank_region'])[0]
    
    if 'group_primary_sector' in df_cox.columns:
        df_cox['sector_id'] = pd.factorize(df_cox['group_primary_sector'])[0]
    
    # Ensure required columns for lifelines
    df_cox['regn'] = df_cox['regn'].astype(int)
    
    return df_cox

def run_mechanism_experiment():
    load_dotenv()
    config = load_config()
    
    # Load data
    loader = MechanismDataLoader()
    df_raw = loader.load_mechanism_data(
        lag_quarters=config['data']['lag_quarters'],
        start_year=config['data']['start_year'],
        end_year=config['data']['end_year']
    )
        
    df_cox = prepare_cox_data(df_raw)
    
    # MLflow tracking
    tracking_uri = "http://localhost:5000"
    mlflow.set_tracking_uri(tracking_uri)
    
    try:
        # Test connection
        mlflow.search_experiments()
        print(f"Connected to MLflow server at {tracking_uri}")
    except Exception:
        print("MLflow server not accessible (403 or down). Using local tracking.")
        mlflow.set_tracking_uri(None)

    mlflow.set_experiment(config['experiment']['name'])
    models = config['experiment']['models']
    
    for model_key, spec in models.items():
        model_name = spec['name']
        print(f"\n--- Running {model_name} ---")
        
        with mlflow.start_run(run_name=model_name):
            try:
                ctv = CoxTimeVaryingFitter(penalizer=config['model_params']['penalizer'])
                ctv.fit(
                    df_cox,
                    id_col='regn',
                    event_col='event',
                    start_col='start',
                    stop_col='stop',
                    formula=spec['formula'],
                    strata=spec['strata']
                )
                
                # Log Summary
                summary = ctv.summary
                print(summary[['coef', 'p', 'exp(coef)']])
                
                # Log metrics
                mlflow.log_metric("log_likelihood", ctv.log_likelihood_)
                mlflow.log_metric("aic_partial", ctv.AIC_partial_)
                mlflow.log_metric("log_likelihood_ratio", ctv.log_likelihood_ratio_test().test_statistic)
                
                # C-index
                try:
                    predicted_hazards = ctv.predict_partial_hazard(df_cox)
                    c_idx = concordance_index(df_cox['stop'], -predicted_hazards, df_cox['event'])
                    mlflow.log_metric("c_index", c_idx)
                except Exception as e:
                    print(f"C-index calculation failed: {e}")
                    c_idx = None

                # Log coefficients & p-values
                for feat, row in summary.iterrows():
                    mlflow.log_metric(f"coef_{feat}", row['coef'])
                    mlflow.log_metric(f"p_{feat}", row['p'])
                
                n_subjects = df_cox['regn'].nunique()

                # Generate Stargazer-compatible CSVs using helper functions
                # 1. Coefficients
                stargazer_df = create_single_column_stargazer(ctv, c_index=c_idx, n_subjects=n_subjects)
                stargazer_path = f"experiments/exp_010_mechanism_testing/stargazer_column.csv"
                stargazer_df.to_csv(stargazer_path)
                mlflow.log_artifact(stargazer_path)

                # 2. Hazard Ratios
                hr_df = create_single_column_stargazer_hr(ctv, c_index=c_idx, n_subjects=n_subjects)
                hr_path = f"experiments/exp_010_mechanism_testing/stargazer_hr_column.csv"
                hr_df.to_csv(hr_path)
                mlflow.log_artifact(hr_path)

                # Save summary as artifact
                summary_path = f"experiments/exp_010_mechanism_testing/summary_{model_key}.csv"
                summary.to_csv(summary_path)
                mlflow.log_artifact(summary_path)
                
                # Tag as column for aggregation script
                mlflow.set_tag("stargazer_column", model_key)
                mlflow.set_tag("human_readable_name", model_name)
                
                print(f"✅ {model_name} completed. LL: {ctv.log_likelihood_:.4f}")
                
            except Exception as e:
                print(f"❌ {model_name} failed: {e}")
                mlflow.log_param("error", str(e))

if __name__ == "__main__":
    run_mechanism_experiment()
