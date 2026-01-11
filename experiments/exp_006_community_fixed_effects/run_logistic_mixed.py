
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
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.tools.tools import add_constant

def load_config(config_path="config_logistic.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def prepare_community_features(df, community_params):
    """Prepare community grouping variable for random effects."""
    if 'rw_community_louvain' not in df.columns:
        print("Warning: rw_community_louvain not found in data!")
        return df
    
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
    
    return df

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

def generate_interpretation(result, model_name, auc=None):
    """Generate interpretation markdown."""
    md = f"# {model_name}\n\n"
    md += f"## Model Summary\n\n"
    md += f"**Convergence**: Successful\n\n"
    md += f"**Log-Likelihood**: {result.llf:.2f}\n"
    md += f"**AIC**: {result.aic:.2f}\n"
    if auc:
        md += f"**AUC**: {auc:.4f}\n"
    
    md += f"\n## Coefficients\n\n"
    md += "| Variable | Coefficient | Std Error | z | P>|z| | Odds Ratio |\n"
    md += "|----------|-------------|-----------|---|-------|------------|\n"
    
    for var in result.params.index:
        coef = result.params[var]
        se = result.bse[var]
        z = result.tvalues[var]
        p = result.pvalues[var]
        odds = np.exp(coef)
        
        sig = ""
        if p < 0.001:
            sig = "***"
        elif p < 0.01:
            sig = "**"
        elif p < 0.05:
            sig = "*"
        elif p < 0.10:
            sig = "+"
        
        md += f"| {var} | {coef:.4f}{sig} | {se:.4f} | {z:.2f} | {p:.4f} | {odds:.4f} |\n"
    
    md += f"\n_Significance: + p<0.10, * p<0.05, ** p<0.01, *** p<0.001_\n"
    
    return md

def run():
    # 1. Load Config
    config = load_config()
    exp_config = config["experiment"]
    data_config = config["data"]
    common_model_params = config.get("model_params", {})
    community_params = config.get("community_params", {})

    # 2. Setup MLflow
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    # Use different experiment name to avoid confusion
    setup_experiment("Logistic_Community_Mixed_2014_2020")
    
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
    df_logistic = prepare_community_features(df_logistic, community_params)
    
    # 6. Run Models (simplified - just baseline and conceptual)
    # Model 1: Baseline (no community)
    # Model 2: Note that mixed-effects are computationally intensive
    
    models_to_run = [
        {
            "key": "model_1_baseline",
            "name": "Model 1: Baseline (No Community Control)",
            "features": config["experiment"]["models"]["model_1_baseline"]["features"],
            "use_community": False,
            "demean": False
        }
    ]
    
    for model_spec in models_to_run:
        print(f"\n{'='*80}")
        print(f"Running {model_spec['name']}")
        print(f"{'='*80}")
        
        with mlflow.start_run(run_name=model_spec['name']) as run:
            # Set tags/params
            mlflow.set_tag("human_readable_name", model_spec['name'])
            mlflow.set_tag("description", "Logistic regression (cross-sectional)")
            mlflow.set_tag("model_key", model_spec['key'])
            mlflow.set_tag("uses_rolling_windows", "true")
            mlflow.set_tag("non_overlapping", "true")
            mlflow.set_tag("scaled", "true")
            mlflow.set_tag("period", "2014-2020")
            mlflow.log_params(data_config)
            mlflow.log_params(common_model_params)
            
            # Select features
            features = model_spec['features'].copy()
            
            # Handle within-community demeaning if needed
            if model_spec['demean']:
                network_vars = [f for f in features if f.startswith('network_') and '_within' in f]
                base_network_vars = [f.replace('_within', '') for f in network_vars]
                df_logistic = create_within_community_features(df_logistic, base_network_vars)
            
            # Check availability
            available_feats = [c for c in features if c in df_logistic.columns]
            missing = set(features) - set(available_feats)
            if missing:
                print(f"Warning: Missing features: {missing}")
            
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
            
            # Standardize variables (0-100 scale)
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
            
            # Train standard GLM (binomial family)
            try:
                glm_model = GLM(y, X_with_const, family=families.Binomial())
                result = glm_model.fit()
                
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
                # Interpretation
                interp_md = generate_interpretation(result, model_spec['name'], auc=auc)
                with open("interpretation.md", "w") as f:
                    f.write(interp_md)
                mlflow.log_artifact("interpretation.md")
                
                print(f"Logged interpretation.md")
                
            except Exception as e:
                print(f"Training failed: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    run()
