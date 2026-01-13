from __future__ import annotations

import argparse
import contextlib
import logging
from pathlib import Path
import sys
# Add project root to sys.path to allow importing mlflow_utils
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import RollingWindowConfig, load_neo4j_config, parse_rel_types
from gds_client import connect_gds
from pipeline import run_windows

try:
    import yaml
except ImportError:
    yaml = None


def _parse_csv_words(values: list[str]) -> tuple[str, ...]:
    out: list[str] = []
    for v in values:
        for part in str(v).split(","):
            part = part.strip()
            if part:
                out.append(part)
    # preserve order, remove duplicates
    seen: set[str] = set()
    deduped: list[str] = []
    for t in out:
        if t not in seen:
            deduped.append(t)
            seen.add(t)
    return tuple(deduped)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run rolling-window temporal graph analytics (Neo4j GDS).")
    p.add_argument("--env-file", default=None, help="Path to a .env file (defaults to project .env discovery).")
    p.add_argument("--config", type=Path, help="Path to a YAML configuration file.")
    p.add_argument("--arrow", action="store_true", help="Enable Arrow Flight (if configured on the server).")
    p.add_argument(
        "--show-progress",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show GDS progress bars during procedure calls.",
    )

    defaults = RollingWindowConfig()
    p.add_argument("--start-year", type=int, default=defaults.start_year, help="First window start year (UTC).")
    p.add_argument(
        "--end-start-year",
        type=int,
        default=defaults.end_start_year,
        help="Last window start year (UTC).",
    )
    p.add_argument("--window-years", type=int, default=3, help="Window size in years.")
    p.add_argument("--step-years", type=int, default=1, help="Step size in years.")

    p.add_argument(
        "--rel-types",
        nargs="+",
        default=["OWNERSHIP", "MANAGEMENT", "FAMILY"],
        help="Relationship types to include (space-separated or comma-separated).",
    )
    p.add_argument("--include-imputed", action="store_true", help="Include imputed FAMILY relationships.")

    p.add_argument("--id-property", default=defaults.id_property, help="Stable node identifier property to export.")

    p.add_argument("--read-concurrency", type=int, default=4, help="GDS concurrency for projection/filter/algs.")
    p.add_argument("--base-graph-name", default="base_temporal", help="Name of the base GDS graph.")
    p.add_argument(
        "--base-projection-cypher",
        default="queries/cypher/003_0_rollwin_base_projection.cypher",
        help="Cypher file used to create the base temporal projection.",
    )
    p.add_argument("--rebuild-base-graph", action="store_true", help="Drop+recreate base graph before running.")

    p.add_argument("--no-louvain", action="store_true", help="Disable Louvain per window.")
    p.add_argument("--no-wcc", action="store_true", help="Disable WCC per window.")
    p.add_argument("--no-fastrp", action="store_true", help="Disable FastRP embeddings per window.")

    p.add_argument("--embedding-dimension", type=int, default=128, help="FastRP embedding dimension.")
    p.add_argument("--embedding-random-seed", type=int, default=42, help="FastRP random seed.")
    p.add_argument(
        "--expand-embeddings",
        action="store_true",
        help="Expand embeddings into emb_0..emb_(d-1) columns (default: keep list column).",
    )
    p.add_argument(
        "--skip-existing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip window outputs that already exist on disk.",
    )
    p.add_argument("--max-retries", type=int, default=3, help="Max retries per window for transient Neo4j failures.")
    p.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=2.0,
        help="Exponential backoff base (seconds) between per-window retries.",
    )

    p.add_argument(
        "--output-dir",
        default="data_processing/rolling_windows/output",
        help="Output directory for parquet datasets.",
    )
    p.add_argument(
        "--export-edges",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export per-window edge lists to parquet.",
    )
    p.add_argument(
        "--edge-id-property",
        default=defaults.edge_id_property,
        help="Stable node identifier property to use for edge lists (exported as source_Id/target_Id).",
    )
    p.add_argument(
        "--export-feature-vectors",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export existing feature vectors (e.g., bank_feats, network_feats) to the node panel parquet.",
    )
    p.add_argument(
        "--export-feature-blocks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export bank_feats-derived feature blocks (e.g., legal_feats, state_feats) to the node panel parquet.",
    )

    p.add_argument(
        "--hashgnn",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run HashGNN per window (mutate in-memory graph and export embedding to parquet).",
    )
    p.add_argument(
        "--hashgnn-feature-properties",
        nargs="+",
        default=["bank_feats"],
        help="Node properties to use as input to HashGNN (space-separated or comma-separated).",
    )
    p.add_argument("--hashgnn-iters", type=int, default=5, help="HashGNN iterations.")
    p.add_argument("--hashgnn-dim", type=int, default=256, help="HashGNN output embedding dimension.")
    p.add_argument("--hashgnn-density", type=int, default=128, help="HashGNN embedding density.")
    p.add_argument("--hashgnn-binarize-dim", type=int, default=77, help="HashGNN binarizeFeatures.dimension.")
    p.add_argument(
        "--hashgnn-binarize-threshold",
        type=float,
        default=0.01,
        help="HashGNN binarizeFeatures.threshold.",
    )
    p.add_argument("--hashgnn-random-seed", type=int, default=42, help="HashGNN random seed.")

    p.add_argument(
        "--node2vec",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run Node2Vec per window (mutate in-memory graph and export embedding to parquet).",
    )
    p.add_argument("--node2vec-dim", type=int, default=256, help="Node2Vec embedding dimension.")
    p.add_argument("--node2vec-iters", type=int, default=20, help="Node2Vec iterations.")
    p.add_argument("--node2vec-random-seed", type=int, default=42, help="Node2Vec random seed.")


    p.add_argument(
        "--link-prediction",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run intra-window link prediction.",
    )
    p.add_argument("--lp-threshold", type=float, default=0.7, help="Link prediction probability threshold.")

    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Python logging verbosity.",
    )
    p.add_argument("--log-file", default=None, help="Optional log file path (in addition to stdout).")
    p.add_argument("--run-name", default=None, help="Name of the run folder. If not provided, defaults to timestamp.")
    return p


def _setup_logging(*, level: str, log_file: str | None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Apply YAML config if provided
    if args.config:
        if yaml is None:
            print("Error: PyYAML is required for --config but not installed. Run 'uv add pyyaml'.", file=sys.stderr)
            sys.exit(1)
        if not args.config.exists():
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        
        with open(args.config, "r") as f:
            yaml_config = yaml.safe_load(f)
            # Re-parse args with YAML values as defaults
            parser.set_defaults(**yaml_config)
            args = parser.parse_args()

    _setup_logging(level=str(args.log_level).upper(), log_file=args.log_file)

    neo4j_cfg = load_neo4j_config(env_file=args.env_file, arrow=bool(args.arrow), show_progress=bool(args.show_progress))
    rel_types = parse_rel_types(args.rel_types)
    hashgnn_feature_properties = _parse_csv_words(list(args.hashgnn_feature_properties))

    # Update output dir with run name
    import datetime
    run_name = args.run_name
    if not run_name:
        run_name = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    cfg = RollingWindowConfig(
        base_graph_name=args.base_graph_name,
        rel_types=rel_types,
        include_imputed01=1 if args.include_imputed else 0,
        window_years=args.window_years,
        step_years=args.step_years,
        start_year=args.start_year,
        end_start_year=args.end_start_year,
        id_property=args.id_property,
        read_concurrency=args.read_concurrency,
        embedding_dimension=args.embedding_dimension,
        embedding_random_seed=args.embedding_random_seed,
        output_dir=Path(args.output_dir) / run_name,
        export_edges=bool(args.export_edges),
        edge_id_property=str(args.edge_id_property),
        export_feature_vectors=bool(args.export_feature_vectors),
        export_feature_blocks=bool(args.export_feature_blocks),
        run_louvain=not args.no_louvain,
        run_wcc=not args.no_wcc,
        run_fastrp=not args.no_fastrp,
        run_hashgnn=bool(args.hashgnn),
        hashgnn_feature_properties=hashgnn_feature_properties,
        hashgnn_iterations=int(args.hashgnn_iters),
        hashgnn_output_dimension=int(args.hashgnn_dim),
        hashgnn_embedding_density=int(args.hashgnn_density),
        hashgnn_binarize_dimension=int(args.hashgnn_binarize_dim),
        hashgnn_binarize_threshold=float(args.hashgnn_binarize_threshold),
        hashgnn_random_seed=int(args.hashgnn_random_seed),
        run_node2vec=bool(args.node2vec),
        node2vec_embedding_dimension=int(args.node2vec_dim),
        node2vec_iterations=int(args.node2vec_iters),
        node2vec_random_seed=int(args.node2vec_random_seed),
        run_link_prediction=bool(args.link_prediction),
        lp_threshold=float(args.lp_threshold),
    )


    base_projection_cypher = Path(args.base_projection_cypher)

    try:
        from tqdm.contrib.logging import logging_redirect_tqdm

        tqdm_logging_ctx = logging_redirect_tqdm()
    except Exception:
        tqdm_logging_ctx = contextlib.nullcontext()

    with tqdm_logging_ctx:
        with connect_gds(neo4j_cfg) as gds:
            run_windows(
                gds,
                cfg=cfg,
                neo4j_cfg=neo4j_cfg,
                base_projection_cypher=base_projection_cypher,
                rebuild_base_graph=bool(args.rebuild_base_graph),
                expand_embeddings=bool(args.expand_embeddings),
                skip_existing=bool(args.skip_existing),
                max_retries=int(args.max_retries),
                retry_backoff_s=float(args.retry_backoff_seconds),
                show_tqdm=bool(args.show_progress),
            )


if __name__ == "__main__":
    main()
