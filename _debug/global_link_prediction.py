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
    
    # 0. Cleanup Old Predictions (Important for idempotency)
    logger.info("Cleaning up old 'logistic_pred' edges...")
    gds.run_cypher("MATCH ()-[r:FAMILY {source: 'logistic_pred'}]-() DELETE r")

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
    # Ensure IDs are strings
    sim_name_df.dropna(subset=['source_id', 'target_id'], inplace=True)
    sim_name_df['source_id'] = sim_name_df['source_id'].astype(str)
    sim_name_df['target_id'] = sim_name_df['target_id'].astype(str)
    
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
    
    # Ensure IDs are strings and not None
    family_df = family_df.dropna(subset=['source_id', 'target_id'])
    family_df['source_id'] = family_df['source_id'].astype(str)
    family_df['target_id'] = family_df['target_id'].astype(str)

    # Cross-Validation Split (Leave 20% out for true evaluation)
    # Using 'is_common_surname' to stratify? Or simple random?
    # Simple random is fine for now as we just want to ensure we don't cheat.
    # Note: build_training_data merges sim and family. We should split FAMILY first?
    # Actually, standard practice is to split the final constructed dataset?
    # BUT, we have "Implicit Negatives" from SimName. 
    # If we split Family edges into Train/Test, we must ensure Test edges appear as "Positives" in Test set
    # and "Negatives" (Candidates) in Train set? No, that's leakage.
    # Correct approach:
    # 1. Split Family Edges -> Train_Family, Test_Family
    # 2. Build Train Set: SimName pairs + Train_Family (label=1). 
    #    Exclude Test_Family from this set (or treat as 0? No, treat as "Unknown/Ignored").
    #    Actually simplest is: Use ALL SimName pairs as candidates. 
    #    Label=1 if in Train_Family. Label=0 otherwise (even if in Test_Family? -> Noise).
    #    Better: Remove Test_Family pairs from Training candidates entirely.
    
    # Let's keep it simple for this sprint as directed: 
    # "use cross vallidation and use 20% of the ground truth for evaluation and NOT use them for training"
    
    train_family, test_family = train_test_split(family_df, test_size=0.2, random_state=42)
    logger.info(f"Split Ground Truth: {len(train_family)} Train, {len(test_family)} Test")
    
    logger.info("Building training data (using only Train split of Positives)...")
    # We pass ONLY train_family to build_training_data
    # This means sim_name pairs that happen to be test_family edges will be labeled 0 (Negative).
    # This creates "Label Noise" (False Negatives in Training).
    # Critical: We must EXCLUDE test_family pairs from the negative sampling pool of the Training set.
    
    # 1. Build initial Train DF with Train positives
    train_df = build_training_data(sim_name_df, train_family, max_negatives_ratio=1.0)
    # Ensure IDs are strings (legacy from build_training_data could be mixed?)
    train_df.dropna(subset=['source_id', 'target_id'], inplace=True)
    train_df['source_id'] = train_df['source_id'].astype(str)
    train_df['target_id'] = train_df['target_id'].astype(str)
    
    # 2. Filter out rows that correspond to Test pairs to avoid False Negatives
    test_pairs = set(zip(test_family['source_id'], test_family['target_id']))
    # Also undirected
    test_pairs_undir = set()
    for s, t in test_pairs:
        test_pairs_undir.add(tuple(sorted((s, t))))
        
    # Filter train_df (where label=0)
    # If a negative sample is actually in test_family, drop it.
    initial_len = len(train_df)
    train_df['pair_key'] = train_df.apply(lambda r: tuple(sorted((r['source_id'], r['target_id']))), axis=1)
    train_df = train_df[~train_df['pair_key'].isin(test_pairs_undir)].drop(columns=['pair_key'])
    logger.info(f"Filtered {initial_len - len(train_df)} potential false negatives (test edges) from training set.")

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
        
        # --- 5b. Evaluate on Test Set (Hold-out) ---
        logger.info("Evaluating Best Model on Test Set...")
        # Build features for Test Pairs
        # Test Set Positives: test_family
        # Test Set Negatives: Sample from remaining SimName that are NOT in family at all?
        # A proper evaluation needs Negatives. 
        # We can re-use `build_training_data` but with test_family and ensuring disjoint from train
        # The key is: build_training_data selects negatives from SimName that are NOT in the passed 'family_df'.
        # If we pass 'test_family', it will pick sim_name pairs NOT in test_family as negatives.
        # BUT some of those "negatives" might be in 'train_family' (which is fine, they are positives there, but here valid negatives?)
        # NO. If a pair is in 'train_family', it IS a family edge. It cannot be a negative in Test.
        # So we must treat 'train_family' edges as "Known Positives" too, even if not in 'test_family'.
        
        # We need to construct a test set where:
        # Positives = test_family
        # Negatives = SimName pairs that are NEITHER in test_family NOR in train_family.
        
        # Manually constructing Test Set to ensure correctness:
        test_positives = test_family.copy()
        test_positives['label'] = 1
        
        # Get all SimName pairs
        # Filter out ANY family edge (Train OR Test)
        all_family_pairs = set(zip(family_df['source_id'], family_df['target_id']))
        all_family_pairs_undir = set()
        for s, t in all_family_pairs:
            all_family_pairs_undir.add(tuple(sorted((s, t))))
            
        test_negatives_candidates = sim_name_df.copy()
        test_negatives_candidates['pair_key'] = test_negatives_candidates.apply(lambda r: tuple(sorted((r['source_id'], r['target_id']))), axis=1)
        test_negatives = test_negatives_candidates[~test_negatives_candidates['pair_key'].isin(all_family_pairs_undir)].drop(columns=['pair_key'])
        
        # Sample negatives (1:1 ratio with test positives)
        n_pos = len(test_positives)
        if len(test_negatives) > n_pos:
            test_negatives = test_negatives.sample(n=n_pos, random_state=42)
        test_negatives['label'] = 0
        
        test_df = pd.concat([test_positives, test_negatives], ignore_index=True)
        # Ensure IDs are strings
        test_df.dropna(subset=['source_id', 'target_id'], inplace=True)
        test_df['source_id'] = test_df['source_id'].astype(str)
        test_df['target_id'] = test_df['target_id'].astype(str)
        
        # Now run prediction on test_df
        # We need to construct features similarly to run_model_variant
        # We can implement a helper or just adapt
        
        def prepare_features(df, variant, df_nodes):
            str_cols = ['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']
            df[str_cols] = df[str_cols].fillna(0.0)
            
            feats = []
            if variant != "baseline_fastrp":
                feats.append(df[str_cols].values)
            
            if "fastrp" in variant:
                emb = compute_embedding_features(df, df_nodes, "fastrp_embedding")
                # Fill missing with 0 for eval (shouldn't happen for valid nodes)
                # For robust stack, let's just use what we have, but shape must match.
                # compute_embedding_features returns list of lists.
                emb_mat = np.array([e if e is not None else [0]*128 for e in emb])
                feats.append(emb_mat)
                
            if "wcc" in variant:
                wcc = compute_community_features(df, df_nodes, "wcc")
                feats.append(wcc.values)
                
            if "louvain" in variant:
                lv = compute_community_features(df, df_nodes, "community_louvain")
                feats.append(lv.values)
            
            return np.hstack(feats)

        X_test = prepare_features(test_df, best_variant, df_nodes)
        X_test_scaled = best_scaler.transform(X_test)
        y_test = test_df['label'].values
        
        y_prob_test = best_model.predict_proba(X_test_scaled)[:, 1]
        test_auc = roc_auc_score(y_test, y_prob_test)
        logger.info(f"Test Set Evaluation ({len(test_df)} samples): AUC={test_auc:.4f}")
        mlflow.log_metric("test_auc", test_auc)


        # 6. Predict on ALL Candidates (Global)
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
