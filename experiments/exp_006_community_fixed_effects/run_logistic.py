
import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.rolling_window_loader import RollingWindowDataLoader
from statsmodels.discrete.discrete_model import Logit
from statsmodels.tools.tools import add_constant
from visualisations.logistic_stargazer import create_single_column_logistic_stargazer, create_single_column_logistic_stargazer_odds
# from visualisations.logistic_interpretation import generate_logistic_interpretation  # Not available

def load_config(config_path="config_logistic.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def prepare_community_features(df, community_params):
    """Prepare community fixed effects indicators."""
    if 'rw_community_louvain' not in df.columns:
        print("Warning: rw_community_louvain not found in data!")
        return df, []
    
    # Check community distribution
    community_counts = df['rw_community_louvain'].value_counts()
    print(f"\nCommunity distribution:")
    print(f"  Unique communities: {df['rw_community_louvain'].nunique()}")
    print(f"  Largest community: {community_counts.max()} observations")
    print(f"  Smallest community: {community_counts.min()} observations")
    print(f"  Median community size: {community_counts.median()}")
    
    # Collapse small communities
    min_size = community_params.get('min_community_size', 5)
    small_communities = community_counts[community_counts < min_size].index.tolist()
    
    if small_communities:
        print(f"\nCollapsing {len(small_communities)} communities with < {min_size} observations into 'other'")
        df['community_collapsed'] = df['rw_community_louvain'].apply(
            lambda x: 'missing' if pd.isna(x) else ('other' if x in small_communities else str(int(x)))
        )
    else:
        df['community_collapsed'] = df['rw_community_louvain'].apply(
            lambda x: 'missing' if pd.isna(x) else str(int(x))
        )
    
    # Create dummy variables
    community_dummies = pd.get_dummies(
        df['community_collapsed'], 
        prefix='community',
        drop_first=community_params.get('drop_first', True)
    )
    
    dummy_cols = community_dummies.columns.tolist()
    print(f"\nCreated {len(dummy_cols)} community indicator variables")
    
    # Add to dataframe
    for col in dummy_cols:
        df[col] = community_dummies[col]
    
    return df, dummy_cols

def create_within_community_features(df, network_vars):
    """Demean network variables within communities."""
    if 'community_collapsed' not in df.columns:
        print("Warning: community_collapsed not found, skipping within-community demeaning")
        return df
    
    within_vars = []
    for var in network_vars:
        if var not in df.columns:
            continue
        
        within_var = f"{var}_within"
        df[within_var] = df.groupby('community_collapsed')[var].transform(lambda x: x - x.mean())
        within_vars.append(within_var)
        
        print(f"Created {within_var} (demeaned within communities)")
    
    return df

def run():
    # 1. Load Config
    config = load_config()
    exp_config = config["experiment"]
    data_config = config["data"]
    common_model_params = config.get("model_params", {})
    community_params = config.get("community_params", {})

    # 2. Setup MLflow
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    setup_experiment(exp_config["name"])
    
    # 3. Load Data
    print("Loading data with 2014-2020 non-overlapping rolling window network metrics...")
    
    os.environ["ROLLING_WINDOW_DIR"] = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../../rolling_windows/output/nodes_2014_2020_nonoverlap"
    ))
    
    loader = RollingWindowDataLoader()
    start_date = f"{data_config['start_year']}-01-01"
    end_date = f"{data_config['end_year']}-12-31"
    
    banks_df = loader.load_training_data_with_rolling_windows(start_date=start_date, end_date=end_date)
    print(f"Loaded {len(banks_df)} rows of merged data with rolling window features.")
    
    if banks_df.empty:
        print("No data loaded. Exiting.")
        return

    # 4. Preprocessing for Logistic
    print("Preprocessing for Logistic Regression...")
    df = banks_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Create event variable: take last observation per bank
    df = df.sort_values(by=['regn', 'date'])
    df['is_last'] = df.groupby('regn')['date'].transform(lambda x: x == x.max())
    
    # Filter to last observation per bank
    df_logistic = df[df['is_last']].copy()
    
    # Event = 1 if bank is dead
    df_logistic['event'] = (df_logistic['is_dead'] == True).astype(int)
    
    print(f"Prepared {len(df_logistic)} observations (last observation per bank)")
    print(f"Total events: {df_logistic['event'].sum()}")
    print(f"Event rate: {100*df_logistic['event'].mean():.1f}%")
    
    # 5. Prepare Community Features
    df_logistic, community_dummy_cols = prepare_community_features(df_logistic, community_params)
    
    # 6. Iterate Models
    models_dict = exp_config["models"]
    
    for model_key, model_cfg in models_dict.items():
        print(f"\n{'='*80}")
        print(f"Running {model_cfg['name']}")
        print(f"{'='*80}")
        
        with mlflow.start_run(run_name=model_cfg['name']) as run:
            # Set tags/params
            mlflow.set_tag("human_readable_name", model_cfg['name'])
            mlflow.set_tag("description", exp_config.get("description", ""))
            mlflow.set_tag("model_key", model_key)
            mlflow.set_tag("uses_rolling_windows", "true")
            mlflow.set_tag("non_overlapping", "true")
            mlflow.set_tag("scaled", "true")
            mlflow.set_tag("period", "2014-2020")
            mlflow.set_tag("community_fe", str(model_cfg.get('use_community_fe', False)))
            mlflow.log_params(data_config)
            mlflow.log_params(common_model_params)
            
            # Select features
            features = model_cfg['features'].copy()
            
            # Handle within-community demeaning
            if model_cfg.get('demean_network_vars', False):
                network_vars = [f for f in features if f.startswith('network_') and '_within' in f]
                base_network_vars = [f.replace('_within', '') for f in network_vars]
                df_logistic = create_within_community_features(df_logistic, base_network_vars)
            
            # Add community dummies if requested
            if model_cfg.get('use_community_fe', False):
                features.extend(community_dummy_cols)
                print(f"Adding {len(community_dummy_cols)} community indicator variables")
            
            # Check availability
            available_feats = [c for c in features if c in df_logistic.columns]
            missing = set(features) - set(available_feats)
            if missing:
                print(f"Warning: Missing features for {model_key}: {missing}")
            
            # Prepare Training Data
            model_df = df_logistic.copy()
            model_df[available_feats] = model_df[available_feats].fillna(0)
            
            # Drop constant columns
            final_feats = []
            for col in available_feats:
                if model_df[col].nunique() > 1:
                    final_feats.append(col)
                else:
                    print(f"Dropping constant column: {col}")
            
            # ===== STANDARDIZE VARIABLES (0-100 SCALE) =====
            if len(final_feats) > 0:
                scaler = StandardScaler()
                model_df[final_feats] = scaler.fit_transform(model_df[final_feats])
                # Scale to 0-100 range
                for col in final_feats:
                    min_val = model_df[col].min()
                    max_val = model_df[col].max()
                    if max_val > min_val:
                        model_df[col] = 100 * (model_df[col] - min_val) / (max_val - min_val)
                
                print(f"Scaled {len(final_feats)} features to 0-100 range using StandardScaler")
            
            # Prepare X and y
            X = model_df[final_feats]
            y = model_df['event']
            
            print(f"Training shape: X={X.shape}, y={y.shape}")
            
            # Add intercept
            X_with_const = add_constant(X, has_constant='add')
            
            # Train
            try:
                # Determine clustering
                cluster_by = community_params.get('cluster_se_by', 'community')
                if cluster_by == 'community' and model_cfg.get('use_community_fe', False):
                    groups = model_df['community_collapsed']
                else:
                    groups = model_df['regn']
                
                logit_model = Logit(y, X_with_const)
                result = logit_model.fit(
                    maxiter=common_model_params.get('maxiter', 100),
                    method='bfgs',
                    disp=True
                )
                
                print("Converged.")
                print(result.summary())
                
                # Log Metrics
                mlflow.log_metric("log_likelihood", result.llf)
                mlflow.log_metric("aic", result.aic)
                mlflow.log_metric("bic", result.bic)
                
                # AUC
                try:
                    y_pred_proba = result.predict(X_with_const)
                    auc = roc_auc_score(y, y_pred_proba)
                    mlflow.log_metric("auc", auc)
                    print(f"AUC: {auc:.4f}")
                except Exception as e:
                    print(f"AUC calculation failed: {e}")
                    auc = None
                
                # Log p-values
                for var_name, pval in result.pvalues.items():
                    mlflow.log_metric(f"pval_{var_name}", pval)
                
                # Artifacts
                n_obs = len(y)
                
                # Stargazer CSV (Coef)
                stg_df = create_single_column_logistic_stargazer(result, y, y_pred_proba, model_name=model_cfg['name'], n_subjects=n_obs)
                stg_df.to_csv("stargazer_column.csv", index=True)
                mlflow.log_artifact("stargazer_column.csv")
                
                # Stargazer CSV (OR)
                or_df = create_single_column_logistic_stargazer_odds(result, y, y_pred_proba, model_name=model_cfg['name'], n_subjects=n_obs)
                or_df.to_csv("stargazer_or_column.csv", index=True)
                mlflow.log_artifact("stargazer_or_column.csv")
                
                # Interpretation (function not available, skip)
                # interp_md = generate_logistic_interpretation(result, model_name=model_cfg['name'])
                # with open("interpretation.md", "w") as f:
                #     f.write(interp_md)
                # mlflow.log_artifact("interpretation.md")
                
            except Exception as e:
                print(f"Training failed for {model_key}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    run()
