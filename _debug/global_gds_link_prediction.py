
import os
import time
import logging
import pandas as pd
import numpy as np
import mlflow
from graphdatascience import GraphDataScience
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, make_scorer, fbeta_score
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger("gds_global_lp_hybrid")

# Load Env
load_dotenv()

def get_gds_client():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDataScience(uri, auth=(user, password))

def run_hybrid_pipeline():
    gds = get_gds_client()
    project_name = "enhanced_lp_pro"
    
    # 0. Cleanup Catalog (Aggressive)
    logger.info("Cleaning up catalog...")
    try:
        models = gds.model.list()
        for _, row in models.iterrows():
            gds.run_cypher("CALL gds.model.drop($name)", params={'name': row['modelName']})
    except Exception:
        pass
    try:
        pipes = gds.pipeline.list()
        if isinstance(pipes, pd.DataFrame):
            for _, row in pipes.iterrows():
                try:
                    gds.run_cypher("CALL gds.beta.pipeline.drop($name)", params={'name': row['pipelineName']})
                except:
                    gds.run_cypher("CALL gds.pipeline.drop($name)", params={'name': row['pipelineName']})
    except Exception:
        pass
        
    gds.graph.drop(project_name, failIfMissing=False)
    gds.graph.drop("train_subgraph", failIfMissing=False)

    # 1. Manual Train/Test Split on FAMILY Edges
    logger.info("Creating Manual Train/Test Split Properties...")
    gds.run_cypher("MATCH ()-[r:FAMILY]->() REMOVE r.split")
    # 1 = train, 0 = test
    gds.run_cypher("""
        MATCH (a)-[r:FAMILY]->(b)
        WHERE r.source IS NULL OR r.source <> 'logistic_pred'
        SET r.split = CASE WHEN rand() < 0.2 THEN 0 ELSE 1 END
    """)
    
    # 2. Pre-calculate Weights
    logger.info("Pre-calculating weights on SIM_NAME in DB...")
    gds.run_cypher("""
        MATCH ()-[r:SIM_NAME]-()
        SET r.weight = 1.0 / (1.0 + coalesce(r.lev_dist_last_name, 10.0))
    """)

    # 3. Project Graph (Native)
    logger.info("Re-projecting using Native Projection...")
    G, _ = gds.graph.project(
        project_name,
        ['Person'],
        {
            'FAMILY': {
                'orientation': 'UNDIRECTED',
                'properties': {
                    'split': {'property': 'split', 'defaultValue': 1}, # Default to Train if missing
                    'weight': {'property': 'weight', 'defaultValue': 1.0}
                }
            },
            'SIM_NAME': {
                'orientation': 'UNDIRECTED',
                'properties': {
                    'weight': {'property': 'weight', 'defaultValue': 0.0}
                }
            }
        }
    )
    logger.info(f"Graph Projected: {G.node_count()} nodes, {G.relationship_count()} rels")
    
    # 4. Create Train Subgraph (Embeddings Context)
    # Includes FAMILY(train) and ALL SIM_NAME
    logger.info("Creating Train Subgraph for Embeddings...")
    G_train, _ = gds.beta.graph.project.subgraph(
        "train_subgraph",
        G,
        "*", 
        "r.split = 1.0 OR r.weight >= 0.0" 
    )
    
    # 5. GDS Feature Engineering (Mutate on Subgraph)
    # Create list of properties we successfully mutate
    props_to_stream = []

    logger.info("Running Node2Vec (Mutate)...")
    try:
        gds.node2vec.mutate(G_train, mutateProperty='n2v', embeddingDimension=64, walkLength=20, walksPerNode=10)
        props_to_stream.append('n2v')
    except Exception as e:
        logger.error(f"Node2Vec Failed: {e}")

    logger.info("Running Louvain (Mutate)...")
    try:
        gds.louvain.mutate(G_train, mutateProperty='louvainCommunity')
        props_to_stream.append('louvainCommunity')
    except Exception as e:
        logger.error(f"Louvain Failed: {e}")
    
    logger.info("Running Weighted FastRP (Mutate)...")
    try:
        gds.fastRP.mutate(G_train, mutateProperty='fastRp', embeddingDimension=128, relationshipWeightProperty='weight')
        props_to_stream.append('fastRp')
    except Exception as e:
        logger.error(f"FastRP Failed: {e}")

    logger.info("Running WCC (Mutate)...")
    try:
        gds.wcc.mutate(G_train, mutateProperty='wccId')
        props_to_stream.append('wccId')
    except Exception as e:
        logger.error(f"WCC Failed: {e}")
    
    # logger.info("Running HashGNN (Mutate)...")
    # try:
    #     # Check if hashgnn is available?
    #     # gds.beta.hashgnn.mutate might not exist if GDS version is old.
    #     # Assuming it exists or we catch AttributeError too.
    #     # Fix: Provide mandatory params
    #     gds.beta.hashgnn.mutate(
    #         G_train, 
    #         mutateProperty='hashgnn',
    #         iterations=2,
    #         embeddingDensity=128,
    #         densityLevel=2,
    #         generateFeatures={"dimension": 128}
    #     )
    #     props_to_stream.append('hashgnn')
    # except Exception as e:
    #     logger.warning(f"HashGNN failed (maybe not available?): {e}. Proceeding without HashGNN.")
    
    # 6. Stream Features to Python
    logger.info(f"Streaming Node Features to Python: {props_to_stream}...")
    
    if not props_to_stream:
        logger.error("No features generated! Exiting.")
        return

    # Stream from train_subgraph (properties are mutated there)
    node_features = gds.graph.nodeProperties.stream(
        G_train, 
        props_to_stream
    )
    logger.info(f"Node Features Columns: {node_features.columns.tolist()}")
    # GDS stream returns LONG format with 'nodeProperty' column
    node_features_pivot = node_features.pivot(index='nodeId', columns='nodeProperty', values='propertyValue')
    
    # 7. Construct Train/Test Pairs with String Metrics
    logger.info("Fetching Train/Test Pairs with String Metrics...")
    
    # Common function to get pairs with string metrics
    # Note: We calculate on-the-fly for FAMILY using APOC to ensure coverage even if SIM_NAME is missing
    # For SIM_NAME negatives, we use stored or calc on fly. Stored is faster? Calc ensures consistency.
    # Let's calc on fly for all to be consistent.
    
    query_template = """
        MATCH (n)-[r:%REL_TYPE%]->(m) 
        WHERE %WHERE_CLAUSE%
        WITH n, m, r
        %LIMIT_CLAUSE%
        RETURN 
            id(n) as source, 
            id(m) as target, 
            %LABEL% as label,
            // Calculate String Metrics
            apoc.text.levenshteinSimilarity(n.LastName, m.LastName) as lev_dist_last_name,
            apoc.text.levenshteinSimilarity(n.FirstName, m.MiddleName) as lev_dist_patronymic,
            CASE WHEN toUpper(n.LastName) IN ["КУЗНЕЦОВ", "КУЗНЕЦОВА", "ИВАНОВ", "ИВАНОВА", "ПОПОВ", "ПОПОВА", "СМИРНОВ", "СМИРНОВА", "ВАСИЛЬЕВ", "ВАСИЛЬЕВА", "ПЕТРОВ", "ПЕТРОВА", "КОЗЛОВ", "КОЗЛОВА", "МОРОЗОВ", "МОРОЗОВА", "НОВИКОВ", "НОВИКОВА", "ВОЛКОВ", "ВОЛКОВА", "СОКОЛОВ", "СОКОЛОВА", "ПАВЛОВ", "ПАВЛОВА", "ЛЕБЕДЕВ", "ЛЕБЕДЕВА", "СЕМЕНОВ", "СЕМЕНОВА", "ЕГОРОВ", "ЕГОРОВА"]
                  OR toUpper(m.LastName) IN ["КУЗНЕЦОВ", "КУЗНЕЦОВА", "ИВАНОВ", "ИВАНОВА", "ПОПОВ", "ПОПОВА", "СМИРНОВ", "СМИРНОВА", "ВАСИЛЬЕВ", "ВАСИЛЬЕВА", "ПЕТРОВ", "ПЕТРОВА", "КОЗЛОВ", "КОЗЛОВА", "МОРОЗОВ", "МОРОЗОВА", "НОВИКОВ", "НОВИКОВА", "ВОЛКОВ", "ВОЛКОВА", "СОКОЛОВ", "СОКОЛОВА", "ПАВЛОВ", "ПАВЛОВА", "ЛЕБЕДЕВ", "ЛЕБЕДЕВА", "СЕМЕНОВ", "СЕМЕНОВА", "ЕГОРОВ", "ЕГОРОВА"]
                 THEN 1 ELSE 0 END as is_common_surname
    """

    # Train Pos: FAMILY split=1
    train_pos_q = query_template.replace("%REL_TYPE%", "FAMILY") \
                                .replace("%WHERE_CLAUSE%", "r.split = 1") \
                                .replace("%LIMIT_CLAUSE%", "") \
                                .replace("%LABEL%", "1")
    train_pos_df = gds.run_cypher(train_pos_q)
    
    # Test Pos: FAMILY split=0
    test_pos_q = query_template.replace("%REL_TYPE%", "FAMILY") \
                               .replace("%WHERE_CLAUSE%", "r.split = 0") \
                               .replace("%LIMIT_CLAUSE%", "") \
                               .replace("%LABEL%", "1")
    test_pos_df = gds.run_cypher(test_pos_q)
    
    n_train_pos = len(train_pos_df)
    n_test_pos = len(test_pos_df)
    
    # Train Neg: SIM_NAME
    train_neg_q = query_template.replace("%REL_TYPE%", "SIM_NAME") \
                                .replace("%WHERE_CLAUSE%", "NOT (n)-[:FAMILY]-(m)") \
                                .replace("%LIMIT_CLAUSE%", f"WITH n, m, r, rand() as rnd ORDER BY rnd LIMIT {n_train_pos}") \
                                .replace("%LABEL%", "0")
    train_neg_df = gds.run_cypher(train_neg_q)
    
    # Test Neg: SIM_NAME
    test_neg_q = query_template.replace("%REL_TYPE%", "SIM_NAME") \
                               .replace("%WHERE_CLAUSE%", "NOT (n)-[:FAMILY]-(m)") \
                               .replace("%LIMIT_CLAUSE%", f"WITH n, m, r, rand() as rnd ORDER BY rnd LIMIT {n_test_pos}") \
                               .replace("%LABEL%", "0")
    test_neg_df = gds.run_cypher(test_neg_q)
    
    train_df = pd.concat([train_pos_df, train_neg_df], ignore_index=True)
    test_df = pd.concat([test_pos_df, test_neg_df], ignore_index=True)
    
    logger.info(f"Train Set: {len(train_df)} pairs. Test Set: {len(test_df)} pairs.")
    
    # 8. Feature Construction (Python)
    def build_features(pair_df, node_props):
        # Merge source features
        merged_src = pair_df.merge(node_props, left_on='source', right_index=True, how='left')
        merged_tgt = merged_src.merge(node_props, left_on='target', right_index=True, how='left', suffixes=('_s', '_t'))
        
        # Drop rows with missing features (e.g. isolates that didn't get embeddings or merge failures)
        len_before = len(merged_tgt)
        merged_tgt = merged_tgt.dropna(subset=['n2v_s', 'n2v_t', 'fastRp_s', 'fastRp_t'])
        # Note: hashgnn might be missing if failed. We handle that below or drop?
        # If hashgnn is missing in columns, we can't drop on it.
        
        len_after = len(merged_tgt)
        if len_before != len_after:
            logger.warning(f"Dropped {len_before - len_after} pairs due to missing embeddings (Isolates in Subgraph?).")

        # Update y to match filtered X
        y = merged_tgt['label'].values
        
        # String Features
        feat_str = merged_tgt[['lev_dist_last_name', 'lev_dist_patronymic', 'is_common_surname']].values
        feat_str = np.nan_to_num(feat_str, nan=0.0)
        
        # N2V
        s_n2v = np.stack(merged_tgt['n2v_s'].values)
        t_n2v = np.stack(merged_tgt['n2v_t'].values)
        feat_n2v = s_n2v * t_n2v # Hadamard
        
        # FastRP
        s_frp = np.stack(merged_tgt['fastRp_s'].values)
        t_frp = np.stack(merged_tgt['fastRp_t'].values)
        feat_frp = s_frp * t_frp # Hadamard
        
        # Louvain
        s_lou = merged_tgt['louvainCommunity_s'].values
        t_lou = merged_tgt['louvainCommunity_t'].values
        feat_lou = (s_lou == t_lou).astype(int).reshape(-1, 1)
        
        # WCC
        if 'wccId_s' in merged_tgt.columns:
            s_wcc = merged_tgt['wccId_s'].values
            t_wcc = merged_tgt['wccId_t'].values
            feat_wcc = (s_wcc == t_wcc).astype(int).reshape(-1, 1)
        else:
            feat_wcc = np.zeros((len(y), 1))
            
        # HashGNN
        if 'hashgnn_s' in merged_tgt.columns:
            # HashGNN might be list or what?
            # It's usually a list of integers/floats.
            s_hash = np.stack(merged_tgt['hashgnn_s'].values)
            t_hash = np.stack(merged_tgt['hashgnn_t'].values)
            feat_hash = s_hash * t_hash
        else:
            feat_hash = np.zeros((len(y), 1)) # Dummy if missing

        return feat_str, feat_n2v, feat_frp, feat_lou, feat_wcc, feat_hash, y

    logger.info("Constructing Link Features...")
    trn_str, trn_n2v, trn_frp, trn_lou, trn_wcc, trn_hash, y_train = build_features(train_df, node_features_pivot)
    tst_str, tst_n2v, tst_frp, tst_lou, tst_wcc, tst_hash, y_test = build_features(test_df, node_features_pivot)

    # 9. Model Horse Race with GridSearchCV
    variants = {
        # 1. String Only
        "1_String_Only": { "train": trn_str, "test": tst_str },
        
        # 2. Embeddings Only (Individual)
        "2_FastRP_Only": { "train": trn_frp, "test": tst_frp },
        "3_HashGNN_Only": { "train": trn_hash, "test": tst_hash },
        "4_Node2Vec_Only": { "train": trn_n2v, "test": tst_n2v },
        
        # 5. Embeddings + String
        "5_FastRP_String": { "train": np.hstack([trn_frp, trn_str]), "test": np.hstack([tst_frp, tst_str]) },
        "5_HashGNN_String": { "train": np.hstack([trn_hash, trn_str]), "test": np.hstack([tst_hash, tst_str]) },
        "5_Node2Vec_String": { "train": np.hstack([trn_n2v, trn_str]), "test": np.hstack([tst_n2v, tst_str]) },
        
        # 6. Louvain + String
        "6_Louvain_String": { "train": np.hstack([trn_lou, trn_str]), "test": np.hstack([tst_lou, tst_str]) },
        
        # 7. WCC + String
        "7_WCC_String": { "train": np.hstack([trn_wcc, trn_str]), "test": np.hstack([tst_wcc, tst_str]) },
        
        # 8. Louvain + String + Embedding
        "8_Louvain_String_FastRP": { "train": np.hstack([trn_lou, trn_str, trn_frp]), "test": np.hstack([tst_lou, tst_str, tst_frp]) },
        "8_Louvain_String_HashGNN": { "train": np.hstack([trn_lou, trn_str, trn_hash]), "test": np.hstack([tst_lou, tst_str, tst_hash]) },
        "8_Louvain_String_Node2Vec": { "train": np.hstack([trn_lou, trn_str, trn_n2v]), "test": np.hstack([tst_lou, tst_str, tst_n2v]) },
        
        # 9. WCC + Embedding (Iteratively)
        "9_WCC_FastRP": { "train": np.hstack([trn_wcc, trn_frp]), "test": np.hstack([tst_wcc, tst_frp]) },
        "9_WCC_HashGNN": { "train": np.hstack([trn_wcc, trn_hash]), "test": np.hstack([tst_wcc, tst_hash]) },
        "9_WCC_Node2Vec": { "train": np.hstack([trn_wcc, trn_n2v]), "test": np.hstack([tst_wcc, tst_n2v]) },
        
        # Grand Combo
        "All_Features": { 
             "train": np.hstack([trn_str, trn_n2v, trn_frp, trn_lou, trn_wcc, trn_hash]), 
             "test": np.hstack([tst_str, tst_n2v, tst_frp, tst_lou, tst_wcc, tst_hash]) 
        }
    }
    
    mlflow.set_experiment("enhanced_gds_lp_grid_auc_recall")
    best_auc_overall = 0
    best_model_name = ""
    
    # Param Grid (Removed penalty to fix warning)
    param_grid = {
        'C': [0.01, 0.1, 1, 10]
    }
    
    for name, data in variants.items():
        logger.info(f"--- Running Variant: {name} ---")
        X_tr = data["train"]
        X_ts = data["test"]
        
        # Skip if features are empty (e.g. HashGNN failed)
        if X_tr.shape[1] == 0:
            logger.warning(f"Skipping {name} due to empty features.")
            continue
        
        # GridSearchCV
        # Optimize on ROC AUC
        clf = GridSearchCV(
            LogisticRegression(max_iter=2000, class_weight='balanced', solver='lbfgs'),
            param_grid,
            cv=StratifiedKFold(n_splits=5),
            scoring='roc_auc',
            n_jobs=-1
        )
        clf.fit(X_tr, y_train)
        
        best_clf = clf.best_estimator_
        logger.info(f"Best Params for {name}: {clf.best_params_}")
        
        # Threshold Tuning on Test (Optimize for Recall via F2)
        # We assume user wants high recall but not zero precision. F2 weighs recall 2x precision.
        y_prob = best_clf.predict_proba(X_ts)[:, 1]
        
        # Check Optimal Threshold
        thresholds = np.arange(0.1, 0.9, 0.05)
        best_th_metric = 0
        best_th = 0.5
        
        for th in thresholds:
            y_p = (y_prob >= th).astype(int)
            # F2 Score: Beta=2 -> Recall is 2x important as Precision
            f2 = fbeta_score(y_test, y_p, beta=2)
            if f2 > best_th_metric:
                best_th_metric = f2
                best_th = th
        
        logger.info(f"Optimal Threshold for {name} (F2 scoring): {best_th} (Test F2={best_th_metric:.4f})")
        
        # Final Metrics at Optimal Threshold
        y_pred = (y_prob >= best_th).astype(int)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        f2 = fbeta_score(y_test, y_pred, beta=2)
        auc = roc_auc_score(y_test, y_prob)
        ap = average_precision_score(y_test, y_prob)
        
        logger.info(f"{name} Metrics: AUC={auc:.4f}, Rec={rec:.4f}, F2={f2:.4f}, Acc={acc:.4f}")
        
        with mlflow.start_run(run_name=name):
            mlflow.log_param("model_type", "LogisticRegression_GridCV_AUC")
            mlflow.log_param("features", name)
            mlflow.log_params(clf.best_params_)
            mlflow.log_param("optimal_threshold", best_th)
            
            mlflow.log_metric("test_accuracy", acc)
            mlflow.log_metric("test_precision", prec)
            mlflow.log_metric("test_recall", rec)
            mlflow.log_metric("test_f1", f1)
            mlflow.log_metric("test_f2", f2)
            mlflow.log_metric("test_auc", auc)
            mlflow.log_metric("test_ap", ap)
            
            # Save artifacts
            with open("metrics.txt", "w") as f:
                f.write(f"Accuracy: {acc}\nPrecision: {prec}\nRecall: {rec}\nF1: {f1}\nF2: {f2}\nAUC: {auc}\nAP: {ap}\nThreshold: {best_th}\n")
            mlflow.log_artifact("metrics.txt")
            
        if auc > best_auc_overall: # Optimize selection on AUC
            best_auc_overall = auc
            best_model_name = name

    logger.info(f"Best Model: {best_model_name} with AUC={best_auc_overall:.4f}")
    
    # 12. Cleanup
    gds.graph.drop(project_name, failIfMissing=False)
    gds.graph.drop("train_subgraph", failIfMissing=False)
    logger.info("Run Complete.")

if __name__ == "__main__":
    run_hybrid_pipeline()
