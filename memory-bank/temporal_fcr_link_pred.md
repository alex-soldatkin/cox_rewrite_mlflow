# Temporal FCR & Link Prediction Implementation Documentation

This document provides an exhaustive record of the files modified and the logic implemented to support **Temporal Family Control Ratio (FCR)** calculation and **Link Prediction** within the rolling window pipeline.

## 1. Pipeline Orchestration & FCR Logic

### File: `rolling_windows/pipeline.py`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/pipeline.py`

**Significant Changes**:

1.  **Louvain-Filtered FCR Calculation**:
    - **Logic**: The Temporal FCR metric (`fcr_temporal`) was refined to only consider "stable" family connections.
    - **Implementation**:
      - We now merge `community_louvain` (computed by the Louvain algorithm) into the ownership edges dataframe for both the **Source** (Shareholder) and **Target** (Bank).
      - **Filtering**: We explicitly filter the ownership edges to keep only those where `source_community == target_community`.
      - **Aggregation**: We sum the `family_degree` (number of family connections) of these filtered owners and divide by the total number of such owners to get `fcr_temporal`.
    - **Snippet**:
      ```python
      merged = merged[merged["source_community"] == merged["target_community"]]
      ```

2.  **Performance Optimization (Logging)**:
    - Added granular `logger.info` statements with timestamps around critical heavy operations:
      - `run_window_algorithms`
      - `gds.graph.nodeProperties.stream`
      - `export_window_edges`
    - This allowed us to identify the streaming/conversion step as the primary bottleneck (taking ~5 minutes previously).

3.  **Property Management**:
    - **`regn_cbr` Handling**: Included logic to forcefully include `regn_cbr` in the exported node properties list (`db_node_props`), ensuring it's available for verification, even if it wasn't used in algorithms.
    - **Type Safety**: Explicit casting of configuration values (e.g., `readConcurrency`) before passing to GDS to avoid Java type errors.

## 2. Data Processing & Performance

### File: `rolling_windows/parquet.py`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/parquet.py`

**Significant Changes**:

1.  **Vector Slicing Optimization**:
    - **Problem**: Converting large NumPy arrays (from GDS embeddings/features) to Python lists of floats for Parquet storage was extremely slow using standard list comprehensions (`[list(map(float, row)) for row in sliced]`).
    - **Solution**: Replaced list comprehensions with NumPy's optimized `tolist()` method.
    - **Impact**: Reduced the "Node streaming" and processing step from ~5 minutes to <1 minute.
    - **Snippet**:
      ```python
      # Optimization: Use tolist() which is much faster than list comprehension
      df[out_column] = sliced.tolist()
      ```

2.  **List Column Coercion Optimization**:
    - **Logic**: Added a check in `coerce_float_list_column` to inspect the first non-null element. If it is already a list of floats (which `tolist()` produces), we skip the expensive `apply` loop entirely.

## 3. Link Prediction

### File: `rolling_windows/link_prediction.py`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/link_prediction.py`

**Significant Changes**:

1.  **Bug Fix (Property Naming)**:
    - **Issue**: The code attempted to access the node labels column using the key `'labels'`, which caused a `KeyError`.
    - **Fix**: Changed the key to `'nodeLabels'`, which matches the output from `gds.graph.nodeProperties.stream(..., listNodeLabels=True)`.
    - **Snippet**:
      ```python
      person_ids = df_nodes[df_nodes['nodeLabels'].apply(lambda x: 'Person' in x)]['entity_id'].tolist()
      ```

## 4. Graph Projection (Cypher)

### File: `queries/cypher/003_0_rollwin_base_projection.cypher`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/queries/cypher/003_0_rollwin_base_projection.cypher`

**Significant Changes**:

1.  **New Projection File**: Created this file specifically for the rolling window pipeline to separate it from legacy queries.
2.  **Property Casting & Null Handling**:
    - **`regn_cbr`**: Explicitly cast to `toString()` (later removed/commented out due to GDS type issues, then potential re-inclusion strategy).
    - **`is_dead`**: Converted Boolean `is_dead` to Integer (0/1) because GDS `graph.project` has strict type requirements and sometimes rejects Booleans in mixed contexts.
    - **Feature Vectors**: Added `coalesce(source.bank_feats, [])` and `network_feats` to ensure these properties exist on the projected graph nodes, preventing "Property key not found" errors during streaming.
    - **Single Statement**: Ensured the file contains only _one_ Cypher statement (`CALL gds.graph.project(...)`) so it can be executed via `gds.run_cypher`.

## 5. Pipeline execution

### File: `rolling_windows/run_pipeline.py`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/run_pipeline.py`

**Significant Changes**:

1.  **Default Configuration**: Updated the default `--base-projection-cypher` path to point to the new `003_0_rollwin_base_projection.cypher`.
2.  **New Flags**:
    - `--arrow`: Added flag to enable Apache Arrow support (passed to GDS client).
    - `--link-prediction`: Flag to enable the link prediction workflow.
    - `--lp-threshold`: Configurable threshold for saving predicted edges.

## 6. Verification

### File: `tests/test_fcr_loading.py`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/tests/test_fcr_loading.py`

**Significant Changes**:

1.  **Validation Logic**:
    - Added logic to load the Parquet output from a specific run (e.g., `verification_run_v11`).
    - Checks for the existence of `fcr_temporal` column.
    - Validates that `Bank` nodes are present.
    - **Adaptability**: Updated to handle cases where `regn_cbr` might be missing (due to export configuration) by falling back to `nodeLabels` for identifying banks.
    - **Pathing**: Updated to look in `data_processing/rolling_windows/output/...` to match the actual execution output structure.

## 7. Metrics (Logging)

### File: `rolling_windows/metrics.py`

**Location**: `/Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/metrics.py`

**Significant Changes**:

1.  **Granular Logging**: Added `logger.info("Running <Algorithm>...")` before each GDS algorithm call (PageRank, Degree, Centrality, FastRP, etc.). This helps visualizing progress and identifying if a specific algorithm hangs.

---

**Summary of Logic Flow**:

1.  **Project**: `run_pipeline.py` triggers `ensure_base_graph` -> logic in `pipeline.py` reads `003_0_rollwin_base_projection.cypher` -> GDS Graph is created.
2.  **Filter**: For each window, `gds.graph.filter` creates a subgraph.
3.  **Compute**: `run_window_algorithms` runs Centrality, FastRP, and **Louvain**.
4.  **Stream**: `gds.graph.nodeProperties.stream` pulls data back to Python (Optimized via `parquet.py`).
5.  **FCR Calc**: `pipeline.py` merges Ownership edges with Node properties (including Louvain communities), filters for `source_community == target_community`, and calculates the ratio.
6.  **Link Pred**: `link_prediction.py` (if enabled) trains a model on valid Family edges and predicts new ones using FastRP embeddings + String distance.
7.  **Export**: Results saved to Parquet.
