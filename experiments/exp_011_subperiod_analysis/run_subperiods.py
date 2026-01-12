#!/usr/bin/env python3
"""
exp_011: Subperiod Analysis (Structural Break Testing)

Runs exp_009 crisis interaction models on three distinct time periods:
- 2004-2007: Early crisis era (2004 banking crisis)
- 2007-2013: GFC and recovery
- 2013-2020: Sanctions and cleanup era

Tests whether ownership effects vary systematically across crisis regimes.
"""

import sys
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
import mlflow
import pandas as pd
from lifelines import CoxTimeVaryingFitter
from mlflow_utils.tracking import setup_experiment
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
from visualisations.cox_stargazer_new import create_single_column_stargazer, create_single_column_stargazer_hr
from datetime import datetime

def load_config(config_path):
    """Load YAML configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def prepare_cox_data(loader, config):
    """
    Prepare data for Cox time-varying model with specified time window.
    """
    # Load quarterly data with 4Q lag
    start_year = config['data']['start_year']
    end_year = config['data']['end_year']
    
    df = loader.load_with_lags(
        lag_quarters=config['data'].get('lag_quarters', 4),
        start_year=start_year,
        end_year=end_year
    )
    
    print(f"\n{'='*60}")
    print(f"SUBPERIOD: {start_year}-{end_year}")
    print(f"{'='*60}")
    print(f"Observations after time filter: {len(df)}")
    print(f"Unique banks: {df['regn'].nunique()}")
    print(f"Events: {df['event'].sum()}")
    
    # Create crisis indicators
    for crisis_name, crisis_cfg in config.get('crisis_periods', {}).items():
        crisis_start = pd.to_datetime(crisis_cfg['start'])
        crisis_end = pd.to_datetime(crisis_cfg['end'])
        
        df[crisis_name] = (
            (pd.to_datetime(df['DT']) >= crisis_start) & 
            (pd.to_datetime(df['DT']) <= crisis_end)
        ).astype(int)
        
        crisis_obs = df[crisis_name].sum()
        crisis_pct = 100 * crisis_obs / len(df)
        print(f"  {crisis_name}: {crisis_obs:,} obs ({crisis_pct:.1f}%)")
    
    # Select features
    ownership_features = config['ownership_features']
    network_features = config['network_features']
    camel_features = config['camel_features']
    
    feature_cols = ownership_features + network_features + camel_features
    
    # Check for missing features
    missing = [col for col in feature_cols if col not in df.columns]
    if missing:
        print(f"\n⚠️  Missing features: {missing}")
        feature_cols = [col for col in feature_cols if col in df.columns]
    
    # Create time intervals (exp_009 pattern)
    df['date'] = pd.to_datetime(df['DT'])
    df = df.sort_values(by=['regn', 'date']).reset_index(drop=True)
    
    # Time intervals for survival analysis
    df['start'] = df['date']
    df['stop'] = df.groupby('regn')['date'].shift(-1)
    
    # Fill last stop interval
    mask_last = df['stop'].isna()
    df.loc[mask_last, 'stop'] = df.loc[mask_last, 'start'] + pd.Timedelta(days=30)
    
    # Time since first observation (days)
    min_dates = df.groupby('regn')['date'].transform('min')
    df['registration_date'] = min_dates
    
    df['start_t'] = (df['start'] - df['registration_date']).dt.days
    df['stop_t'] = (df['stop'] - df['registration_date']).dt.days
    
    # Filter to valid intervals only
    df = df[df['stop_t'] > df['start_t']].copy()
    
    # Fill NaN with 0 (exp_009 pattern)
    df[feature_cols] = df[feature_cols].fillna(0)
    
    # Drop constant columns
    final_feats = []
    for col in feature_cols:
        if df[col].nunique() > 1:
            final_feats.append(col)
        else:
            print(f"  Dropping constant column: {col}")
    
    # StandardScaler normalization (0-100 range) - from exp_009
    if len(final_feats) > 0:
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        df[final_feats] = scaler.fit_transform(df[final_feats])
        # Scale to 0-100 range
        for col in final_feats:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:
                df[col] = 100 * (df[col] - min_val) / (max_val - min_val)
        
        print(f"  ✅ Scaled {len(final_feats)} features to 0-100 range")
    
    print(f"\nFinal dataset: {len(df):,} observations, {df['regn'].nunique()} banks, {df['event'].sum()} events")
    
    return df, final_feats

def run_model(df, feature_cols, model_cfg, config, model_key, output_dir):
    """
    Run a single Cox model specification.
    """
    # Build formula
    formula_parts = feature_cols.copy()
    
    # Add crisis dummies if specified
    if model_cfg.get('include_crisis_dummies', False):
        crisis_names = list(config.get('crisis_periods', {}).keys())
        formula_parts.extend(crisis_names)
    
    # Add interaction terms if specified
    interaction_features = model_cfg.get('interaction_features', [])
    for crisis_name in config.get('crisis_periods', {}).keys():
        for feature in interaction_features:
            interaction_name = f"{feature}_x_{crisis_name}"
            df[interaction_name] = df[feature] * df[crisis_name]
            formula_parts.append(interaction_name)
    
    formula = " + ".join(formula_parts)
    
    print(f"\n{'='*60}")
    print(f"MODEL: {model_cfg['name']}")
    print(f"{'='*60}")
    print(f"Formula: event ~ {formula}")
    print(f"Training observations: {len(df):,}")
    print(f"Events: {df['event'].sum()} ({100*df['event'].mean():.1f}%)")
    
    # Fit Cox model (exp_009 pattern - use column filtering, not formula)
    penalizer = config['model_params'].get('penalizer', 0.01)
    
    # Select only needed columns
    keep_cols = ['regn', 'start_t', 'stop_t', 'event'] + formula_parts
    df_model = df[keep_cols].copy()
    
    ctv = CoxTimeVaryingFitter(penalizer=penalizer, l1_ratio=0.0)
    
    try:
        ctv.fit(
            df_model,
            id_col='regn',
            event_col='event',
            start_col='start_t',
            stop_col='stop_t',
            show_progress=False
        )
        
        print(f"\n✅ Model converged successfully")
        
        # Log metrics
        log_lik = ctv.log_likelihood_
        aic = ctv.AIC_partial_
        
        # C-index (manually compute like exp_009)
        try:
            from lifelines.utils import concordance_index
            predicted_hazards = ctv.predict_partial_hazard(df_model)
            c_index = concordance_index(df_model['stop_t'], -predicted_hazards, df_model['event'])
            mlflow.log_metric("c_index", c_index)
            print(f"   C-index: {c_index:.4f}")
        except Exception as e:
            print(f"   ⚠️  Could not compute C-index: {e}")
            c_index = None
        
        mlflow.log_metric("log_likelihood", log_lik)
        mlflow.log_metric("aic_partial", aic)
        mlflow.log_metric("n_observations", len(df))
        mlflow.log_metric("n_subjects", df['regn'].nunique())
        mlflow.log_metric("n_events", df['event'].sum())
        
        print(f"\n✅ Model converged successfully")
        print(f"   C-index: {c_index:.4f}")
        print(f"   Log-likelihood: {log_lik:.2f}")
        print(f"   AIC: {aic:.2f}")
        
        # Generate Stargazer tables
        n_subjects = df['regn'].nunique()
        stargazer_coef = create_single_column_stargazer(ctv, c_index=c_index, n_subjects=n_subjects)
        stargazer_hr = create_single_column_stargazer_hr(ctv, c_index=c_index, n_subjects=n_subjects)
        
        # Generate interpretation
        interpretation = generate_interpretation(ctv, model_cfg['name'])
        
        # Create period-specific output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save artifacts to period directory
        stargazer_coef_path = output_path / f"stargazer_coef_{model_key}.csv"
        stargazer_hr_path = output_path / f"stargazer_hr_{model_key}.csv"
        interpretation_path = output_path / f"interpretation_{model_key}.md"
        summary_path = output_path / f"summary_{model_key}.csv"
        
        stargazer_coef.to_csv(stargazer_coef_path)
        stargazer_hr.to_csv(stargazer_hr_path)
        with open(interpretation_path, 'w') as f:
            f.write(interpretation)
        ctv.summary.to_csv(summary_path)
        
        # Log artifacts to MLflow
        mlflow.log_artifact(str(stargazer_coef_path))
        mlflow.log_artifact(str(stargazer_hr_path))
        mlflow.log_artifact(str(interpretation_path))
        mlflow.log_artifact(str(summary_path))
        
        print(f"  📁 Artifacts saved to: {output_path}")
        
        return ctv
        
    except Exception as e:
        print(f"\n❌ Model failed: {e}")
        mlflow.log_param("convergence_error", str(e))
        return None

def generate_interpretation(model, model_name):
    """Generate interpretation markdown from model results."""
    summary = model.summary
    
    lines = [
        f"# Interpretation Report: {model_name}\n",
        "## 1. Variable Interpretations",
        "Interpretation logic: *Holding all other covariates constant...*\n"
    ]
    
    for var in summary.index:
        coef = summary.loc[var, 'coef']
        hr = summary.loc[var, 'exp(coef)']
        p_val = summary.loc[var, 'p']
        
        # Determine significance
        if p_val < 0.001:
            sig = "(*** p<0.001)"
        elif p_val < 0.01:
            sig = "(** p<0.01)"
        elif p_val < 0.05:
            sig = "(* p<0.05)"
        else:
            sig = "(not significant)"
        
        # Interpretation
        pct_change = abs((hr - 1) * 100)
        direction = "increases" if coef > 0 else "decreases"
        
        lines.append(
            f"- **{var}**: A one-unit increase {direction} the hazard of failure by **{pct_change:.1f}%**. {sig}"
        )
    
    lines.append("\n## 2. Most Protective Variables (Decreased Risk)")
    lines.append("Ranked by strength of protection (largest % decrease in hazard).\n")
    
    protective = summary[summary['coef'] < 0].copy()
    protective['pct_effect'] = abs((protective['exp(coef)'] - 1) * 100)
    protective = protective.sort_values('pct_effect', ascending=False)
    
    for idx, (var, row) in enumerate(protective.iterrows(), 1):
        sig = "*" if row['p'] < 0.05 else ""
        lines.append(
            f"{idx}. **{var}{sig}**: Reduces hazard by **{row['pct_effect']:.1f}%** (HR = {row['exp(coef)']:.3f})"
        )
    
    lines.append("\n## 3. Highest Risk Variables (Increased Risk)")
    lines.append("Ranked by strength of risk (largest % increase in hazard).\n")
    
    risky = summary[summary['coef'] > 0].copy()
    risky['pct_effect'] = (risky['exp(coef)'] - 1) * 100
    risky = risky.sort_values('pct_effect', ascending=False)
    
    for idx, (var, row) in enumerate(risky.iterrows(), 1):
        sig = "*" if row['p'] < 0.05 else ""
        lines.append(
            f"{idx}. **{var}{sig}**: Increases hazard by **{row['pct_effect']:.1f}%** (HR = {row['exp(coef)']:.3f})"
        )
    
    lines.extend([
        "\n---",
        "*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*"
    ])
    
    return "\n".join(lines)

def run_subperiod(config_path):
    """Run all models for a single subperiod."""
    config = load_config(config_path)
    exp_name = config['experiment']['name']
    
    # Create period-specific output directory
    period_slug = f"{config['data']['start_year']}_{config['data']['end_year']}"
    output_dir = Path("output") / period_slug
    
    # Setup MLflow
    setup_experiment(exp_name)
    
    # Load data
    loader = QuarterlyWindowDataLoader()
    df, feature_cols = prepare_cox_data(loader, config)
    
    # Run all models
    results = {}
    for model_key, model_cfg in config['models'].items():
        with mlflow.start_run(run_name=model_cfg['name']):
            # Log configuration
            mlflow.log_param("subperiod", f"{config['data']['start_year']}-{config['data']['end_year']}")
            mlflow.log_param("model_key", model_key)
            mlflow.log_param("description", model_cfg['description'])
            
            model = run_model(df, feature_cols, model_cfg, config, model_key, output_dir)
            results[model_key] = model
    
    return results

def main():
    """Run all three subperiods sequentially."""
    config_dir = Path(__file__).parent
    
    subperiods = [
        ("2004-2007", config_dir / "config_2004_2007.yaml"),
        ("2007-2013", config_dir / "config_2007_2013.yaml"),
        ("2013-2020", config_dir / "config_2013_2020.yaml")
    ]
    
    all_results = {}
    
    for period_name, config_path in subperiods:
        print(f"\n\n{'#'*80}")
        print(f"# RUNNING SUBPERIOD: {period_name}")
        print(f"{'#'*80}\n")
        
        results = run_subperiod(config_path)
        all_results[period_name] = results
        
        print(f"\n✅ Completed subperiod: {period_name}")
    
    print(f"\n\n{'#'*80}")
    print(f"# ALL SUBPERIODS COMPLETED")
    print(f"{'#'*80}\n")
    
    for period_name, results in all_results.items():
        n_converged = sum(1 for model in results.values() if model is not None)
        n_total = len(results)
        print(f"{period_name}: {n_converged}/{n_total} models converged")

if __name__ == "__main__":
    main()
