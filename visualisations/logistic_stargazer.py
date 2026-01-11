
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score, roc_auc_score

def create_single_column_logistic_stargazer(model_result, y_true, y_pred_prob, model_name="Logistic Model", threshold=0.5, n_subjects=None):
    """
    Creates a single-column DataFrame for a fitted Logistic model (statsmodels or similar),
    formatted in Stargazer style (Coef*** (SE)) and including classification metrics.

    Args:
        model_result: The fitted model result object (e.g. statsmodels LogitResult).
                      Must have .params, .bse, .pvalues, .llf, .aic.
        y_true: Array-like of true binary labels (0/1).
        y_pred_prob: Array-like of predicted probabilities (0-1).
        model_name: Name of the model (column header).
        threshold: Classification threshold (default 0.5).
        n_subjects: Optional count of unique subjects (banks).

    Returns:
        pd.DataFrame: A DataFrame with the model results.
    """
    
    # 1. Extract Coefficients
    params = model_result.params
    se = model_result.bse
    pvalues = model_result.pvalues
    
    # Build a DataFrame for coefficients
    # Using index from params
    coef_df = pd.DataFrame(index=params.index)
    
    # Helper for stars
    def get_stars(p):
        if p < 0.001: return "***"
        if p < 0.01: return "**"
        if p < 0.05: return "*"
        return ""
    
    formatted_values = []
    for var in params.index:
        coef_val = params[var]
        se_val = se[var]
        p_val = pvalues[var]
        
        star_str = get_stars(p_val)
        val_str = f"{coef_val:.3f}{star_str} ({se_val:.3f})"
        formatted_values.append(val_str)
        
    coef_df[model_name] = formatted_values
    
    # 2. Calculate Metrics using Dynamic Threshold (Max F1)
    from sklearn.metrics import precision_recall_curve
    
    # Calculate Precision-Recall Curve to find best F1 threshold
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_pred_prob)
    
    numerator = 2 * precisions * recalls
    denominator = precisions + recalls
    f1_scores = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator!=0)
    
    if len(thresholds) > 0:
        best_idx = np.argmax(f1_scores)
        if best_idx >= len(thresholds):
            best_threshold = 0.5
        else:
            best_threshold = thresholds[best_idx]
    else:
        best_threshold = 0.5
        
    y_pred = (np.array(y_pred_prob) >= best_threshold).astype(int)
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_pred_prob)
    except:
        auc = float('nan')
        
    llf = model_result.llf
    aic = model_result.aic
    obs = len(y_true)
    events = int(sum(y_true))
    
    metrics_data = {
        "Observations": f"{obs}",
        "Subjects": f"{n_subjects}" if n_subjects is not None else "",
        "Events": f"{events}",
        "Log Likelihood": f"{llf:.2f}",
        "AIC": f"{aic:.2f}",
        "AUC": f"{auc:.3f}",
        "Optimal Threshold": f"{best_threshold:.3f}",
        "Accuracy": f"{acc:.3f}",
        "Precision": f"{prec:.3f}",
        "Recall": f"{rec:.3f}",
        "F1 Score": f"{f1:.3f}"
    }
    
    metrics_df = pd.DataFrame.from_dict(metrics_data, orient='index', columns=[model_name])
    
    # 4. Concatenate
    final_df = pd.concat([coef_df, metrics_df])
    final_df.index.name = "variable"
    
    return final_df

def create_single_column_logistic_stargazer_odds(model_result, y_true, y_pred_prob, model_name="Logistic Model", threshold=0.5, n_subjects=None):
    """
    Same as above but reports Odds Ratios (exp(coef)) and SE(OR) via Delta Method.
    SE(OR) = OR * SE(coef).
    """
    
    params = model_result.params
    se = model_result.bse
    pvalues = model_result.pvalues
    
    coef_df = pd.DataFrame(index=params.index)
    
    def get_stars(p):
        if p < 0.001: return "***"
        if p < 0.01: return "**"
        if p < 0.05: return "*"
        return ""
    
    formatted_values = []
    for var in params.index:
        coef_val = params[var]
        se_val = se[var]
        p_val = pvalues[var]
        
        or_val = np.exp(coef_val)
        or_se = or_val * se_val
        
        star_str = get_stars(p_val)
        val_str = f"{or_val:.3f}{star_str} ({or_se:.3f})"
        formatted_values.append(val_str)
        
    coef_df[model_name] = formatted_values
    
    # Metrics
    # (Same logic as above, can reuse)
    # 2. Calculate Metrics using Dynamic Threshold (Max F1)
    from sklearn.metrics import precision_recall_curve
    
    # Calculate Precision-Recall Curve to find best F1 threshold
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_pred_prob)
    
    # F1 = 2 * (P * R) / (P + R)
    numerator = 2 * precisions * recalls
    denominator = precisions + recalls
    f1_scores = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator!=0)
    
    # Find index of max F1
    if len(thresholds) > 0:
        best_idx = np.argmax(f1_scores)
        # thresholds array is 1 shorter than prec/rec arrays
        # if best_idx is the last element (accidental 1.0 prob), clamp it
        if best_idx >= len(thresholds):
            best_threshold = 0.5
        else:
            best_threshold = thresholds[best_idx]
            
        best_f1 = f1_scores[best_idx]
    else:
        best_threshold = 0.5
        best_f1 = 0
        
    # Apply optimal threshold
    y_pred = (np.array(y_pred_prob) >= best_threshold).astype(int)
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    # recalculate f1 from components to be safe, or use best_f1
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    try:
        auc = roc_auc_score(y_true, y_pred_prob)
    except:
        auc = float('nan')
        
    llf = model_result.llf
    aic = model_result.aic
    obs = len(y_true)
    events = int(sum(y_true))
    
    metrics_data = {
        "Observations": f"{obs}",
        "Subjects": f"{n_subjects}" if n_subjects is not None else "",
        "Events": f"{events}",
        "Log Likelihood": f"{llf:.2f}",
        "AIC": f"{aic:.2f}",
        "AUC": f"{auc:.3f}",
        "Optimal Threshold": f"{best_threshold:.3f}",
        "Accuracy": f"{acc:.3f}",
        "Precision": f"{prec:.3f}",
        "Recall": f"{rec:.3f}",
        "F1 Score": f"{f1:.3f}"
    }
    
    metrics_df = pd.DataFrame.from_dict(metrics_data, orient='index', columns=[model_name])
    
    final_df = pd.concat([coef_df, metrics_df])
    final_df.index.name = "variable"
    return final_df
