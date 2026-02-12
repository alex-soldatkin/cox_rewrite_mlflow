
import mlflow
import pandas as pd
import os
import datetime
import glob
import argparse
from mlflow.tracking import MlflowClient

def aggregate_artifacts(artifact_name="stargazer_column.csv", output_suffix="coef", experiment_id="*", output_dir="stargazer"):
    """
    Aggregates a specific CSV artifact from all runs matching the pattern.
    """
    # Setup
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    try:
        mlflow.search_experiments()
    except Exception:
        print("MLflow server not accessible. Using local tracking.")
        mlflow.set_tracking_uri(None)
        
    client = MlflowClient()
    
    print(f"\nScanning experiments ({experiment_id}) for '{artifact_name}'...")
    
    # Path pattern: mlartifacts/<exp_id>/<run_id>/artifacts/<artifact_name>
    search_pattern_artifacts = f"mlartifacts/{experiment_id}/*/artifacts/{artifact_name}"
    search_pattern_runs = f"mlruns/{experiment_id}/*/artifacts/{artifact_name}"
    
    artifact_paths = glob.glob(search_pattern_artifacts) + glob.glob(search_pattern_runs)
    
    if not artifact_paths:
        print(f"No artifacts found for experiment {experiment_id}")
        return

    print(f"Found {len(artifact_paths)} artifact files.")
    
    dfs = []
    
    for filepath in artifact_paths:
        try:
            parts = filepath.split(os.sep)
            # Structure: mlartifacts / exp_id / run_id / artifacts / filename
            if "artifacts" in parts:
                idx = parts.index("artifacts")
                run_id = parts[idx-1]
            else:
                run_id = "unknown"

            # Fetch tags
            try:
                run = client.get_run(run_id)
                tags = run.data.tags
                status = run.info.status
                
                if status != "FINISHED":
                    # print(f"    - Skipping run {run_id[:8]} (Status: {status})")
                    continue
                    
                col_name = tags.get("human_readable_name")
                if not col_name:
                    col_name = tags.get("mlflow.runName", run_id[:8])
            except Exception as e:
                # print(f"    ! Could not fetch metadata for {run_id[:8]}: {e}")
                col_name = run_id[:8]

            # Read CSV
            run_df = pd.read_csv(filepath, index_col=0)
            
            # Identify the value column (could be "Stargazer_Output" or something else)
            # Usually it's the only column if index is variable name. 
            # But the generated CSV has "Stargazer_Output" as header usually?
            # Let's just take the first column if "Stargazer_Output" isn't there, or rename it.
            
            target_col = run_df.columns[0]
            if "Stargazer_Output" in run_df.columns:
                target_col = "Stargazer_Output"
            
            run_df = run_df[[target_col]].rename(columns={target_col: col_name})
            
            # Deduplicate columns if multiple runs have same name (append run_id)
            # We handle this by appending to list and then concat handles duplicates by creating multiple cols
            # But duplicate names in final DF are confusing.
            # Lets leave as is, user can dedup.
            
            dfs.append(run_df)
            print(f"  + Added '{col_name}' from {run_id[:8]}")

        except Exception as e:
            print(f"  ! Error processing {filepath}: {e}")

    if not dfs:
        print("No valid data collected.")
        return

    # Merge
    print("Aggregating...")
    aggregated_df = pd.concat(dfs, axis=1, sort=False)
    aggregated_df = aggregated_df.fillna("")
    
    # Save
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stargazer_aggregated_{output_suffix}_{timestamp}.csv"
    full_path = os.path.join(output_dir, filename)
    
    os.makedirs(output_dir, exist_ok=True)
    aggregated_df.to_csv(full_path)
    
    print(f"saved: {full_path}")
    print(aggregated_df.head())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp_id", default="*", help="Experiment ID to scan (default: *)")
    args = parser.parse_args()
    
    # Aggregate Coefficients
    aggregate_artifacts(artifact_name="stargazer_column.csv", output_suffix="coef", experiment_id=args.exp_id)
    
    # Aggregate Hazard Ratios
    aggregate_artifacts(artifact_name="stargazer_hr_column.csv", output_suffix="hr", experiment_id=args.exp_id)
