from __future__ import annotations

from typing import Any

from graphdatascience import GraphDataScience
from graphdatascience.graph.graph_object import Graph
import logging

logger = logging.getLogger(__name__)

from config import RollingWindowConfig


def run_window_algorithms(gds: GraphDataScience, G: Graph, cfg: RollingWindowConfig) -> list[str]:
    properties_written: list[str] = []

    logger.info("Running PageRank...")
    gds.pageRank.mutate(
        G,
        mutateProperty="page_rank",
        relationshipWeightProperty="weight",
        maxIterations=cfg.pagerank_max_iterations,
        dampingFactor=cfg.pagerank_damping_factor,
    )
    properties_written.append("page_rank")

    logger.info("Running Degree (in/out)...")
    gds.degree.mutate(G, mutateProperty="in_degree", orientation="REVERSE")
    properties_written.append("in_degree")

    gds.degree.mutate(G, mutateProperty="out_degree", orientation="NATURAL")
    properties_written.append("out_degree")

    properties_written.append("out_degree")

    # Family connections degree
    if "FAMILY" in G.relationship_types():
        logger.info("Running Family Degree...")
        gds.degree.mutate(
            G,
            mutateProperty="family_degree",
            relationshipTypes=["FAMILY"],
            orientation="UNDIRECTED",
            concurrency=cfg.read_concurrency,
        )
        properties_written.append("family_degree")
    else:
        # If no FAMILY edges, we can't compute degree directly on them.
        # But we might need the property to exist for later steps (FCR calculation).
        # We can run a dummy Degree on ALL types but 0-weight? No.
        # Just skip and handle missing prop in pipeline.
        pass

    # Betweenness centrality
    logger.info("Running Betweenness Centrality...")
    gds.betweenness.mutate(
        G,
        mutateProperty="betweenness",
        concurrency=cfg.read_concurrency,
    )
    properties_written.append("betweenness")

    # Closeness centrality
    logger.info("Running Closeness Centrality...")
    gds.closeness.mutate(
        G,
        mutateProperty="closeness",
        concurrency=cfg.read_concurrency,
    )
    properties_written.append("closeness")

    # Eigenvector centrality
    logger.info("Running Eigenvector Centrality...")
    gds.eigenvector.mutate(
        G,
        mutateProperty="eigenvector",
        maxIterations=20,
        concurrency=cfg.read_concurrency,
    )
    properties_written.append("eigenvector")

    if cfg.run_wcc:
        logger.info("Running WCC...")
        gds.wcc.mutate(G, mutateProperty="wcc")
        properties_written.append("wcc")

    if cfg.run_louvain:
        logger.info("Running Louvain...")
        gds.louvain.mutate(
            G,
            mutateProperty="community_louvain",
            relationshipWeightProperty="weight",
            maxIterations=20,
            includeIntermediateCommunities=True,
            concurrency=cfg.read_concurrency,
        )
        properties_written.append("community_louvain")

    if cfg.run_fastrp:
        logger.info("Running FastRP...")
        gds.fastRP.mutate(
            G,
            mutateProperty="fastrp_embedding",
            embeddingDimension=cfg.embedding_dimension,
            iterationWeights=[0.2, 0.2, 0.2, 0.2, 0.2],
            nodeSelfInfluence=0.7,
            randomSeed=cfg.embedding_random_seed,
            relationshipWeightProperty="weight",
            concurrency=cfg.read_concurrency,
        )
        properties_written.append("fastrp_embedding")

    if cfg.run_hashgnn:
        logger.info("Running HashGNN...")
        gds.hashgnn.mutate(
            G,
            mutateProperty="hash_gnn_embedding",
            featureProperties=list(cfg.hashgnn_feature_properties),
            relationshipTypes=list(cfg.rel_types),
            binarizeFeatures={
                "dimension": int(cfg.hashgnn_binarize_dimension),
                "threshold": float(cfg.hashgnn_binarize_threshold),
            },
            iterations=int(cfg.hashgnn_iterations),
            outputDimension=int(cfg.hashgnn_output_dimension),
            embeddingDensity=int(cfg.hashgnn_embedding_density),
            heterogeneous=True,
            randomSeed=int(cfg.hashgnn_random_seed),
            concurrency=cfg.read_concurrency,
        )
        properties_written.append("hash_gnn_embedding")

    if cfg.run_node2vec:
        logger.info("Running Node2Vec...")
        gds.node2vec.mutate(
            G,
            mutateProperty="node2vec_embedding",
            embeddingDimension=int(cfg.node2vec_embedding_dimension),
            iterations=int(cfg.node2vec_iterations),
            randomSeed=int(cfg.node2vec_random_seed),
            relationshipWeightProperty="weight",
            concurrency=cfg.read_concurrency,
        )
        properties_written.append("node2vec_embedding")

    return properties_written


def compute_fcr_temporal(
    gds: GraphDataScience,
    cfg: RollingWindowConfig,
    window_start_ms: float,
    window_end_ms: float,
) -> dict[str, float]:
    """
    Compute temporal Family Connection Ratio (FCR) for Banks using Neo4j.
    
    FCR = sum(family_degree of direct owners) / count(direct owners)
    
    This runs on the Neo4j database using temporal filtering, not on the GDS graph.
    Returns a dict mapping entity_id -> fcr_temporal value.
    
    Args:
        gds: GDS client (used for run_cypher)
        cfg: Rolling window config
        window_start_ms: Window start timestamp in ms
        window_end_ms: Window end timestamp in ms
        
    Returns:
        Dict mapping neo4jImportId -> fcr_temporal
    """
    logger.info("Computing FCR temporal via Cypher...")
    
    # Query computes FCR for each Bank within the temporal window:
    # 1. Find Banks active in window
    # 2. Find their OWNERSHIP edges active in window
    # 3. For each owner, count their FAMILY edges active in window
    # 4. Aggregate to get FCR per bank
    query = """
    MATCH (entity:Bank|Company)
    WHERE entity.temporal_start < $window_end AND entity.temporal_end > $window_start
    
    // Find owners with active OWNERSHIP edges
    OPTIONAL MATCH (owner)-[o:OWNERSHIP]->(entity)
    WHERE o.temporal_start < $window_end AND o.temporal_end > $window_start
    
    WITH entity, owner
    WHERE owner IS NOT NULL
    
    // Count family connections for each owner (active in window)
    OPTIONAL MATCH (owner)-[f:FAMILY]-(family_member)
    WHERE (f.temporal_start IS NULL OR f.temporal_start < $window_end)
      AND (f.temporal_end IS NULL OR f.temporal_end > $window_start)
      AND coalesce(f.source, '') <> 'imputed'
    
    WITH entity, owner, count(DISTINCT family_member) AS owner_family_degree
    
    // Aggregate per entity
    WITH entity,
         sum(owner_family_degree) AS total_family_connections,
         count(owner) AS direct_owner_count
    
    RETURN 
        id(entity) AS gds_id,
        CASE WHEN direct_owner_count > 0 
             THEN toFloat(total_family_connections) / direct_owner_count 
             ELSE 0.0 
        END AS fcr_temporal
    """
    
    result = gds.run_cypher(
        query,
        params={
            "window_start": window_start_ms,
            "window_end": window_end_ms,
        }
    )
    
    if result.empty:
        logger.warning("FCR query returned no results")
        return {}
    
    fcr_map = dict(zip(result['gds_id'], result['fcr_temporal']))
    logger.info("Computed FCR for %d banks", len(fcr_map))
    
    return fcr_map


def gds_config_metadata(cfg: RollingWindowConfig) -> dict[str, Any]:
    return {
        "base_graph_name": cfg.base_graph_name,
        "rel_types": list(cfg.rel_types),
        "include_imputed01": int(cfg.include_imputed01),
        "export_edges": bool(cfg.export_edges),
        "edge_id_property": str(cfg.edge_id_property),
        "export_feature_vectors": bool(cfg.export_feature_vectors),
        "export_feature_blocks": bool(cfg.export_feature_blocks),
        "window_years": int(cfg.window_years),
        "step_years": int(cfg.step_years),
        "start_year": int(cfg.start_year),
        "end_start_year": int(cfg.end_start_year),
        "id_property": cfg.id_property,
        "read_concurrency": int(cfg.read_concurrency),
        "pagerank_max_iterations": int(cfg.pagerank_max_iterations),
        "pagerank_damping_factor": float(cfg.pagerank_damping_factor),
        "embedding_dimension": int(cfg.embedding_dimension),
        "embedding_random_seed": int(cfg.embedding_random_seed),
        "run_louvain": bool(cfg.run_louvain),
        "run_wcc": bool(cfg.run_wcc),
        "run_fastrp": bool(cfg.run_fastrp),
        "run_hashgnn": bool(cfg.run_hashgnn),
        "hashgnn_feature_properties": list(cfg.hashgnn_feature_properties),
        "hashgnn_iterations": int(cfg.hashgnn_iterations),
        "hashgnn_output_dimension": int(cfg.hashgnn_output_dimension),
        "hashgnn_embedding_density": int(cfg.hashgnn_embedding_density),
        "hashgnn_binarize_dimension": int(cfg.hashgnn_binarize_dimension),
        "hashgnn_binarize_threshold": float(cfg.hashgnn_binarize_threshold),
        "hashgnn_random_seed": int(cfg.hashgnn_random_seed),
        "run_node2vec": bool(cfg.run_node2vec),
        "node2vec_embedding_dimension": int(cfg.node2vec_embedding_dimension),
        "node2vec_iterations": int(cfg.node2vec_iterations),
        "node2vec_iterations": int(cfg.node2vec_iterations),
        "node2vec_random_seed": int(cfg.node2vec_random_seed),
        "run_link_prediction": bool(cfg.run_link_prediction),
        "lp_threshold": float(cfg.lp_threshold),
    }
