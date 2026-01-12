"""
Link Prediction Module - GDS Link Prediction with Precomputed SIM_NAME

This module implements link prediction for family relationships using:
1. Precomputed SIM_NAME relationships (lev_dist_last_name, lev_dist_patronymic, is_common_surname)
2. GDS-computed features (FastRP, Louvain, centrality metrics)
3. Model horse race with multiple feature combinations
4. MLflow tracking for all experiments
"""

import logging
from dataclasses import dataclass
from typing import Optional, Any

import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from mlflow_utils.tracking import log_metrics_classification

logger = logging.getLogger(__name__)


@dataclass
class LinkPredictionConfig:
    """Configuration for link prediction horse race."""
    variants: tuple[str, ...] = (
        "baseline_fastrp",
        "string_only",
        "fastrp_string",
        "fastrp_string_louvain",
        "fastrp_string_wcc",
        "fastrp_string_full",
    )
    common_surname_penalty: float = 0.3
    test_split: float = 0.2
    random_state: int = 42
    min_training_samples: int = 100


def fetch_sim_name_pairs(gds, include_family: bool = False) -> pd.DataFrame:
    """
    Fetch SIM_NAME relationships with their properties.
    
    Args:
        gds: GDS client
        include_family: If True, also return whether pair has FAMILY relationship
        
    Returns:
        DataFrame with columns: source_id, target_id, lev_dist_last_name, 
        lev_dist_patronymic, is_common_surname, has_family (if include_family)
    """
    logger.info("Fetching SIM_NAME relationships...")
    
    if include_family:
        query = """
        MATCH (p1:Person)-[s:SIM_NAME]->(p2:Person)
        OPTIONAL MATCH (p1)-[f:FAMILY]-(p2)
        WHERE f IS NULL OR f.source <> 'imputed'
        RETURN 
            p1.Id AS source_id,
            p2.Id AS target_id,
            s.lev_dist_last_name AS lev_dist_last_name,
            s.lev_dist_patronymic AS lev_dist_patronymic,
            s.is_common_surname AS is_common_surname,
            CASE WHEN f IS NOT NULL AND f.source <> 'imputed' THEN 1 ELSE 0 END AS has_family
        """
    else:
        query = """
        MATCH (p1:Person)-[s:SIM_NAME]->(p2:Person)
        RETURN 
            p1.Id AS source_id,
            p2.Id AS target_id,
            s.lev_dist_last_name AS lev_dist_last_name,
            s.lev_dist_patronymic AS lev_dist_patronymic,
            s.is_common_surname AS is_common_surname
        """
    
    df = gds.run_cypher(query)
    logger.info("Fetched %d SIM_NAME pairs", len(df))
    return df


def fetch_official_family_edges(gds) -> pd.DataFrame:
    """
    Fetch official (non-imputed) FAMILY relationships with string features computed on-the-fly.
    
    Returns:
        DataFrame with columns: source_id, target_id, lev_dist_last_name, 
        lev_dist_patronymic, is_common_surname, rel_type
    """
    logger.info("Fetching official FAMILY relationships...")
    
    query = """
    MATCH (p1:Person)-[f:FAMILY]->(p2:Person)
    WHERE f.source <> 'imputed'
    WITH p1, p2, f
    // Compute string features on the fly since SIM_NAME doesn't exist for FAMILY pairs
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
    
    df = gds.run_cypher(query)
    logger.info("Fetched %d official FAMILY edges", len(df))
    return df


def build_training_data(
    sim_name_df: pd.DataFrame,
    family_df: pd.DataFrame,
    include_hard_negatives: bool = True,
    max_negatives_ratio: float = 1.0,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Build training dataset for link prediction.
    
    Positives: Official FAMILY edges that also have SIM_NAME
    Negatives: SIM_NAME edges that are NOT FAMILY (hard negatives)
    
    Args:
        sim_name_df: DataFrame from fetch_sim_name_pairs
        family_df: DataFrame from fetch_official_family_edges
        include_hard_negatives: Use SIM_NAME non-family pairs as negatives
        max_negatives_ratio: Max ratio of negatives to positives
        random_state: Random seed for sampling
        
    Returns:
        Training DataFrame with label column
    """
    # Create family edge set (both directions) for filtering negatives
    family_set = set()
    for _, row in family_df.iterrows():
        family_set.add((row['source_id'], row['target_id']))
        family_set.add((row['target_id'], row['source_id']))
    
    # Positives: Official FAMILY edges
    positives = family_df.copy()
    positives['label'] = 1
    # Keep only common columns
    cols = ['source_id', 'target_id', 'lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname', 'label']
    positives = positives[cols]
    
    # Negatives: SIM_NAME pairs that are NOT FAMILY (hard negatives)
    sim_name_df = sim_name_df.copy()
    sim_name_df['is_family'] = sim_name_df.apply(
        lambda row: (row['source_id'], row['target_id']) in family_set or 
                    (row['target_id'], row['source_id']) in family_set,
        axis=1
    )
    negatives = sim_name_df[~sim_name_df['is_family']].copy()
    negatives['label'] = 0
    negatives = negatives[cols]
    
    # Sample negatives to balance dataset
    n_positives = len(positives)
    n_negatives = int(n_positives * max_negatives_ratio)
    
    if len(negatives) > n_negatives:
        negatives = negatives.sample(n=n_negatives, random_state=random_state)
    
    # Combine
    train_df = pd.concat([positives, negatives], ignore_index=True)
    
    logger.info(
        "Built training data: %d samples (%d positives, %d negatives)",
        len(train_df), n_positives, len(negatives)
    )
    
    # Fill NaNs in string features with 0.0 (no similarity)
    str_cols = ['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']
    train_df[str_cols] = train_df[str_cols].fillna(0.0)
    
    return train_df


def compute_embedding_features(
    pairs_df: pd.DataFrame,
    node_df: pd.DataFrame,
    embedding_col: str = "fastrp_embedding",
) -> np.ndarray:
    """
    Compute link features from node embeddings.
    
    Returns: Array of [hadamard..., l2_distance, cosine_similarity]
    """
    # Build embedding lookup as dict (handles duplicates, faster lookup)
    emb_dict = {}
    for _, row in node_df.iterrows():
        eid = row['entity_id']
        emb = row.get(embedding_col)
        if eid is not None and emb is not None:
            if isinstance(emb, (list, np.ndarray)) and len(emb) > 0:
                emb_dict[eid] = emb
    
    # Get embeddings for pairs
    source_ids = pairs_df['source_id'].values
    target_ids = pairs_df['target_id'].values
    
    source_emb = []
    target_emb = []
    
    for src, tgt in zip(source_ids, target_ids):
        src_e = emb_dict.get(src)
        tgt_e = emb_dict.get(tgt)
        if src_e is not None and tgt_e is not None:
            source_emb.append(src_e)
            target_emb.append(tgt_e)
        else:
            source_emb.append(None)
            target_emb.append(None)
    
    # Build feature matrix
    features = []
    for src_e, tgt_e in zip(source_emb, target_emb):
        if src_e is None or tgt_e is None:
            features.append(None)
            continue
            
        src_arr = np.array(src_e)
        tgt_arr = np.array(tgt_e)
        
        # Hadamard product
        hadamard = src_arr * tgt_arr
        
        # L2 distance
        l2 = np.linalg.norm(src_arr - tgt_arr)
        
        # Cosine similarity
        denom = (np.linalg.norm(src_arr) * np.linalg.norm(tgt_arr))
        cosine = np.dot(src_arr, tgt_arr) / denom if denom > 0 else 0.0
        
        feat_vec = list(hadamard) + [l2, cosine]
        features.append(feat_vec)
        
    return np.array(features, dtype=object)


def compute_community_features(
    pairs_df: pd.DataFrame,
    node_df: pd.DataFrame,
    community_col: str = "community_louvain",
) -> pd.DataFrame:
    """
    Compute binary feature: same_community.
    """
    # Build lookup
    comm_dict = node_df.set_index('entity_id')[community_col].to_dict()
    
    same_comm = []
    for _, row in pairs_df.iterrows():
        c1 = comm_dict.get(row['source_id'])
        c2 = comm_dict.get(row['target_id'])
        
        if c1 is not None and c2 is not None and c1 == c2 and c1 != -1:
            same_comm.append(1)
        else:
            same_comm.append(0)
            
    return pd.DataFrame({f"same_{community_col}": same_comm})


def compute_network_features(
    pairs_df: pd.DataFrame,
    node_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute network-based features for pairs."""
    node_df = node_df.set_index('entity_id')
    
    feature_cols = ['degree', 'pagerank', 'betweenness_centrality', 'closeness_centrality']
    available_cols = [c for c in feature_cols if c in node_df.columns]
    
    features = []
    for _, row in pairs_df.iterrows():
        src, tgt = row['source_id'], row['target_id']
        
        feat = {}
        for col in available_cols:
            src_val = node_df.loc[src, col] if src in node_df.index else 0
            tgt_val = node_df.loc[tgt, col] if tgt in node_df.index else 0
            
            feat[f'{col}_sum'] = src_val + tgt_val
            feat[f'{col}_diff'] = abs(src_val - tgt_val)
        
        features.append(feat)
    
    return pd.DataFrame(features)


def run_model_variant(
    variant_name: str,
    train_df: pd.DataFrame,
    node_df: pd.DataFrame,
    cfg: LinkPredictionConfig,
) -> tuple[Any, dict[str, float], Any]:
    """
    Train and evaluate a specific model variant.
    """
    logger.info("Training variant: %s", variant_name)
    
    feature_sets = []
    
    # String features (always included except for baseline_fastrp)
    if variant_name != "baseline_fastrp":
        feature_sets.append(train_df[['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']].values)
    
    # Embedding features
    if "fastrp" in variant_name:
        emb_features = compute_embedding_features(train_df, node_df, "fastrp_embedding")
        # Filter out rows where embeddings are missing
        valid_mask = [f is not None for f in emb_features]
        if sum(valid_mask) < len(emb_features):
            logger.warning("Dropping %d rows without embeddings", len(emb_features) - sum(valid_mask))
            train_df = train_df[valid_mask]
            
            # Re-filter string features if we subsetted
            if variant_name != "baseline_fastrp":
                feature_sets = [train_df[['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']].values]
            else:
                feature_sets = []
                
            # Re-compute embeddings for valid subset
            emb_features = compute_embedding_features(train_df, node_df, "fastrp_embedding")
            
        # Stack embedding features
        emb_matrix = np.stack([np.array(f) for f in emb_features if f is not None])
        feature_sets.append(emb_matrix)
        
    # Community features
    if "louvain" in variant_name:
        comm_df = compute_community_features(train_df, node_df, "community_louvain")
        feature_sets.append(comm_df.values)
        
    if "wcc" in variant_name:
        wcc_df = compute_community_features(train_df, node_df, "wcc")
        feature_sets.append(wcc_df.values)
        
    # Network features
    if "full" in variant_name:
        net_df = compute_network_features(train_df, node_df)
        feature_sets.append(net_df.values)
    
    # Combine features
    X = np.hstack(feature_sets)
    y = train_df['label'].values
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=cfg.test_split, 
        random_state=cfg.random_state,
        stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Train model
    model = LogisticRegression(max_iter=1000, random_state=cfg.random_state)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Compute metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
    }
    
    try:
        metrics['auc'] = roc_auc_score(y_test, y_prob)
    except ValueError:
        metrics['auc'] = 0.0
    
    logger.info("Variant %s: AUC=%.3f F1=%.3f", variant_name, metrics['auc'], metrics['f1'])
    
    return model, metrics, scaler


def run_link_prediction_workflow(
    gds,
    cfg,
    window_graph_name: str,
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
) -> Optional[pd.DataFrame]:
    """
    Main workflow for per-window link prediction with model horse race.
    
    Args:
        gds: GDS client
        cfg: RollingWindowConfig
        window_graph_name: Name of current window graph
        df_nodes: Node features DataFrame
        df_edges: Edge list DataFrame
        
    Returns:
        DataFrame of predicted edges (best model)
    """
    lp_config = LinkPredictionConfig()
    
    # 1. Fetch SIM_NAME data
    sim_name_df = fetch_sim_name_pairs(gds, include_family=False)
    if sim_name_df.empty:
        logger.warning("No SIM_NAME relationships found")
        return None
    
    # 2. Fetch official FAMILY edges
    family_df = fetch_official_family_edges(gds)
    if family_df.empty:
        logger.warning("No official FAMILY edges found for training")
        return None
    
    # 3. Build training data
    train_df = build_training_data(sim_name_df, family_df, random_state=lp_config.random_state)
    
    if len(train_df) < lp_config.min_training_samples:
        logger.warning(
            "Insufficient training samples: %d < %d", 
            len(train_df), lp_config.min_training_samples
        )
        return None
    
    # 4. Run horse race
    best_model = None
    best_scaler = None
    best_auc = -1
    best_variant = None
    
    for variant in lp_config.variants:
        with mlflow.start_run(run_name=f"{window_graph_name}_{variant}", nested=True):
            try:
                model, metrics, scaler = run_model_variant(variant, train_df.copy(), df_nodes, lp_config)
                
                # Log to MLflow
                mlflow.log_param("variant", variant)
                mlflow.log_param("window", window_graph_name)
                mlflow.log_param("n_positives", int((train_df['label'] == 1).sum()))
                mlflow.log_param("n_negatives", int((train_df['label'] == 0).sum()))
                mlflow.log_param("threshold", cfg.lp_threshold)
                mlflow.log_metrics(metrics)
                
                if metrics['auc'] > best_auc:
                    best_auc = metrics['auc']
                    best_model = model
                    best_scaler = scaler
                    best_variant = variant
                    
            except Exception as e:
                logger.error("Failed to train variant %s: %s", variant, e)
                mlflow.log_param("error", str(e))
    
    if best_model is None:
        logger.error("All model variants failed")
        return None
    
    logger.info("Best model: %s with AUC=%.3f", best_variant, best_auc)
    
    # 5. Predict on all SIM_NAME pairs (that aren't already FAMILY)
    # Build candidate set
    family_set = set()
    for _, row in family_df.iterrows():
        family_set.add((row['source_id'], row['target_id']))
        family_set.add((row['target_id'], row['source_id']))
    
    candidates = sim_name_df[
        ~sim_name_df.apply(
            lambda row: (row['source_id'], row['target_id']) in family_set or 
                        (row['target_id'], row['source_id']) in family_set,
            axis=1
        )
    ].copy()
    
    if candidates.empty:
        logger.info("No candidates for prediction (all SIM_NAME pairs are already FAMILY)")
        return pd.DataFrame()
    
    logger.info("Predicting on %d candidate pairs...", len(candidates))
    
    # Fill NaNs in string features for candidates
    # (Same as training)
    str_cols = ['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']
    candidates[str_cols] = candidates[str_cols].fillna(0.0)
    
    feature_sets = []
    
    # String features
    if best_variant != "baseline_fastrp":
        feature_sets.append(candidates[str_cols].values)
    
    # Embedding features
    if "fastrp" in best_variant:
        emb_features = compute_embedding_features(candidates, df_nodes, "fastrp_embedding")
        valid_mask = [f is not None for f in emb_features]
        if sum(valid_mask) < len(emb_features):
            logger.warning("Dropping %d candidates without embeddings", len(emb_features) - sum(valid_mask))
            candidates = candidates.iloc[valid_mask].reset_index(drop=True)
            
            # Re-filter string features if subsetted
            if best_variant != "baseline_fastrp":
                feature_sets = [candidates[str_cols].values]
            else:
                feature_sets = []
                
            # Re-compute embeddings
            emb_features = compute_embedding_features(candidates, df_nodes, "fastrp_embedding")
            
        emb_matrix = np.stack([np.array(f) for f in emb_features if f is not None])
        feature_sets.append(emb_matrix)
        
    # Community features
    if "louvain" in best_variant:
        comm_df = compute_community_features(candidates, df_nodes, "community_louvain")
        feature_sets.append(comm_df.values)
        
    if "wcc" in best_variant:
        wcc_df = compute_community_features(candidates, df_nodes, "wcc")
        feature_sets.append(wcc_df.values)
        
    # Network features
    if "full" in best_variant:
        net_df = compute_network_features(candidates, df_nodes)
        feature_sets.append(net_df.values)
        
    X_cand = np.hstack(feature_sets)
    X_cand = best_scaler.transform(X_cand)
    
    # Predict
    probs = best_model.predict_proba(X_cand)[:, 1]
    
    # Filter by threshold
    mask = probs > cfg.lp_threshold
    
    predicted_edges = candidates[mask].copy()
    predicted_edges['probability'] = probs[mask]
    predicted_edges['window_graph_name'] = window_graph_name
    predicted_edges['model_variant'] = best_variant
    predicted_edges['window_start_ms'] = df_nodes['window_start_ms'].iloc[0] if not df_nodes.empty else 0
    
    logger.info(
        "Found %d predicted edges above threshold %.2f (using %s model)",
        len(predicted_edges), cfg.lp_threshold, best_variant
    )
    
    return predicted_edges
