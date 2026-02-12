# Temporal FCR Migration Plan: Experiments 007, 008, 011, 012, 013

**Created**: 2026-01-13  
**Status**: Planning  
**Priority**: High

---

## Executive Summary

This plan outlines the migration of five critical experiments to use **temporal, time-varying Family Connection Ratio (FCR)** data from the new rolling windows pipeline (`production_run_1990_2022_v6`). The temporal FCR combines:

1. **Ground truth observations** from Neo4j ownership data
2. **Link prediction imputed values** from the enhanced GDS pipeline (MLflow experiment: `enhanced_gds_lp_grid`)

### Current State vs Target State

| Aspect            | Current (Static)                             | Target (Temporal)                                    |
| ----------------- | -------------------------------------------- | ---------------------------------------------------- |
| **FCR Source**    | Single snapshot per 2-year window            | Biannual temporal FCR (1990-2022)                    |
| **Variability**   | 99.8% time-invariant within sample           | Fully time-varying with biannual resolution          |
| **Coverage**      | Ground truth only                            | Ground truth + imputed (link prediction)             |
| **Data Location** | `rolling_windows/output/quarterly_2010_2020` | `rolling_windows/output/production_run_1990_2022_v6` |

### Migration Scope

**Experiments to Migrate** (in order of complexity):

1. **exp_007_lagged_network** - Lagged network effects (2014-2020, originally quarterly)
2. **exp_008_family_community** - Family-community interaction with stratification
3. **exp_011_subperiod_analysis** - Structural breaks across three periods
4. **exp_012_governor_regimes** - Governor × ownership interactions (2004-2020)
5. **exp_013_reverse_causality** - Biennial cross-sections testing FCR growth

---

## 1. Temporal FCR Data Specification

### 1.1 Data Location

**Base Directory**: `data_processing/rolling_windows/output/production_run_1990_2022_v6/`

**Structure**:

```
production_run_1990_2022_v6/
├── nodes/
│   ├── node_features_rw_1990_1991.parquet
│   ├── node_features_rw_1992_1993.parquet
│   ├── ...
│   └── node_features_rw_2022_2023.parquet  # 17 files total
├── edges/
│   ├── edge_list_rw_1990_1991.parquet
│   └── ...
└── manifest/  # Gitignored metadata
```

### 1.2 Node Features Schema

**Key Columns** (per `node_features_rw_YYYY_YYYY.parquet`):

| Column              | Type  | Description                               |
| ------------------- | ----- | ----------------------------------------- |
| `nodeId`            | int   | GDS internal node ID                      |
| `entity_id`         | str   | Neo4j Bank ID (regn_cbr)                  |
| `window_start_ms`   | int   | Window start (milliseconds)               |
| `window_end_ms`     | int   | Window end (milliseconds)                 |
| `family_degree`     | float | **Temporal FCR** (ground truth + imputed) |
| `betweenness`       | float | Betweenness centrality                    |
| `closeness`         | float | Closeness centrality                      |
| `eigenvector`       | float | Eigenvector centrality                    |
| `community_louvain` | array | Louvain community (hierarchical)          |
| `page_rank`         | float | PageRank                                  |
| `in_degree`         | int   | In-degree                                 |
| `out_degree`        | int   | Out-degree                                |
| `is_dead`           | bool  | Dead bank indicator                       |
| `fastrp_embedding`  | array | FastRP embedding (for link prediction)    |
| `bank_feats`        | array | Bank-specific features                    |
| `network_feats`     | array | Network-derived features                  |

**Critical Change**: `family_degree` is now **`family_degree`** (not `family_connection_ratio`) and includes:

- Ground truth from Neo4j ownership edges
- Imputed values from link prediction model

### 1.3 Temporal Coverage

**Windows**: 2-year rolling windows from 1990-2022

| Window    | File                                 | Observations (approx) |
| --------- | ------------------------------------ | --------------------- |
| 1990-1991 | `node_features_rw_1990_1991.parquet` | 3.8 MB                |
| 1992-1993 | `node_features_rw_1992_1993.parquet` | 4.7 MB                |
| ...       | ...                                  | ...                   |
| 2020-2021 | `node_features_rw_2020_2021.parquet` | 13.6 MB               |
| 2022-2023 | `node_features_rw_2022_2023.parquet` | 12.8 MB               |

**Total**: 17 windows covering 33 years

---

## 2. Experiment-Specific Migration Plans

### 2.1 exp_007_lagged_network (Simplest)

**Current Implementation**:

- Loader: `QuarterlyWindowDataLoader` (quarterly snapshots 2010-2020)
- FCR source: `family_rho_F` from Neo4j (static)
- Period: 2014-2020
- Models: M2 (simple lagged network)

**Migration Steps**:

#### Step 1: Copy Experiment Directory

```bash
cp -r experiments/exp_007_lagged_network experiments/exp_007_temporal_fcr
```

#### Step 2: Create New Data Loader

**File**: `mlflow_utils/temporal_fcr_loader.py`

**Purpose**: Load temporal FCR data from `production_run_1990_2022_v6`

**Key Functions**:

```python
class TemporalFCRLoader:
    def __init__(self, base_dir='data_processing/rolling_windows/output/production_run_1990_2022_v6'):
        self.nodes_dir = Path(base_dir) / 'nodes'
        self.edges_dir = Path(base_dir) / 'edges'

    def load_with_lags(self, lag_quarters=4, start_year=2014, end_year=2020):
        """
        Load temporal FCR with biannual lags.

        Returns DataFrame with columns:
        - regn: Bank ID
        - DT: Date
        - family_degree: Temporal FCR (ground truth + imputed)
        - family_degree_4q_lag: Lagged FCR
        - rw_page_rank_4q_lag: Lagged PageRank
        - rw_out_degree_4q_lag: Lagged out-degree
        - camel_roa, camel_npl_ratio, camel_tier1_capital_ratio
        - event: Event indicator
        - is_dead: Death indicator
        """
        pass
```

**Logic**:

1. Read all parquet files in date range
2. Convert `window_start_ms`, `window_end_ms` to datetime
3. Map `entity_id` → `regn`
4. Rename `family_degree` → `family_connection_ratio_temporal`
5. Create lagged versions using biannual offset
6. Merge with CAMEL ratios from accounting data (existing Neo4j query)
7. Create event indicators (last observation only for dead banks)

#### Step 3: Update `run_cox.py`

**Changes**:

1. Import: `from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader`
2. Replace loader instantiation:

   ```python
   # OLD
   loader = QuarterlyWindowDataLoader()

   # NEW
   loader = TemporalFCRLoader()
   ```

3. Update feature names in `prepare_cox_data`:
   ```python
   family_foreign_features = [
       'family_connection_ratio_temporal',  # NEW
       'foreign_FEC_d'
   ]
   ```

#### Step 4: Update Config (if exists)

No config file in exp_007, so skip.

#### Step 5: Verification

**Run**:

```bash
cd experiments/exp_007_temporal_fcr
uv run python run_cox.py
```

**Expected**:

- New MLflow experiment: `exp_007_temporal_fcr`
- C-index similar to original (~0.728)
- FCR coefficient potentially different (now time-varying)
- Compare with original `exp_007_lagged_network` run

**Diagnostic Checks**:

```python
# In run_cox.py, add before fitting:
print(f"FCR variance (temporal): {df['family_connection_ratio_temporal'].var():.4f}")
print(f"FCR % time-varying: {(df.groupby('regn')['family_connection_ratio_temporal'].nunique() > 1).mean():.1%}")
```

---

### 2.2 exp_008_family_community (Medium Complexity)

**Current Implementation**:

- Uses `QuarterlyWindowDataLoader` with `family_connection_ratio` from Neo4j
- 3 models: M1 (baseline), M2 (community stratified), M3 (FCR focus)
- Community processing: Louvain collapse + temporal aggregation
- Period: 2014-2020

**Migration Steps**:

#### Step 1: Copy Experiment

```bash
cp -r experiments/exp_008_family_community experiments/exp_008_temporal_fcr
```

#### Step 2: Update Data Loader

**In `run_cox.py`**:

```python
# Line ~24 (import)
from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader

# Line ~466 (load data)
loader = TemporalFCRLoader()  # Changed
df = loader.load_with_lags(
    lag_quarters=data_config['lag_quarters'],
    start_year=data_config['start_year'],
    end_year=data_config['end_year']
)
```

#### Step 3: Update Community Processing

**Challenge**: Temporal FCR data already has `community_louvain` from rolling windows pipeline

**Solution**: Reuse existing community processing functions, but extract from temporal data:

```python
def collapse_small_communities(df, community_col='community_louvain', min_size=5):
    """
    Already implemented in exp_008/run_cox.py.
    No changes needed - works with array-valued Louvain from temporal data.
    """
    pass
```

**Verify** `community_louvain` column exists in temporal data (it does, per schema above).

#### Step 4: Update Feature Names

**In `config_cox.yaml`**:

```yaml
ownership_features:
  - family_connection_ratio_temporal  # Changed from family_connection_ratio
  - family_ownership_pct
  - foreign_ownership_total_pct
  - state_ownership_pct
```

**In `run_cox.py` where features are referenced**:

- Search for `family_connection_ratio`
- Replace with `family_connection_ratio_temporal`

#### Step 5: Verification

**Key Comparison**:

| Metric                 | Original exp_008 | Temporal exp_008 | Change            |
| ---------------------- | ---------------- | ---------------- | ----------------- |
| FCR HR (M1)            | 0.9880\*\*\*     | ?                | Expected: similar |
| FCR HR (M2 stratified) | 0.9877\*\*\*     | ?                | Expected: similar |
| C-index (M2)           | 0.6481           | ?                | Expected: ±0.01   |
| FCR time-varying %     | 0.2%             | ~20-40%?         | Major increase    |

**Diagnostic**:

```python
# Add to run_cox.py
print(f"\n{'='*70}")
print(f"TEMPORAL FCR DIAGNOSTICS")
print(f"{'='*70}")
fcr_col = 'family_connection_ratio_temporal'
print(f"  Mean: {df[fcr_col].mean():.3f}")
print(f"  Std: {df[fcr_col].std():.3f}")
print(f"  Banks with changing FCR: {(df.groupby('regn')[fcr_col].nunique() > 1).sum()}")
print(f"  % time-varying: {(df.groupby('regn')[fcr_col].nunique() > 1).mean():.1%}")
```

---

### 2.3 exp_011_subperiod_analysis (High Complexity)

**Current Implementation**:

- 3 config files for 3 periods: `config_2004_2007.yaml`, `config_2007_2013.yaml`, `config_2013_2020.yaml`
- Runner: `run_subperiods.py` iterates over configs
- Each config specifies crisis periods dynamically
- Uses `QuarterlyWindowDataLoader`

**Migration Steps**:

#### Step 1: Copy Experiment

```bash
cp -r experiments/exp_011_subperiod_analysis experiments/exp_011_temporal_fcr
```

#### Step 2: Update Loader in `run_subperiods.py`

**Line ~24** (imports):

```python
from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader
```

**Line ~327** (in `run_subperiod` function):

```python
# OLD
loader = QuarterlyWindowDataLoader()

# NEW
loader = TemporalFCRLoader()
```

#### Step 3: Update All 3 Config Files

**Pattern** (apply to all):

**Before**:

```yaml
ownership_features:
  - family_connection_ratio
  - family_ownership_pct
  - state_ownership_pct
  - foreign_ownership_total_pct
```

**After**:

```yaml
ownership_features:
  - family_connection_ratio_temporal  # <-- Changed
  - family_ownership_pct
  - state_ownership_pct
  - foreign_ownership_total_pct
```

**Files to modify**:

1. `config_2004_2007.yaml`
2. `config_2007_2013.yaml`
3. `config_2013_2020.yaml`

#### Step 4: Extended Period Coverage

**Opportunity**: Temporal data starts 1990, but configs start 2004

**Decision**: Keep 2004 start for comparability with original exp_011, but note that 1990-2003 is now available for future extensions

#### Step 5: Verification

**Run**:

```bash
cd experiments/exp_011_temporal_fcr
uv run python run_subperiods.py
```

**Expected Output**:

- 3 subperiods run successfully
- Artifacts in `output/2004_2007/`, `output/2007_2013/`, `output/2013_2020/`
- Key comparison: FCR coefficient evolution

| Period    | Original FCR HR | Temporal FCR HR | Interpretation                                         |
| --------- | --------------- | --------------- | ------------------------------------------------------ |
| 2004-2007 | 0.982\*\*\*     | ?               | Expect similar if FCR stable early                     |
| 2007-2013 | 0.984\*\*\*     | ?               | Expect similar                                         |
| 2013-2020 | 0.989\*\*\*     | ?               | Expect **more variation** if cleanup drove FCR changes |

**Diagnostic Focus**: Do temporal FCR changes explain coefficient weakening?

**Add to `run_subperiods.py`** (in `prepare_cox_data`):

```python
# After line ~129
fcr_changes = df.groupby('regn')['family_connection_ratio_temporal'].nunique()
print(f"\n  FCR Time-Varying Banks: {(fcr_changes > 1).sum()} ({100*(fcr_changes > 1).sum()/len(fcr_changes):.1f}%)")
```

---

### 2.4 exp_012_governor_regimes (High Complexity)

**Current Implementation**:

- Pooled model 2004-2020
- Governor dummy (`governor_nabiullina`) + crisis dummies
- Ownership × governor interactions
- Community stratification
- 6 models (M1-M6)

**Migration Steps**:

#### Step 1: Copy Experiment

```bash
cp -r experiments/exp_012_governor_regimes experiments/exp_012_temporal_fcr
```

#### Step 2: Update Loader

**In `run_cox.py`** (which is actually exp_009 code based on comments):

**Line ~24**:

```python
from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader
```

**Line ~471**:

```python
# OLD
loader = QuarterlyWindowDataLoader(quarterly_dir=network_dir)

# NEW
loader = TemporalFCRLoader()  # Uses default base_dir
```

**Remove `network_dir` config** (no longer needed, hardcoded in `TemporalFCRLoader`).

#### Step 3: Update Config

**File**: `config_cox.yaml`

**Change**:

```yaml
ownership_features:
  - family_connection_ratio_temporal  # <-- Changed
  - family_ownership_pct
  - state_ownership_pct
  - foreign_ownership_total_pct
```

#### Step 4: Critical Test: Does Reverse Causality Change?

**Hypothesis** (from exp_013): Reverse causality operates 2014-2018

**Question**: Does temporal FCR (with ∆FCR visible) change the family × governor interaction?

**Original exp_012 finding**: family × governor = -0.006+ (HR=0.994, p=0.063)

**Expected with temporal FCR**:

- If FCR changes drive interaction: Coefficient **weakens** (less significant)
- If selection drives interaction: Coefficient **stable** (FCR changes orthogonal)

**Add diagnostic**:

```python
# In run_cox.py, before fitting governor models
fcr_col = 'family_connection_ratio_temporal'
nabiullina_fcr = df[df['governor_nabiullina']==1].groupby('regn')[fcr_col].mean().mean()
ignatyev_fcr = df[df['governor_nabiullina']==0].groupby('regn')[fcr_col].mean().mean()
print(f"\nFCR by regime:")
print(f"  Ignatyev: {ignatyev_fcr:.3f}")
print(f"  Nabiullina: {nabiullina_fcr:.3f}")
print(f"  Ratio: {nabiullina_fcr/ignatyev_fcr:.2f}")
```

#### Step 5: Verification

**Key Metrics**:

| Model              | Original Interaction HR | Temporal Interaction HR | Inference                   |
| ------------------ | ----------------------- | ----------------------- | --------------------------- |
| M3 (Family × Gov)  | 0.994+ (p=0.063)        | ?                       | Test if FCR dynamics matter |
| M4 (State × Gov)   | 0.996 (p=0.256)         | ?                       | Expect similar              |
| M5 (Foreign × Gov) | 1.004 (p=0.741)         | ?                       | Expect similar              |

---

### 2.5 exp_013_reverse_causality (Highest Complexity)

**Current Implementation**:

- OLS regressions (not Cox)
- Biennial cross-sections: 2012, 2014, 2016, 2018, 2020
- Outcome: `family_connection_ratio` (static within-bank)
- Predictor: `survived_to_cutoff` (binary)
- **Critical**: Current FCR 99.8% time-invariant → cannot test accumulation hypothesis

**Migration Impact**: **MOST SIGNIFICANT**

#### Why This Matters Most

**Original exp_013 caveat** (from writeup line 427):

> "**Static FCR (99.8% time-invariant)**: Current findings show survivors have higher FCR but **cannot definitively prove** they actively build connections."

**Temporal FCR enables**:

1. **∆FCR regression**: Test whether survival → FCR growth
2. **Distinguish** selection (pre-existing high FCR) vs accumulation (FCR increases post-survival)
3. **Resolve ambiguity** in original exp_013

#### Step 1: Copy Experiment

```bash
cp -r experiments/exp_013_reverse_causality experiments/exp_013_temporal_fcr
```

#### Step 2: Update Loader

**In `run_regression.py`**:

**Line ~19**:

```python
from mlflow_utils.temporal_fcr_loader import TemporalFCRLoader
```

**Line ~150**:

```python
# OLD
loader = QuarterlyWindowDataLoader()

# NEW
loader = TemporalFCRLoader()
```

#### Step 3: Update Config

**File**: `config_ols.yaml`

**Models section**: No change needed (predictors don't include FCR name directly)

**But note**: Outcome variable is currently `family_connection_ratio`

**Change in `run_regression.py` line ~69**:

```python
# OLD
y = df_clean['family_connection_ratio']

# NEW
y = df_clean['family_connection_ratio_temporal']
```

#### Step 4: **NEW MODELS**: ∆FCR Regressions

**Add to `run_regression.py`** (new function):

```python
def run_delta_fcr_models(df, config):
    """
    Test whether survival predicts FCR GROWTH (∆FCR).

    This is the CRITICAL extension from original exp_013.
    """
    results_list = []

    for model_key, model_cfg in config["experiment"]["models"].items():
        if model_cfg['type'] != 'ols':
            continue

        year = model_cfg['data_year']
        quarter = model_cfg['data_quarter']
        cutoff_year = model_cfg['cutoff_year']

        # Filter to year/quarter
        df_year = create_survival_indicators_for_cutoff(df.copy(), cutoff_year)
        df_base = df_year[
            (df_year['date'].dt.year == year) &
            (df_year['date'].dt.quarter == quarter)
        ].copy()

        # Compute ∆FCR: FCR at cutoff_year - FCR at year
        # Need to get FCR at cutoff_year for same banks
        df_future = df_year[
            (df_year['date'].dt.year == cutoff_year) &
            (df_year['date'].dt.quarter == 4)
        ][['regn', 'family_connection_ratio_temporal']].rename(
            columns={'family_connection_ratio_temporal': 'fcr_future'}
        )

        df_merged = df_base.merge(df_future, on='regn', how='inner')
        df_merged['delta_fcr'] = df_merged['fcr_future'] - df_merged['family_connection_ratio_temporal']

        print(f"\n{'='*70}")
        print(f"∆FCR Regression: {year}Q{quarter} → {cutoff_year}Q4")
        print(f"{'='*70}")
        print(f"  Observations: {len(df_merged)}")
        print(f"  Mean ∆FCR: {df_merged['delta_fcr'].mean():.4f}")
        print(f"  Survivors with ∆FCR>0: {(df_merged[df_merged['survived_to_cutoff']==1]['delta_fcr'] > 0).sum()}")

        # Regression: ∆FCR ~ survived + controls
        predictors = model_cfg['predictors']
        available_preds = [p for p in predictors if p in df_merged.columns]
        df_clean = df_merged[['delta_fcr'] + available_preds].dropna()

        y = df_clean['delta_fcr']
        X = sm.add_constant(df_clean[available_preds])

        with mlflow.start_run(run_name=f"DeltaFCR_{year}"):
            model = OLS(y, X).fit(cov_type='HC3')

            mlflow.log_param("model_type", "delta_fcr")
            mlflow.log_param("year", year)
            mlflow.log_param("cutoff_year", cutoff_year)
            mlflow.log_param("n_obs", int(model.nobs))
            mlflow.log_metric("r_squared", model.rsquared)

            if 'survived_to_cutoff' in model.params.index:
                coef = model.params['survived_to_cutoff']
                pval = model.pvalues['survived_to_cutoff']

                mlflow.log_metric("survived_coef_delta", coef)
                mlflow.log_metric("survived_pval_delta", pval)

                results_list.append({
                    'year': year,
                    'cutoff': cutoff_year,
                    'delta_fcr_coef': coef,
                    'delta_fcr_pval': pval,
                    'r_squared': model.rsquared
                })

                print(f"  survived_to_cutoff → ∆FCR: {coef:.4f} (p={pval:.4f})")

            # Save
            with open(f"delta_fcr_summary_{year}.txt", "w") as f:
                f.write(str(model.summary()))
            mlflow.log_artifact(f"delta_fcr_summary_{year}.txt")

    return pd.DataFrame(results_list)
```

**Call in `main()`**:

```python
# After line ~172
# Run biennial models
results_df = run_biennial_models(df, config)

# NEW: Run ∆FCR models
print("\n4. Running ∆FCR accumulation tests...")
delta_results_df = run_delta_fcr_models(df, config)

# Save
delta_results_df.to_csv("delta_fcr_results.csv", index=False)
print(f"✅ Saved delta_fcr_results.csv")
```

#### Step 5: Interpretation Framework

**Original exp_013** (static FCR):

- survived_to_2016 → FCR = +0.248\*\*\* (p<0.001)
- **Ambiguous**: Selection or accumulation?

**New with ∆FCR**:

**Case 1**: survived_to_2016 → ∆FCR = 0.00 (n.s.)

- **Interpretation**: Pure selection (survivors already had high FCR, didn't build more)
- **Implication**: exp_007-012 coefficients are valid (no active reverse causality)

**Case 2**: survived_to_2016 → ∆FCR = +0.15\*\*\* (p<0.001)

- **Interpretation**: Active accumulation (survivors build connections)
- **Implication**: exp_007-012 coefficients biased upward by **both** selection AND accumulation

**Case 3**: survived_to_2016 → ∆FCR = -0.05\*\* (p<0.01)

- **Interpretation**: Failed banks had rising FCR (last-ditch connection-building)
- **Implication**: Reverse causality **negative** → exp_007-012 underestimate true protection

#### Step 6: Verification

**Key Outputs**:

| Year | Original FCR Coef | Temporal FCR Coef | ∆FCR Coef | Interpretation    |
| ---- | ----------------- | ----------------- | --------- | ----------------- |
| 2012 | -0.143 (n.s.)     | ?                 | ?         | Baseline          |
| 2014 | +0.157\*\*        | ?                 | ?         | Cleanup emergence |
| 2016 | +0.248\*\*\*      | ?                 | ?         | **Critical test** |
| 2018 | +0.195\*\*        | ?                 | ?         | Post-cleanup      |
| 2020 | +0.038 (n.s.)     | ?                 | ?         | Normalization     |

---

## 3. Cross-Cutting Migration Tasks

### 3.1 Create Unified Temporal FCR Loader

**File**: `mlflow_utils/temporal_fcr_loader.py`

**Requirements**:

1. Read from `production_run_1990_2022_v6`
2. Handle 2-year windows (biannual observations or optional pseudo-quarterly expansion)
3. Merge with CAMEL ratios (from Neo4j accounting query)
4. Create lagged features (e.g., 2-period lag = 4 years)
5. Create event indicators (Cox TV pattern)
6. Match interface of existing `QuarterlyWindowDataLoader` (for compatibility)

**Implementation Steps**:

#### Step 3.1.1: Core Loading Logic

```python
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

class TemporalFCRLoader:
    def __init__(self, base_dir='data_processing/rolling_windows/output/production_run_1990_2022_v6'):
        self.base_dir = Path(base_dir)
        self.nodes_dir = self.base_dir / 'nodes'
        self.edges_dir = self.base_dir / 'edges'

    def load_with_lags(self, lag_periods=2, start_year=2014, end_year=2020):
        """Load temporal FCR with biannual lags (lag_periods in 2-year increments)."""
        # 1. Load all node files in range
        dfs = []
        for file in sorted(self.nodes_dir.glob('node_features_rw_*.parquet')):
            df_window = pd.read_parquet(file)
            # Convert windows to datetime
            df_window['window_start'] = pd.to_datetime(df_window['window_start_ms'], unit='ms')
            df_window['window_end'] = pd.to_datetime(df_window['window_end_ms'], unit='ms')
            # Filter by year range
            if df_window['window_start'].dt.year.max() < start_year:
                continue
            if df_window['window_end'].dt.year.min() > end_year:
                continue
            dfs.append(df_window)

        df_all = pd.concat(dfs, ignore_index=True)

        # 2. Assign observation dates (window midpoint approach)
        df_biannual = self._assign_window_midpoints(df_all)

        # 3. Rename columns
        df_biannual = df_biannual.rename(columns={
            'entity_id': 'regn',
            'fcr_temporal': 'family_connection_ratio_temporal'
        })

        # 4. Create lagged features (lag in 2-year periods)
        df_lagged = self._create_lags(df_biannual, lag_periods)

        # 5. Merge CAMEL
        df_merged = self._merge_camel(df_lagged)

        # 6. Create event indicators
        df_final = self._create_events(df_merged)

        return df_final
```

#### Step 3.1.2: Biannual Window Handling

**Reality**: Windows are 2-year (biannual), NOT quarterly

**Recommended Approach: Window Midpoint**:

```python
def _assign_window_midpoints(self, df):
    """
    Assign window midpoint as the observation date.
    Each 2-year window = single biannual observation.
    """
    df['window_start'] = pd.to_datetime(df['window_start_ms'], unit='ms')
    df['window_end'] = pd.to_datetime(df['window_end_ms'], unit='ms')

    # Midpoint as observation date
    df['DT'] = df['window_start'] + (df['window_end'] - df['window_start']) / 2

    return df
```

**Alternative (ONLY if experiments require pseudo-quarterly)**:

```python
def _expand_to_pseudo_quarterly(self, df):
    """
    Forward-fill each 2-year window into 8 quarterly observations.
    WARNING: Artificially inflates temporal resolution.
    """
    records = []
    for _, row in df.iterrows():
        start = row['window_start']
        for quarter_offset in range(8):  # 8 quarters in 2 years
            record = row.to_dict()
            record['DT'] = start + pd.DateOffset(months=quarter_offset * 3)
            records.append(record)
    return pd.DataFrame(records)
```

#### Step 3.1.3: Merge with CAMEL Ratios

```python
def _merge_camel(self, df):
    """Merge CAMEL ratios from Neo4j accounting data using gds_id."""
    # Query Neo4j for CAMEL data (reuse existing query logic)
    # Use gds_id for robust merging (see temporal_fcr_addendum.md)
    from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
    loader_existing = QuarterlyWindowDataLoader()
    # ... adapt CAMEL loading logic for gds_id merge
    pass
```

### 3.2 Validation Suite

**File**: `tests/test_temporal_fcr_migration.py`

**Purpose**: Ensure temporal data loads correctly and matches expected schema

```python
def test_temporal_fcr_loader():
    """Test TemporalFCRLoader basic functionality."""
    loader = TemporalFCRLoader()
    df = loader.load_with_lags(lag_quarters=4, start_year= 2014, end_year=2020)

    # Schema checks
    assert 'family_connection_ratio_temporal' in df.columns
    assert 'regn' in df.columns
    assert 'DT' in df.columns

    # Time-varying check
    fcr_varying_pct = (df.groupby('regn')['family_connection_ratio_temporal'].nunique() > 1).mean()
    assert fcr_varying_pct > 0.01, f"Expected >1% time-varying FCR, got {fcr_varying_pct:.1%}"

    print(f"✅ Temporal FCR Loader validated")
    print(f"   FCR time-varying: {fcr_varying_pct:.1%}")
```

---

## 4. Execution Plan & Timeline

### Phase 1: Infrastructure (Week 1)

**Tasks**:

1. Create `mlflow_utils/temporal_fcr_loader.py`
   - Core loading logic
   - Window midpoint assignment (biannual observations)
   - CAMEL merge
   - Event indicator creation
2. Create validation test suite
3. Document temporal FCR schema

**Deliverables**:

- Working `TemporalFCRLoader` class
- Passing unit tests
- Documentation in `memory-bank/temporal_fcr_loader.md`

### Phase 2: Simple Migrations (Week 2)

**Order**:

1. **exp_007** (1 day) - Simplest, single model
2. **exp_008** (2 days) - 3 models, community stratification
3. Verify both experiments produce similar results to originals

**Success Criteria**:

- MLflow experiments created
- C-indices within ±0.02 of originals
- FCR coefficients directionally consistent

### Phase 3: Complex Migrations (Week 3)

**Order**:

1. **exp_011** (2 days) - 3 subperiods, multi-config
2. **exp_012** (2 days) - Governor interactions, 6 models
3. Verify cross-experiment consistency

**Success Criteria**:

- All models converge
- Governor × family interaction tested with temporal FCR
- Subperiod coefficient evolution compared

### Phase 4: Critical Extension (Week 4)

**Focus**: **exp_013** with ∆FCR regressions

**Tasks**:

1. Migrate base biennial models (1 day)
2. Implement ∆FCR regression framework (2 days)
3. Run full analysis (1 day)
4. Write up findings (1 day)

**Success Criteria**:

- ∆FCR results definitively answer: selection vs accumulation
- Update exp_013 writeup with new findings
- Revise exp_007-012 interpretations based on ∆FCR evidence

### Phase 5: Documentation & Synthesis (Week 5)

**Tasks**:

1. Update all 5 experiment writeups
2. Create comparative summary document
3. Update MLflow experiment descriptions
4. Archive old experiments (rename with `_static_fcr` suffix)

---

## 5. Risk Assessment & Mitigation

### Risk 1: Temporal FCR Schema Mismatch

**Problem**: Column names or types differ from expected

**Likelihood**: Medium  
**Impact**: High (blocks all migrations)

**Mitigation**:

- Create `TemporalFCRLoader` with extensive schema validation
- Test on single window file first
- Add fallback logic for missing columns

### Risk 2: Biannual to Pseudo-Quarterly Expansion Issues

**Problem**: If using pseudo-quarterly expansion, may create interpolation artifacts

**Likelihood**: Medium  
**Impact**: Medium (biased coefficients)

**Mitigation**:

- **Prefer window midpoint approach** (no interpolation, no artifacts)
- If pseudo-quarterly expansion needed, compare against original 2-year windows
- Document temporal resolution approach clearly in experiment writeups

### Risk 3: FCR Too Time-Varying (Multicollinearity)

**Problem**: Temporal FCR changes rapidly, causing instability

**Likelihood**: Low (FCR structural, slow-changing)  
**Impact**: Medium (convergence issues)

**Mitigation**:

- Add FCR smoothing option (moving average)
- Use penalised regression (already in specs)
- Compare LevelFCR vs ∆FCR models

### Risk 4: CAMEL Merge Failures

**Problem**: Temporal data missing CAMEL ratios

**Likelihood**: Low (separate data source)  
**Impact**: High (cannot run models)

**Mitigation**:

- Reuse existing Neo4j CAMEL query
- Add merge diagnostics (% merged)
- Fallback: Use last-observation-carried-forward

### Risk 5: ∆FCR Null Results (exp_013)

**Problem**: ∆FCR regressions all non-significant

**Likelihood**: Medium (possible if selection dominates)  
**Impact**: Low (still scientifically valuable)

**Mitigation**:

- Not a bug, a finding
- Document as evidence for selection hypothesis
- Run sensitivity analysis (different cutoff windows)

---

## 6. Success Metrics

### Quantitative

1. **All 5 experiments migrate successfully** (100%)
2. **C-indices within ±0.03 of originals** (acceptable given FCR variability)
3. **FCR time-varying % > 10%** (vs 0.2% in static)
4. **∆FCR regressions run for all 5 biennial periods** (exp_013)

### Qualitative

1. **Scientific clarity**: Resolve selection vs accumulation ambiguity (exp_013)
2. **Coefficient stability**: FCR effects directionally consistent across temporal/static
3. **Cross-experiment coherence**: Temporal results integrate with existing findings
4. **Documentation**: All experiments have updated writeups citing temporal FCR

---

## 7. Post-Migration Analysis

### Comparative Summary Document

**File**: `memory-bank/writeups/temporal_fcr_comparison.md`

**Contents**:

1. **Static vs Temporal FCR Table**

| Experiment           | Static FCR HR | Temporal FCR HR | ∆   | Interpretation |
| -------------------- | ------------- | --------------- | --- | -------------- |
| exp_007              | 0.988\*\*\*   | ?               | ?   | ?              |
| exp_008 M2           | 0.988\*\*\*   | ?               | ?   | ?              |
| exp_011 (2013-2020)  | 0.989\*\*\*   | ?               | ?   | ?              |
| exp_012 (Nabiullina) | 0.984+        | ?               | ?   | ?              |
| exp_013 (2016)       | +0.248\*\*\*  | ?               | ?   | ?              |

2. **∆FCR Evidence Summary** (exp_013)

| Year | ∆FCR Coef | p-value | Conclusion        |
| ---- | --------- | ------- | ----------------- |
| 2012 | ?         | ?       | ?                 |
| 2014 | ?         | ?       | ?                 |
| 2016 | ?         | ?       | **Critical test** |
| 2018 | ?         | ?       | ?                 |
| 2020 | ?         | ?       | ?                 |

3. **Revised Interpretations**
   - If ∆FCR null → Selection dominates, Cox estimates valid
   - If ∆FCR significant → Accumulation exists, Cox estimates biased

---

## 8. Long-Term Extensions

### Extension 1: Full 1990-2022 Coverage

**Current**: Experiments use 2004-2020 (comparability)  
**Target**: Extend to 1990-2022 (full temporal data)

**Benefits**:

- Test early transition period (1990s)
- Longer pre-crisis baseline
- More statistical power

### Extension 2: Higher Frequency Reverse Causality Tests

**Current**: exp_013 uses biennial (2012, 2014, ...) - perfectly aligned with biannual data  
**Target**: Test at biannual frequency (2013, 2015, 2017, ...) or attempt pseudo-quarterly if expansion implemented

**Benefits**:

- Test at full available temporal resolution (biannual)
- More data points than current biennial (2012, 2014, 2016, 2018, 2020)
- Note: Resolution limited by underlying biannual data structure

### Extension 3: Link Prediction Quality Analysis

**Question**: Do imputed FCR values (from link prediction) behave differently from ground truth?

**Approach**:

```python
# Separate FCR into components
df['fcr_ground_truth'] = ...  # From Neo4j ownership
df['fcr_imputed'] = ...  # From link prediction
df['fcr_total'] = df['fcr_ground_truth'] + df['fcr_imputed']

# Run models separately
model_ground_truth = fit_cox(df, features=['fcr_ground_truth'])
model_imputed = fit_cox(df, features=['fcr_imputed'])
model_total = fit_cox(df, features=['fcr_total'])
```

**Hypothesis**: Ground truth has stronger effect than imputed

---

## 9. Appendices

### Appendix A: File Checklist

**New Files**:

- [ ] `mlflow_utils/temporal_fcr_loader.py`
- [ ] `tests/test_temporal_fcr_migration.py`
- [ ] `memory-bank/experiment_plans/temporal_fcr_redo_exp.md` (this file)
- [ ] `memory-bank/writeups/temporal_fcr_comparison.md` (post-migration)

**Modified Experiments**:

- [ ] `experiments/exp_007_temporal_fcr/run_cox.py`
- [ ] `experiments/exp_008_temporal_fcr/run_cox.py`
- [ ] `experiments/exp_008_temporal_fcr/config_cox.yaml`
- [ ] `experiments/exp_011_temporal_fcr/run_subperiods.py`
- [ ] `experiments/exp_011_temporal_fcr/config_2004_2007.yaml`
- [ ] `experiments/exp_011_temporal_fcr/config_2007_2013.yaml`
- [ ] `experiments/exp_011_temporal_fcr/config_2013_2020.yaml`
- [ ] `experiments/exp_012_temporal_fcr/run_cox.py`
- [ ] `experiments/exp_012_temporal_fcr/config_cox.yaml`
- [ ] `experiments/exp_013_temporal_fcr/run_regression.py`
- [ ] `experiments/exp_013_temporal_fcr/config_ols.yaml`

### Appendix B: Key Questions to Answer

1. **Does temporal FCR change coefficient magnitudes?** (exp_007, 008, 011, 012)
2. **Does temporal FCR change governor × family interaction?** (exp_012)
3. **Does ∆FCR resolve selection vs accumulation?** (exp_013) - **CRITICAL**
4. **What % of FCR is imputed vs ground truth?** (all)
5. **Does FCR time-variation explain coefficient weakening over time?** (exp_011)

### Appendix C: Original vs Temporal Feature Mapping

| Original Feature          | Temporal Feature                   | Source                   |
| ------------------------- | ---------------------------------- | ------------------------ |
| `family_rho_F`            | `family_connection_ratio_temporal` | Rolling windows / GDS LP |
| `family_connection_ratio` | `family_connection_ratio_temporal` | Rolling windows / GDS LP |
| `rw_page_rank`            | `page_rank`                        | GDS PageRank             |
| `rw_out_degree`           | `out_degree`                       | GDS Degree               |
| `rw_community_louvain`    | `community_louvain`                | GDS Louvain              |

---

**Plan Status**: Draft  
**Next Step**: Review with user, then begin Phase 1 (Infrastructure)  
**Estimated Total Effort**: 4-5 weeks  
**Critical Path**: TemporalFCRLoader → exp_013 ∆FCR analysis
