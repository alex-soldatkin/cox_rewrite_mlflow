
import mlflow

# Try to connect to the server
mlflow.set_tracking_uri("http://localhost:5000")

try:
    print("Listing experiments from localhost:5000...")
    experiments = mlflow.search_experiments()
    for exp in experiments:
        print(f"ID: {exp.experiment_id}, Name: {exp.name}, Artifact Location: {exp.artifact_location}")
except Exception as e:
    print(f"Error connecting to server: {e}")
