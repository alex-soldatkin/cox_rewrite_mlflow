"""
Global Link Prediction Pipeline
===============================

Runs link prediction on the entire graph (all time) to discover potential family connections.
Predicted edges are written back to Neo4j with source='logistic_pred'.

Workflow:
1. Project Global Graph (Native Projection: Person, Bank, Company; Rels: FAMILY, OWNERSHIP, MANAGEMENT).
   - Includes isolates.
2. Compute Graph Features (FastRP, Louvain, WCC).
3. Fetch Training Data:
   - Positives: Existing FAMILY edges (excluding imputed).
   - Negatives/Candidates: SIM_NAME pairs.
4. Train Model Horse Race (Logistic Regression).
5. Predict on all SIM_NAME candidates.
6. Write predicted edges to Neo4j.
"""

import os
import sys
import logging
import argparse
from typing import Optional, Any
import time

import mlflow
import pandas as pd
import numpy as np
from graphdatascience import GraphDataScience
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Add project root to path
sys.path.append(os.getcwd())

from rolling_windows.link_prediction import LinkPredictionConfig, build_training_data, compute_embedding_features, compute_community_features, compute_network_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("global_lp")


def get_gds_client() -> GraphDataScience:
    """Connect to Neo4j GDS."""
    from dotenv import load_dotenv
    load_dotenv()
    
    neo4j_url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
    
    return GraphDataScience(neo4j_url, auth=(neo4j_user, neo4j_pass))


def project_global_graph(gds, graph_name: str) -> bool:
    """
    Project the global graph including structure edges.
    Includes ALL nodes to ensure isolates have embeddings (though they will be random/null structure).
    """
    if gds.graph.exists(graph_name).exists:
        logger.info(f"Graph '{graph_name}' already exists. Dropping.")
        gds.graph.drop(graph_name)
    
    logger.info(f"Projecting global graph '{graph_name}'...")
    
    # Native projection with ALL nodes
    # We use Native Projection to avoid the Cypher Projection error (AccessMode$Static)
    # This implies 'imputed' edges are included in the graph topology. 
    # This is acceptable as we strictly exclude them from training Labels.
    
    node_projection = {
        "Person": { "properties": [] },
        "Bank": { "properties": [] },
        "Company": { "properties": [] }
    }
    
    relationship_projection = {
        "FAMILY": {
            "type": "FAMILY",
            "orientation": "UNDIRECTED",
            "aggregation": "SINGLE"
        },
        "OWNERSHIP": {
            "type": "OWNERSHIP",
            "orientation": "UNDIRECTED",
            "aggregation": "SINGLE"
        },
        "MANAGEMENT": {
            "type": "MANAGEMENT",
            "orientation": "UNDIRECTED",
            "aggregation": "SINGLE"
        }
    }
    
    try:
        G, result = gds.graph.project(
            graph_name,
            node_projection,
            relationship_projection
        )
        logger.info(f"Graph '{graph_name}' created. Nodes: {result['nodeCount']}, Rels: {result['relationshipCount']}")
        return G
    except Exception as e:
        logger.error(f"Failed to project graph: {e}")
        raise e


def run_algorithms(gds, G):
    """Run FastRP, Louvain, WCC on global graph and mutate DB."""
    # Note: G is the Graph object
    logger.info("Running WCC...")
    gds.wcc.write(G, writeProperty="wcc_global")
    
    logger.info("Running Louvain...")
    gds.louvain.write(G, writeProperty="louvain_global")
    
    logger.info("Running FastRP...")
    gds.fastRP.write(G, 
                     embeddingDimension=128,
                     writeProperty="fastrp_global")
    
    logger.info("Algorithms completed and written to DB.")

    
def fetch_node_features(gds) -> pd.DataFrame:
    """Fetch computed features from DB."""
    logger.info("Fetching node features from DB...")
    query = """
    MATCH (n:Person)
    RETURN 
        n.Id AS entity_id,
        n.wcc_global AS wcc,
        n.louvain_global AS community_louvain,
        n.fastrp_global AS fastrp_embedding
    """
    df = gds.run_cypher(query)
    logger.info(f"Fetched features for {len(df)} nodes.")
    return df


def write_predictions(gds, predictions: pd.DataFrame, run_id: str):
    """Write predicted edges to Neo4j."""
    if predictions.empty:
        logger.info("No predictions to write.")
        return

    logger.info(f"Writing {len(predictions)} predicted edges to Neo4j...")
    
    # Use UNWIND for batch creation
    query = """
    UNWIND $batch AS row
    MATCH (s:Person {Id: row.source_id})
    MATCH (t:Person {Id: row.target_id})
    MERGE (s)-[r:FAMILY {source: 'logistic_pred', run_id: $run_id}]-(t)
    SET r.confidence = row.probability,
        r.temporal_start = -2208988800000,  // 1900-01-01 (Roughly unbound)
        r.temporal_end = 64060588800000     // 4000-01-01
    """
    
    batch_size = 1000
    records = predictions[['source_id', 'target_id', 'probability']].to_dict('records')
    
    total = len(records)
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        gds.run_cypher(query, params={"batch": batch, "run_id": run_id})
        logger.debug(f"Written batch {i}-{i+batch_size}/{total}")
        
    logger.info("Write-back complete.")


def run_global_pipeline(lp_threshold: float = 0.7):
    gds = get_gds_client()
    graph_name = "global_lp_graph"
    
    # 1. Project
    G = project_global_graph(gds, graph_name)
    
    # 2. Algo
    # Check if properties exist or force run? 
    # Let's force run to ensure sync with projection
    run_algorithms(gds, G)
    
    # 3. Fetch Data
    df_nodes = fetch_node_features(gds)
    
    # 4. Fetch Training Data (SimName & Family)
    # Reusing functions from link_prediction.py but passing correct GDS
    from rolling_windows.link_prediction import fetch_sim_name_pairs, fetch_official_family_edges
    
    sim_name_df = fetch_sim_name_pairs(gds, include_family=False)
    
    # Define local fetch function to ensure we exclude 'logistic_pred' from training data
    # (Ground truth only)
    logger.info("Fetching official FAMILY relationships (Ground Truth)...")
    family_query = """
    MATCH (p1:Person)-[f:FAMILY]->(p2:Person)
    WHERE coalesce(f.source, '') <> 'imputed' 
      AND coalesce(f.source, '') <> 'logistic_pred'
    WITH p1, p2, f
    WITH p1, p2, f,
         apoc.text.levenshteinSimilarity(p1.LastName, p2.LastName) AS lev_dist_last_name,
         apoc.text.levenshteinSimilarity(p1.FirstName, p2.MiddleName) AS lev_dist_patronymic,
         CASE WHEN toUpper(p1.LastName) IN ['KUZNETSOV','IVANOV','PETROV','POPOV','SMIRNOV']
                OR toUpper(p2.LastName) IN ['KUZNETSOV','IVANOV','PETROV','POPOV','SMIRNOV']
              THEN 1 ELSE 0 END AS is_common_surname
    RETURN 
        p1.Id AS source_id,
        p2.Id AS target_id,
        lev_dist_last_name,
        lev_dist_patronymic,
        is_common_surname,
        f.type AS rel_type
    """
    family_df = gds.run_cypher(family_query)
    logger.info(f"Fetched {len(family_df)} ground truth FAMILY edges.")
    
    logger.info("Building training data...")
    train_df = build_training_data(sim_name_df, family_df, max_negatives_ratio=1.0)
    
    # 5. Train & Predict
    cfg = LinkPredictionConfig()
    
    # Use existing best model finding logic or just hardcode the best approach?
    # Let's run the horse race for rigour, or at least the best one.
    # User said "APPLY the best model".
    
    # We will replicate the run_model_variant logic but adapted for this script's node feature column names
    # Note: df_nodes here has `community_louvain` (from louvain_global) and `wcc` (from wcc_global).
    # `link_prediction.py` expects `entity_id` which we have.
    
    from rolling_windows.link_prediction import run_model_variant
    
    # We need to map config variants to string names? 
    # run_model_variant uses string matching
    
    best_variant = "fastrp_string_wcc" 
    # We can perform full horse race if we want:
    variants = ["string_only", "fastrp_string_wcc"] # Minimal set
    
    best_model = None
    best_scaler = None
    best_metric = -1
    
    # MLflow
    mlflow.set_experiment("global_link_prediction")
    
    with mlflow.start_run(run_name=f"global_run_{int(time.time())}") as run:
        run_id = run.info.run_id
        
        for variant in variants:
            with mlflow.start_run(run_name=variant, nested=True):
                try:
                    model, metrics, scaler = run_model_variant(variant, train_df.copy(), df_nodes, cfg)
                    logger.info(f"Variant {variant}: AUC={metrics['auc']:.3f}")
                    
                    mlflow.log_metrics(metrics)
                    
                    if metrics['auc'] > best_metric:
                        best_metric = metrics['auc']
                        best_model = model
                        best_scaler = scaler
                        best_variant = variant
                except Exception as e:
                    logger.error(f"Variant {variant} failed: {e}")
                    raise e
        
        logger.info(f"Best model: {best_variant} (AUC={best_metric:.3f})")
        
        # 6. Predict
        # Build Candidates (SIM_NAME - FAMILY)
        # Using logic from link_prediction.py (but we need to replicate it here or import function? 
        # link_prediction.py has it embedded in run_link_prediction_workflow. We should extract it or copy-paste adapted)
        
        # Candidate generation
        family_set = set()
        for _, row in family_df.iterrows():
            family_set.add((row['source_id'], row['target_id']))
            family_set.add((row['target_id'], row['source_id']))
        
        candidates = sim_name_df[
            ~sim_name_df.apply(lambda r: (r['source_id'], r['target_id']) in family_set, axis=1)
        ].copy()
        
        logger.info(f"Predicting on {len(candidates)} candidates using {best_variant}...")
        
        # Build properties for candidates
        # Must match feature construction in run_model_variant
        # We can implement a clean `build_features` here or re-use logic
        
        # ... (Feature Construction Logic - Copied/Adapted for robust execution) ...
        # Fill NaNs
        str_cols = ['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']
        candidates[str_cols] = candidates[str_cols].fillna(0.0)
        
        feature_sets = []
        if best_variant != "baseline_fastrp":
            feature_sets.append(candidates[str_cols].values)
            
        if "fastrp" in best_variant:
            # We must be careful: compute_embedding_features in link_prediction.py expects `fastrp_embedding` column in df_nodes
            # Our df_nodes has it.
            emb_features = compute_embedding_features(candidates, df_nodes, "fastrp_embedding")
            
            # Handle missing embeddings (isolates? wait, we projected isolates, so they have embeddings!)
            # But just in case
            valid_mask = [f is not None for f in emb_features]
            if sum(valid_mask) < len(emb_features):
                logger.warning(f"Dropping {len(emb_features) - sum(valid_mask)} candidates (no embeddings)")
                candidates = candidates.iloc[valid_mask].reset_index(drop=True)
                if best_variant != "baseline_fastrp":
                     feature_sets = [candidates[str_cols].values]
                else:
                    feature_sets = []
                emb_features = compute_embedding_features(candidates, df_nodes, "fastrp_embedding")

            emb_matrix = np.stack([np.array(f) for f in emb_features if f is not None])
            feature_sets.append(emb_matrix)
            
        if "wcc" in best_variant:
            # compute_community_features expects 'wcc' column if we pass 'wcc' arg
            # Our df_nodes has 'wcc' column
            wcc_df = compute_community_features(candidates, df_nodes, "wcc")
            feature_sets.append(wcc_df.values)
            
        if "louvain" in best_variant:
            louvain_df = compute_community_features(candidates, df_nodes, "community_louvain")
            feature_sets.append(louvain_df.values)
            
        X_cand = np.hstack(feature_sets)
        X_cand = best_scaler.transform(X_cand)
        
        probs = best_model.predict_proba(X_cand)[:, 1]
        
        candidates['probability'] = probs
        predicted_edges = candidates[candidates['probability'] > lp_threshold].copy()
        
        # 7. Write Back
        write_predictions(gds, predicted_edges, run_id)
        
        # Cleanup
        gds.graph.drop(graph_name)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.7)
    args = parser.parse_args()
    
    run_global_pipeline(args.threshold)
