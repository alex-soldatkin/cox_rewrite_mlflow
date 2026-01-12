# Temporal Family Connection Ratio (FCR) Implementation Plan

## Goal

Improve the static `family_connection_ratio` (which uses all-time edges) with a **temporally aware `fcr_temporal`** metric calculated specifically for each rolling window. This ensures that the ratio reflects the network structure as it existed at that point in time.

## Background

- **Current State**: FCR is a static property on `Bank` nodes, calculated using all historical `OWNERSHIP` and `FAMILY` edges.
- **Desired State**: `fcr_temporal` is computed for each rolling window (e.g., 2014-2017) using only the active edges in that window.
- **Constraint**: Use the existing `rolling_windows` pipeline which projects specific time windows from a base temporal graph.

## Methodology

### 1. Metric Definition

The Family Connection Ratio (FCR) for a Bank $b$ is defined as:
$$ FCR*b = \frac{\sum*{o \in Owners(b)} FamilyDegree(o)}{Count(Owners(b))} $$
Where:

- $Owners(b)$ are nodes with an `OWNERSHIP` edge to Bank $b$ in the current window.
- $FamilyDegree(o)$ is the number of `FAMILY` edges connected to owner $o$ in the current window.

### 2. Implementation Strategy

We will implement a hybrid approach:

1.  **GDS (In-Memory)**: specific metrics on the window graph.
2.  **Python (Post-Processing)**: Efficient aggregations using the exported edge lists.

This avoids complex custom Cypher operations on GDS graphs and leverages the efficient Parquet export pipeline.

### 3. Step-by-Step Plan

#### Step 1: Update `rolling_windows/metrics.py`

Add functions to compute required base metrics:

- `family_degree`: Degree of `FAMILY` relationships for all Person nodes.
- `owner_degree`: Out-degree of `OWNERSHIP` relationships (redundant if using edge list, but good for validation).

#### Step 2: Update `rolling_windows/pipeline.py`

Modify `run_windows` to:

1.  **Ensure Edges are Exported**: we rely on the edge list to map Owners to Banks.
2.  **Compute Metrics**: Run the new metric functions.
3.  **Compute FCR**:
    - Load the window's `node_features` (contains `family_degree`) and `edge_list`.
    - Filter `edge_list` for `OWNERSHIP` type.
    - Join `edge_list` with `node_features` on `source_id` to get `family_degree` of the owner.
    - Group by `target_id` (Bank) to calculate:
      - `sum_family_degree`: Sum of owners' family degrees.
      - `count_owners`: Count of owners.
    - `fcr_temporal = sum_family_degree / count_owners`.
    - Merge `fcr_temporal` back into the `node_features` DataFrame before saving to Parquet.
    - **Note**: Ensure column name matches `QuarterlyWindowDataLoader` expectations or update loader mapping.

#### Step 3: Configuration Updates

- Update `rolling_windows/config.py` to Include `fcr_temporal` in the output schema.

## Detailed Code Changes

### `rolling_windows/metrics.py`

```python
def run_family_degree(gds, G, cfg):
    """Mutate family_degree property."""
    gds.degree.mutate(
        G,
        mutateProperty="family_degree",
        relationshipTypes=["FAMILY"],
        orientation="UNDIRECTED"
    )
    return "family_degree"
```

### `rolling_windows/pipeline.py` logic (pseudo-code)

```python
# ... inside loop ...

# 1. Run GDS Algos
run_window_algorithms(...) # now includes run_family_degree

# 2. Export to DataFrame
df_nodes = ... # Get node properties including family_degree
df_edges = ... # Get edge list

# 3. Compute FCR (Python Side)
# Filter for ownership edges: (Owner) -> (Bank)
ownership_edges = df_edges[df_edges['relationshipType'] == 'OWNERSHIP']

# Map owner's family degree to the interaction
# df_nodes has 'entity_id' and 'family_degree'
merged = ownership_edges.merge(
    df_nodes[['entity_id', 'family_degree']],
    left_on='source_entity_id',
    right_on='entity_id',
    how='left'
)

# Aggregate by Bank (target)
bank_stats = merged.groupby('target_entity_id').agg(
    total_family_connections=('family_degree', 'sum'),
    direct_owners=('source_entity_id', 'count')
).reset_index()

# Calculate Ratio
bank_stats['fcr_temporal'] = bank_stats['total_family_connections'] / bank_stats['direct_owners']

# Merge back to df_nodes
df_nodes = df_nodes.merge(
    bank_stats[['target_entity_id', 'fcr_temporal']],
    left_on='target_entity_id',
    right_on='target_entity_id',
    how='left'
)
df_nodes['fcr_temporal'] = df_nodes['fcr_temporal'].fillna(0.0)

# 4. Save Parquet
write_parquet(df_nodes, ...)
```

## Verification & Standards

1.  **Data Loading Test**: Create `tests/test_fcr_loading.py` based on `experiments/exp_007/test_data_loading.py`.
    - Initialize `QuarterlyWindowDataLoader`.
    - Load data and assert `fcr_temporal` column exists and is not all zero.
    - Check for `NaN` values.
2.  **Consistency Check**: Compare `fcr_temporal` for a known high-family-connection bank in a specific window against manual calculation.
3.  **Artifact Tracing**: Ensure the generated parquet files are used as the definitive source for subsequent experiments, maintained in the standard `rolling_windows/output` directory.
