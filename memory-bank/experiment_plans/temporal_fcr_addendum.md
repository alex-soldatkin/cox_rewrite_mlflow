# Temporal FCR Migration: Critical Implementation Details

**Date**: 2026-01-13  
**Status**: Technical Addendum to Main Plan

---

## 1. Biannual Data Reality (NOT Quarterly)

**CRITICAL CORRECTION**: The temporal FCR data from `production_run_1990_2022_v6` is **BIANNUAL** (2-year windows), NOT quarterly.

### Data Structure

- **Windows**: 17 files covering 1990-2022
- **Step Size**: 2 years (e.g., 1990-1991, 1992-1993, ...)
- **File naming**: `node_features_rw_YYYY_YYYY.parquet` where YYYY spans 2 years

### Implications for Migration

**Challenge**: Cox models in exp_007, exp_008, exp_011, exp_012 currently expect quarterly observations.

**Options**:

**Option A: Use Window Midpoint** (Recommended for initial migration)

- Treat each 2-year window as a single biannual observation
- Assign observation date = window midpoint
- Adjust lag specifications: `lag_periods=2` → 4-year lag (comparable to original 4-quarter lag)

**Option B: Forward-Fill to Pseudo-Quarterly** (If needed for compatibility)

- Expand each window into 8 quarterly pseudo-observations
- **Warning**: Artificially inflates temporal resolution
- Use only if experiments break without quarterly data

**Recommended Approach**: Start with Option A. Only implement Option B if necessary.

---

## 2. GDS ID Merge Strategy (Critical for Robustness)

### The Problem: NodeId Renumbering

From `rolling_windows/pipeline.py` and `metrics.py`:

- **GDS Internal `nodeId`**: Renumbered per filtered subgraph (unstable)
- **`gds_id` Property**: Persistent `id(n)` from Neo4j (stable across all windows)

### Implementation (From `rolling_windows/pipeline.py`: Lines 436-449)

```python
# Fetch Node IDs via Cypher using gds_id match
id_query = """
MATCH (n)
RETURN id(n) as gds_id, coalesce(n.Id, n.neo4jImportId, "GDS_" + toString(id(n))) as entity_id
"""
ids_df = gds.run_cypher(id_query)
ids_df["gds_id"] = ids_df["gds_id"].astype("int64")

# Merge on gds_id (persistent ID)
if "gds_id" in df.columns:
    df["gds_id"] = df["gds_id"].astype("int64")
    df = df.merge(ids_df, on="gds_id", how="left")
```

### Key Points

1. **Always use `gds_id` for merging**, not `entity_id` or `nodeId`
2. `gds_id` = Neo4j's internal `id(n)`, stored as a node property (setby `migration_gds_id.py`)
3. FCR computation in `metrics.py:compute_fcr_temporal` returns dict keyed by `gds_id` (line 204)
4. Temporal FCR data already includes `gds_id` column in parquet files

### TemporalFCRLoader Must:

```python
# In loader
def load_with_lags(...):
    # 1. Load parquet (has gds_id already)
    df = pd.read_parquet(node_file)

    # 2. gds_id is already present - use it for any Neo4j merges
    # Do NOT rely on entity_id for critical joins

    # 3. Fetch CAMEL data from Neo4j using gds_id
    camel_query = """
    MATCH (n:Bank)
    RETURN id(n) AS gds_id, n.regn_cbr AS regn, ...CAMEL ratios...
    """
    camel_df = gds.run_cypher(camel_query)
    camel_df["gds_id"] = camel_df["gds_id"].astype("int64")

    # 4. Merge on gds_id
    df = df.merge(camel_df, on="gds_id", how="left")
```

---

## 3. FCR Column Naming

**In parquet files**: `fcr_temporal` (from `pipeline.py` line 480)

```python
df["fcr_temporal"] = df["gds_id"].map(fcr_map).fillna(0.0)
```

**NOT**: `family_degree` (that's the raw GDS degree count, different metric)

### Column Mapping for Loader

| Parquet Column  | Rename To (for experiments)        | Source                                    |
| --------------- | ---------------------------------- | ----------------------------------------- |
| `fcr_temporal`  | `family_connection_ratio_temporal` | Cypher FCR computation (includes imputed) |
| `family_degree` | (keep as is, or drop)              | GDS degree.mutate on FAMILY edges only    |
| `gds_id`        | (keep for merging)                 | Neo4j `id(n)`                             |
| `entity_id`     | `regn` (if using entity_id)        | Neo4j `.Id` or `.neo4jImportId`           |

**Recommendation**: Use `fcr_temporal` as the primary FCR metric.

---

## 4. Updated TemporalFCRLoader Specification

```python
class TemporalFCRLoader:
    """Load temporal FCR data from production_run_1990_2022_v6."""

    def __init__(self, base_dir='data_processing/rolling_windows/output/production_run_1990_2022_v6'):
        self.base_dir = Path(base_dir)
        self.nodes_dir = self.base_dir / 'nodes'

    def load_with_lags(self, lag_periods=2, start_year=2014, end_year=2020):
        """
        Load biannual temporal FCR data.

        Args:
            lag_periods: Number of 2-year periods to lag (default=2 → 4-year lag)
            start_year: Filter windows starting from this year
            end_year: Filter windows ending before this year

        Returns:
            DataFrame with columns:
            - regn: Bank ID
            - DT: Observation date (window midpoint)
            - fcr_temporal: Temporal FCR (ground truth + imputed)
            - fcr_temporal_lag: Lagged FCR
            - page_rank: PageRank from GDS
            - page_rank_lag: Lagged PageRank
            - out_degree, in_degree: Degree centrality
            - camel_roa, camel_npl_ratio, camel_tier1_capital_ratio: Accounting
            - is_dead: Bank death indicator
            - event: Cox TV event indicator (1 only for last obs of dead banks)
            - gds_id: Persistent Neo4j ID (for advanced merging)
        """
        # 1. Load parquet files
        dfs = []
        for file in sorted(self.nodes_dir.glob('node_features_rw_*.parquet')):
            df_window = pd.read_parquet(file)

            # Filter by year
            start_ms = df_window['window_start_ms'].iloc[0]
            end_ms = df_window['window_end_ms'].iloc[0]
            start_dt = pd.to_datetime(start_ms, unit='ms')
            end_dt = pd.to_datetime(end_ms, unit='ms')

            if start_dt.year < start_year - 2:  # Include lag buffer
                continue
            if end_dt.year > end_year + 2:
                continue

            dfs.append(df_window)

        df = pd.concat(dfs, ignore_index=True)

        # 2. Assign observation date (window midpoint)
        df['window_start'] = pd.to_datetime(df['window_start_ms'], unit='ms')
        df['window_end'] = pd.to_datetime(df['window_end_ms'], unit='ms')
        df['DT'] = df['window_start'] + (df['window_end'] - df['window_start']) / 2

        # 3. Rename columns
        df = df.rename(columns={
            'fcr_temporal': 'family_connection_ratio_temporal',
            'entity_id': 'regn'  # If entity_id exists, otherwise use gds_id merge
        })

        # 4. Create lagged features (shift by lag_periods × 2 years)
        df = df.sort_values(['regn', 'DT'])
        for col in ['family_connection_ratio_temporal', 'page_rank', 'out_degree']:
            df[f'{col}_lag'] = df.groupby('regn')[col].shift(lag_periods)

        # 5. Merge CAMEL data (using gds_id for robustness)
        df = self._merge_camel_data(df)

        # 6. Create Cox event indicators
        df = self._create_event_indicators(df)

        return df

    def _merge_camel_data(self, df):
        """Merge CAMEL ratios from Neo4j using gds_id."""
        # Implementation: Query Neo4j for CAMEL by gds_id
        pass

    def _create_event_indicators(self, df):
        """Create event=1 only for last observation of dead banks."""
        df['event'] = 0
        dead_banks = df[df['is_dead'] == True]['regn'].unique()
        for bank in dead_banks:
            last_date = df[df['regn'] == bank]['DT'].max()
            df.loc[(df['regn'] == bank) & (df['DT'] == last_date), 'event'] = 1
        return df
```

---

## 5. Lag Specification Conversion

**Original experiments**: `lag_quarters=4` (1-year lag in quarterly data)

**Temporal (biannual)**: `lag_periods=2` (4-year lag in 2-year windows)

**Conversion Table**:

| Original Quarterly Lag | Temporal Biannual Lag                       | Actual Time Span |
| ---------------------- | ------------------------------------------- | ---------------- |
| `lag_quarters=1`       | `lag_periods=0.5` (fractional, problematic) | 3 months         |
| `lag_quarters=2`       | `lag_periods=0.5` (fractional, problematic) | 6 months         |
| `lag_quarters=4`       | `lag_periods=2`                             | 1 year           |
| `lag_quarters=8`       | `lag_periods=4`                             | 2 years          |

**Recommendation**: Only use `lag_periods` in multiples of 1 (2-year increments). Fractional lags not possible with biannual data.

**Alternative**: If experiments truly need quarterly lags, must implement Option B (forward-fill to pseudo-quarterly).

---

## 6. Experiment-Specific Adjustments

### exp_007, exp_008: Lagged Network (4Q lag)

- Original: `QuarterlyWindowDataLoader(lag_quarters=4)`
- Temporal: `TemporalFCRLoader(lag_periods=2)`
- Effect: 4-year lag instead of 1-year (more conservative endogeneity test)

### exp_011: Subperiod Analysis

- Originally spans 2004-2020
- Temporal data starts 1990 → Can extend to 1990-2020 if desired
- Keep 2004 start for comparability, note 1990-2003 available

### exp_013: Reverse Causality (Biennial)

- **Perfect alignment**: Biennial cross-sections + biannual data
- Each cross-section = one 2-year window
- No interpolation needed for base biennial models
- ∆FCR computation straightforward: `FCR(t+2) - FCR(t)`

---

## 7. Action Items

**Phase 1: Infrastructure**

- [ ] Create `TemporalFCRLoader` with biannual handling (Option A: midpoint)
- [ ] Test `gds_id` merge robustness with sample Neo4j query
- [ ] Validate `fcr_temporal` column exists and has expected distribution

**Phase 2: Simple Migration (exp_007)**

- [ ] Migrate exp_007 with `lag_periods=2`
- [ ] Compare coefficients with original (expect attenuation due to longer lag)
- [ ] Document biannual vs quarterly difference in writeup

**Phase 3: Test Cases**

- [ ] Verify FCR time-varying % > 10% (vs 0.2% in static)
- [ ] Check gds_id merge success rate (should be ~100%)
- [ ] Validate CAMEL merge rates (report missing %)

---

## 8. References

**Implementation Files Reviewed**:

- `rolling_windows/pipeline.py` (Lines 90-632): Native projection, gds_id usage, FCR merge
- `rolling_windows/metrics.py` (Lines 149-227): `compute_fcr_temporal` Cypher query
- `memory-bank/temporal_fcr_link_pred_implementation.md`: Full pipeline documentation

**Key Insights**:

- `gds_id` = `id(n)` from Neo4j, stored as node property before projection
- FCR computed via Cypher on temporal ownership edges, keyed by `gds_id`
- Biannual windows (not quarterly) with 2-year steps

---

**Status**: Ready for implementation  
**Next Step**: Create `TemporalFCRLoader` skeleton and test on single window
