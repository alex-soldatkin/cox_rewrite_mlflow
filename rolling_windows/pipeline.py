from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
from graphdatascience import GraphDataScience
from neo4j.exceptions import ServiceUnavailable, SessionExpired
from tqdm.auto import tqdm

from config import RollingWindowConfig, validate_rel_types
from dates import iter_year_windows
from feature_blocks import BANK_FEATS_BLOCKS, BANK_FEATS_DIM, other_bank_feats_indices
from hashing import stable_hash_dict
from metrics import gds_config_metadata, run_window_algorithms
from parquet import coerce_float_list_column, expand_embedding_column, slice_vector_column, write_parquet

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
    cypher_path: Path,
    rebuild: bool = False,
) -> None:
    logger.info("Ensuring base graph '%s' (rebuild=%s)", cfg.base_graph_name, rebuild)
    try:
        G = gds.graph.get(cfg.base_graph_name)
        if not rebuild:
            required_props = _required_base_node_properties(cfg)
            by_label = G.node_properties()
            missing_by_label: dict[str, list[str]] = {}
            for label, props in by_label.to_dict().items():
                missing = sorted(required_props.difference(set(props)))
                if missing:
                    missing_by_label[str(label)] = missing
            if missing_by_label:
                logger.info(
                    "Base graph '%s' exists but is missing required node properties; rebuilding. missing_by_label=%s",
                    cfg.base_graph_name,
                    missing_by_label,
                )
                rebuild = True
            else:
                logger.info("Base graph '%s' already exists; skipping projection", cfg.base_graph_name)
                return
    except ValueError:
        pass

    logger.info("Dropping base graph '%s' (if exists)", cfg.base_graph_name)
    gds.graph.drop(cfg.base_graph_name, failIfMissing=False)

    query = _load_text(cypher_path)
    logger.info("Projecting base graph from %s", cypher_path)
    projection_df = gds.run_cypher(
        query,
        {
            "baseGraphName": cfg.base_graph_name,
            "baseRelTypes": list(cfg.rel_types),
            "readConcurrency": int(cfg.read_concurrency),
        },
    )
    if projection_df.empty:
        raise RuntimeError(
            "Base graph projection returned no rows. "
            "This usually means the MATCH clause found no relationships in the selected database "
            "for the given labels/relationship types."
        )

    gds.graph.get(cfg.base_graph_name)
    row = projection_df.iloc[0].to_dict()
    logger.info(
        "Base graph '%s' ready (nodes=%s rels=%s projectMillis=%s)",
        cfg.base_graph_name,
        row.get("nodeCount", "?"),
        row.get("relationshipCount", "?"),
        row.get("projectMillis", "?"),
    )


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
            while True:
                try:
                    logger.info("Creating window graph %s (attempt %d/%d)", window_graph_name, attempt + 1, max_retries + 1)
                    gds.graph.drop(window_graph_name, failIfMissing=False)
                    with gds.graph.filter(
                        window_graph_name,
                        base_G,
                        node_filter,
                        rel_filter,
                        parameters=filter_params,
                        concurrency=cfg.read_concurrency,
                    ) as G:
                        df = None
                        df_edges = None

                        if need_nodes:
                            properties = run_window_algorithms(gds, G, cfg)

                            if cfg.export_feature_vectors:
                                properties.extend(["bank_feats", "network_feats", "is_dead"])
                            elif cfg.export_feature_blocks:
                                properties.append("bank_feats")
                            properties = _unique_preserve_order(properties)

                            db_node_props = [cfg.id_property]
                            if cfg.export_edges and cfg.edge_id_property != cfg.id_property:
                                db_node_props.append(cfg.edge_id_property)

                            df = gds.graph.nodeProperties.stream(
                                G,
                                properties,
                                separate_property_columns=True,
                                db_node_properties=db_node_props,
                                listNodeLabels=True,
                            )

                        if need_edges:
                            df_edges = export_window_edges(
                                gds,
                                G,
                                rel_types=cfg.rel_types,
                                edge_id_property=cfg.edge_id_property,
                            )
                    break
                except (ServiceUnavailable, SessionExpired) as e:
                    attempt += 1
                    if attempt > max_retries:
                        logger.exception("Window %s failed after %d retries", window_graph_name, max_retries)
                        raise
                    logger.warning(
                        "Transient Neo4j error for %s (attempt %d/%d): %s; retrying in %.1fs",
                        window_graph_name,
                        attempt,
                        max_retries,
                        str(e),
                        retry_backoff_s * (2 ** (attempt - 1)),
                    )
                    time.sleep(retry_backoff_s * (2 ** (attempt - 1)))

            node_count = 0
            edge_count = 0

            if df is not None:
                df = df.rename(columns={cfg.id_property: "entity_id"})
                df["window_start_ms"] = w.start_ms
                df["window_end_ms"] = w.end_ms
                df["window_start_year"] = w.start_year
                df["window_end_year_inclusive"] = w.end_year_inclusive
                df["window_graph_name"] = window_graph_name
                df["params_hash"] = params_hash

                if "in_degree" in df.columns and "out_degree" in df.columns:
                    df["degree"] = df["in_degree"] + df["out_degree"]

                if "fastrp_embedding" in df.columns:
                    df = coerce_float_list_column(df, column="fastrp_embedding")
                if "hash_gnn_embedding" in df.columns:
                    df = coerce_float_list_column(df, column="hash_gnn_embedding")
                if "node2vec_embedding" in df.columns:
                    df = coerce_float_list_column(df, column="node2vec_embedding")

                if cfg.export_feature_vectors:
                    df = coerce_float_list_column(df, column="bank_feats")
                    df = coerce_float_list_column(df, column="network_feats")

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

            if df is None and node_out_path.exists():
                node_count = int(pq.ParquetFile(node_out_path).metadata.num_rows)
            if df_edges is None and edges_out_path.exists():
                edge_count = int(pq.ParquetFile(edges_out_path).metadata.num_rows)

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
    finally:
        manifest = pd.DataFrame(manifest_rows)
        logger.info("Writing manifest: %s (windows=%d)", manifest_path, manifest.shape[0])
        write_parquet(manifest, manifest_path)
