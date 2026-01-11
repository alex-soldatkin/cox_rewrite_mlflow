# exp_007 Progress Summary

## ✅ Completed (Phase 1: Data Infrastructure)

### 1. Quarterly Network Snapshots Generated

- **44 quarterly windows** (2010-2020) successfully generated in **13.7 minutes**
- **100% success rate** (44/44 windows processed)
- Output: `rolling_windows/output/quarterly_2010_2020/`
- **1.7M bank-quarter observations** with network metrics:
  - `rw_page_rank`, `rw_in_degree`, `rw_out_degree`, `rw_degree`
  - `rw_community_louvain` (hierarchical)
  - `rw_wcc` (weakly connected component)

### 2. Quarterly Window Data Loader Created

- File: `mlflow_utils/quarterly_window_loader.py`
- **Successfully loads and lags network data**
- **86.7% merge rate** (44,482/51,316 observations)
- **51K observations** across **933 unique banks** (2014-2020)
- Supports flexible lag specifications (tested with 4-quarter = 1 year lag)

### 3. MLflow Integration

- Experiment created: `exp_007_lagged_network`
- Successfully connects to MLflow server (http://127.0.0.1:5000)

### 4. Multicollinearity Diagnostics

- Created `test_multicollinearity.py` script
- **Identified severe multicollinearity** in raw accounting variables:
  - `total_loans`: VIF = **155** ❌
  - `total_deposits`: VIF = **124** ❌
  - `total_liquid_assets`: VIF = **37** ❌
  - `total_equity`: VIF = **27** ❌
- **Confirmed**: Need CAMEL ratios (not raw balance sheet items)

## ⚠️ Identified Issues

### Issue 1: Missing Derived Features

Current quarterly loader only has:

- ✅ Raw accounting data (total_assets, total_equity, etc.)
- ✅ Lagged network metrics

**Missing** (needed to match exp_006 specification):

- ❌ CAMEL ratios: `camel_roa`, `camel_npl_ratio`, `camel_tier1_capital_ratio`
- ❌ Family metrics: `family_rho_F`, `family_FOP`
- ❌ Foreign ownership: `foreign_FEC_d`
- ❌ Event indicator (`event` - from Neo4j death dates)
- ❌ Time columns (`start_t`, `stop_t` - for Cox time-varying)

### Issue 2: Data Integration Pattern

The `QuarterlyWindowDataLoader` is standalone, but should follow the same pattern as `RollingWindowDataLoader`:

Current exp_006 pattern:

```python
# 1. Load bank population from Neo4j (family, foreign, bank_id, death dates)
# 2. Load accounting data
# 3. Load rolling window network metrics
# 4. Merge: Accounting + Neo4j first → add network metrics
# 5. Compute derived features (CAMEL ratios, event indicators)
```

Current exp_007 pattern (incomplete):

```python
# 1. Load accounting data ✅
# 2. Load quarterly network metrics ✅
# 3. Merge on regn/quarter ✅
# [MISSING: Neo4j population, derived features]
```

## 📋 Next Steps (Phase 2)

### Option A: Minimal Integration (Quick)

Just add CAMEL ratio computation to quarterly loader:

```python
df['camel_roa'] = df['operating_income'] / df['total_assets']
df['camel_npl_ratio'] = df['npl_amount'] / df['total_loans']
df['camel_tier1_capital_ratio'] = df['tier1_capital'] / df['total_assets']
```

**Limitations**: Still missing family/foreign metrics, proper event handling

### Option B: Full Integration (Proper)

Extend `QuarterlyWindowDataLoader` to integrate with existing pipeline:

1. Call `RollingWindowDataLoader` to get full feature set
2. Add quarterly lagged network metrics on top
3. Properly handle time-varying structure

**Advantages**: Complete feature parity with exp_006, proper Cox setup

### Option C: Hybrid Approach (Recommended)

1. Use existing `RollingWindowDataLoader` for current features + event
2. Create a **merger utility** that adds quarterly lagged network to existing data
3. Minimal code changes to proven pipeline

## 🎯 Recommended Implementation (Option C)

Create `add_quarterly_lags.py` utility:

```python
def add_quarterly_lagged_network(df_full, lag_quarters=4):
    """
    Add quarterly lagged network metrics to existing full-feature DataFrame.

    Args:
        df_full: DataFrame from RollingWindowDataLoader (has all features)
        lag_quarters: Lag specification

    Returns:
        df_full with added columns: network_*_{lag_quarters}q_lag
    """
    # Load quarterly snapshots
    # Match on regn + quarter
    # Merge lagged metrics
    pass
```

Then in `run_cox.py`:

```python
# Use existing proven loader
loader = RollingWindowDataLoader()
df = loader.load_training_data_with_rolling_windows(...)

# Add quarterly lags on top
df = add_quarterly_lagged_network(df, lag_quarters=4)

# Now have: all exp_006 features + lagged network
```

## 📊 Current Data Statistics

- **Quarterly snapshots**: 44 windows (2010Q1 - 2020Q4)
- **Observations**: 51,316 (after merge)
- **Banks**: 933 unique
- **Date range**: 2014-01-01 to 2020-12-01
- **Merge success**: 86.7%
- **Network features**: 6 (page_rank, in/out/degree, wcc, community)

## ✅ Files Created

1. `rolling_windows/output/quarterly_2010_2020/` - 44 parquet files
2. `mlflow_utils/quarterly_window_loader.py` - Standalone loader
3. `experiments/exp_007_lagged_network/run_cox.py` - Cox model runner
4. `experiments/exp_007_lagged_network/test_data_loading.py` - Validation
5. `experiments/exp_007_lagged_network/test_multicollinearity.py` - Diagnostics

## 🔬 Key Findings

1. **Efficient quarterly generation**: 12x faster than estimated (13.7 min vs 2.9 hours)
2. **Master projection approach works**: Reusing `base_temporal` highly effective
3. **High merge success**: 86.7% is excellent for temporal matching
4. **Raw accounting variables unusable**: Need ratios to avoid multicollinearity
5. **Integration pattern needed**: Can't use quarterly loader standalone

## 💡 Conclusion

**Phase 1 (Data Infrastructure)**: ✅ **COMPLETE**

- Quarterly network data generated and validated
- Loader working with good merge rates
- MLflow connected

**Phase 2 (Model Implementation)**: ⏸️ **PAUSED**

- Need proper integration with full feature set
- Recommend Option C (hybrid approach)
- Estimated time: 2-3 hours for proper integration

**Decision Point**:
Should we proceed with quick CAMEL computation (Option A) to get initial results,
or invest in proper integration (Option C) for production-ready implementation?
