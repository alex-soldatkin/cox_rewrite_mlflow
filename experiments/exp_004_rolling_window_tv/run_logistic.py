
import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np
import statsmodels.api as sm

# Add project root to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.rolling_window_loader import RollingWindowDataLoader
from visualisations.logistic_stargazer import create_single_column_logistic_stargazer, create_single_column_logistic_stargazer_odds
from visualisations.logistic_interpretation import generate_logistic_interpretation_report

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
    setup_experiment(exp_config["name"])
    
    # 3. Load Data with Rolling Window Features
    print("Loading data with rolling window network metrics...")
    loader = RollingWindowDataLoader()
    start_date = f"{data_config['start_year']}-01-01"
    end_date = f"{data_config['end_year']}-12-31"
    
    banks_df = loader.load_training_data_with_rolling_windows(start_date=start_date, end_date=end_date)
    print(f"Loaded {len(banks_df)} rows of merged data with rolling window features.")
    
    if banks_df.empty:
        print("No data loaded. Exiting.")
        return

    # 4. Preprocessing for Pooled Logistic
    print("Preprocessing for Pooled Logistic...")
    df = banks_df.copy()
    
    # Ensure date/time columns
    df['date'] = pd.to_datetime(df['date'])
    for col in ['death_date', 'registration_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    df = df.sort_values(by=['regn', 'date'])
    
    # Define Target: Event = 1 only at failure observation
    df['event'] = 0
    
    # Identify dead banks
    dead_mask = df['is_dead'] == True
    dead_regns = df.loc[dead_mask, 'regn'].unique()
    
    # Vectorized 'last row' mask
    df['next_regn'] = df['regn'].shift(-1)
    is_last_observation = df['regn'] != df['next_regn']
    
    # Set event=1 if bank is dead AND it is the last observation
    df.loc[df['regn'].isin(dead_regns) & is_last_observation, 'event'] = 1
    
    print(f"Total Events created: {df['event'].sum()}")
    print(f"Number of subjects: {df['regn'].nunique()}")

    # 5. Iterate Models
    models_dict = exp_config["models"]
    
    for model_key, model_cfg in models_dict.items():
        print(f"\n--- Running {model_cfg['name']} ---")
        
        with mlflow.start_run(run_name=model_cfg['name']) as run:
            # Metadata
            mlflow.set_tag("human_readable_name", model_cfg['name'])
            mlflow.set_tag("description", exp_config.get("description", ""))
            mlflow.set_tag("model_key", model_key)
            mlflow.set_tag("uses_rolling_windows", "true")
            mlflow.log_params(data_config)
            mlflow.log_params(common_model_params)
            
            features = model_cfg['features']
            
            # Check availability
            available_feats = [c for c in features if c in df.columns]
            missing = set(features) - set(available_feats)
            if missing:
                print(f"Warning: Missing features for {model_key}: {missing}")
                
            # Prepare X and y
            model_df = df.copy()
            model_df[available_feats] = model_df[available_feats].fillna(0)
            
            # Constant check
            final_feats = []
            for col in available_feats:
                if model_df[col].nunique() > 1:
                    final_feats.append(col)
                    
            X = model_df[final_feats]
            y = model_df['event']
            
            # Add constant for statsmodels
            X = sm.add_constant(X)
            
            print(f"Training shape: {X.shape}")
            
            try:
                # Train Logistic Regression
                model = sm.Logit(y, X)
                
                # Fit with clustered SEs
                res = model.fit(method=common_model_params.get('method', 'newton'), 
                                maxiter=common_model_params.get('maxiter', 100), 
                                disp=0,
                                cov_type='cluster',
                                cov_kwds={'groups': model_df['regn']})
                                
                print("Converged.")
                
                # Log Metrics
                mlflow.log_metric("log_likelihood", res.llf)
                mlflow.log_metric("aic", res.aic)
                mlflow.log_metric("bic", res.bic)
                
                # Classification Metrics
                y_pred_prob = res.predict(X)
                y_pred = (y_pred_prob >= 0.5).astype(int)
                
                from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
                
                acc = accuracy_score(y, y_pred)
                prec = precision_score(y, y_pred, zero_division=0)
                rec = recall_score(y, y_pred, zero_division=0)
                f1 = f1_score(y, y_pred, zero_division=0)
                try:
                    auc = roc_auc_score(y, y_pred_prob)
                except:
                    auc = None

                mlflow.log_metric("accuracy", acc)
                mlflow.log_metric("precision", prec)
                mlflow.log_metric("recall", rec)
                mlflow.log_metric("f1_score", f1)
                if auc: mlflow.log_metric("auc", auc)
                
                print(f"Acc: {acc:.3f}, F1: {f1:.3f}, AUC: {auc:.3f}" if auc else f"Acc: {acc:.3f}, F1: {f1:.3f}, AUC: N/A")

                # Artifacts
                n_subjects = model_df['regn'].nunique()
                
                # Stargazer CSV (Coef)
                stg_df = create_single_column_logistic_stargazer(res, y, y_pred_prob, 
                                                                 model_name=model_cfg['name'], 
                                                                 n_subjects=n_subjects)
                stg_df.to_csv("stargazer_column.csv", index=True)
                mlflow.log_artifact("stargazer_column.csv")
                
                # Stargazer CSV (Odds Ratios)
                or_df = create_single_column_logistic_stargazer_odds(res, y, y_pred_prob,
                                                                     model_name=model_cfg['name'],
                                                                     n_subjects=n_subjects)
                or_df.to_csv("stargazer_hr_column.csv", index=True)
                mlflow.log_artifact("stargazer_hr_column.csv")
                
                # Interpretation Report
                report = generate_logistic_interpretation_report(res, model_name=model_cfg['name'])
                with open("interpretation.md", "w") as f:
                    f.write(report)
                mlflow.log_artifact("interpretation.md")
                
            except Exception as e:
                print(f"Training failed: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    run()
