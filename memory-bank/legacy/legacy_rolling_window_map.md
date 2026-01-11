# Legacy Rolling Window Analysis Map

**Directory:** `ROLLING_WINDOW_DIR`
**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/data_processing/rolling_windows`

This directory contains a modular pipeline for performing rolling window network analysis on the Neo4j graph. It projects temporal snapshots of the graph, calculates network metrics (centrality, community detection, embeddings), and exports the results to Parquet files.

## Core Pipeline

### 1. `run_pipeline.py`

- **Purpose**: Entry point for the analysis.
- **Functionality**:
  - Parses command-line arguments (window size, step size, algorithms to run).
  - Initializes configuration (`RollingWindowConfig`).
  - Sets up logging.
  - Calls `pipeline.run_windows`.
- **Key Arguments**: `--window-years`, `--step-years`, `--start-year`, `--no-louvain`, `--no-fastrp`, `--hashgnn`.

### 2. `pipeline.py`

- **Purpose**: Orchestrator of the rolling window logic.
- **Key Function**: `run_windows`
  - Iterates through time windows defined by `iter_year_windows`.
  - Checks for existing output (manifest) to skip completed windows.
  - **Graph Projection**: Uses `gds.graph.filter` to create a subgraph for the specific time window from a base temporal projection.
  - **Metric Calculation**: Calls `run_window_algorithms` (from `metrics.py`).
  - **Export**: Streams node properties (including calculated metrics and feature vectors) and edge lists to Parquet files via `parquet.py`.
  - **Manifest**: Maintains a `manifest.parquet` tracking processed windows and their metadata.

### 3. `metrics.py`

- **Purpose**: Wrappers for running GDS algorithms.
- **Key Function**: `run_window_algorithms` runs a sequence of algorithms based on config:
  - **Louvain**: Community detection (`gds.louvain.write`).
  - **WCC**: Weakly Connected Components (`gds.wcc.write`).
  - **FastRP**: Node embeddings (`gds.fastRP.mutate`).
  - **HashGNN**: Optional, specialized embedding (`gds.hashgnn.mutate`).
  - **Node2Vec**: Optional, random walk embedding (`gds.node2vec.mutate`).
  - **Degree Centrality**: Calculated via `gds.degree.mutate`.
  - **PageRank**: Calculated via `gds.pageRank.mutate`.

## Configuration & Data Structures

### 4. `config.py`

- **Classes**:
  - `Neo4jConfig`: Connection details (URI, user, password).
  - `RollingWindowConfig`: Comprehensive configuration for the pipeline (window parameters, algorithm settings, output paths, feature toggles).

### 5. `dates.py`

- **Classes**: `Window` (dataclass for start/end times).
- **Functions**: `iter_year_windows` generates the sequence of temporal windows.

### 6. `feature_blocks.py`

- **Purpose**: Defines subsets of features ("blocks") from the `bank_feats` vector.
- **Blocks**: `state_feats`, `legal_feats`, `governance_feats`, `finance_feats`, `ip_feats`, `ops_feats`.

## Utilities

### 7. `gds_client.py`

- **Purpose**: Factory for creating the `GraphDataScience` client with appropriate timeout/connection settings.

### 8. `parquet.py`

- **Purpose**: Helper functions for Parquet I/O.
- **Features**: Handling list columns (coercion to float lists), expanding embedding vectors into separate columns.

### 9. `hashing.py`

- **Purpose**: Generates stable hashes of configuration dictionaries to detect parameter changes between runs associated with the manifest.

## Output Structure

- **`output/manifest/`**: Contains `manifest_*.parquet` files logging run metadata.
- **`output/nodes/`**: Per-window node feature files (e.g., `node_features_rw_2000_2003.parquet`).
- **`output/edges/`**: Per-window edge list files (e.g., `edge_list_rw_2000_2003.parquet`).
