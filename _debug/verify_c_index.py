
import mlflow
import os

# Set URI to match the working configuration
mlflow.set_tracking_uri("http://127.0.0.1:5000")

# Run ID from the latest successful execution
run_id = "261bdc78798b48a9be103455714caed3"
artifact_path = "stargazer_column.csv"

try:
    print(f"Attempting to download {artifact_path} from run {run_id}...")
    local_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=artifact_path)
    
    with open(local_path, 'r') as f:
        content = f.read()
        print("File content snippet:")
        print(content[-200:]) # Check end where C-index usually resides
        
        if "C-index,0.76" in content or "C-index,0.7" in content:
            print("VERIFICATION PASSED: C-index found.")
        else:
            print("VERIFICATION FAILED: C-index missing or empty.")
            
except Exception as e:
    print(f"Failed to download/verify artifact: {e}")
