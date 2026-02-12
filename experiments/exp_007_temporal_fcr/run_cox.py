"""
exp_007: Lagged Network Effects Cox Models

Tests whether lagged network positions (t-4 quarters) predict bank survival,
addressing endogeneity concerns from exp_004-006.

Models:
- M1: Baseline contemporaneous (reproduction)
- M2: Simple lagged network (4Q lag)
- M3: Lagged network + current controls
- M4: Fully lagged specification

Usage:
    uv run python experiments/exp_007_temporal_fcr/run_cox.py
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import mlflow
from lifelines import CoxTimeVaryingFitter

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader
from mlflow_utils.tracking import setup_experiment

def prepare_cox_data(df, use_lagged_network=False, fully_lagged=False):
    """
    Prepare data for Cox time-varying analysis following exp_004 pattern.
    
    Args:
        df: DataFrame from QuarterlyWindowDataLoader
        use_lagged_network: Use network_{t-4} instead of network_t
        fully_lagged: Use all variables from t-4 (not implemented yet)
    
    Returns:
        DataFrame ready for CoxTimeVaryingFitter
    """
    print(f"\nPreparing Cox data (lagged_network={use_lagged_network}, fully_lagged={fully_lagged})...")
    
    df_cox = df.copy()
    
    # Convert dates (following exp_004 line 51-54)
    df_cox['date'] = pd.to_datetime(df_cox['DT'])
    df_cox = df_cox.sort_values(by=['regn', 'date'])
    
    # Time intervals (following exp_004 line 57-62)
    df_cox['start'] = df_cox['date']
    df_cox['stop'] = df_cox.groupby('regn')['date'].shift(-1)
    
    # Fill last stop interval
    mask_last = df_cox['stop'].isna()
    df_cox.loc[mask_last, 'stop'] = df_cox.loc[mask_last, 'start'] + pd.Timedelta(days=30)
    
    # Time since registration (following exp_004 line 70-74)
    min_dates = df_cox.groupby('regn')['date'].transform('min')
    df_cox['registration_date'] = min_dates  # Simplified since we don't have actual registration_date
    
    df_cox['start_t'] = (df_cox['start'] - df_cox['registration_date']).dt.days
    df_cox['stop_t'] = (df_cox['stop'] - df_cox['registration_date']).dt.days
    
    # Filter valid intervals (following exp_004 line 76)
    df_cox = df_cox[df_cox['stop_t'] > df_cox['start_t']]
    
    # Define features matching exp_006 specification
    if use_lagged_network:
        # Use lagged network metrics (t-4 quarters)
        network_features = [
            'rw_page_rank_4q_lag',
            'rw_out_degree_4q_lag'
        ]
    else:
        # Contemporaneous (would use current rw_ metrics if available)
        network_features = []
    
    # CAMEL ratios (from accounting data)
    camel_features = [
        'camel_roa',
        'camel_npl_ratio',
        'camel_tier1_capital_ratio'
    ]
    
    # Family and foreign features (from Neo4j)
    family_foreign_features = [
        'family_connection_ratio_temporal',
        'foreign_FEC_d'
    ]
    
    # Combine all features
    all_features = network_features + camel_features + family_foreign_features
    
    # Filter to available columns
    feature_cols = [c for c in all_features if c in df_cox.columns]
    
    # Fill NaN with 0 (following exp_004 line 108)
    df_cox[feature_cols] = df_cox[feature_cols].fillna(0)
    
    # Drop constant columns (following exp_004 line 111-116)
    final_feats = []
    for col in feature_cols:
        if df_cox[col].nunique() > 1:
            final_feats.append(col)
        else:
            print(f"  Dropping constant column: {col}")
    
    # ===== STANDARDIZE VARIABLES (0-100 SCALE) ===== (following exp_006 line 228-238)
    if len(final_feats) > 0:
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        df_cox[final_feats] = scaler.fit_transform(df_cox[final_feats])
        # Scale to 0-100 range
        for col in final_feats:
            min_val = df_cox[col].min()
            max_val = df_cox[col].max()
            if max_val > min_val:
                df_cox[col] = 100 * (df_cox[col] - min_val) / (max_val - min_val)
        
        print(f"  ✅ Scaled {len(final_feats)} features to 0-100 range using StandardScaler")
    
    # Keep necessary columns
    keep_cols = ['regn', 'start_t', 'stop_t', 'event'] + final_feats
    df_cox = df_cox[keep_cols].copy()
    
    print(f"  Prepared {len(df_cox):,} observations")
    print(f"  Features: {final_feats}")
    print(f"  Unique banks: {df_cox['regn'].nunique()}")
    print(f"  Events: {df_cox['event'].sum()} ({100*df_cox['event'].mean():.1f}%)")
    
    return df_cox, final_feats

def run_model(model_name, df_cox, features, **kwargs):
    """
    Run a single Cox model and log to MLflow.
    
    Args:
        model_name: Name for MLflow run
        df_cox: Prepared Cox data
        features: List of feature column names
        **kwargs: Additional parameters to log
    """
    print(f"\n{'='*70}")
    print(f"Running: {model_name}")
    print(f"{'='*70}")
    
    with mlflow.start_run(run_name=model_name):
        # Log parameters
        mlflow.log_param("model_type", "CoxTimeVarying")
        mlflow.log_param("n_observations", len(df_cox))
        mlflow.log_param("n_banks", df_cox['regn'].nunique())
        mlflow.log_param("n_features", len(features))
        mlflow.log_param("features", ", ".join(features))
        mlflow.log_param("n_events", df_cox['event'].sum())
        
        for key, value in kwargs.items():
            mlflow.log_param(key, value)
        
        # Build formula
        formula = " + ".join(features)
        
        print(f"\nFormula: event ~ {formula}")
        print(f"Features: {features}")
        print(f"Training observations: {len(df_cox):,}")
        print(f"Events: {df_cox['event'].sum()} ({100*df_cox['event'].mean():.1f}%)")
        
        # Fit model (following exp_004 line 124-126)
        try:
            from lifelines import CoxTimeVaryingFitter
            from lifelines.utils import concordance_index
            from visualisations.cox_stargazer_new import create_single_column_stargazer, create_single_column_stargazer_hr
            from visualisations.cox_interpretation import generate_interpretation_report
            
            ctv = CoxTimeVaryingFitter(penalizer=0.01, l1_ratio=0.0)
            ctv.fit(df_cox, id_col='regn', event_col='event', 
                   start_col='start_t', stop_col='stop_t', show_progress=True)
            
            print("\n✅ Model converged successfully!")
            
            # Log Summary Metrics (following exp_004 line 130-141)
            mlflow.log_metric("log_likelihood", ctv.log_likelihood_)
            mlflow.log_metric("aic_partial", ctv.AIC_partial_)
            
            # C-index
            try:
                predicted_hazards = ctv.predict_partial_hazard(df_cox)
                c_idx = concordance_index(df_cox['stop_t'], -predicted_hazards, df_cox['event'])
                mlflow.log_metric("c_index", c_idx)
                print(f"C-index: {c_idx:.4f}")
            except Exception as e:
                print(f"C-index calculation failed: {e}")
                c_idx = None
            
            # Log Coefficients & p-values (following exp_004 line 144-148)
            summary_df = ctv.summary
            for var_name, row in summary_df.iterrows():
                p_val = row.get("p") if "p" in row else row.get("p-value")
                if p_val is not None:
                    mlflow.log_metric(f"pval_{var_name}", p_val)
            
            # Generate Artifacts (following exp_004 line 150-167)
            n_subjects = df_cox['regn'].nunique()
            
            # Stargazer CSV (Coefficients)
            stg_df = create_single_column_stargazer(ctv, c_index=c_idx, n_subjects=n_subjects)
            stg_df.to_csv("stargazer_column.csv", index=True)
            mlflow.log_artifact("stargazer_column.csv")
            print("  ✅ Generated stargazer_column.csv")
            
            # Stargazer CSV (Hazard Ratios)
            hr_df = create_single_column_stargazer_hr(ctv, c_index=c_idx, n_subjects=n_subjects)
            hr_df.to_csv("stargazer_hr_column.csv", index=True)
            mlflow.log_artifact("stargazer_hr_column.csv")
            print("  ✅ Generated stargazer_hr_column.csv")
            
            # Interpretation Report
            interp_md = generate_interpretation_report(ctv, model_name=model_name)
            with open("interpretation.md", "w") as f:
                f.write(interp_md)
            mlflow.log_artifact("interpretation.md")
            print("  ✅ Generated interpretation.md")
            
            # Print summary
            print(f"\nModel Summary:")
            print(ctv.summary)
            
            return ctv
            
        except Exception as e:
            print(f"\n❌ Model failed: {e}")
            mlflow.log_param("status", "failed")
            mlflow.log_param("error", str(e))
            import traceback
            traceback.print_exc()
            return None

def main():
    print("="*70)
    print("EXP_007: LAGGED NETWORK EFFECTS")
    print("="*70)
    
    # Set up MLflow experiment
    setup_experiment("exp_007_temporal_fcr")
    
    # Set up GDS client for regn_cbr mapping and CAMEL merge
    print("\n1. Connecting to Neo4j...")
    from graphdatascience import GraphDataScience
    from dotenv import load_dotenv
    
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    gds = GraphDataScience(uri, auth=(user, password))
    print(f"   Connected to: {uri}")
    
    # Load data with 2-period biannual lag
    print("\n2. Loading temporal FCR data with 2-period biannual lag...")
    print("   Note: lag_periods=2 means 4-year lag (2 × 2-year periods)")
    loader = TemporalFCRLoader(gds_client=gds)
    df = loader.load_with_lags(lag_periods=2, start_year=2014, end_year=2020, merge_camel=True)
    
    print(f"\n✅ Loaded {len(df):,} observations")
    print(f"   Unique banks: {df['regn'].nunique()}")
    print(f"   Date range: {df['DT'].min()} to {df['DT'].max()}")
    
    # Add foreign_FEC_d if not present (set to 0 for now)
    if 'foreign_FEC_d' not in df.columns:
        df['foreign_FEC_d'] = 0
        print("   Added foreign_FEC_d (set to 0 - foreign ownership data not in temporal FCR)")
    
    # Model 2: Simple Lagged Network (Primary specification)
    print("\n3. Running Model 2: Simple Lagged Network with Temporal FCR...")
    df_cox_m2, features_m2 = prepare_cox_data(df, use_lagged_network=True)
    
    model_m2 = run_model(
        "M2: Simple Lagged Network (t-4Q)",
        df_cox_m2,
        features_m2,
        lag_periods=2,
        specification="lagged_network_simple"
    )
    
    print(f"\n{'='*70}")
    print("EXP_007 COMPLETE")
    print(f"{'='*70}")
    print(f"\nMLflow UI: {mlflow.get_tracking_uri()}")
    print(f"Check experiment: exp_007_temporal_fcr")

if __name__ == '__main__':
    main()
