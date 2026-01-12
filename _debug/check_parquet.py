import pandas as pd
import glob
import os

def check_output():
    # Find latest run output
    run_dirs = glob.glob("data_processing/rolling_windows/output/run_*")
    if not run_dirs:
        print("No run output found.")
        return
    latest_run = sorted(run_dirs)[-1]
    print(f"Checking output in: {latest_run}")
    
    # Check Nodes
    node_files = glob.glob(f"{latest_run}/nodes/*.parquet")
    if node_files:
        df_nodes = pd.read_parquet(node_files[0])
        print(f"Nodes Shape: {df_nodes.shape}")
        print("Columns:", df_nodes.columns.tolist())
        
        if "fcr_temporal" in df_nodes.columns:
            non_zero_fcr = (df_nodes["fcr_temporal"] > 0).sum()
            print(f"Non-zero FCR count: {non_zero_fcr}")
            print("FCR Stats:\n", df_nodes["fcr_temporal"].describe())
            
        if "entity_id" in df_nodes.columns:
             missing_ids = df_nodes["entity_id"].isna().sum()
             print(f"Missing entity_id: {missing_ids}")
             print("Sample IDs:", df_nodes["entity_id"].dropna().head().tolist())
             
        if "bank_feats" in df_nodes.columns:
             print("bank_feats sample:", df_nodes["bank_feats"].head())

    # Check Edges (Basic)
    edge_files = glob.glob(f"{latest_run}/edges/*.parquet")
    if edge_files:
        df_edges = pd.read_parquet(edge_files[0])
        print(f"Edges Shape: {df_edges.shape}")
        print("Columns:", df_edges.columns.tolist())

if __name__ == "__main__":
    check_output()
