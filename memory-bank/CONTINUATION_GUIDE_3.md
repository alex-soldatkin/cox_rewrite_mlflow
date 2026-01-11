# Continuation Guide 3: exp_007 Lagged Network Effects

**Session Date**: 2026-01-11  
**Checkpoint**: 8  
**Status**: Data infrastructure complete, model tuning needed

---

## Executive Summary

Successfully implemented **exp_007: Lagged Network Effects** to address endogeneity concerns from exp_004-006 by using temporally lagged network positions (t-4 quarters) to predict bank survival. Generated 44 quarterly network snapshots covering 2010-2020, created a specialized quarterly data loader, and integrated Neo4j death indicators and family/foreign features. Cox model now runs with proper data structure (44,295 observations, 472 events); requires scaling/penalization tuning to converge.

---

## Motivation & Research Context

### Problem: Network Endogeneity

Previous experiments (exp_004-006) showed strong network effects on bank survival, but faced endogeneity concerns:

1. **Simultaneity bias**: High centrality might result from banks absorbing failing competitors, not causing survival
2. **Omitted variables**: Unobserved factors affecting both network position and survival
3. **Reverse causality**: Survival causing network position rather than vice versa

### Solution: Temporal Lag

Use network position from **t-4 quarters** to predict survival at time **t**, exploiting temporal ordering for causal identification:

- Network metrics measured 1 year before outcome
- Reduces simultaneity bias
- Allows testing if past centrality predicts future survival
- Follows Granger causality logic

### Experimental Design

- **Data**: Quarterly snapshots (2010Q1-2020Q4) instead of rolling windows
- **Lag**: 4 quarters (1 year) as primary specification
- **Models**: Cox time-varying regression with lagged network predictors
- **Features**: Same as exp_006 (CAMEL, family, foreign) + lagged network

---

## Implementation Overview

### Phase 1: Quarterly Network Data Generation (COMPLETE ✅)

**Objective**: Generate 44 quarterly network snapshots with GDS metrics

**Approach**: Master projection + filtering (adapted from rolling windows pipeline)

**Files Created**:

1. `experiments/exp_007_lagged_network/execute_quarterly_efficient.py` - Snapshot generator
2. `rolling_windows/output/quarterly_2010_2020/*.parquet` - 44 output files
3. `rolling_windows/output/quarterly_2010_2020/quarterly_queries.cypher` - Generated queries

**Key Decisions**:

- Reuse existing `base_temporal` GDS graph projection (don't create new one)
- Use `gds.graph.filter()` for temporal subsetting (not `gds.graph.project.cypher()`)
- Run 5 algorithms per window: PageRank, InDegree, OutDegree, WCC, Louvain

**Performance**: 13.7 minutes for 44 windows (12x faster than estimated 2.9 hours)

### Phase 2: Quarterly Data Loader (COMPLETE ✅)

**Objective**: Load quarterly snapshots + accounting + Neo4j, create lagged features

**Files Created**:

1. `mlflow_utils/quarterly_window_loader.py` - Main loader class

**Key Features**:

```python
class QuarterlyWindowDataLoader:
    def load_with_lags(lag_quarters=4, start_year=2014, end_year=2020):
        # 1. Query Neo4j for bank population (death dates, family, foreign)
        # 2. Load accounting data (CAMEL ratios)
        # 3. Merge accounting + Neo4j
        # 4. Load quarterly network snapshots
        # 5. Create lagged network metrics (shift quarters forward)
        # 6. Merge on regn + quarter
        # 7. Create event indicators (last observation only)
        # Returns: DataFrame ready for Cox TV regression
```

**Integration Points**:

- Neo4j: `queries/cypher/001_get_all_banks.cypher` for deaths/family/foreign
- Accounting: `ACCOUNTING_DIR` env variable
- Network: `rolling_windows/output/quarterly_2010_2020/`

### Phase 3: Cox Model Runner (COMPLETE ✅)

**Objective**: Run Cox time-varying models with lagged network predictors

**Files Created**:

1. `experiments/exp_007_lagged_network/run_cox.py` - Model runner
2. `experiments/exp_007_lagged_network/test_data_loading.py` - Validation script
3. `experiments/exp_007_lagged_network/test_multicollinearity.py` - VIF diagnostics

**Model Specification**:

```python
Features = [
    'rw_page_rank_4q_lag',      # Lagged network
    'rw_out_degree_4q_lag',
    'camel_roa',                 # CAMEL ratios
    'camel_npl_ratio',
    'camel_tier1_capital_ratio',
    'family_rho_F',              # From Neo4j
    'foreign_FEC_d'
]
```

---

## Critical Implementation Details

### 1. Event Indicator Pattern (CRITICAL ⚠️)

**Problem Found**: Initially set `event=1` for ALL observations where `is_dead=True`, resulting in 19,172 events.

**Correct Pattern** (from exp_004 line 64-67):

```python
# event=1 ONLY for LAST observation of each dead bank
df['event'] = 0
dead_banks = df[df['is_dead'] == True]['regn'].unique()
mask_last = df.groupby('regn')['DT'].transform('max') == df['DT']
df.loc[mask_last & df['regn'].isin(dead_banks), 'event'] = 1
```

**Result**: 472 events (1.1%) - one per dead bank's final observation

**Why This Matters**: Cox time-varying models require event=1 only at transition time, not for all post-death observations.

### 2. Death Date Handling

**Discovery**: `death_date` column in Neo4j is ALL NULL

**Solution**: Use `is_dead` boolean flag instead

```python
# Don't do this:
df['event'] = df['death_date'].notna().astype(int)  # All False

# Do this:
dead_banks = df[df['is_dead'] == True]['regn'].unique()
```

### 3. Type Conversions for Merging

**Problem**: Type mismatches caused merge failures

**Solutions**:

```python
# Accounting: regn is int16
# Neo4j: regn_cbr is object (string)
# Network: regn_cbr is object (string)

# Normalize all to Int64:
banks_df['regn'] = pd.to_numeric(banks_df['regn_cbr'], errors='coerce').astype('Int64')
df_network['regn_cbr'] = pd.to_numeric(df_network['regn_cbr'], errors='coerce').astype('Int64')
```

### 4. CAMEL Ratio Mapping

**Discovery**: Accounting parquet already has CAMEL ratios, just different names

**Mapping**:

```python
df['camel_roa'] = df['ROA']
df['camel_npl_ratio'] = df['npl_ratio']
df['camel_tier1_capital_ratio'] = df['total_equity'] / df['total_assets']
```

### 5. Time Interval Creation (from exp_004)

**Critical Pattern**: Match exp_004 exactly for Cox time-varying

```python
# Create intervals
df['start'] = df['date']
df['stop'] = df.groupby('regn')['date'].shift(-1)  # Next observation

# Fill last interval
mask_last = df['stop'].isna()
df.loc[mask_last, 'stop'] = df.loc[mask_last, 'start'] + pd.Timedelta(days=30)

# Convert to days since registration
min_dates = df.groupby('regn')['date'].transform('min')
df['start_t'] = (df['start'] - min_dates).dt.days
df['stop_t'] = (df['stop'] - min_dates).dt.days

# Filter valid intervals
df = df[df['stop_t'] > df['start_t']]
```

### 6. Missing Data Strategy

**Key Decision**: Use `fillna(0)` NOT `dropna()` to preserve events

**Rationale**:

- `dropna()` drops rows with missing `camel_roa` (66% of data)
- This eliminates events disproportionately
- `fillna(0)` preserves all 472 events for model fitting

```python
# Before fillna: 14,748 obs, 0 events (all dropped)
# After fillna: 44,295 obs, 472 events ✅
df[feature_cols] = df[feature_cols].fillna(0)
```

---

## Pitfalls Encountered & Solutions

### Pitfall 1: gds.graph.project.cypher() Error

**Error**: `java.lang.NoClassDefFoundError` when calling `gds.graph.project.cypher()`

**Root Cause**: GDS version 2.16.0 compatibility issue or incorrect syntax

**Solution**: Reuse existing `base_temporal` graph instead of creating new projection

```python
# Don't create new graph
# gds.graph.project.cypher(...)  # FAILS

# Reuse existing
if not gds.graph.exists('base_temporal')['exists']:
    raise ValueError("base_temporal graph not found")
```

### Pitfall 2: Parquet Schema Conflicts

**Error**: `Expected bytes, got a 'int' object` for `regn_cbr` column

**Root Cause**: Mixed types in column (some int, some str)

**Solution**: Explicit type conversion before export

```python
df['regn_cbr'] = df['regn_cbr'].astype(str)
df['Id'] = df['Id'].astype(str)
```

### Pitfall 3: Zero Events After Data Prep

**Issue**: Cox data had 0 events despite 472 in raw data

**Root Causes**:

1. Dropping all rows with missing `camel_roa` (66% of data)
2. Events concentrated in dropped rows

**Solution**: Use `fillna(0)` strategy as exp_004 does

### Pitfall 4: Singular Matrix Error

**Issue**: Model failed with "Matrix is singular"

**Root Causes**:

1. Placeholder features (family/foreign) all zeros → removed
2. Raw accounting variables highly correlated (VIF > 150)

**Solutions**:

1. Remove constant columns before fitting
2. Use CAMEL ratios instead of raw balance sheet items
3. Integrate Neo4j for real family/foreign values

### Pitfall 5: Convergence Failure (Current)

**Issue**: Model iterates but hits NaN/Inf in hessian

**Root Cause**: Feature scaling issues (CAMEL ratios ~0.01-0.1, network ~0-100)

**Solution Needed**: Add StandardScaler normalization (see exp_006 lines 228-238)

---

## Best Practices Learned

### Data Generation

1. **Reuse master projections**: 12x speedup vs creating separate graphs
2. **Use filtering over projection**: `gds.graph.filter()` faster than `gds.graph.project.cypher()`
3. **Validate output incrementally**: Check first few windows before running all 44
4. **Explicit type conversions**: Always specify dtypes for Parquet export

### Data Loading

1. **Follow proven patterns**: Copy exp_004 event/time logic exactly
2. **Query Neo4j early**: Get deaths/family/foreign before accounting merge
3. **Handle nulls explicitly**: `fillna(False)` before type conversion
4. **Validate merge rates**: Print stats after each merge step
5. **Type consistency critical**: Normalize all keys to same type (Int64)

### Model Preparation

1. **Event timing matters**: Last observation only for Cox time-varying
2. **Preserve events**: Use `fillna(0)` not `dropna()` when possible
3. **Match reference implementations**: Copy exp_004 time interval logic exactly
4. **Test incrementally**: Small feature set first, then add complexity

### Debugging

1. **Check column names**: `REGN` vs `regn`, `ROA` vs `camel_roa`
2. **Validate data at each step**: Print shapes, null counts, event counts
3. **Use VIF diagnostics**: Identify multicollinearity before modeling
4. **Compare with working code**: exp_004 has proven patterns to follow

---

## Files Modified/Created

### New Files (exp_007)

```
experiments/exp_007_lagged_network/
├── execute_quarterly_efficient.py    # Quarterly snapshot generator
├── run_cox.py                         # Cox model runner (main script)
├── test_data_loading.py               # Standalone data validation
├── test_multicollinearity.py          # VIF diagnostics
└── PROGRESS_SUMMARY.md                # Session notes

rolling_windows/output/quarterly_2010_2020/
├── node_features_Q1_2010.parquet      # 44 quarterly snapshot files
├── ...
├── node_features_Q4_2020.parquet
├── quarterly_queries.cypher           # Generated Cypher queries
└── quarterly_summary.json             # Metadata

mlflow_utils/
└── quarterly_window_loader.py         # NEW: Quarterly data loader class
```

### Modified Files

```
queries/cypher/
└── 001_get_all_banks.cypher           # Added is_isolate filter (earlier session)

memory-bank/
└── experiment_plans/
    └── exp_007_lagged_network.md      # Detailed experiment plan

.gemini/antigravity/brain/.../
├── task.md                            # Task tracking
├── walkthrough.md                     # Session accomplishments
└── CONTINUATION_GUIDE_3.md            # This file
```

---

## Current State & Next Steps

### What Works ✅

- Quarterly data generation (44 snapshots, 13.7 min)
- Data loader with Neo4j integration (99.8% merge rate)
- Event indicators (472 events, 1.1% rate)
- Cox model accepts data and attempts to fit
- Feature set complete (network + CAMEL + family + foreign)

### Current Blocker ⚠️

**Model Convergence**: Hessian contains NaN/Inf after 4 iterations

**Diagnosis**: Feature scaling issue (common ML problem)

**Solution**: Add StandardScaler + 0-100 normalization

```python
from sklearn.preprocessing import StandardScaler

# Step 1: StandardScaler
scaler = StandardScaler()
df_cox[feature_cols] = scaler.fit_transform(df_cox[feature_cols])

# Step 2: Scale to 0-100 range
for col in feature_cols:
    min_val, max_val = df_cox[col].min(), df_cox[col].max()
    if max_val > min_val:
        df_cox[col] = 100 * (df_cox[col] - min_val) / (max_val - min_val)
```

**Alternative**: Add penalization

```python
ctv = CoxTimeVaryingFitter(penalizer=0.01, l1_ratio=0.0)
```

### Immediate Next Actions

1. Add feature scaling to `prepare_cox_data()` function
2. Re-run Cox model
3. If converges: Generate stargazer tables + interpretation
4. If still fails: Test with smaller feature set (just network + 1 CAMEL)
5. Document results in writeup

### Future Enhancements

1. **Robustness checks**: Test different lag specifications (t-1, t-2, t-8)
2. **Delta features**: Create first-difference features for autocorrelation
3. **Community stratification**: Add community strata like exp_006
4. **Instrumental variables**: Consider alternative identification strategies
5. **Placebo tests**: Future network predicting past survival

---

## Key Statistics

### Data Generation

- **Snapshots generated**: 44 (2010Q1 - 2020Q4)
- **Generation time**: 13.7 minutes (49.7 MB total)
- **Success rate**: 100% (44/44 windows)
- **Average per window**: 18.7 seconds

### Data Loader

- **Total observations**: 44,688 (after Neo4j merge)
- **Network matches**: 44,594 (99.8%)
- **Unique banks**: 791
- **Dead banks**: 472 (59.7% of banks)
- **Events**: 472 (1.1% of observations)

### Features

- **Lagged network**: 2 features (PageRank, OutDegree)
- **CAMEL ratios**: 3 features (ROA, NPL, Tier1)
- **Family/Foreign**: 2 features
- **Total**: 7 features

### Data Quality

- camel_roa: 33.8% coverage (low - filled with 0)
- camel_npl_ratio: 94.3% coverage
- camel_tier1_capital_ratio: 100% coverage
- lagged network: 99.8% coverage
- family/foreign: 100% coverage (from Neo4j)

---

## Environment & Dependencies

### Required Environment Variables

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>
ACCOUNTING_DIR=/path/to/accounting_cbr_imputed  # Note: ACCOUNTING_DIR not ACCOUNTING_PATH
```

### Key Dependencies

- `graphdatascience` (GDS Python client)
- `pandas`, `pyarrow` (Parquet I/O)
- `lifelines` (Cox models)
- `sklearn` (StandardScaler - needed for next step)
- `mlflow` (experiment tracking)

### GDS Version

- Neo4j GDS: 2.16.0
- Issue: `gds.graph.project.cypher()` not reliable - use filtering instead

---

## Code Patterns to Follow

### Quarterly Data Loading

```python
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader

loader = QuarterlyWindowDataLoader()
df = loader.load_with_lags(lag_quarters=4, start_year=2014, end_year=2020)

# Returns DataFrame with:
# - Accounting features (CAMEL ratios)
# - Lagged network metrics (rw_*_4q_lag)
# - Family/foreign features
# - Event indicators (event=1 for last obs of dead banks)
```

### Cox Model Fitting (exp_004 pattern)

```python
# Time intervals
df['start'] = df['date']
df['stop'] = df.groupby('regn')['date'].shift(-1)
mask_last = df['stop'].isna()
df.loc[mask_last, 'stop'] = df.loc[mask_last, 'start'] + pd.Timedelta(days=30)

# Time since registration
min_dates = df.groupby('regn')['date'].transform('min')
df['start_t'] = (df['start'] - min_dates).dt.days
df['stop_t'] = (df['stop'] - min_dates).dt.days

# Filter valid intervals
df = df[df['stop_t'] > df['start_t']]

# Fit
ctv = CoxTimeVaryingFitter(penalizer=0.01)
ctv.fit(df, id_col='regn', event_col='event',
        start_col='start_t', stop_col='stop_t')
```

---

## Troubleshooting Guide

### "Matrix is singular" error

**Causes**: Constant columns, perfect collinearity
**Solutions**:

1. Drop constant columns: `df[col].nunique() > 1`
2. Check VIF: Use `test_multicollinearity.py`
3. Use ratios not raw values

### "Hessian contains NaN/Inf" error

**Causes**: Feature scaling issues, extreme values
**Solutions**:

1. Add StandardScaler normalization
2. Add penalization (`penalizer > 0`)
3. Check for outliers: `df.describe()`

### Zero events after data prep

**Causes**: Dropping rows with NaN disproportionately removes events
**Solutions**:

1. Use `fillna(0)` instead of `dropna()`
2. Impute missing values strategically
3. Check event preservation at each step

### Type mismatch in merge

**Causes**: Inconsistent types between DataFrames
**Solutions**:

1. Normalize all keys to Int64: `pd.to_numeric(...).astype('Int64')`
2. Check dtypes before merge: `df.dtypes`
3. Use `.astype()` consistently

### death_date all null

**Cause**: Neo4j property DeathDate not populated
**Solution**: Use `is_dead` boolean flag instead

```python
dead_banks = df[df['is_dead'] == True]['regn'].unique()
mask_last = df.groupby('regn')['DT'].transform('max') == df['DT']
df.loc[mask_last & df['regn'].isin(dead_banks), 'event'] = 1
```

---

## References to Previous Work

### Patterns Borrowed From:

- **exp_004**: Event indicator logic, time interval creation
- **exp_006**: Feature specification, CAMEL ratios, StandardScaler normalization
- **rolling_windows/pipeline.py**: Master projection + filtering approach

### Key Files to Reference:

1. `experiments/exp_004_rolling_window_tv/run_cox.py` - Time-varying Cox pattern
2. `experiments/exp_006_community_fixed_effects/run_cox.py` - Normalization
3. `mlflow_utils/rolling_window_loader.py` - Neo4j integration pattern
4. `rolling_windows/pipeline.py` - GDS filtering approach

---

## Success Criteria

### Phase 1: Data Infrastructure (COMPLETE ✅)

- [x] Generate quarterly network snapshots
- [x] Create quarterly data loader
- [x] Integrate Neo4j for deaths/family/foreign
- [x] Match exp_004 event/time patterns
- [x] Achieve >85% network merge rate

### Phase 2: Model Implementation (IN PROGRESS ⏳)

- [x] Cox model accepts data structure
- [x] Event indicators correct (472 events)
- [ ] Model converges (needs scaling)
- [ ] Generate coefficients + stargazer tables
- [ ] Create interpretation report

### Phase 3: Analysis (NOT STARTED)

- [ ] Compare lagged vs contemporaneous effects
- [ ] Test different lag specifications
- [ ] Implement autocorrelation diagnostics
- [ ] Write up results

---

## Conclusion

**Status**: Data pipeline complete and validated. Model structure correct. Requires standard ML tuning (feature scaling) to converge.

**Time Investment**: ~4 hours total

- Data generation: 13.7 minutes
- Loader development: ~2 hours (with debugging)
- Model setup: ~1.5 hours (matching exp_004 patterns)
- Documentation: ~30 minutes

**Key Achievement**: Successfully created reusable quarterly snapshot infrastructure that can support multiple lag specifications and robustness checks for addressing network endog eneity.

**Next Session**: Add StandardScaler normalization to `prepare_cox_data()`, re-run model, and document results if convergence achieved.
