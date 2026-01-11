
import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.rolling_window_loader import RollingWindowDataLoader
from visualisations.logistic_stargazer import create_single_column_stargazer, create_single_column_stargazer_or
from visualisations.logistic_interpretation import generate_interpretation_report
import statsmodels.api as sm

def load_config(config_path="config_logistic.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def run():
    # 1. Load Config
    config = load_config()
    exp_config = config["experiment"]
    data_config = config["data"]
    common_model_params = config["model_params"]

    # 2. Setup MLflow
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    setup_experiment(exp_config["name"])
    
    # 3. Load Data
    print("Loading data with 2014-2020 non-overlapping rolling window network metrics...")
    
    # Set environment variable to point to non-overlapping 2014-2020 base directory
    # Loader will append "/output/nodes" automatically
    os.environ["ROLLING_WINDOW_DIR"] = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../../rolling_windows/output/nodes_2014_2020_nonoverlap"
    ))
    
    loader = RollingWindowDataLoader()
    start_date = f"{data_config['start_year']}-01-01"
    end_date = f"{data_config['end_year']}-12-31"
    
    banks_df = loader.load_training_data_with_rolling_windows(start_date=start_date, end_date=end_date)
    print(f"Loaded {len(banks_df)} rows of merged data.")
    
    if banks_df.empty:
        print("No data loaded. Exiting.")
        return

    # 4. Preprocessing for Pooled Logistic
    print("Preprocessing for Pooled Logistic...")
    df = banks_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Create forward-looking event indicator
    df = df.sort_values(by=['regn', 'date'])
    df['next_period_exists'] = df.groupby('regn')['date'].shift(-1).notna()
    df['event'] = 0
    
    # Mark events
    dead_banks = df[df['is_dead'] == True]['regn'].unique()
    last_obs_mask = ~df['next_period_exists']
    df.loc[last_obs_mask & df['regn'].isin(dead_banks), 'event'] = 1
    
    print(f"Total Events created: {df['event'].sum()}")
    print(f"Number of subjects: {df['regn'].nunique()}")
    
    # 5. Iterate Models
    models_dict = exp_config["models"]
    
    for model_key, model_cfg in models_dict.items():
        print(f"\n--- Running {model_cfg['name']} ---")
        
        with mlflow.start_run(run_name=model_cfg['name']) as run:
            mlflow.set_tag("human_readable_name", model_cfg['name'])
            mlflow.set_tag("description", exp_config.get("description", ""))
            mlflow.set_tag("model_key", model_key)
            mlflow.set_tag("uses_rolling_windows", "true")
            mlflow.set_tag("non_overlapping", "true")
            mlflow.set_tag("scaled", "true")
            mlflow.set_tag("period", "2014-2020")
            mlflow.log_params(data_config)
            mlflow.log_params(common_model_params)
            
            features = model_cfg['features']
            available_feats = [c for c in features if c in df.columns]
            missing = set(features) - set(available_feats)
            if missing:
                print(f"Warning: Missing features for {model_key}: {missing}")
            
            model_df = df.copy()
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
            
            print(f"Training shape: {model_df.shape}")
            
            # Prepare data
            X = model_df[final_feats]
            y = model_df['event']
            X_with_const = sm.add_constant(X)
            
            # Train with statsmodels for clustered SE
            try:
                logit_model = sm.Logit(y, X_with_const)
                result = logit_model.fit(
                    method=common_model_params.get('method', 'newton'),
                    maxiter=common_model_params.get('maxiter', 100),
                    disp=False
                )
                
                # Use clustered standard errors (grouped by bank)
                result_clustered = result.get_robustcov_results(
                    cov_type='cluster',
                    groups=model_df['regn']
                )
                
                print("Converged.")
                
                # Metrics
                y_pred_proba = result_clustered.predict(X_with_const)
                
                # Find optimal threshold
                if y.sum() > 0:
                    fpr, tpr, thresholds = roc_curve(y, y_pred_proba)
                    optimal_idx = np.argmax(tpr - fpr)
                    optimal_threshold = thresholds[optimal_idx]
                    auc = roc_auc_score(y, y_pred_proba)
                else:
                    optimal_threshold = 0.5
                    auc = None
                
                y_pred = (y_pred_proba >= optimal_threshold).astype(int)
                
                acc = accuracy_score(y, y_pred)
                prec = precision_score(y, y_pred, zero_division=0)
                rec = recall_score(y, y_pred, zero_division=0)
                f1 = f1_score(y, y_pred, zero_division=0)
                
                print(f"Acc: {acc:.3f}, F1: {f1:.3f}, AUC: {auc:.3f}" if auc else f"Acc: {acc:.3f}, F1: {f1:.3f}, AUC: N/A")
                
                # Log metrics
                mlflow.log_metric("log_likelihood", result_clustered.llf)
                mlflow.log_metric("aic", result_clustered.aic)
                if auc:
                    mlflow.log_metric("auc", auc)
                mlflow.log_metric("accuracy", acc)
                mlflow.log_metric("precision", prec)
                mlflow.log_metric("recall", rec)
                mlflow.log_metric("f1_score", f1)
                mlflow.log_metric("optimal_threshold", optimal_threshold)
                
                # Log p-values
                for var_name, p_val in result_clustered.pvalues.items():
                    if var_name != 'const':
                        mlflow.log_metric(f"pval_{var_name}", p_val)
                
                # Artifacts
                n_subjects = model_df['regn'].nunique()
                n_events = int(y.sum())
                
                # Stargazer CSV (Coef)
                stg_df = create_single_column_stargazer(
                    result_clustered, 
                    model_name=model_cfg['name'],
                    n_obs=len(y),
                    n_subjects=n_subjects,
                    n_events=n_events,
                    auc=auc,
                    optimal_threshold=optimal_threshold,
                    accuracy=acc,
                    precision=prec,
                    recall=rec,
                    f1_score=f1
                )
                stg_df.to_csv("stargazer_column.csv", index=True)
                mlflow.log_artifact("stargazer_column.csv")
                
                # Stargazer CSV (OR)
                or_df = create_single_column_stargazer_or(
                    result_clustered,
                    model_name=model_cfg['name'],
                    n_obs=len(y),
                    n_subjects=n_subjects,
                    n_events=n_events,
                    auc=auc,
                    optimal_threshold=optimal_threshold,
                    accuracy=acc,
                    precision=prec,
                    recall=rec,
                    f1_score=f1
                )
                or_df.to_csv("stargazer_hr_column.csv", index=True)
                mlflow.log_artifact("stargazer_hr_column.csv")
                
                # Interpretation
                interp_md = generate_interpretation_report(result_clustered, model_name=model_cfg['name'])
                with open("interpretation.md", "w") as f:
                    f.write(interp_md)
                mlflow.log_artifact("interpretation.md")
                
            except Exception as e:
                print(f"Training failed for {model_key}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    run()
