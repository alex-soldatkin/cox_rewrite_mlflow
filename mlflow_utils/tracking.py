
import mlflow
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel

def setup_experiment(experiment_name: str, tracking_uri: Optional[str] = None):
    """
    Sets the active experiment. Creates it if it doesn't exist.
    """
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    else:
        # Default to local server if not specified, or env var
        # Use 127.0.0.1 to avoid localhost IPv6/v4 ambiguity and AirPlay conflicts on macOS
        default_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
        mlflow.set_tracking_uri(default_uri)

    print(f"Setting MLflow experiment to: {experiment_name}")
    mlflow.set_experiment(experiment_name)

def log_pydantic_params(model: BaseModel, prefix: str = ""):
    """
    Logs fields of a Pydantic model as MLflow parameters.
    """
    params = model.model_dump()
    flattened = _flatten_dict(params, parent_key=prefix)
    # Convert all to string to avoid issues, or let mlflow handle it
    mlflow.log_params(flattened)

def log_metrics_classification(y_true, y_pred, y_prob=None, prefix: str = ""):
    """
    Logs standard classification metrics: Accuracy, Precision, Recall, F1, AUC.
    """
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    
    metrics = {
        f"{prefix}accuracy": accuracy_score(y_true, y_pred),
        f"{prefix}precision": precision_score(y_true, y_pred, zero_division=0),
        f"{prefix}recall": recall_score(y_true, y_pred, zero_division=0),
        f"{prefix}f1": f1_score(y_true, y_pred, zero_division=0),
    }
    
    if y_prob is not None:
        try:
            metrics[f"{prefix}auc"] = roc_auc_score(y_true, y_prob)
        except ValueError:
            pass # Handle case with one class only

    mlflow.log_metrics(metrics)

def log_metrics_survival(cph_model, df, duration_col, event_col, id_col=None, prefix: str = ""):
    """
    Logs survival analysis metrics using specific model instance (e.g. Lifelines CoxPHFitter).
    """
    # Concordance Index
    # Lifelines score() method signature varies slightly or handles internals
    # For CoxTimeVaryingFitter, it expects a dataframe with id_col if it was trained with it.
    
    # We try to use the generic score method which usually computes partial log likelihood or c-index
    try:
        c_index = cph_model.score(df, scoring_method="concordance_index")
        mlflow.log_metric(f"{prefix}c_index", c_index)
    except Exception as e:
        print(f"Could not log c_index: {e}")


def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
