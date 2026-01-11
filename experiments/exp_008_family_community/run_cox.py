"""
exp_008: Family Connection Ratio with Community Stratification

Examines family connection ratio (FCR) effects on bank survival with 
Louvain community control using quarterly lagged network data.

Combines:
- exp_007: Quarterly lagged network infrastructure
- exp_006: Community stratification methodology  
- Focus: Family metrics, state/foreign ownership
"""

import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
from lifelines import CoxTimeVaryingFitter
from lifelines.utils import concordance_index
from visualisations.cox_stargazer_new import create_single_column_stargazer, create_single_column_stargazer_hr
from visualisations.cox_interpretation import generate_interpretation_report
from sklearn.preprocessing import StandardScaler

def load_config(config_path="config_cox.yaml"):
    """Load experiment configuration."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def collapse_small_communities(df, community_col='rw_community_louvain_4q_lag', min_size=5):
    """
    Collapse communities with fewer than min_size members into 'other' category.
    
    Args:
        df: DataFrame with community column
        community_col: Name of community column
        min_size: Minimum community size
        
    Returns:
        DataFrame with 'community_collapsed' column
    """
    if community_col not in df.columns:
        print(f"Warning: {community_col} not found, creating dummy community")
        df['community_collapsed'] = 0
        return df
    
    # Extract scalar from hierarchical Louvain (array) - use coarsest level
    print(f"\nProcessing Louvain communities...")
    
    def extract_coarsest(val):
        """Extract coarsest level from hierarchical Louvain array."""
        # Check if it's an array first
        if isinstance(val, (list, np.ndarray)):
            if len(val) > 0:
                return float(val[0])
            else:
                return -1.0
        # Check for None/NaN
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return -1.0
        # Scalar value
        try:
            return float(val)
        except (ValueError, TypeError):
            return -1.0
    
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
    n_small = len(small_communities)
    
    print(f"  Original communities: {n_original}")
    print(f"  Small communities (<{min_size} banks): {n_small}")
    print(f"  Final communities: {n_collapsed}")
    
    return df

def aggregate_temporal_communities(df, community_col='community_collapsed'):
    """
    Assign each bank its most frequent community across time.
    
    Args:
        df: DataFrame with temporal community assignments
        community_col: Community column name
        
    Returns:
        DataFrame with stable community assignments
    """
    if community_col not in df.columns:
        return df
    
    print(f"\nAggregating temporal communities...")
    
    # Get most frequent community per bank
    bank_stable_community = (
        df[df[community_col].notna()]
        .groupby('regn')[community_col]
        .agg(lambda x: x.value_counts().index[0] if len(x) > 0 else -1)
    )
    
    # Map all observations to stable community
    df[community_col] = df['regn'].map(bank_stable_community)
    
    n_communities = df[community_col].nunique()
    print(f"  Stable bank communities: {n_communities}")
    
    return df

def prepare_cox_data(df, features, use_lagged_network=True, stratify_by_community=False):
    """
    Prepare data for Cox time-varying analysis following exp_007 pattern.
    
    Args:
        df: DataFrame from QuarterlyWindowDataLoader
        features: List of feature names to include
        use_lagged_network: Whether lagged network metrics are included
        stratify_by_community: Whether to stratify by community
    
    Returns:
        Tuple of (df_cox, final_features)
    """
    print(f"\nPreparing Cox data (stratify={stratify_by_community})...")
    
    df_cox = df.copy()
    
    # Convert dates (exp_004 pattern)
    df_cox['date'] = pd.to_datetime(df_cox['DT'])
    df_cox = df_cox.sort_values(by=['regn', 'date'])
    
    # Time intervals
    df_cox['start'] = df_cox['date']
    df_cox['stop'] = df_cox.groupby('regn')['date'].shift(-1)
    
    # Fill last stop interval
    mask_last = df_cox['stop'].isna()
    df_cox.loc[mask_last, 'stop'] = df_cox.loc[mask_last, 'start'] + pd.Timedelta(days=30)
    
    # Time since registration
    min_dates = df_cox.groupby('regn')['date'].transform('min')
    df_cox['registration_date'] = min_dates
    
    df_cox['start_t'] = (df_cox['start'] - df_cox['registration_date']).dt.days
    df_cox['stop_t'] = (df_cox['stop'] - df_cox['registration_date']).dt.days
    
    # Filter valid intervals
    df_cox = df_cox[df_cox['stop_t'] > df_cox['start_t']]
    
    # Filter to available features
    feature_cols = [c for c in features if c in df_cox.columns]
    missing = set(features) - set(feature_cols)
    if missing:
        print(f"  Warning: Missing features: {missing}")
    
    # Fill NaN with 0
    df_cox[feature_cols] = df_cox[feature_cols].fillna(0)
    
    # Drop constant columns
    final_feats = []
    for col in feature_cols:
        if df_cox[col].nunique() > 1:
            final_feats.append(col)
        else:
            print(f"  Dropping constant column: {col}")
    
    # StandardScaler normalization (0-100 range) - from exp_007
    if len(final_feats) > 0:
        scaler = StandardScaler()
        df_cox[final_feats] = scaler.fit_transform(df_cox[final_feats])
        # Scale to 0-100 range
        for col in final_feats:
            min_val = df_cox[col].min()
            max_val = df_cox[col].max()
            if max_val > min_val:
                df_cox[col] = 100 * (df_cox[col] - min_val) / (max_val - min_val)
        
        print(f"  ✅ Scaled {len(final_feats)} features to 0-100 range")
    
    # Keep necessary columns
    keep_cols = ['regn', 'start_t', 'stop_t', 'event'] + final_feats
    if stratify_by_community and 'community_collapsed' in df_cox.columns:
        keep_cols.append('community_collapsed')
    
    df_cox = df_cox[keep_cols].copy()
    
    print(f"  Prepared {len(df_cox):,} observations")
    print(f"  Features: {final_feats}")
    print(f"  Unique banks: {df_cox['regn'].nunique()}")
    print(f"  Events: {df_cox['event'].sum()} ({100*df_cox['event'].mean():.1f}%)")
    
    return df_cox, final_feats

def run_model(model_name, df_cox, features, stratify=False, **kwargs):
    """
    Run a single Cox model and log to MLflow.
    
    Args:
        model_name: Name for MLflow run
        df_cox: Prepared Cox data
        features: List of feature column names
        stratify: Whether to stratify by community
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
        mlflow.log_param("stratify_by_community", stratify)
        
        if stratify and 'community_collapsed' in df_cox.columns:
            mlflow.log_param("n_communities", df_cox['community_collapsed'].nunique())
        
        for key, value in kwargs.items():
            mlflow.log_param(key, value)
        
        # Build formula
        formula = " + ".join(features)
        
        print(f"\nFormula: event ~ {formula}")
        if stratify:
            print(f"Stratified by: community_collapsed")
        print(f"Training observations: {len(df_cox):,}")
        print(f"Events: {df_cox['event'].sum()} ({100*df_cox['event'].mean():.1f}%)")
        
        # Fit model
        try:
            ctv = CoxTimeVaryingFitter(penalizer=0.01, l1_ratio=0.0)
            
            if stratify and 'community_collapsed' in df_cox.columns:
                ctv.fit(df_cox, id_col='regn', event_col='event', 
                       start_col='start_t', stop_col='stop_t',
                       strata=['community_collapsed'], show_progress=True)
            else:
                ctv.fit(df_cox, id_col='regn', event_col='event', 
                       start_col='start_t', stop_col='stop_t', show_progress=True)
            
            print("\n✅ Model converged successfully!")
            
            # Log metrics
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
            
            # Log coefficients & p-values
            summary_df = ctv.summary
            for var_name, row in summary_df.iterrows():
                p_val = row.get("p") if "p" in row else row.get("p-value")
                if p_val is not None:
                    mlflow.log_metric(f"pval_{var_name}", p_val)
            
            # Generate artifacts
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
    """Main execution function."""
    print("="*70)
    print("EXP_008: FAMILY CONNECTION RATIO WITH COMMUNITY STRATIFICATION")
    print("="*70)
    
    # 1. Load Config
    config = load_config()
    exp_config = config["experiment"]
    data_config = config["data"]
    model_params = config["model_params"]
    community_params = config.get("community_params", {})
    
    # 2. Setup MLflow
    setup_experiment(exp_config["name"])
    
    print(f"\nExperiment: {exp_config['human_readable_name']}")
    print(f"Description: {exp_config['description']}")
    
    # 3. Load Data with Quarterly Lags
    print(f"\n1. Loading data with {data_config['lag_quarters']}-quarter lag...")
    
    loader = QuarterlyWindowDataLoader()
    df = loader.load_with_lags(
        lag_quarters=data_config['lag_quarters'],
        start_year=data_config['start_year'],
        end_year=data_config['end_year']
    )
    
    print(f"\n✅ Loaded {len(df):,} observations")
    print(f"   Unique banks: {df['regn'].nunique():,}")
    print(f"   Date range: {df['DT'].min()} to {df['DT'].max()}")
    
    # 4. Process Communities
    print(f"\n2. Processing communities...")
    
    # Collapse small communities
    df = collapse_small_communities(
        df, 
        min_size=community_params.get('min_community_size', 5)
    )
    
    # Aggregate to stable communities
    df = aggregate_temporal_communities(df)
    
    # 5. Iterate Over Models
    models_dict = exp_config["models"]
    
    for model_key, model_cfg in models_dict.items():
        print(f"\n{'='*70}")
        print(f"3. Running {model_cfg['name']}...")
        print(f"{'='*70}")
        
        # Prepare data
        df_cox, features = prepare_cox_data(
            df,
            features=model_cfg['features'],
            stratify_by_community=model_cfg.get('stratify_by_community', False)
        )
        
        # Run model
        run_model(
            model_name=model_cfg['name'],
            df_cox=df_cox,
            features=features,
            stratify=model_cfg.get('stratify_by_community', False),
            model_key=model_key,
            lag_quarters=data_config['lag_quarters']
        )
    
    print(f"\n{'='*70}")
    print("EXP_008 COMPLETE")
    print(f"{'='*70}")
    print(f"\nMLflow UI: {mlflow.get_tracking_uri()}")
    print(f"Check experiment: {exp_config['name']}")

if __name__ == '__main__':
    main()
