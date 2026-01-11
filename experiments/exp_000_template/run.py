
import yaml
import mlflow
import sys
import os
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Add project root to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment, log_pydantic_params, log_metrics_classification, log_metrics_survival
from mlflow_utils.loader import ExperimentDataLoader

def load_config(config_path="config.yaml"):
    # Resolve relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def run():
    # 1. Load Config
    config = load_config()
    exp_config = config["experiment"]
    data_config = config["data"]
    model_params = config["model"]["params"]

    # 2. Setup MLflow
    setup_experiment(exp_config["name"])
    
    # 3. Start Run
    with mlflow.start_run():
        mlflow.set_tags(exp_config.get("tags", {}))
        mlflow.log_params(data_config)
        mlflow.log_params(model_params)
        
        # 4. Load Data
        loader = ExperimentDataLoader()
        banks_df = loader.load_training_data(start_date=str(data_config.get("start_year", 2010)) + "-01-01",
                                             end_date=str(data_config.get("end_year", 2020)) + "-12-31")
        print(f"Loaded {len(banks_df)} rows of merged data.")
        
        if banks_df.empty:
            print("No data loaded. Exiting.")
            return

        # 5. Preprocessing for Cox Model
        # Columns needed: duration, event, covariates
        # Map: events -> banks_df['is_dead'] (bool) -> int
        #      duration -> banks_df['lifespan_days'] / 365 (years)
        #      covariates -> CAMEL (e.g. ROA, total_assets) + family_connection_ratio
        
        # Fill missing values for pilot (simple mean or 0)
        df_model = banks_df.copy()
        
        # Target construction
        df_model['failed'] = df_model['is_dead'].fillna(False).astype(int)
        df_model['survival_time'] = df_model['lifespan_days'].fillna(10*365) / 365.0 # Fallback/Censoring logic needed
        
        # Covariates - select a subset for pilot
        features = [
            "ROA", "total_assets", "family_connection_ratio", 
            "npl_ratio", "capital_adequacy" # if available/computed
        ]
        # Check availability
        available_feats = [c for c in features if c in df_model.columns]
        
        # Simple imputation
        df_model[available_feats] = df_model[available_feats].fillna(0)
        
        # Drop constant columns (for small samples)
        for col in available_feats:
            if df_model[col].nunique() <= 1:
                print(f"Dropping constant column: {col}")
                available_feats.remove(col)
        
        # Select final columns
        final_cols = available_feats + ['failed', 'survival_time']
        df_train = df_model[final_cols]
        
        print(f"Training data shape: {df_train.shape}")
        print("Features:", available_feats)

        # 6. Train Model
        model_type = exp_config.get("tags", {}).get("model_type", "logistic_regression")
        print(f"Training {model_type} with params: {model_params}")

        if model_type == "cox_ph":
            from lifelines import CoxPHFitter
            cph = CoxPHFitter(**model_params)
            
            try:
                # Add a small variance to avoid singular matrix if still problematic
                # or rely on penalizer
                cph.fit(df_train, duration_col='survival_time', event_col='failed', show_progress=True)
                print("CoxPHFitter converged.")
                
                # Log Summary
                cph.print_summary()
                mlflow.log_metric("c_index", cph.score(df_train, scoring_method="concordance_index"))
                
                # Log coefficients
                params_dict = cph.params_.to_dict()
                mlflow.log_params({f"coef_{k}": v for k, v in params_dict.items()})
                
            except Exception as e:
                print(f"Cox fitting failed: {e}")
                
        else:
            # Default to sklearn (Logistic Regression)
            # Need to drop duration for classification if not using it
            X = df_train[available_feats]
            y = df_train['failed']
            
            model = LogisticRegression(**model_params)
            model.fit(X, y)
            
            score = model.score(X, y)
            mlflow.log_metric("accuracy", score)
            print(f"Logistic Regression Accuracy: {score}")

        print("Run complete.")


if __name__ == "__main__":
    run()
