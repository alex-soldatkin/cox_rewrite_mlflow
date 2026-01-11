# Rolling Windows: Implementation Notes

This directory contains a modular rolling-window pipeline for temporal graph analytics using Neo4j Graph Data Science (GDS) and Python.

## What was added

### Output folder (gitignored)

- `data_processing/rolling_windows/output/.gitignore` ignores all generated outputs in `data_processing/rolling_windows/output/`.
- The pipeline writes Parquet datasets under `data_processing/rolling_windows/output/`.

### Python modules

- `data_processing/rolling_windows/config.py`: config + `.env` loading (via `python-dotenv`).
- `data_processing/rolling_windows/dates.py`: year-based rolling window schedule.
- `data_processing/rolling_windows/gds_client.py`: `GraphDataScience` client creation.
- `data_processing/rolling_windows/metrics.py`: per-window algorithm calls (mutate mode).
- `data_processing/rolling_windows/parquet.py`: embedding expansion + parquet writer helpers.
- `data_processing/rolling_windows/pipeline.py`: orchestration (base graph → filter windows → run algos → export).
- `data_processing/rolling_windows/run_pipeline.py`: CLI entrypoint.

### Cypher templates (new files; existing Cypher left unchanged)

These are added under `data_processing/cypher/` as *pipeline-owned* templates and references:

- `data_processing/cypher/35_0_rollwin_base_temporal_projection.cypher`: creates the base superset graph for filtering.
- `data_processing/cypher/35_1_rollwin_filter_window_graph.cypher`: reference filter query (Browser/debugging).
- `data_processing/cypher/35_2_rollwin_metrics_reference.cypher`: reference mutate+stream calls (Browser/debugging).

## Pipeline semantics (aligned to existing schema)

### Base temporal projection

The pipeline creates (if missing) a GDS in-memory graph named `base_temporal` (configurable):

- Nodes: `:Bank|:Company|:Person`
- Relationships: subset of `['OWNERSHIP','MANAGEMENT','FAMILY']` (configurable)
- Projected properties:
  - nodes:
    - `tStart`, `tEnd` (double; from `temporal_start` / `temporal_end` epochMillis, coalesced to ±(2^53−1))
    - `bank_feats`, `network_feats` (LIST; existing feature vectors stored on nodes in Neo4j)
    - `is_dead` (double; from boolean `is_dead`)
  - rels: `weight` (double; from `r.Size` default 1.0), `tStart`, `tEnd`, `imputedFlag` (numeric)

### Window membership

Each rolling window uses `[start, end)` overlap rules:

- node active if `n.tStart < end AND n.tEnd > start`
- relationship active if `r.tStart < end AND r.tEnd > start`
- imputed FAMILY handling:
  - exclude imputed FAMILY by default (`include_imputed01 = 0`)
  - include if `include_imputed01 = 1`

### Metrics/embeddings per window

Per window graph (named `rw_<startYear>_<endYearInclusive>`):

- PageRank → `page_rank` (weighted by `weight`)
- Degree (unweighted):
  - in-degree → `in_degree` (orientation `REVERSE`)
  - out-degree → `out_degree` (orientation `NATURAL`)
  - total `degree` is computed in Python as `in_degree + out_degree`
- WCC (optional) → `wcc`
- Louvain (optional) → `community_louvain` (weighted by `weight`)
- FastRP (optional) → `fastrp_embedding` (weighted by `weight`)
- HashGNN (optional) → `hash_gnn_embedding` (uses `bank_feats` by default)
- Node2Vec (optional) → `node2vec_embedding` (weighted by `weight`)

The pipeline streams node properties from the in-memory graph and also fetches a stable node identifier from the DB:

- default `id_property`: `neo4jImportId`
- exported as: `entity_id`

## Outputs

All outputs go under `data_processing/rolling_windows/output/`:

- Node panel per window:
  - `data_processing/rolling_windows/output/nodes/node_features_rw_<start>_<end>.parquet`
  - columns include:
    - `entity_id`, `nodeId`, `nodeLabels`
    - `window_start_ms`, `window_end_ms`, `window_start_year`, `window_end_year_inclusive`, `window_graph_name`
    - metrics (`page_rank`, `in_degree`, `out_degree`, `degree`, …)
    - feature vectors (`bank_feats`, `network_feats`)
    - feature blocks derived from `bank_feats` (`state_feats`, `legal_feats`, `governance_feats`, `finance_feats`, `ip_feats`, `ops_feats`, `other_feats`)
    - `fastrp_embedding` stored as list< float > (no flattening by default)
    - optional embeddings (`hash_gnn_embedding`, `node2vec_embedding`)
- Edge list per window:
  - `data_processing/rolling_windows/output/edges/edge_list_rw_<start>_<end>.parquet`
  - columns include:
    - `sourceNodeId`, `targetNodeId`, `relationshipType`
    - `source_Id`, `target_Id` (from Neo4j node property `Id` by default; configurable)
    - `window_start_ms`, `window_end_ms`, `window_start_year`, `window_end_year_inclusive`, `window_graph_name`
- Run manifest:
  - `data_processing/rolling_windows/output/manifest/manifest_<params_hash>.parquet`

## How to run

From the project root, with the uv environment active:

```bash
uv run data_processing/rolling_windows/run_pipeline.py \
  --start-year 2005 \
  --end-start-year 2010 \
  --window-years 3 \
  --step-years 1
```

Common options:

- include imputed FAMILY relationships:
  - `--include-imputed`
- choose relationship types:
  - `--rel-types OWNERSHIP MANAGEMENT FAMILY`
- disable expensive steps:
  - `--no-louvain`, `--no-wcc`, `--no-fastrp`
- expand embeddings into `emb_0..emb_(d-1)` columns (while keeping `fastrp_embedding` list column):
  - `--expand-embeddings`
- disable/enable edge-list export:
  - `--export-edges` (default) / `--no-export-edges`
- choose which Neo4j property is used to label endpoints in the edge list:
  - `--edge-id-property Id`
- disable/enable exporting feature vectors / blocks:
  - `--export-feature-vectors` (default) / `--no-export-feature-vectors`
  - `--export-feature-blocks` (default) / `--no-export-feature-blocks`
- run additional embeddings per window:
  - `--hashgnn` / `--no-hashgnn`
  - `--node2vec` / `--no-node2vec`
- resume runs by skipping already-written windows:
  - `--skip-existing` (default) / `--no-skip-existing`
- enable/disable GDS progress bars:
  - `--show-progress` (default) / `--no-show-progress`
- retry transient Neo4j failures per window:
  - `--max-retries`, `--retry-backoff-seconds`
- logging:
  - `--log-level {DEBUG,INFO,WARNING,ERROR}`
  - `--log-file path/to/run.log`
- rebuild the base graph:
  - `--rebuild-base-graph`

## Required environment variables

Loaded from `.env` using `python-dotenv`:

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- optional: `NEO4J_DATABASE` (defaults to Neo4j server default)

## Existing feature vectors + embeddings (already in DB)

Rolling windows currently compute window-specific graph metrics/embeddings in-memory and export them, but the project also has **global** (non-windowed) feature vectors and embeddings already computed/written into Neo4j and used in existing projections.

### `bank_feats` (domain features vector)

Defined and written by `data_processing/cypher/23_1_set_feature_vector.cypher`.

Key properties:

- `bank_feats` is created from a curated list of node properties (mostly counts/flags).
- Missing values are coerced to `0.0`, booleans are mapped to `1.0/0.0`, non-numeric values are `0.0` after `toFloat` coercion.
- The feature list is **sorted alphabetically** before building the vector; therefore the vector index mapping is deterministic (see “Vector index map” below).
- The Cypher writes `bank_feats` not only for `:Bank` but also for `:Company`, `:Person`, `:MunicipalSubject` (and zero-fills others).

### `network_feats` (network-metrics vector)

Defined and written by `data_processing/cypher/23_1_set_feature_vector.cypher`.

It is built from network metrics that are written to nodes by:

- `data_processing/cypher/21_network_metrics.cypher` (e.g. `page_rank`, `in_degree`, `out_degree`, `betweenness`, `eigenvector`, `closeness`, `harmonic_centrality`).

`network_feats` specifically uses (alphabetically sorted) the subset:

- `betweenness`, `eigenvector`, `in_degree`, `out_degree`, `page_rank`

### `hash_gnn_embedding` (HashGNN)

Written by `data_processing/cypher/23_4_hash_gnn_node2vec_embedding.cypher` using `gds.hashgnn.write(...)`.

Notes:

- Feature input: `featureProperties: ['bank_feats']`
- Output: `hash_gnn_embedding` is an embedding vector on each node (configured as `outputDimension: 256` in the Cypher).

### `node2vec_embedding` (Node2Vec)

Also written by `data_processing/cypher/23_4_hash_gnn_node2vec_embedding.cypher` using `gds.node2vec.write(...)`.

### Other existing “global” network stats

These are currently computed on the non-temporal projections (not per rolling window):

- `data_processing/cypher/31_network_stats.cypher`:
  - triangle count → `triangles`
  - local clustering coefficient → `clustering_coefficient_7hop`
  - all-pairs shortest paths stats (diameter / avg distance)
- `data_processing/cypher/23_0_write_louvain.cypher`:
  - Louvain communities → `community_louvain`

### Existing projections that use these properties

- `data_processing/cypher/20_project_bank_ownership_mgmt.cypher` projects `bank_feats`, `network_feats`, and `is_dead` onto `banks_network_7hops` / `banks_network_7hops_undirected` along with relationship property `Size`.
- `data_processing/cypher/23_2_fastrp_embeddings.cypher` runs FastRP using `featureProperties: ['bank_feats', 'network_feats']` (and `relationshipWeightProperty: 'Size'`).
- `data_processing/cypher/23_3_hdbscan_Comms.cypher` clusters nodes using `nodeProperty: 'bank_feats'`.

## Vector index map (0-based)

In `data_processing/cypher/23_1_set_feature_vector.cypher`, both vectors are constructed by sorting the chosen property list alphabetically and then emitting `[prop IN props | ...]`.
That means:

- vector index is **0-based**
- index `i` corresponds to the `i`-th element of the **alphabetically sorted** property list

### `network_feats` index → metric

| idx | property |
|---:|---|
| 0 | `betweenness` |
| 1 | `eigenvector` |
| 2 | `in_degree` |
| 3 | `out_degree` |
| 4 | `page_rank` |

### `bank_feats` index → property

| idx | property |
|---:|---|
| 0 | `Accreditation` |
| 1 | `Arbitr` |
| 2 | `AsEntrepreneur` |
| 3 | `AsManagementCompany` |
| 4 | `AsManager` |
| 5 | `AsRegistrar` |
| 6 | `AsShareholder` |
| 7 | `Auditors` |
| 8 | `AuthorisedCapital` |
| 9 | `Bailiffs` |
| 10 | `Branch` |
| 11 | `Contacts` |
| 12 | `Contracts` |
| 13 | `CustomsWarehouses` |
| 14 | `EgrulListsDebtors` |
| 15 | `EgrulListsDisqPersons` |
| 16 | `EgrulListsEntitiesWithDisqPersons` |
| 17 | `EgrulListsMassFounder` |
| 18 | `EgrulListsMassManager` |
| 19 | `EgrulListsUnreported` |
| 20 | `ExporterProducts` |
| 21 | `FedresursMessages` |
| 22 | `FedresursPledge` |
| 23 | `Finance` |
| 24 | `FipsApplications` |
| 25 | `FipsPatents` |
| 26 | `FnsDocuments` |
| 27 | `GeneralJurisdictionCourts` |
| 28 | `Insurance` |
| 29 | `IsActual` |
| 30 | `IssuersMessages` |
| 31 | `License` |
| 32 | `LlcShare` |
| 33 | `ManagementCompany` |
| 34 | `Manager` |
| 35 | `MassMedia` |
| 36 | `PaidTax` |
| 37 | `Patents` |
| 38 | `Predecessor` |
| 39 | `Receipts` |
| 40 | `Registrar` |
| 41 | `ReorganizationInfo` |
| 42 | `RepresentativeOffice` |
| 43 | `Salaries` |
| 44 | `Shareholder` |
| 45 | `Subsidies` |
| 46 | `Successor` |
| 47 | `TaxArrears` |
| 48 | `Trademark` |
| 49 | `Vacancies` |
| 50 | `Vehicles` |
| 51 | `WaterObjects` |
| 52 | `WoodDeals` |
| 53 | `WoodRents` |
| 54 | `state_control_paths` |
| 55 | `state_controlled_companies` |
| 56 | `state_direct_owners` |
| 57 | `state_direct_ownership_value` |
| 58 | `state_ownership_percentage` |
| 59 | `unique_state_entities` |

## Suggested decomposition of `bank_feats` into thematic feature blocks

The project currently stores a single `bank_feats` vector, but for modeling/interpretability it’s useful to treat it as multiple **feature blocks** (e.g., `state_feats`, `legal_feats`, …) derived from the same underlying vector.

Below is a suggested mapping based on the **property names** in `data_processing/cypher/23_1_set_feature_vector.cypher` and the 0-based index map above.
This is documentation-only: no separate vectors are written in the rolling-window pipeline at the moment.

### `state_feats`

State/ownership/control-related fields:

- 45: `Subsidies`
- 54: `state_control_paths`
- 55: `state_controlled_companies`
- 56: `state_direct_owners`
- 57: `state_direct_ownership_value`
- 58: `state_ownership_percentage`
- 59: `unique_state_entities`

### `legal_feats`

Legal enforcement / registries / public-record signals:

- 1: `Arbitr`
- 9: `Bailiffs`
- 14: `EgrulListsDebtors`
- 15: `EgrulListsDisqPersons`
- 16: `EgrulListsEntitiesWithDisqPersons`
- 17: `EgrulListsMassFounder`
- 18: `EgrulListsMassManager`
- 19: `EgrulListsUnreported`
- 21: `FedresursMessages`
- 22: `FedresursPledge`
- 27: `GeneralJurisdictionCourts`
- 41: `ReorganizationInfo`

### `governance_feats`

Corporate governance / roles / org structure:

- 3: `AsManagementCompany`
- 4: `AsManager`
- 5: `AsRegistrar`
- 6: `AsShareholder`
- 10: `Branch`
- 33: `ManagementCompany`
- 34: `Manager`
- 40: `Registrar`
- 42: `RepresentativeOffice`
- 44: `Shareholder`
- 38: `Predecessor`
- 46: `Successor`

### `finance_feats`

Finance/tax/liability proxies:

- 8: `AuthorisedCapital`
- 12: `Contracts`
- 23: `Finance`
- 36: `PaidTax`
- 39: `Receipts`
- 47: `TaxArrears`
- 32: `LlcShare`
- 28: `Insurance`

### `ip_feats`

IP / licensing / patents:

- 31: `License`
- 25: `FipsPatents`
- 37: `Patents`
- 48: `Trademark`

### `ops_feats`

Operational footprint / staffing / activity:

- 20: `ExporterProducts`
- 43: `Salaries`
- 49: `Vacancies`
- 50: `Vehicles`
- 51: `WaterObjects`
- 52: `WoodDeals`
- 53: `WoodRents`

### `other_feats` (catch-all)

Everything else in `bank_feats` not listed above (e.g., `Accreditation`, `Auditors`, `Contacts`, `CustomsWarehouses`, `FipsApplications`, `FnsDocuments`, `IssuersMessages`, `MassMedia`, etc.) can be kept as `other_feats` or re-assigned to a more specific block once we formalize a schema for feature groups.

## Edge-list export schema (for source_/target_ columns)

The rolling-window pipeline exports an **edge list per window** under `data_processing/rolling_windows/output/edges/`.
The current implementation focuses on a minimal, join-friendly schema (endpoints labeled by a stable Neo4j node property).

Currently exported columns:

- `window_start_ms`, `window_end_ms`, `window_start_year`, `window_end_year_inclusive`, `window_graph_name`
- `sourceNodeId`, `targetNodeId`, `relationshipType`
- `source_Id`, `target_Id` (by default; configurable via `--edge-id-property`)

If we want a richer edge schema later, add:

- `source_neo4jImportId`, `target_neo4jImportId` (to align with node panel `entity_id`)
- `source_Ogrn`, `source_Inn`, `target_Ogrn`, `target_Inn`
- relationship properties like `weight` (projected from `r.Size`) and temporal bounds (`tStart`, `tEnd`)

Relevant reference files for this:

- `data_processing/cypher/32_2_stream_projection.cypher` (streams relationships from a projected graph)
- `data_processing/cypher/current_db_schema.json` (shows which labels expose `Id` / `Ogrn` / `Inn`, etc.)


For a 5-year window with 1-year overlap, set step-years = 5 - 1 = 4:

```shell
uv run data_processing/rolling_windows/run_pipeline.py \
  --start-year 2000 \
  --end-start-year 2010 \
  --window-years 5 \
  --step-years 4
``` 

(If instead you meant “advance by 1 year each time”, use --step-years 1 — that gives a 4-year overlap.)