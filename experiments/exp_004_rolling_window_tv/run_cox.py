
import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np

# Add project root to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.rolling_window_loader import RollingWindowDataLoader
from lifelines import CoxTimeVaryingFitter
from lifelines.utils import concordance_index
from visualisations.cox_stargazer_new import create_single_column_stargazer, create_single_column_stargazer_hr
from visualisations.cox_interpretation import generate_interpretation_report

def load_config(config_path="config_cox.yaml"):
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

    # 4. Preprocessing for CoxTimeVarying
    print("Preprocessing for CoxTimeVarying...")
    df = banks_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    for col in ['death_date', 'registration_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df = df.sort_values(by=['regn', 'date'])
    df['start'] = df['date']
    df['stop'] = df.groupby('regn')['date'].shift(-1)
    
    # Fill last stop
    mask_last = df['stop'].isna()
    df.loc[mask_last, 'stop'] = df.loc[mask_last, 'start'] + pd.Timedelta(days=30)
    
    # Events
    df['event'] = 0
    dead_banks = df[df['is_dead'] == True]['regn'].unique()
    df.loc[mask_last & df['regn'].isin(dead_banks), 'event'] = 1
    
    # Time intervals
    min_dates = df.groupby('regn')['date'].transform('min')
    df['registration_date'] = df['registration_date'].fillna(min_dates)
    
    df['start_t'] = (df['start'] - df['registration_date']).dt.days
    df['stop_t'] = (df['stop'] - df['registration_date']).dt.days
    
    df = df[df['stop_t'] > df['start_t']]
    
    print(f"Prepared {len(df)} time-varying observations")
    print(f"Total events: {df['event'].sum()}")
    print(f"Number of subjects: {df['regn'].nunique()}")
    
    # 5. Iterate Models
    models_dict = exp_config["models"]
    
    for model_key, model_cfg in models_dict.items():
        print(f"\n--- Running {model_cfg['name']} ---")
        
        with mlflow.start_run(run_name=model_cfg['name']) as run:
            # Set tags/params
            mlflow.set_tag("human_readable_name", model_cfg['name'])
            mlflow.set_tag("description", exp_config.get("description", ""))
            mlflow.set_tag("model_key", model_key)
            mlflow.set_tag("uses_rolling_windows", "true")
            mlflow.log_params(data_config)
            mlflow.log_params(common_model_params)
            
            # Select features
            features = model_cfg['features']
            
            # Check availability
            available_feats = [c for c in features if c in df.columns]
            missing = set(features) - set(available_feats)
            if missing:
                print(f"Warning: Missing features for {model_key}: {missing}")
            
            # Prepare Training Data
            model_df = df.copy()
            model_df[available_feats] = model_df[available_feats].fillna(0)
            
            # Drop constant columns
            final_feats = []
            for col in available_feats:
                if model_df[col].nunique() > 1:
                    final_feats.append(col)
                else:
                    print(f"Dropping constant column: {col}")
            
            final_cols = ['regn', 'start_t', 'stop_t', 'event'] + final_feats
            df_train = model_df[final_cols]
            
            print(f"Training shape: {df_train.shape} with {len(final_feats)} covariates.")
            
            # Train
            ctv = CoxTimeVaryingFitter(**common_model_params)
            try:
                ctv.fit(df_train, id_col="regn", event_col="event", start_col="start_t", stop_col="stop_t", show_progress=True)
                print("Converged.")
                
                # Log Summary Metrics
                mlflow.log_metric("log_likelihood", ctv.log_likelihood_)
                mlflow.log_metric("aic_partial", ctv.AIC_partial_)
                
                # C-index
                try:
                    predicted_hazards = ctv.predict_partial_hazard(df_train)
                    c_idx = concordance_index(df_train['stop_t'], -predicted_hazards, df_train['event'])
                    mlflow.log_metric("c_index", c_idx)
                    print(f"C-index: {c_idx:.4f}")
                except Exception as e:
                    print(f"C-idx failed: {e}")
                    c_idx = None

                # Log Coefficients & Details
                summary_df = ctv.summary
                for var_name, row in summary_df.iterrows():
                    p_val = row.get("p") if "p" in row else row.get("p-value")
                    if p_val is not None:
                        mlflow.log_metric(f"pval_{var_name}", p_val)
                
                # Artifacts
                n_subjects = df_train['regn'].nunique()
                
                # Stargazer CSV (Coef)
                stg_df = create_single_column_stargazer(ctv, c_index=c_idx, n_subjects=n_subjects)
                stg_df.to_csv("stargazer_column.csv", index=True)
                mlflow.log_artifact("stargazer_column.csv")
                
                # Stargazer CSV (HR)
                hr_df = create_single_column_stargazer_hr(ctv, c_index=c_idx, n_subjects=n_subjects)
                hr_df.to_csv("stargazer_hr_column.csv", index=True)
                mlflow.log_artifact("stargazer_hr_column.csv")
                
                # Interpretation
                interp_md = generate_interpretation_report(ctv, model_name=model_cfg['name'])
                with open("interpretation.md", "w") as f:
                    f.write(interp_md)
                mlflow.log_artifact("interpretation.md")
                
            except Exception as e:
                print(f"Training failed for {model_key}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    run()
