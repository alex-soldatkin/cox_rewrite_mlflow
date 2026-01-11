
import pandas as pd
import numpy as np
import mlflow
from lifelines import CoxTimeVaryingFitter

def generate_isolated_predictions(model: CoxTimeVaryingFitter, df: pd.DataFrame, 
                                  id_col: str, 
                                  variables: list, 
                                  time_grid: np.array = None) -> pd.DataFrame:
    """
    Generates survival predictions for each subject in df, for each variable of interest,
    holding all *other* variables constant at their mean (or mode).
    
    This allows visualizing the isolated effect of 'variable' on that specific subject's survival curve.
    
    Args:
        model: Fitted CoxTimeVaryingFitter
        df: The training DataFrame (long format)
        id_col: The column name for subject ID (e.g. 'regn')
        variables: List of feature names to isolate
        time_grid: Optional time points to predict at. If None, uses model's event times.
        
    Returns:
        pd.DataFrame: Columns [id_col (str), time, variable, value, survival_prob]
    """
    
    # 1. Calculate Baselines (Means/Modes) for all features
    # This is "the average bank"
    # We use the training data `df` to calculate these
    feature_means = {}
    for col in model.params_.index:
        if col in df.columns:
            if np.issubdtype(df[col].dtype, np.number):
                feature_means[col] = df[col].mean()
            else:
                # Mode for categorical (though CoxTV usually expects numeric/dummies)
                feature_means[col] = df[col].mode()[0]
    
    results = []
    
    # Get unique subjects to predict for
    # Predicting for *every* time interval of every subject is expensive.
    # Usually we predict survival curves for specific subjects.
    # But CoxTV `predict_survival_function` expects a dataframe representing the covariate path or static covariates.
    # For simplicity/efficiency in "visualising", usually we pick the *last known state* or *average state* of the bank?
    # Or do we use the *actual* time-varying covariates?
    # "holding other variables constant at mean" implies constructing a synthetic covariate path.
    
    # Let's assume we want to predict survival from t=0 onwards based on the values in `df`?
    # BUT `df` has multiple rows per bank. 
    # Standard approach: Take the LAST row for each bank (current state) and project forward?
    # OR Take the average values for that bank?
    
    # Let's take the LAST row for each bank (most recent data point) to characterize the bank.
    last_rows = df.sort_values('stop_t').groupby(id_col).last().reset_index()
    
    # Limit number of subjects if too huge? 
    # User said "save the predictions ... alongside original string regn". 
    # We will do it for all unique regns in the provided df.
    
    print(f"Generating isolated predictions for {len(variables)} variables across {len(last_rows)} subjects...")
    
    for var in variables:
        if var not in feature_means:
            continue
            
        print(f"  ... processing {var}")
        
        # Create a synthetic dataframe for this variable context
        # Copy the 'last_rows' (real subjects)
        synthetic_df = last_rows.copy()
        
        # For ALL other variables, overwrite with Global Mean
        for other_var, mean_val in feature_means.items():
            if other_var != var:
                synthetic_df[other_var] = mean_val
        
        # Now synthetic_df has:
        # - Real values for 'var'
        # - Mean values for everything else
        # - Real 'regn'
        
        # Predict Survival MANUALLY as CoxTV doesn't have predict_survival_function
        # S(t|x) = exp(-H0(t) * partial_hazard)
        # where H0(t) is baseline cumulative hazard
        
        try:
            # 1. Compute Partial Hazard for each subject (row)
            # predict_partial_hazard returns Series indexed by synthetic_df.index
            partial_hazards = model.predict_partial_hazard(synthetic_df)
            
            # 2. Get Baseline Cumulative Hazard H0(t)
            # This is a DataFrame with index=Time, column='baseline_hazard'
            h0 = model.baseline_cumulative_hazard_
            
            # 3. Compute Survival Curves
            # We want matrix S[Time, Subject]
            # S = exp(- H0 @ partial_hazard.T) ? No
            # S[t, i] = exp( - H0(t) * P_i )
            
            # Use broadcasting
            # h0.values is (T, 1)
            # partial_hazards.values is (N,)
            # Result (T, N)
            
            cumulative_hazard_matrix = np.dot(h0.values, partial_hazards.values.reshape(1, -1))
            survival_matrix = np.exp(-cumulative_hazard_matrix)
            
            # Create DataFrame
            survival_df = pd.DataFrame(survival_matrix, index=h0.index, columns=synthetic_df.index)
            
            # Add time column
            survival_df["time"] = survival_df.index
            
            # Melt
            melted = survival_df.melt(id_vars="time", var_name="temp_idx", value_name="survival_prob")
            
            # Map temp_idx back to regn and the variable value
            # synthetic_df index matches temp_idx if we didn't shuffle
            
            # Prepare metadata to merge
            metadata = synthetic_df[[id_col, var]].reset_index(drop=True) 
            metadata['temp_idx'] = metadata.index
            
            # Merge survival curves with metadata
            merged = pd.merge(melted, metadata, on="temp_idx")
            
            # Structure for final output
            # [regn, time, variable_name, variable_value, survival_prob]
            merged_subset = merged[[id_col, "time", var, "survival_prob"]].copy()
            merged_subset.columns = [id_col, "time", "value", "survival_prob"]
            merged_subset["variable"] = var
            
            # Ensure proper typing
            merged_subset[id_col] = merged_subset[id_col].astype(str)
            
            results.append(merged_subset)
            
        except Exception as e:
            print(f"Error predicting for {var}: {e}")
            
    if not results:
        return pd.DataFrame()
        
    final_df = pd.concat(results, ignore_index=True)
    return final_df
