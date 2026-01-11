from __future__ import annotations

from typing import Any

from graphdatascience import GraphDataScience
from graphdatascience.graph.graph_object import Graph

from config import RollingWindowConfig


def run_window_algorithms(gds: GraphDataScience, G: Graph, cfg: RollingWindowConfig) -> list[str]:
    properties_written: list[str] = []

    gds.pageRank.mutate(
        G,
        mutateProperty="page_rank",
        relationshipWeightProperty="weight",
        maxIterations=cfg.pagerank_max_iterations,
        dampingFactor=cfg.pagerank_damping_factor,
    )
    properties_written.append("page_rank")

    gds.degree.mutate(G, mutateProperty="in_degree", orientation="REVERSE")
    properties_written.append("in_degree")

    gds.degree.mutate(G, mutateProperty="out_degree", orientation="NATURAL")
    properties_written.append("out_degree")

    # Betweenness centrality
    gds.betweenness.mutate(
        G,
        mutateProperty="betweenness",
        concurrency=cfg.read_concurrency,
    )
    properties_written.append("betweenness")

    # Closeness centrality
    gds.closeness.mutate(
        G,
        mutateProperty="closeness",
        concurrency=cfg.read_concurrency,
    )
    properties_written.append("closeness")

    # Eigenvector centrality
    gds.eigenvector.mutate(
        G,
        mutateProperty="eigenvector",
        maxIterations=20,
        concurrency=cfg.read_concurrency,
    )
    properties_written.append("eigenvector")

    if cfg.run_wcc:
        gds.wcc.mutate(G, mutateProperty="wcc")
        properties_written.append("wcc")

    if cfg.run_louvain:
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
        "node2vec_random_seed": int(cfg.node2vec_random_seed),
    }
