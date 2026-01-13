from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
from graphdatascience import GraphDataScience
from neo4j.exceptions import ServiceUnavailable, SessionExpired, ClientError, GqlError
from tqdm.auto import tqdm

from config import Neo4jConfig, RollingWindowConfig, validate_rel_types
from dates import iter_year_windows
from gds_client import connect_gds
from feature_blocks import BANK_FEATS_BLOCKS, BANK_FEATS_DIM, other_bank_feats_indices
from hashing import stable_hash_dict
from metrics import gds_config_metadata, run_window_algorithms, compute_fcr_temporal
from mlflow_utils.tracking import setup_experiment
from parquet import coerce_float_list_column, expand_embedding_column, slice_vector_column, write_parquet
from link_prediction import run_link_prediction_workflow

logger = logging.getLogger(__name__)


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v in seen:
            continue
        out.append(v)
        seen.add(v)
    return out


def _required_base_node_properties(cfg: RollingWindowConfig) -> set[str]:
    required: set[str] = {"tStart", "tEnd"}

    if cfg.export_feature_vectors or cfg.export_feature_blocks:
        required.add("bank_feats")
    if cfg.export_feature_vectors:
        required.update({"network_feats", "is_dead"})
    if cfg.run_hashgnn:
        required.update(cfg.hashgnn_feature_properties)

    return required



def ensure_base_graph(
    gds: GraphDataScience,
    *,
    cfg: RollingWindowConfig,
    cypher_path: Path | None = None,  # Kept for compatibility but unused
    rebuild: bool = False,
) -> None:
    """
    Ensure the base graph exists in GDS using Native Projection.
    This replaces the old Cypher-based projection to ensure robust handling of Isolates.
    """
    logger.info("Ensuring base graph '%s' (rebuild=%s)", cfg.base_graph_name, rebuild)
    
    # Check if exists
    try:
        G = gds.graph.get(cfg.base_graph_name)
        if not rebuild:
            # We could check properties here, but native projection configuration is hard to inspect deeply via API.
            # Assuming if it exists and we don't request rebuild, it's fine.
            # But let's check node count at least?
            logger.info("Base graph '%s' already exists (nodes=%d); skipping projection", cfg.base_graph_name, G.node_count())
            return
    except ValueError:
        pass  # Does not exist or error getting it
    except Exception:
        pass 

    logger.info("Dropping base graph '%s' (if exists)", cfg.base_graph_name)
    gds.graph.drop(cfg.base_graph_name, failIfMissing=False)

    logger.info("Projecting base graph '%s' using Native Projection...", cfg.base_graph_name)
    
    # Constants for defaults
    MIN_T = -9_007_199_254_740_991.0
    MAX_T = 9_007_199_254_740_991.0
    

    # Node Projection: Label specific to avoid NPE on missing properties
    # Common props (Scalars only - robust)
    base_props = {
        "tStart": {"property": "temporal_start", "defaultValue": MIN_T},
        "tEnd": {"property": "temporal_end", "defaultValue": MAX_T},
        "is_dead": {"property": "is_dead_int", "defaultValue": 0},
        "gds_id": {"property": "gds_id", "defaultValue": -1},
    }
    
    # We do NOT project array features (bank_feats, network_feats) into GDS 
    # because GDS Native Projection for arrays with defaults is unstable (NPEs/Crash).
    # Instead, we fetch them from DB during streaming.

    node_projection = {
        "Bank": {"properties": base_props},
        "Company": {"properties": base_props},
        "Person": {"properties": base_props}
    }

    # Relationship Projection
    # Mapped from migration (imputed_flag) and existing properties.
    rel_props = {
        "weight": {"property": "Size", "defaultValue": 1.0},
        "tStart": {"property": "temporal_start", "defaultValue": MIN_T},
        "tEnd": {"property": "temporal_end", "defaultValue": MAX_T},
        "imputedFlag": {"property": "imputed_flag", "defaultValue": 0.0}
    }

    relationship_projection = {
        rel_type: {
            "type": rel_type,
            "properties": rel_props,
            "orientation": "NATURAL"
        }
        for rel_type in cfg.rel_types
    }

    try:
        G, result = gds.graph.project(
            cfg.base_graph_name,
            node_projection,
            relationship_projection,
            readConcurrency=int(cfg.read_concurrency)
        )
        
        logger.info(
            "Base graph '%s' ready (nodes=%s rels=%s projectMillis=%s)",
            cfg.base_graph_name,
            result.get("nodeCount"),
            result.get("relationshipCount"),
            result.get("projectMillis"),
        )
    except Exception as e:
        logger.error("Failed to project base graph: %s", e)
        raise e


def _relationship_type_predicate(rel_types: tuple[str, ...]) -> str:
    validate_rel_types(rel_types)
    return " OR ".join(f"r:{t}" for t in rel_types)


def build_filter_predicates(*, rel_types: tuple[str, ...], include_imputed01: int) -> tuple[str, str, dict[str, Any]]:
    node_filter = "(n:Bank OR n:Company OR n:Person) AND n.tStart < $end AND n.tEnd > $start"

    rel_type_pred = _relationship_type_predicate(rel_types)
    rel_filter = (
        f"({rel_type_pred}) AND r.tStart < $end AND r.tEnd > $start "
        "AND (r:FAMILY = FALSE OR $includeImputed01 = 1.0 OR r.imputedFlag = 0.0)"
    )

    params = {"includeImputed01": float(include_imputed01)}
    return node_filter, rel_filter, params


def export_window_edges(
    gds: GraphDataScience,
    G,
    *,
    rel_types: tuple[str, ...],
    edge_id_property: str,
) -> pd.DataFrame:
    validate_rel_types(rel_types)
    rels = gds.graph.relationships.stream(G, relationship_types=list(rel_types))

    # Map internal nodeIds -> stable DB property (e.g. `Id`) once, then join twice.
    node_map = gds.graph.nodeProperties.stream(
        G,
        ["tStart"],
        separate_property_columns=True,
        db_node_properties=[edge_id_property],
    )[["nodeId", edge_id_property]]

    source_col = f"source_{edge_id_property}"
    target_col = f"target_{edge_id_property}"

    rels = rels.merge(
        node_map.rename(columns={"nodeId": "sourceNodeId", edge_id_property: source_col}),
        on="sourceNodeId",
        how="left",
    ).merge(
        node_map.rename(columns={"nodeId": "targetNodeId", edge_id_property: target_col}),
        on="targetNodeId",
        how="left",
    )
    return rels


def run_windows(
    gds: GraphDataScience,
    *,
    cfg: RollingWindowConfig,
    neo4j_cfg: Neo4jConfig,
    base_projection_cypher: Path,
    rebuild_base_graph: bool = False,
    expand_embeddings: bool = False,
    skip_existing: bool = True,
    max_retries: int = 3,
    retry_backoff_s: float = 2.0,
    show_tqdm: bool = True,
) -> None:
    ensure_base_graph(gds, cfg=cfg, cypher_path=base_projection_cypher, rebuild=rebuild_base_graph)
    base_G = gds.graph.get(cfg.base_graph_name)

    if cfg.run_link_prediction:
        setup_experiment("exp_014_link_prediction")

    windows = iter_year_windows(
        start_year=cfg.start_year,
        end_start_year=cfg.end_start_year,
        window_years=cfg.window_years,
        step_years=cfg.step_years,
    )

    metadata = gds_config_metadata(cfg)
    params_hash = stable_hash_dict(metadata)

    manifest_rows: list[dict[str, Any]] = []
    manifest_path = cfg.output_dir / "manifest" / f"manifest_{params_hash}.parquet"

    try:
        logger.info(
            "Processing %d windows (start_year=%d end_start_year=%d window_years=%d step_years=%d)",
            len(windows),
            cfg.start_year,
            cfg.end_start_year,
            cfg.window_years,
            cfg.step_years,
        )
        pbar = tqdm(windows, desc="Rolling windows", unit="window", disable=not show_tqdm)
        for w in pbar:
            window_graph_name = f"rw_{w.name_suffix}"
            node_out_path = cfg.output_dir / "nodes" / f"node_features_{window_graph_name}.parquet"
            edges_out_path = cfg.output_dir / "edges" / f"edge_list_{window_graph_name}.parquet"
            if show_tqdm:
                pbar.set_postfix_str(f"{window_graph_name} | check")

            required_node_cols: set[str] = set()
            if cfg.export_feature_vectors:
                required_node_cols.update({"bank_feats", "network_feats", "is_dead"})
            if cfg.export_feature_blocks:
                required_node_cols.update(BANK_FEATS_BLOCKS.keys())
                required_node_cols.add("other_feats")
            if cfg.run_hashgnn:
                required_node_cols.add("hash_gnn_embedding")
            if cfg.run_node2vec:
                required_node_cols.add("node2vec_embedding")

            need_nodes = True
            if skip_existing and node_out_path.exists():
                existing_node_cols = set(pq.ParquetFile(node_out_path).schema_arrow.names)
                missing_node_cols = required_node_cols.difference(existing_node_cols)
                if missing_node_cols:
                    logger.info(
                        "Existing node parquet is missing required columns %s; recomputing: %s",
                        sorted(missing_node_cols),
                        node_out_path,
                    )
                else:
                    need_nodes = False

            need_edges = bool(cfg.export_edges)
            if need_edges and skip_existing and edges_out_path.exists():
                required_edge_cols = {
                    "sourceNodeId",
                    "targetNodeId",
                    "relationshipType",
                    f"source_{cfg.edge_id_property}",
                    f"target_{cfg.edge_id_property}",
                }
                existing_edge_cols = set(pq.ParquetFile(edges_out_path).schema_arrow.names)
                missing_edge_cols = required_edge_cols.difference(existing_edge_cols)
                if missing_edge_cols:
                    logger.info(
                        "Existing edge parquet is missing required columns %s; recomputing: %s",
                        sorted(missing_edge_cols),
                        edges_out_path,
                    )
                else:
                    need_edges = False

            if not need_nodes and not need_edges:
                if show_tqdm:
                    pbar.set_postfix_str(f"{window_graph_name} | skip")
                logger.info(
                    "Skipping %s (outputs exist): nodes=%s edges=%s",
                    window_graph_name,
                    node_out_path,
                    edges_out_path if cfg.export_edges else "(disabled)",
                )
                node_row_count = pq.ParquetFile(node_out_path).metadata.num_rows if node_out_path.exists() else 0
                edge_row_count = pq.ParquetFile(edges_out_path).metadata.num_rows if edges_out_path.exists() else 0
                manifest_rows.append(
                    {
                        "window_graph_name": window_graph_name,
                        "window_start_ms": w.start_ms,
                        "window_end_ms": w.end_ms,
                        "window_start_year": w.start_year,
                        "window_end_year_inclusive": w.end_year_inclusive,
                        "node_count": int(node_row_count),
                        "edge_count": int(edge_row_count),
                        "rel_types": list(cfg.rel_types),
                        "include_imputed01": int(cfg.include_imputed01),
                        "export_edges": bool(cfg.export_edges),
                        "edge_id_property": str(cfg.edge_id_property),
                        "export_feature_vectors": bool(cfg.export_feature_vectors),
                        "export_feature_blocks": bool(cfg.export_feature_blocks),
                        "run_hashgnn": bool(cfg.run_hashgnn),
                        "run_node2vec": bool(cfg.run_node2vec),
                        "params_hash": params_hash,
                        "skipped_existing": True,
                    }
                )
                continue

            logger.info(
                "Window %s (start=%d end=%d): filtering base graph and running algorithms",
                window_graph_name,
                w.start_ms,
                w.end_ms,
            )
            if show_tqdm:
                pbar.set_postfix_str(f"{window_graph_name} | filter+algs")
            node_filter, rel_filter, base_params = build_filter_predicates(
                rel_types=cfg.rel_types,
                include_imputed01=cfg.include_imputed01,
            )

            filter_params = {
                **base_params,
                "start": float(w.start_ms),
                "end": float(w.end_ms),
            }

            attempt = 0
            while attempt <= max_retries:
                temp_graph_name = f"temp_{window_graph_name}"
                try:
                    logger.info("Creating window graph %s (attempt %d/%d)", window_graph_name, attempt + 1, max_retries + 1)
                    
                    # Ensure clean slate
                    gds.graph.drop(window_graph_name, failIfMissing=False)
                    gds.graph.drop(temp_graph_name, failIfMissing=False)

                    # --- PASS 1: Temporal Filter ---
                    # Includes all Banks/Companies and all Persons active or defaulting (since Persons lack temporal props)
                    logger.info("Pass 1: Temporal filtering...")
                    with gds.graph.filter(
                        temp_graph_name,
                        base_G,
                        node_filter,
                        rel_filter,
                        parameters=filter_params,
                        concurrency=cfg.read_concurrency,
                    ) as temp_G:
                        
                        # --- PASS 2: Degree Filter for Persons ---
                        # Run degree once to find who is actually participant
                        logger.info("Pass 2: Degree mutation for participants...")
                        gds.degree.mutate(temp_G, mutateProperty="active_degree", concurrency=cfg.read_concurrency)
                        
                        # Final Filter: Keep only connected Persons OR any Bank/Company
                        # (We keep all banks/companies even if isolates for FCR census)
                        final_node_filter = "n.active_degree > 0.0 OR n:Bank OR n:Company"
                        
                        logger.info("Pass 3: Final participant filtering...")
                        with gds.graph.filter(
                            window_graph_name,
                            temp_G,
                            final_node_filter,
                            "*", # Keep all relationships from temp_G
                            concurrency=cfg.read_concurrency
                        ) as G:
                            df = None
                            df_edges = None

                            if need_nodes:
                                logger.info("Running window algorithms...")
                                properties = run_window_algorithms(gds, G, cfg)
                                logger.info("Algorithms completed.")

                                # Determine properties to fetch from GDS (In-Memory) vs DB
                                if cfg.export_feature_vectors:
                                    properties.extend(["is_dead"])
                                
                                # Ensure gds_id is streamed for ID merging
                                properties.append("gds_id")
                                
                                properties = _unique_preserve_order(properties)
                                
                                db_node_props = [cfg.id_property]
                                if cfg.export_edges and cfg.edge_id_property != cfg.id_property:
                                    db_node_props.append(cfg.edge_id_property)
                                
                                if cfg.export_feature_vectors:
                                    db_node_props.extend(["bank_feats", "network_feats"])
                                elif cfg.export_feature_blocks:
                                    db_node_props.append("bank_feats")
                                
                                logger.info("Streaming node properties...")
                                df = gds.graph.nodeProperties.stream(
                                    G,
                                    properties,
                                    separate_property_columns=True,
                                    db_node_properties=db_node_props,
                                    listNodeLabels=True,
                                )
                                logger.info("Node streaming completed. Shape: %s", df.shape if df is not None else "None")

                            if need_edges:
                                logger.info("Exporting edges...")
                                df_edges = export_window_edges(
                                    gds,
                                    G,
                                    rel_types=cfg.rel_types,
                                    edge_id_property=cfg.edge_id_property,
                                )
                                logger.info("Edge export completed. Shape: %s", df_edges.shape if df_edges is not None else "None")

                            # --- Resilient Post-Processing (Inside attempt loop) ---
                            
                            # Merge IDs from Cypher using gds_id (Robust fallback)
                            logger.info("Fetching Node IDs via Cypher (using gds_id match)...")
                            id_query = f"""
                            MATCH (n)
                            WHERE n.{cfg.id_property} IS NOT NULL
                            RETURN id(n) as gds_id, n.{cfg.id_property} as entity_id
                            """
                            ids_df = gds.run_cypher(id_query)
                            ids_df["gds_id"] = ids_df["gds_id"].astype("int64")

                            # Merge
                            if df is not None:
                                if "gds_id" in df.columns:
                                    df["gds_id"] = df["gds_id"].astype("int64")
                                    df = df.merge(ids_df, on="gds_id", how="left")
                                else:
                                    logger.error("gds_id missing from dataframe! Cannot merge IDs.")

                                missing_ids = df["entity_id"].isna().sum() if "entity_id" in df.columns else len(df)
                                if missing_ids > 0:
                                    logger.warning("Merged %d nodes, but %d have missing entity_id", len(df), missing_ids)
                            
                            if df is not None and "entity_id" in df.columns:
                                sample_ids = df["entity_id"].dropna().head().tolist()
                                logger.info("IDs fetched successfully. Sample: %s", sample_ids)

                            # Compute FCR
                            node_count = 0
                            edge_count = 0

                            if df is not None:
                                df["window_start_ms"] = w.start_ms
                                df["window_end_ms"] = w.end_ms
                                df["window_start_year"] = w.start_year
                                df["window_end_year_inclusive"] = w.end_year_inclusive
                                df["window_graph_name"] = window_graph_name
                                df["params_hash"] = params_hash

                                # Degrees & Labels
                                if "in_degree" in df.columns and "out_degree" in df.columns:
                                    df["total_degree"] = df["in_degree"] + df["out_degree"]
                                
                                # FCR calculation
                                logger.info("Computing FCR temporal via Cypher...")
                                fcr_map = compute_fcr_temporal(gds, w.start_ms, w.end_ms, cfg.id_property)
                                if fcr_map:
                                    # Use entity_id (UUID) to map FCR
                                    df["fcr_temporal"] = df["entity_id"].map(fcr_map).fillna(0.0)
                                    applied = df["fcr_temporal"].gt(0).sum()
                                    logger.info("Applied fcr_temporal to %d nodes", applied)
                                else:
                                    df["fcr_temporal"] = 0.0

                                # --- Feature Transformations ---
                                if "fastrp_embedding" in df.columns:
                                    df = coerce_float_list_column(df, column="fastrp_embedding")
                                if "hash_gnn_embedding" in df.columns:
                                    df = coerce_float_list_column(df, column="hash_gnn_embedding")
                                if "node2vec_embedding" in df.columns:
                                    df = coerce_float_list_column(df, column="node2vec_embedding")

                                if cfg.export_feature_vectors:
                                    df = coerce_float_list_column(df, column="bank_feats")
                                    df = coerce_float_list_column(df, column="network_feats")
                                    
                                    # Fill missing bank_feats (e.g. for Persons) with zeros for slicing
                                    if "bank_feats" in df.columns:
                                        zero_vec = [0.0] * BANK_FEATS_DIM
                                        df["bank_feats"] = df["bank_feats"].apply(lambda x: zero_vec if x is None or (isinstance(x, list) and not x) else x)

                                if cfg.export_feature_blocks and "bank_feats" in df.columns:
                                    for block_name, indices in BANK_FEATS_BLOCKS.items():
                                        df = slice_vector_column(
                                            df,
                                            column="bank_feats",
                                            indices=indices,
                                            out_column=block_name,
                                            expected_dim=BANK_FEATS_DIM,
                                        )
                                    df = slice_vector_column(
                                        df,
                                        column="bank_feats",
                                        indices=other_bank_feats_indices(),
                                        out_column="other_feats",
                                        expected_dim=BANK_FEATS_DIM,
                                    )

                                if expand_embeddings and "fastrp_embedding" in df.columns:
                                    emb_df = expand_embedding_column(
                                        df[["fastrp_embedding"]],
                                        column="fastrp_embedding",
                                        dim=cfg.embedding_dimension,
                                        prefix="emb_",
                                    )
                                    df = pd.concat([df, emb_df], axis=1)

                                if show_tqdm:
                                    pbar.set_postfix_str(f"{window_graph_name} | write_nodes")
                                logger.info("Writing %s (rows=%d cols=%d)", node_out_path, df.shape[0], df.shape[1])
                                write_parquet(df, node_out_path)
                                node_count = int(df.shape[0])

                            if df_edges is not None:
                                df_edges["window_start_ms"] = w.start_ms
                                df_edges["window_end_ms"] = w.end_ms
                                df_edges["window_start_year"] = w.start_year
                                df_edges["window_end_year_inclusive"] = w.end_year_inclusive
                                df_edges["window_graph_name"] = window_graph_name
                                df_edges["params_hash"] = params_hash
                                df_edges["edge_id_property"] = str(cfg.edge_id_property)

                                if show_tqdm:
                                    pbar.set_postfix_str(f"{window_graph_name} | write_edges")
                                logger.info("Writing %s (rows=%d cols=%d)", edges_out_path, df_edges.shape[0], df_edges.shape[1])
                                write_parquet(df_edges, edges_out_path)
                                edge_count = int(df_edges.shape[0])

                            # Link Prediction
                            if cfg.run_link_prediction and df is not None and df_edges is not None:
                                try:
                                    predicted_edges = run_link_prediction_workflow(gds, cfg, window_graph_name, df, df_edges)
                                    if predicted_edges is not None and not predicted_edges.empty:
                                        pred_path = cfg.output_dir / "predicted_edges" / f"predicted_edges_{window_graph_name}.parquet"
                                        pred_path.parent.mkdir(parents=True, exist_ok=True)
                                        write_parquet(predicted_edges, pred_path)
                                        logger.info("Saved %d predicted edges to %s", len(predicted_edges), pred_path)
                                except Exception as lp_err:
                                    logger.error("Link prediction failed for %s: %s", window_graph_name, lp_err)

                            # Record in manifest
                            manifest_rows.append(
                                {
                                    "window_graph_name": window_graph_name,
                                    "window_start_ms": w.start_ms,
                                    "window_end_ms": w.end_ms,
                                    "window_start_year": w.start_year,
                                    "window_end_year_inclusive": w.end_year_inclusive,
                                    "node_count": int(node_count),
                                    "edge_count": int(edge_count),
                                    "rel_types": list(cfg.rel_types),
                                    "include_imputed01": int(cfg.include_imputed01),
                                    "export_edges": bool(cfg.export_edges),
                                    "edge_id_property": str(cfg.edge_id_property),
                                    "export_feature_vectors": bool(cfg.export_feature_vectors),
                                    "export_feature_blocks": bool(cfg.export_feature_blocks),
                                    "run_hashgnn": bool(cfg.run_hashgnn),
                                    "run_node2vec": bool(cfg.run_node2vec),
                                    "params_hash": params_hash,
                                    "skipped_existing": False,
                                }
                            )

                            break # Success! Exit retry loop

                except (ServiceUnavailable, SessionExpired, ClientError, GqlError) as e:
                    attempt += 1
                    if attempt > max_retries:
                        logger.exception("Window %s failed after %d retries", window_graph_name, max_retries)
                        raise
                    
                    # If it's a ClientError, check if it's "GraphNotFound" which is often transient due to session drop
                    err_msg = str(e)
                    is_graph_not_found = "GraphNotFoundException" in err_msg or "does not exist" in err_msg
                    
                    logger.warning(
                        "Transient Neo4j error for %s (attempt %d/%d, is_gnf=%s): %s; retrying in %.1fs",
                        window_graph_name,
                        attempt,
                        max_retries,
                        is_graph_not_found,
                        err_msg,
                        retry_backoff_s * (2 ** (attempt - 1)),
                    )
                    # Re-connect
                    try:
                        logger.info("Re-establishing GDS connection...")
                        gds = connect_gds(neo4j_cfg)
                        # Re-ensure base graph (crucial if DB restarted)
                        ensure_base_graph(gds, cfg=cfg, cypher_path=base_projection_cypher, rebuild=False)
                        base_G = gds.graph.get(cfg.base_graph_name)
                    except Exception as conn_err:
                        logger.error("Failed to re-establish connection: %s", conn_err)
                    
                    time.sleep(retry_backoff_s * (2 ** (attempt - 1)))
                finally:
                    # Robust cleanup: Always ensure temporary graphs are dropped
                    gds.graph.drop(temp_graph_name, failIfMissing=False)
                    # We do NOT drop window_graph_name here because we need it if we didn't finish algorithms?
                    # Actually, if we are in the 'finally' of the loop iteration, we should drop it IF we are done or failed.
                    # But the 'with' statement handles it. 
                    pass




    finally:
        manifest = pd.DataFrame(manifest_rows)
        logger.info("Writing manifest: %s (windows=%d)", manifest_path, manifest.shape[0])
        write_parquet(manifest, manifest_path)
