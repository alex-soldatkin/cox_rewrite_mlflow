from __future__ import annotations

from graphdatascience import GraphDataScience
from neo4j import GraphDatabase

from config import Neo4jConfig


def connect_gds(cfg: Neo4jConfig) -> GraphDataScience:
    driver_kwargs: dict[str, object] = {
        "keep_alive": cfg.keep_alive,
        "max_connection_lifetime": cfg.max_connection_lifetime_s,
        "max_connection_pool_size": cfg.max_connection_pool_size,
    }
    if cfg.connection_acquisition_timeout_s is not None:
        driver_kwargs["connection_acquisition_timeout"] = cfg.connection_acquisition_timeout_s

    driver = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password), **driver_kwargs)
    return GraphDataScience(
        driver,
        database=cfg.database,
        arrow=cfg.arrow,
        show_progress=cfg.show_progress,
    )
