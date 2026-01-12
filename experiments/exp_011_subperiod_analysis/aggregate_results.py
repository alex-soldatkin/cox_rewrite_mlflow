#!/usr/bin/env python3
"""
Aggregate exp_011 subperiod results from MLflow into Stargazer-style comparison tables.

Generates side-by-side tables comparing the same model specification across
three time periods (2004-2007, 2007-2013, 2013-2020).
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mlflow
import pandas as pd
from datetime import datetime

# MLflow experiments for the three subperiods
EXPERIMENTS = {
    "2004-2007": "exp_011_subperiod_2004_2007",
    "2007-2013": "exp_011_subperiod_2007_2013",
    "2013-2020": "exp_011_subperiod_2013_2020"
}

# Model specifications (consistent across all periods)
MODELS = [
    "M1: Baseline",
    "M2: Crisis",
    "M3: Family × Crisis",
    "M4: State × Crisis",
    "M5: Foreign × Crisis",
    "M6: Full Interactions"
]

def get_experiment_runs(exp_name):
    """Get all runs from an MLflow experiment."""
    client = mlflow.tracking.MlflowClient()
    
    # Get experiment by name
    experiment = client.get_experiment_by_name(exp_name)
    if experiment is None:
        print(f"⚠️  Experiment '{exp_name}' not found")
        return []
    
    # Get all runs
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time ASC"]
    )
    
    return runs

def extract_coefficients(run):
    """Extract coefficient summary from a run's artifacts."""
    client = mlflow.tracking.MlflowClient()
    
    # Try to download summary CSV
    try:
        artifacts = client.list_artifacts(run.info.run_id)
        summary_artifacts = [a for a in artifacts if 'summary_' in a.path and a.path.endswith('.csv')]
        
        if not summary_artifacts:
            return None
        
        # Download first summary file
        local_path = client.download_artifacts(run.info.run_id, summary_artifacts[0].path)
        df = pd.read_csv(local_path, index_col=0)
        
        return df
    except Exception as e:
        print(f"  ⚠️  Could not extract coefficients from run {run.info.run_name}: {e}")
        return None

def create_comparison_table(model_name, period_summaries):
    """
    Create side-by-side table for one model across all periods.
    
    Args:
        model_name: Model specification name
        period_summaries: Dict mapping period name -> summary DataFrame
        
    Returns:
        Combined DataFrame with columns: Variable, Coef_2004-2007, SE_2004-2007, ...
    """
    combined = None
    
    for period, summary_df in period_summaries.items():
        if summary_df is None:
            continue
        
        # Select relevant columns
        period_df = summary_df[['coef', 'se(coef)', 'p']].copy()
        period_df.columns = [f'coef_{period}', f'se_{period}', f'p_{period}']
        
        if combined is None:
            combined = period_df
        else:
            combined = combined.join(period_df, how='outer')
    
    return combined

def format_stargazer_row(variable, row_data, periods):
    """Format a single row for Stargazer output."""
    parts = [variable]
    
    for period in periods:
        coef_col = f'coef_{period}'
        se_col = f'se_{period}'
        p_col = f'p_{period}'
        
        if coef_col in row_data and not pd.isna(row_data[coef_col]):
            coef = row_data[coef_col]
            se = row_data[se_col]
            p = row_data[p_col]
            
            # Significance stars
            stars = ""
            if p < 0.001:
                stars = "***"
            elif p < 0.01:
                stars = "**"
            elif p < 0.05:
                stars = "*"
            
            # Format: coef (se) stars
            parts.append(f"{coef:.4f}{stars}")
            parts.append(f"({se:.4f})")
        else:
            parts.append("")
            parts.append("")
    
    return parts

def main():
    """Main aggregation routine."""
    # Set tracking URI to project root sqlite database (where experiments were actually logged)
    project_root = Path(__file__).parent.parent.parent
    mlflow_db_path = project_root / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{mlflow_db_path}")
    
    print("="*80)
    print("exp_011 Subperiod Analysis: Aggregating Results")
    print("="*80)
    print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
    print(f"Database path: {mlflow_db_path}")
    
    # Collect runs from all three experiments
    all_results = {}
    
    for period, exp_name in EXPERIMENTS.items():
        print(f"\nFetching runs from: {exp_name}")
        runs = get_experiment_runs(exp_name)
        print(f"  Found {len(runs)} runs")
        
        period_results = {}
        for run in runs:
            run_name = run.data.params.get('model_key', run.info.run_name)
            summary = extract_coefficients(run)
            
            if summary is not None:
                period_results[run.info.run_name] = summary
                print(f"  ✅ {run.info.run_name}: {len(summary)} coefficients")
        
        all_results[period] = period_results
    
    # Generate comparison tables for each model
    print(f"\n{'='*80}")
    print("Generating Comparison Tables")
    print(f"{'='*80}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("stargazer_subperiod")
    output_dir.mkdir(exist_ok=True)
    
    periods = list(EXPERIMENTS.keys())
    
    for model_spec in MODELS:
        # Find matching runs across periods
        period_summaries = {}
        
        for period in periods:
            # Find run matching this model spec
            matching_runs = [
                (name, df) for name, df in all_results[period].items()
                if model_spec in name
            ]
            
            if matching_runs:
                period_summaries[period] = matching_runs[0][1]
        
        if not period_summaries:
            print(f"⚠️  No data for {model_spec}")
            continue
        
        # Create comparison table
        comparison = create_comparison_table(model_spec, period_summaries)
        
        # Format as Stargazer
        stargazer_rows = []
        header = ['Variable'] + [f'{p} (Coef)' for p in periods] + [f'{p} (SE)' for p in periods]
        
        for variable in comparison.index:
            row = format_stargazer_row(variable, comparison.loc[variable], periods)
            stargazer_rows.append(row)
        
        # Create DataFrame
        stargazer_df = pd.DataFrame(stargazer_rows)
        
        # Save to CSV
        model_slug = model_spec.replace(" ", "_").replace(":", "").replace("×", "x")
        output_path = output_dir / f"{model_slug}_{timestamp}.csv"
        stargazer_df.to_csv(output_path, index=False, header=False)
        
        print(f"✅ {model_spec}: {len(stargazer_rows)} variables → {output_path}")
    
    # Create aggregated summary
    summary_data = []
    
    for period in periods:
        for model_name, summary_df in all_results[period].items():
            # Extract key metrics
            n_vars = len(summary_df)
            sig_vars = (summary_df['p'] < 0.05).sum()
            
            summary_data.append({
                'Period': period,
                'Model': model_name,
                'N_Variables': n_vars,
                'N_Significant': sig_vars,
                'Pct_Significant': f"{100*sig_vars/n_vars:.1f}%"
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_path = output_dir / f"summary_{timestamp}.csv"
    summary_df.to_csv(summary_path, index=False)
    
    print(f"\n✅ Summary table: {summary_path}")
    
    print(f"\n{'='*80}")
    print("Aggregation Complete!")
    print(f"{'='*80}")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Files created: {len(list(output_dir.glob('*.csv')))}")

if __name__ == "__main__":
    main()
