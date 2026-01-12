
import mlflow
import os

# Set URI to match the working configuration
mlflow.set_tracking_uri("http://127.0.0.1:5000")

# Run ID from the latest successful execution
run_id = "b911738f0fbf407b895894cf063dc437"
artifact_path = "stargazer_column.csv"

try:
    print(f"Attempting to download {artifact_path} from run {run_id}...")
    local_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=artifact_path)
    print(f"Success! Downloaded to: {local_path}")
    
    # Check content briefly
    with open(local_path, 'r') as f:
        print("File head:")
        print(f.read()[:100])
        
except Exception as e:
    print(f"Failed to download artifact: {e}")
