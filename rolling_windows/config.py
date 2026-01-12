from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from dotenv import load_dotenv


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str
    database: str | None = None
    arrow: bool = False
    show_progress: bool = True
    keep_alive: bool = True
    max_connection_lifetime_s: int = 60 * 8
    max_connection_pool_size: int = 50
    connection_acquisition_timeout_s: int | None = 60


@dataclass(frozen=True)
class RollingWindowConfig:
    base_graph_name: str = "base_temporal"
    rel_types: tuple[str, ...] = ("OWNERSHIP", "MANAGEMENT", "FAMILY")
    include_imputed01: int = 0

    window_years: int = 3
    step_years: int = 1
    start_year: int = 2000
    end_start_year: int = 2010

    id_property: str = "Id"

    read_concurrency: int = 4

    pagerank_max_iterations: int = 20
    pagerank_damping_factor: float = 0.85

    embedding_dimension: int = 128
    embedding_random_seed: int = 42

    output_dir: Path = Path("rolling_windows/output")

    export_edges: bool = True
    edge_id_property: str = "Id"

    export_feature_vectors: bool = True
    export_feature_blocks: bool = True

    run_louvain: bool = True
    run_wcc: bool = True
    run_fastrp: bool = True

    run_hashgnn: bool = False
    hashgnn_feature_properties: tuple[str, ...] = ("bank_feats",)
    hashgnn_iterations: int = 5
    hashgnn_output_dimension: int = 256
    hashgnn_embedding_density: int = 128
    hashgnn_binarize_dimension: int = 77
    hashgnn_binarize_threshold: float = 0.01
    hashgnn_random_seed: int = 42

    run_node2vec: bool = False
    node2vec_embedding_dimension: int = 256
    node2vec_iterations: int = 20
    node2vec_random_seed: int = 42

    run_link_prediction: bool = False
    lp_threshold: float = 0.7


def load_neo4j_config(
    *,
    env_file: str | None = None,
    arrow: bool = False,
    show_progress: bool = True,
) -> Neo4jConfig:
    load_dotenv(dotenv_path=env_file, override=False)

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE") or None

    missing = [
        name
        for name, value in [("NEO4J_URI", uri), ("NEO4J_USER", user), ("NEO4J_PASSWORD", password)]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    return Neo4jConfig(
        uri=uri,
        user=user,
        password=password,
        database=database,
        arrow=arrow,
        show_progress=show_progress,
    )


def parse_rel_types(values: Sequence[str]) -> tuple[str, ...]:
    rel_types: list[str] = []
    for v in values:
        if not v:
            continue
        for part in v.split(","):
            part = part.strip()
            if part:
                rel_types.append(part)
    # preserve order, remove duplicates
    seen: set[str] = set()
    deduped: list[str] = []
    for t in rel_types:
        if t not in seen:
            deduped.append(t)
            seen.add(t)
    return tuple(deduped)


def validate_rel_types(rel_types: Iterable[str]) -> None:
    for t in rel_types:
        if not t or any(ch.isspace() for ch in t):
            raise ValueError(f"Invalid relationship type: {t!r}")
