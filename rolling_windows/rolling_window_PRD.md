# PRD: Temporal Rolling-Window Graph Analytics Pipeline (Neo4j GDS + Python + Parquet)

We are using uv for env management. to activate the environment, run `source .venv/bin/activate` in the project root (/Users/alexandersoldatkin/projects/factions-networks-thesis). To run scripts, use `uv run <script>.py`. Check the available modules in pyproject.toml.


## 1) Overview

Build a production-ready pipeline that:

* Generates **rolling 3-year temporal graph snapshots** from a Neo4j property graph.
* Runs **network metrics** (e.g., PageRank, degree, WCC, centralities as needed).
* Runs **node embeddings** per snapshot (FastRP per window; optional GraphSAGE for cross-window stability).
* Exports results into an **analytics-friendly panel dataset** (Parquet) for downstream **regression** and **visualization**.
* Optionally writes a curated subset back into Neo4j for interactive graph exploration.

This PRD is written for another LLM/engineer to implement end-to-end, including pitfalls observed during Cypher + GDS development.

---

## 2) Goals

### Core goals

1. **Rolling snapshots:** For each rolling 3-year window (e.g., 2000–2003, 2001–2004, …), produce a subgraph containing only entities/edges active in that interval.
2. **Compute metrics + embeddings:** Compute centrality metrics and node embeddings for each window graph efficiently.
3. **Export stable tabular outputs:** Produce Parquet datasets suitable for panel regression and visualization tooling.
4. **Efficiency:** Avoid costly DB scans per window; keep compute in-memory (GDS) and orchestrate windows in Python.

### Secondary goals

* Provide reproducibility hooks (random seeds, stable config hashes).
* Make it easy to switch relationship-type subsets and inclusion rules (e.g., exclude imputed FAMILY edges).

---

## 3) Non-goals

* Building a full UI or dashboard (only providing data for visualization).
* Building a real-time streaming solution. This is batch/periodic.
* Solving perfect cross-time embedding alignment unless GraphSAGE “train once, infer many” is explicitly used.

---

## 4) Context & Constraints

### Graph size and workload

* Full graph: ~60k nodes, ~140k relationships.
* Per 3-year rolling window: ~15k nodes/relationships.
* Rolling windows imply high overlap; must avoid rebuilding projections from store per window.

### Temporal semantics

* Nodes and relationships have `temporal_start` and `temporal_end`.
* Values have now been normalized to **epochMillis INTEGER or NULL**.
* Window membership is based on **interval overlap**:

  * Active in window `[start, end)` if `(startProp < end) AND (endProp > start)` with open-ended NULL treated as ±∞.

---

## 5) Key Pitfalls & Syntax/Conversion Issues (Observed)

These must be handled explicitly:

1. **GDS projection does NOT accept string relationship properties**

   * Attempting to project `r.source` (string) causes: “Unsupported conversion… String”.
   * Fix: project numeric flags instead (e.g., `imputedFlag: 0/1`).

2. **Cypher `type(x)` is for relationships, not datatype**

   * Use `valueType(x)` to inspect property datatype.

3. **Temporal properties may be mixed types in legacy data**

   * We observed `ZONED DATETIME` vs INTEGER.
   * Solution: normalize to epochMillis **in DB** before doing GDS work.

4. **Sentinel values must be double-safe**

   * Using `Long.MAX_VALUE` fails conversion to double safely.
   * Use ±(2^53−1) = ±9007199254740991.

5. **GDS filter parameter typing**

   * Passing boolean parameters into `gds.graph.filter` can trigger `Boolean cannot be cast to Number`.
   * Fix: pass booleans as numeric `0/1` and compare numerically in predicates.

6. **WITH scoping**

   * Cypher `WITH` drops variables not explicitly forwarded.
   * Always carry forward variables used later (e.g., `relTypes`) via chained `WITH`s.

7. **Node-only projection / optional matches**

   * Mixing `sourceNodeProperties` without `targetNodeProperties` causes config errors.
   * For simplest/most reliable path: base graph should be projected from edges; isolated nodes are not required unless explicitly needed.

---

## 6) Architecture

### High-level design

**Phase A — Data normalization (one-time or periodic)**

* Ensure all `temporal_start` / `temporal_end` are INTEGER epochMillis or NULL.
* Ensure any filtering-required categorical values are encoded numerically (e.g., `imputedFlag` projected property).

**Phase B — Base in-memory graph (GDS graph catalog)**

* Project a single **base superset graph** once into GDS memory:

  * Node properties: `tStart`, `tEnd` (double).
  * Relationship properties: `tStart`, `tEnd`, `weight`, `imputedFlag` (double).
  * Relationship types limited to a superset you will filter from (OWNERSHIP/MANAGEMENT/FAMILY etc.).

**Phase C — Rolling window loop (Python orchestration)**
For each window:

1. Create window subgraph using `gds.graph.filter(base_graph → window_graph)`.
2. Run algorithms (metrics + embeddings) on `window_graph` in **mutate mode** where possible.
3. Stream computed node properties out.
4. Persist to Parquet (partition by window start/end).
5. Drop `window_graph`.

**Phase D — Optional Neo4j persistence**

* Only write back if needed for in-DB exploration, and do it in a time-indexed data model (not wide node properties).

---

## 7) Data Model & Outputs

### Identifiers

* Each row must include stable `entity_id`.

  * Prefer a unique property (e.g., `n.id`) over internal Neo4j node id.
  * If none exists, add one (mandatory for regression panel data).

### Output datasets (Parquet)

1. **Node features panel**

   * Columns:

     * `entity_id`
     * `window_start_ms`
     * `window_end_ms`
     * `graph_name` (optional)
     * metrics: `pagerank`, `degree`, `wcc_id`, etc.
     * embedding: `embedding` (vector) or separate `emb_0..emb_(d-1)`
     * config fields: `rel_types`, `include_imputed`, `weight_spec`, `algo_params_hash`

2. **Optional edge list per window**

   * Columns: `src_entity_id`, `dst_entity_id`, `rel_type`, `weight`, `window_start_ms`, `window_end_ms`

Partition strategy:

* Partition Parquet by `window_start_ms` or by year (derived).
* Keep a separate “manifest” table listing each window and its exact parameters.

---

## 8) Canonical Cypher: Base Projection + Window Filter

### 8.1 Base projection (validated working pattern)

**Assumptions**

* `temporal_start/end` on nodes & rels are INTEGER epochMillis or NULL.
* `r.Size` numeric or NULL.
* `r.source` is string but NOT projected; only used to compute numeric `imputedFlag`.

```cypher
CALL gds.graph.drop('base_temporal', false) YIELD graphName;

:param baseRelTypes => ['OWNERSHIP','MANAGEMENT','FAMILY'];

WITH
  'base_temporal' AS baseGraph,
  $baseRelTypes AS baseRelTypes,
  -9007199254740991.0 AS MIN_T,
   9007199254740991.0 AS MAX_T

MATCH (source:Bank|Company|Person)-[r]->(target:Bank|Company|Person)
WHERE type(r) IN baseRelTypes

WITH gds.graph.project(
  baseGraph,
  source,
  target,
  {
    sourceNodeLabels: labels(source),
    targetNodeLabels: labels(target),

    sourceNodeProperties: {
      tStart: toFloat(coalesce(source.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(source.temporal_end,   MAX_T))
    },
    targetNodeProperties: {
      tStart: toFloat(coalesce(target.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(target.temporal_end,   MAX_T))
    },

    relationshipType: type(r),
    relationshipProperties: {
      weight: toFloat(coalesce(r.Size, 1.0)),
      tStart: toFloat(coalesce(r.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(r.temporal_end,   MAX_T)),
      imputedFlag: CASE
        WHEN type(r) = 'FAMILY' AND coalesce(r.source,'') = 'imputed' THEN 1.0
        ELSE 0.0
      END
    }
  },
  { readConcurrency: 4 }
) AS g
RETURN g.graphName, g.nodeCount, g.relationshipCount, g.projectMillis;
```

### 8.2 Window filter (validated working pattern)

**Important:** use numeric `includeImputed01` (0/1) to avoid Boolean→Number cast errors.

```cypher
CALL gds.graph.drop($windowGraph, false) YIELD graphName;

WITH
  $windowGraph AS windowGraph,
  toFloat($windowStart) AS start,
  toFloat($windowEnd)   AS end,
  toFloat($includeImputed01) AS includeImputed01,
  $relTypes AS relTypes
WITH
  windowGraph, start, end, includeImputed01, relTypes,
  reduce(pred = '', t IN relTypes |
    pred + CASE WHEN pred = '' THEN '' ELSE ' OR ' END + 'r:' + t
  ) AS relTypePred

CALL gds.graph.filter(
  windowGraph,
  'base_temporal',
  '(n:Bank OR n:Company OR n:Person) AND n.tStart < $end AND n.tEnd > $start',
  '(' + relTypePred + ')
   AND r.tStart < $end AND r.tEnd > $start
   AND (r:FAMILY = FALSE OR $includeImputed01 = 1.0 OR r.imputedFlag = 0.0)',
  { parameters: { start: start, end: end, includeImputed01: includeImputed01 } }
)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis;
```

---

## 9) Algorithms to Run per Window

### 9.1 Metrics (suggested baseline)

* Degree (in/out/total) — cheap, good baseline predictor.
* PageRank — robust centrality for directed influence.
* WCC / SCC depending on directionality requirements.
* (Optional) Betweenness — expensive; consider sampling/approx if needed.

**Execution mode guidance**

* Prefer **mutate** mode for multiple algorithms on same window graph (reduce overhead).
* Stream properties out afterward.

### 9.2 Embeddings

Two recommended modes:

**Mode A (default): FastRP per window**

* Best when you accept window-specific embeddings (not strictly aligned across years).
* Set consistent parameters across windows; optionally set seed.

**Mode B (advanced): GraphSAGE**

* Train once on base graph (or a representative sample).
* Infer embeddings per window using the same model for better cross-window comparability.

---

## 10) Python Orchestration

### Responsibilities

Python should:

* Generate the window schedule (rolling 3-year windows).
* Create window graph names deterministically.
* Call:

  1. filter
  2. run algorithms
  3. export results
  4. drop graph
* Write Parquet partitions.

### Example window generation

* Let `window_size_years = 3`
* Rolling step = 1 year (or monthly if needed)
* Use `[start, end)` intervals
* Represent start/end in epoch millis

### GDS compute pattern per window

1. `CALL gds.graph.filter(...)`
2. `CALL gds.pageRank.mutate(windowGraph, {mutateProperty:'pagerank', relationshipWeightProperty:'weight'})`
3. `CALL gds.degree.mutate(windowGraph, {mutateProperty:'degree'})`
4. `CALL gds.fastRP.mutate(windowGraph, {mutateProperty:'embedding', embeddingDimension:128, relationshipWeightProperty:'weight'})`
5. `CALL gds.graph.nodeProperties.stream(windowGraph, ['pagerank','degree','embedding'])`
6. Write results → Parquet
7. `CALL gds.graph.drop(windowGraph)`

### Export format decision

* For regression: prefer embeddings as:

  * either `embedding` array column (if your stack supports list columns), or
  * expanded columns `emb_0..emb_127` (universally compatible).

### Determinism & metadata

For each window, store metadata:

* `window_start`, `window_end`
* `rel_types`
* `include_imputed`
* algorithm params (dimensions, iterations, damping factor, etc.)
* a `params_hash` (stable hash of config dict)

---

## 11) Optional Neo4j Persistence Strategy

Avoid writing per-window metrics as separate properties on nodes (schema bloat).
Instead, model time-indexed facts:

* `(:Period {start_ms, end_ms, relTypes, includeImputed01, paramsHash})`
* `(e:Entity {entity_id})-[:HAS_METRIC {name:'pagerank', value:...}]->(p:Period)`
* `(e)-[:HAS_EMBEDDING {name:'fastrp', dim:128, value:[...]}]->(p)`

Only persist:

* a small number of windows, or
* a small number of metrics required for graph exploration,
  because embedding storage can get large quickly.

---

## 12) Testing & Validation

### Unit-like checks in Neo4j

* Verify normalized types:

  * `valueType(n.temporal_start)` returns only INTEGER/NULL.
* Verify base graph node/rel counts.
* Verify filtered graph counts match expectations (spot-check a few windows).
* Verify imputed exclusion toggles counts:

  * run with `includeImputed01=0` and `1`, compare relationshipCount.

### Data correctness checks in Python

* Ensure each window output includes:

  * all nodes in window graph
  * consistent row counts per algorithm property
* Ensure embeddings dimension matches config
* Ensure no NaNs / unexpected nulls in numeric metrics

### Performance checks

* Time per window for filter + algorithms.
* Memory usage (GDS graph catalog).
* Ensure window graphs are dropped even on failure.

---

## 13) Failure Handling & Operational Safety

### Common failure modes

* Filter predicate issues (type casts, missing params).
* Graph name collisions (same windowGraph created twice).
* Forgetting to drop graphs → memory leak.
* Attempting to project unsupported property types (strings).

### Required mitigations

* Always `drop(windowGraph, false)` before creating.
* Use try/finally in Python to drop graphs on exceptions.
* Keep base graph name stable; drop/recreate only when needed.
* Log every window’s `nodeCount/relationshipCount/projectMillis`.

---

## 14) Implementation Checklist

1. **Normalization**

   * Confirm nodes/relationships temporal properties are epochMillis INTEGER/NULL.
2. **Base graph**

   * Project once with numeric-only properties and `imputedFlag`.
3. **Window loop**

   * Filter → compute metrics → compute embeddings → stream results → persist → drop.
4. **Storage**

   * Parquet partitioned by window; manifest table.
5. **Reproducibility**

   * Save full config + params hash per window.
6. **Monitoring**

   * Per-window timings, counts, and failures.

---

## 15) Exact Requirements Summary

### Must

* Use base GDS graph + `gds.graph.filter` for rolling windows.
* Use numeric flags for any filtering criteria derived from string properties.
* Use numeric parameter for include/exclude toggles (`0/1`).
* Export window results to Parquet as a panel dataset.
* Ensure cleanup of in-memory window graphs.

### Should

* Keep algorithms in mutate mode and export via nodeProperties stream.
* Maintain a manifest of windows + parameters.
* Prefer stable `entity_id` rather than Neo4j internal ids.

### Could

* Add GraphSAGE “train once, infer many” for aligned embeddings.
* Add edge-list Parquet per window for external graph tooling.

Below is a **reference Python skeleton** that implements the full “base projection → rolling window filter → compute metrics+embeddings → export to Parquet → cleanup” loop, with the **exact Cypher calls** (via `gds.run_cypher`) and the **DataFrames produced**.

It assumes:

* `temporal_start` / `temporal_end` are **epoch millis INTEGER or NULL** on both nodes and relationships (you already fixed this).
* You have a stable identifier property on nodes, e.g. `n.entity_id` (string). Since GDS can’t project strings, we’ll map `nodeId → entity_id` at export time using `gds.util.asNode(nodeId)` in Cypher.

---

# Reference implementation (Python)

## 0) Dependencies

```bash
pip install graphdatascience neo4j pandas pyarrow
```

## 1) Config + connection

```python
from __future__ import annotations

import os
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable, List, Dict, Any, Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from graphdatascience import GraphDataScience


@dataclass(frozen=True)
class PipelineConfig:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str = "neo4j"

    base_graph: str = "base_temporal"
    base_rel_types: Tuple[str, ...] = ("OWNERSHIP", "MANAGEMENT", "FAMILY")

    # Rolling windows
    window_years: int = 3
    step_years: int = 1  # rolling by 1y
    # Export
    out_dir: str = "out_parquet"

    # Filtering toggle (0/1 numeric to avoid GDS boolean cast issues)
    include_imputed01_default: int = 0

    # Algorithms
    weight_property: str = "weight"
    pagerank_mutate: str = "pagerank"
    degree_mutate: str = "degree"
    wcc_mutate: str = "wccId"  # optional
    embedding_mutate: str = "embedding"
    embedding_dim: int = 128

    # Repro hooks
    random_seed: int = 42
    concurrency: int = 4  # can set 1 for max reproducibility


def params_hash(d: Dict[str, Any]) -> str:
    blob = json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]
```

---

# 2) Cypher: base projection + window filter + export queries

### 2.1 Base projection query (validated working pattern)

This matches what you already got working: numeric-only properties, `imputedFlag` derived from string.

```python
BASE_PROJECTION_CYPHER = """
CALL gds.graph.drop($baseGraph, false) YIELD graphName;

WITH
  $baseGraph AS baseGraph,
  $baseRelTypes AS baseRelTypes,
  -9007199254740991.0 AS MIN_T,
   9007199254740991.0 AS MAX_T

MATCH (source:Bank|Company|Person)-[r]->(target:Bank|Company|Person)
WHERE type(r) IN baseRelTypes

WITH gds.graph.project(
  baseGraph,
  source,
  target,
  {
    sourceNodeLabels: labels(source),
    targetNodeLabels: labels(target),

    sourceNodeProperties: {
      tStart: toFloat(coalesce(source.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(source.temporal_end,   MAX_T))
    },
    targetNodeProperties: {
      tStart: toFloat(coalesce(target.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(target.temporal_end,   MAX_T))
    },

    relationshipType: type(r),
    relationshipProperties: {
      weight: toFloat(coalesce(r.Size, 1.0)),
      tStart: toFloat(coalesce(r.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(r.temporal_end,   MAX_T)),
      imputedFlag: CASE
        WHEN type(r) = 'FAMILY' AND coalesce(r.source,'') = 'imputed' THEN 1.0
        ELSE 0.0
      END
    }
  },
  { readConcurrency: 4 }
) AS g
RETURN g.graphName AS graphName, g.nodeCount AS nodeCount, g.relationshipCount AS relationshipCount, g.projectMillis AS projectMillis;
"""
```

### 2.2 Window filter query (numeric include_imputed01 to avoid Boolean→Number cast)

```python
WINDOW_FILTER_CYPHER = """
CALL gds.graph.drop($windowGraph, false) YIELD graphName;

WITH
  $windowGraph AS windowGraph,
  toFloat($windowStart) AS start,
  toFloat($windowEnd)   AS end,
  toFloat($includeImputed01) AS includeImputed01,
  $relTypes AS relTypes
WITH
  windowGraph, start, end, includeImputed01, relTypes,
  reduce(pred = '', t IN relTypes |
    pred + CASE WHEN pred = '' THEN '' ELSE ' OR ' END + 'r:' + t
  ) AS relTypePred

CALL gds.graph.filter(
  windowGraph,
  $baseGraph,
  '(n:Bank OR n:Company OR n:Person) AND n.tStart < $end AND n.tEnd > $start',
  '(' + relTypePred + ')
   AND r.tStart < $end AND r.tEnd > $start
   AND (r:FAMILY = FALSE OR $includeImputed01 = 1.0 OR r.imputedFlag = 0.0)',
  { parameters: { start: start, end: end, includeImputed01: includeImputed01 } }
)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis;
"""
```

### 2.3 Export query: stream metrics+embeddings **with entity_id**

This produces a DataFrame suitable for Parquet.

**Why this shape:**

* GDS node properties streaming yields `nodeId`, and you can join it back to the DB node with `gds.util.asNode(nodeId)`.
* This avoids trying to project string IDs into GDS (not supported).

```python
EXPORT_NODE_FEATURES_CYPHER = """
CALL gds.graph.nodeProperties.stream($windowGraph, $properties)
YIELD nodeId, propertyName, propertyValue
WITH
  gds.util.asNode(nodeId) AS n,
  propertyName,
  propertyValue
WITH
  n.entity_id AS entity_id,
  // pivot properties into columns
  collect([propertyName, propertyValue]) AS kvs
WITH
  entity_id,
  reduce(m = {}, kv IN kvs | m + { [kv[0]]: kv[1] }) AS props
RETURN
  entity_id,
  $windowStart AS window_start_ms,
  $windowEnd AS window_end_ms,
  $paramsHash AS params_hash,
  props[$pagerankProp] AS pagerank,
  props[$degreeProp] AS degree,
  props[$embeddingProp] AS embedding;
"""
```

> If your stable ID property is not `entity_id`, replace `n.entity_id` with the correct property. If it’s missing, add one before doing this pipeline.

---

# 3) Compute per window (algorithms)

We’ll do algorithm execution via the Python GDS client for clarity, then export via Cypher (to include `entity_id`).

```python
def ensure_base_graph(gds: GraphDataScience, cfg: PipelineConfig) -> None:
    res = gds.run_cypher(
        BASE_PROJECTION_CYPHER,
        params={
            "baseGraph": cfg.base_graph,
            "baseRelTypes": list(cfg.base_rel_types),
        },
        database=cfg.neo4j_database,
    )
    print("Base graph:", res.to_dict(orient="records")[0])


def create_window_graph(gds: GraphDataScience, cfg: PipelineConfig,
                        window_graph: str, window_start_ms: int, window_end_ms: int,
                        rel_types: List[str], include_imputed01: int) -> Dict[str, Any]:
    res = gds.run_cypher(
        WINDOW_FILTER_CYPHER,
        params={
            "windowGraph": window_graph,
            "windowStart": window_start_ms,
            "windowEnd": window_end_ms,
            "includeImputed01": include_imputed01,
            "relTypes": rel_types,
            "baseGraph": cfg.base_graph,
        },
        database=cfg.neo4j_database,
    )
    return res.to_dict(orient="records")[0]


def run_algorithms_mutate(gds: GraphDataScience, window_graph: str, cfg: PipelineConfig) -> None:
    G = gds.graph.get(window_graph)

    # Degree (cheap baseline)
    gds.degree.mutate(
        G,
        mutateProperty=cfg.degree_mutate,
        concurrency=cfg.concurrency,
    )

    # PageRank (weighted)
    gds.pageRank.mutate(
        G,
        mutateProperty=cfg.pagerank_mutate,
        relationshipWeightProperty=cfg.weight_property,
        concurrency=cfg.concurrency,
        maxIterations=20,
        dampingFactor=0.85,
    )

    # Embedding: FastRP (per window)
    gds.fastRP.mutate(
        G,
        mutateProperty=cfg.embedding_mutate,
        embeddingDimension=cfg.embedding_dim,
        relationshipWeightProperty=cfg.weight_property,
        randomSeed=cfg.random_seed,
        concurrency=cfg.concurrency,
    )


def export_window_features(gds: GraphDataScience, cfg: PipelineConfig,
                           window_graph: str, window_start_ms: int, window_end_ms: int,
                           include_imputed01: int, rel_types: List[str],
                           algo_params: Dict[str, Any]) -> pd.DataFrame:
    # Stable hash so you can join/debug later
    phash = params_hash({
        "window_start_ms": window_start_ms,
        "window_end_ms": window_end_ms,
        "include_imputed01": include_imputed01,
        "rel_types": rel_types,
        "algo_params": algo_params,
    })

    props = [cfg.pagerank_mutate, cfg.degree_mutate, cfg.embedding_mutate]

    df = gds.run_cypher(
        EXPORT_NODE_FEATURES_CYPHER,
        params={
            "windowGraph": window_graph,
            "properties": props,
            "windowStart": window_start_ms,
            "windowEnd": window_end_ms,
            "paramsHash": phash,
            "pagerankProp": cfg.pagerank_mutate,
            "degreeProp": cfg.degree_mutate,
            "embeddingProp": cfg.embedding_mutate,
        },
        database=cfg.neo4j_database,
    )

    # DataFrame columns produced:
    # entity_id (string), window_start_ms (int), window_end_ms (int),
    # params_hash (string), pagerank (float), degree (int/float), embedding (list[float])
    return df


def drop_graph(gds: GraphDataScience, cfg: PipelineConfig, graph_name: str) -> None:
    gds.graph.drop(graph_name, failIfMissing=False)
```

---

# 4) Rolling window scheduler

You’ll want window boundaries in epoch millis. Here’s a simple year-based rolling schedule using UTC.

```python
def to_epoch_ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def rolling_year_windows(start_year: int, end_year_exclusive: int, window_years: int, step_years: int) -> Iterable[Tuple[int, int]]:
    """
    Produces [start, end) windows in epoch ms.
    Example: start_year=1990, end_year_exclusive=2011, window_years=3, step_years=1
    yields 1990-1993, 1991-1994, ..., 2008-2011
    """
    y = start_year
    while y + window_years <= end_year_exclusive:
        ws = datetime(y, 1, 1, tzinfo=timezone.utc)
        we = datetime(y + window_years, 1, 1, tzinfo=timezone.utc)
        yield to_epoch_ms(ws), to_epoch_ms(we)
        y += step_years
```

---

# 5) Parquet writing (partitioned by window)

Simple “one file per window” is easiest and robust.

```python
def write_window_parquet(df: pd.DataFrame, cfg: PipelineConfig, window_start_ms: int, window_end_ms: int) -> str:
    os.makedirs(cfg.out_dir, exist_ok=True)
    fname = f"node_features_ws={window_start_ms}_we={window_end_ms}.parquet"
    path = os.path.join(cfg.out_dir, fname)
    df.to_parquet(path, index=False)
    return path
```

If you prefer a partitioned dataset layout (Hive style), use `pyarrow.dataset.write_dataset`, but one-file-per-window is often good enough.

---

# 6) Main pipeline runner

```python
def run_pipeline(cfg: PipelineConfig, start_year: int, end_year_exclusive: int) -> None:
    gds = GraphDataScience(
        cfg.neo4j_uri,
        auth=(cfg.neo4j_user, cfg.neo4j_password),
        database=cfg.neo4j_database,
    )

    ensure_base_graph(gds, cfg)

    rel_types = list(cfg.base_rel_types)
    include_imputed01 = cfg.include_imputed01_default

    algo_params = {
        "degree": {},
        "pagerank": {"maxIterations": 20, "dampingFactor": 0.85, "weight": cfg.weight_property},
        "fastrp": {"dim": cfg.embedding_dim, "seed": cfg.random_seed, "weight": cfg.weight_property},
        "concurrency": cfg.concurrency,
    }

    for ws, we in rolling_year_windows(start_year, end_year_exclusive, cfg.window_years, cfg.step_years):
        window_graph = f"win_{ws}_{we}"
        print(f"\n=== Window {ws} → {we} : {window_graph} ===")

        try:
            meta = create_window_graph(gds, cfg, window_graph, ws, we, rel_types, include_imputed01)
            print("Filtered graph:", meta)

            run_algorithms_mutate(gds, window_graph, cfg)

            df = export_window_features(
                gds, cfg,
                window_graph=window_graph,
                window_start_ms=ws,
                window_end_ms=we,
                include_imputed01=include_imputed01,
                rel_types=rel_types,
                algo_params=algo_params,
            )
            print("Export rows:", len(df))

            out_path = write_window_parquet(df, cfg, ws, we)
            print("Wrote:", out_path)

        finally:
            # Always cleanup to avoid graph-catalog memory leaks
            drop_graph(gds, cfg, window_graph)

    # Optional: keep base graph for subsequent runs, or drop it:
    # drop_graph(gds, cfg, cfg.base_graph)

    gds.close()
```

Run it:

```python
if __name__ == "__main__":
    cfg = PipelineConfig(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        neo4j_database="neo4j",
        out_dir="out_parquet",
        concurrency=4,
        random_seed=42,
    )
    run_pipeline(cfg, start_year=1990, end_year_exclusive=2011)
```

---

# 7) What DataFrames you get (exact schema)

### Node features DataFrame (`df`)

Produced by `EXPORT_NODE_FEATURES_CYPHER`:

* `entity_id` : string
* `window_start_ms` : int
* `window_end_ms` : int
* `params_hash` : string
* `pagerank` : float
* `degree` : int/float (depending on GDS return)
* `embedding` : list[float] length = `embedding_dim`

For regression pipelines that don’t like list columns, add a post-step:

```python
def expand_embedding(df: pd.DataFrame, dim: int) -> pd.DataFrame:
    emb = pd.DataFrame(df["embedding"].tolist(), columns=[f"emb_{i}" for i in range(dim)])
    df2 = pd.concat([df.drop(columns=["embedding"]), emb], axis=1)
    return df2
```

---

# 8) Notes for robustness & performance

* **Boolean parameters to filter:** keep using `includeImputed01` numeric (0/1). You already hit the cast exception when passing booleans.
* **No string projection into GDS:** never project string properties. Convert to numeric flags (`imputedFlag`) at projection time.
* **Cleanup is mandatory:** always `drop(window_graph)` in a `finally` block.
* **Entity ID mapping cost:** `gds.util.asNode(nodeId).entity_id` requires DB lookups during export. At your size (15k nodes/window) it’s usually fine, but if it becomes a bottleneck:

  * consider storing a numeric `entity_id_int` on nodes and projecting it as a numeric node property, or
  * export `nodeId` and do a separate mapping join once.
