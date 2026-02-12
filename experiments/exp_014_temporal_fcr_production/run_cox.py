"""
exp_014: Temporal FCR with Biannual Production Data (2000-2021)

Tests the family connection ratio (FCR) effect on bank survival using:
1. Biannual temporal FCR data (1990-2022 v6)
2. 4-year lags (2 periods)
3. Full historical range (2000-2021)
4. Feature scaling to ensuring convergence

Usage:
    uv run python experiments/exp_014_temporal_fcr_production/run_cox.py
"""

import os
import sys

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd
import numpy as np
from pathlib import Path
import mlflow
from lifelines import CoxTimeVaryingFitter
from lifelines.utils import concordance_index
from sklearn.preprocessing import StandardScaler
from visualisations.cox_stargazer_new import create_single_column_stargazer, create_single_column_stargazer_hr
from visualisations.cox_interpretation import generate_interpretation_report

from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader
from mlflow_utils.tracking import setup_experiment
from graphdatascience import GraphDataScience
from dotenv import load_dotenv

# Load env variables for GDS
load_dotenv()

def collapse_small_communities(df, community_col='rw_community_louvain_4q_lag', min_size=5):
    """
    Collapse communities with fewer than min_size members into 'other' category.
    """
    if community_col not in df.columns:
        print(f"Warning: {community_col} not found for stratification")
        df['community_collapsed'] = 0
        return df
    
    print(f"\nProcessing communities from {community_col}...")
    
    # Helper to handle arrays (from exp_008)
    def extract_coarsest(val):
        if isinstance(val, (list, np.ndarray)):
            if len(val) > 0:
                return float(val[0])
            return -1.0
        if pd.isna(val):
            return -1.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return -1.0

    # Extract scalar and Fill NaNs
    df['community_scalar'] = df[community_col].apply(extract_coarsest)
    
    # Count banks per community
    community_counts = df.groupby('community_scalar')['regn'].nunique()
    
    # Identify small communities
    small_communities = community_counts[community_counts < min_size].index
    
    # Create collapsed version
    df['community_collapsed'] = df['community_scalar'].copy()
    df.loc[df['community_scalar'].isin(small_communities), 'community_collapsed'] = -1  # 'other' category
    
    n_original = df['community_scalar'].nunique()
    n_collapsed = df['community_collapsed'].nunique()
    
    print(f"  Original communities: {n_original}")
    print(f"  Final communities: {n_collapsed}")
    
    return df

def prepare_cox_data(df, features, stratify_by_community=False):
    """
    Prepare data for Cox time-varying analysis.
    """
    print(f"\nPreparing Cox data (stratify={stratify_by_community})...")
    
    df_cox = df.copy()
    
    # 1. Date Conversion & Sorting
    df_cox['date'] = pd.to_datetime(df_cox['DT'])
    df_cox = df_cox.sort_values(by=['regn', 'date'])
    
    # 2. Create Time Intervals (Start/Stop)
    df_cox['start'] = df_cox['date']
    df_cox['stop'] = df_cox.groupby('regn')['date'].shift(-1)
    
    # Fill last stop interval
    mask_last = df_cox['stop'].isna()
    df_cox.loc[mask_last, 'stop'] = df_cox.loc[mask_last, 'start'] + pd.DateOffset(years=2)
    
    # 3. Time Since Registration
    min_dates = df_cox.groupby('regn')['date'].transform('min')
    df_cox['entry_date'] = min_dates
    
    df_cox['start_t'] = (df_cox['start'] - df_cox['entry_date']).dt.days
    df_cox['stop_t'] = (df_cox['stop'] - df_cox['entry_date']).dt.days
    
    # Handle t=0 issue
    mask_equal = df_cox['start_t'] == df_cox['stop_t']
    df_cox.loc[mask_equal, 'stop_t'] += 1
    
    # Filter valid intervals
    df_cox = df_cox[df_cox['stop_t'] > df_cox['start_t']]
    
    # 4. Filter Features
    available_features = [c for c in features if c in df_cox.columns]
    
    # 5. Missing Value Imputation
    df_cox[available_features] = df_cox[available_features].fillna(0)
    
    # 6. Scaling
    print("\n  Scaling features to 0-100 range...")
    if available_features:
        scaler = StandardScaler()
        df_cox[available_features] = scaler.fit_transform(df_cox[available_features])
        
        # Drop constant columns
        drop_cols = []
        for col in available_features:
            if df_cox[col].std() == 0:
                print(f"  ⚠️ Dropping constant column: {col}")
                drop_cols.append(col)
        
        if drop_cols:
            df_cox = df_cox.drop(columns=drop_cols)
            for c in drop_cols:
                if c in available_features:
                    available_features.remove(c)
        
        # Min-Max scale
        for col in available_features:
            min_val = df_cox[col].min()
            max_val = df_cox[col].max()
            if max_val > min_val:
                df_cox[col] = 100 * (df_cox[col] - min_val) / (max_val - min_val)

    # 7. Final Cleanup
    keep_cols = ['regn', 'start_t', 'stop_t', 'event'] + available_features
    if stratify_by_community and 'community_collapsed' in df_cox.columns:
        keep_cols.append('community_collapsed')
        
    df_cox = df_cox[keep_cols].copy()
    
    print(f"  Prepared {len(df_cox):,} observations")
    print(f"  Features: {available_features}")
    
    return df_cox, available_features

def run_model(model_name, df_cox, features, stratify=False):
    print(f"\nRunning: {model_name}")
    
    ctv = CoxTimeVaryingFitter(penalizer=0.01)
    
    try:
        if stratify and 'community_collapsed' in df_cox.columns:
            print("  Stratifying by 'community_collapsed'")
            ctv.fit(df_cox, id_col='regn', event_col='event', 
                   start_col='start_t', stop_col='stop_t',
                   strata=['community_collapsed'], show_progress=True)
        else:
            ctv.fit(df_cox, id_col='regn', event_col='event', 
                    start_col='start_t', stop_col='stop_t', 
                    show_progress=True)
        
        print("\n✅ Model Converged!")
        
        return ctv
        
    except Exception as e:
        print(f"\n❌ Model Failed: {e}")
        return None

def main():
    setup_experiment("exp_014_temporal_fcr_production")
    
    # Initialize GDS
    try:
        gds = GraphDataScience(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
    except Exception as e:
        print(f"Warning: Could not connect to Neo4j: {e}")
        gds = None
        
    loader = TemporalFCRLoader(gds_client=gds)
    
    # Load data
    print("Loading data...")
    df = loader.load_with_lags(lag_periods=2, start_year=2000, end_year=2021)
    
    # Process communities
    df = collapse_small_communities(df, community_col='rw_community_louvain_4q_lag')
    
    # Define Models
    models = {
        "M1": {
            "name": "M1: Baseline (FCR Only)",
            "features": ['family_connection_ratio_temporal_lag'],
            "stratify": False
        },
        "M2": {
            "name": "M2: + Bank Controls",
            "features": [
                'family_connection_ratio_temporal_lag',
                'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio'
            ],
            "stratify": False
        },
        "M3": {
            "name": "M3: + Network Controls",
            "features": [
                'family_connection_ratio_temporal_lag',
                'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio',
                'rw_page_rank_4q_lag', 'rw_out_degree_4q_lag'
            ],
            "stratify": False
        },
        "M4": {
            "name": "M4: Full Model + Ownership",
            "features": [
                'family_connection_ratio_temporal_lag',
                'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio',
                'rw_page_rank_4q_lag', 'rw_out_degree_4q_lag',
                'family_ownership_pct', 'foreign_ownership_total_pct', 'state_ownership_pct'
            ],
            "stratify": False
        },
        "M5": {
            "name": "M5: Full + Stratified",
            "features": [
                'family_connection_ratio_temporal_lag',
                'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio',
                'rw_page_rank_4q_lag', 'rw_out_degree_4q_lag',
                'family_ownership_pct', 'foreign_ownership_total_pct', 'state_ownership_pct'
            ],
            "stratify": True
        }
    }
    
    for key, cfg in models.items():
        print(f"\n{'='*60}")
        print(f"Processing {cfg['name']}")
        print(f"{'='*60}")
        
        # Prepare
        df_cox, model_features = prepare_cox_data(df, cfg['features'], cfg['stratify'])
        
        with mlflow.start_run(run_name=cfg['name']):
            mlflow.log_params({
                "model": key,
                "features": model_features,
                "stratify": cfg['stratify']
            })
            
            # Tag for aggregation tool
            mlflow.set_tag("human_readable_name", cfg['name'])
            
            model = run_model(cfg['name'], df_cox, model_features, cfg['stratify'])
            
            if model:
                # Metrics
                mlflow.log_metric("aic", model.AIC_partial_)
                
                # C-index
                try:
                    pred = model.predict_partial_hazard(df_cox)
                    c_idx = concordance_index(df_cox['stop_t'], -pred, df_cox['event'])
                    mlflow.log_metric("concordance", c_idx)
                    print(f"  C-index: {c_idx:.4f}")
                except Exception as e:
                    print(f"  C-index failed: {e}")
                    c_idx = None
                
                # Artifacts
                n_subjects = df_cox['regn'].nunique()
                
                # Stargazer
                # Note: aggregation script expects these names exactly
                try:
                    stg_df = create_single_column_stargazer(model, c_index=c_idx, n_subjects=n_subjects)
                    stg_df.to_csv("stargazer_column.csv", index=True)
                    mlflow.log_artifact("stargazer_column.csv")
                except Exception as e:
                    print(f"Error stg_col: {e}")

                try:
                    hr_df = create_single_column_stargazer_hr(model, c_index=c_idx, n_subjects=n_subjects)
                    hr_df.to_csv("stargazer_hr_column.csv", index=True)
                    mlflow.log_artifact("stargazer_hr_column.csv")
                except Exception as e:
                    print(f"Error stg_hr: {e}")
                    
                # Interpretation
                try:
                    interp = generate_interpretation_report(model, model_name=cfg['name'])
                    with open("interpretation.md", "w") as f:
                        f.write(interp)
                    mlflow.log_artifact("interpretation.md")
                except Exception as e:
                    print(f"Error interpretation: {e}")

if __name__ == "__main__":
    main()
