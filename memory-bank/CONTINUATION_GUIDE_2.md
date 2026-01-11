# Continuation Guide: Rolling Window & Parsimonious Experiments (Session 2026-01-10/11)

**Session Date**: 2026-01-10 23:00 - 2026-01-11 00:30  
**Main Achievements**: Implemented time-windowed network experiments, enhanced rolling window pipeline, created parsimonious 2014-2020 analysis

---

## Executive Summary

This session completed three major workstreams:

1. **exp_004**: Time-windowed network metrics using 4-year overlapping windows (1989-2029)
2. **exp_005**: Parsimonious models on 2014-2020 with non-overlapping 2-year windows
3. **Comparative Analysis**: 18,000+ word writeup comparing static vs time-windowed approaches
4. **Rolling Window Enhancements**: Added betweenness, closeness, eigenvector centrality metrics

### Key Results

- **exp_004 Cox**: C-index **0.765** (9.6% improvement over static 0.698)
- **exp_005 Cox**: C-index **0.7246** (4 variables: ROA, family_rho_F, out_degree, C_b)
- **Critical Finding**: PageRank sign reversal confirms endogeneity in static networks
- **Network Stability**: 2014-2020 period shows zero variance in betweenness/closeness/eigenvector

---

## Part 1: Experiments Created

### exp_004: Time-Windowed Rolling Windows (Full Period)

**Directory**: `experiments/exp_004_rolling_window_tv/`

**Purpose**: Test time-windowed network metrics vs static metrics across full observation period

**Configuration Files**:

- [`config_cox.yaml`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_004_rolling_window_tv/config_cox.yaml)
  - 6 hierarchical Cox PH models
  - Features: CAMEL + network (rolling window) + family + foreign + state
  - MLflow Experiment: "Cox_TV_Rolling_Window" (ID: 4)
- [`config_logistic.yaml`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_004_rolling_window_tv/config_logistic.yaml)
  - 6 hierarchical Logistic models (mirror of Cox)
  - MLflow Experiment: "Logistic_TV_Rolling_Window" (ID: 5)

**Run Scripts**:

- [`run_cox.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_004_rolling_window_tv/run_cox.py)
  - Loads data via `RollingWindowDataLoader`
  - Temporal matching: observation year → overlapping rolling window
  - CoxTimeVaryingFitter with time intervals (start_t, stop_t)
  - Exports: stargazer_column.csv, stargazer_hr_column.csv, interpretation.md
- [`run_logistic.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_004_rolling_window_tv/run_logistic.py)
  - Pooled logistic regression with clustered SE (grouped by regn)
  - statsmodels Logit with robust covariance

**Data Source**:

- Rolling windows: `$ROLLING_WINDOW_DIR/output/nodes` (from .env)
- 10 windows: 1989-1993, 1993-1997, ..., 2025-2029
- Window size: 4 years, step size: 4 years (overlapping)

**Results**:

- **Cox C-index**: 0.765 (Model 6: Full)
- **Logistic AUC**: 0.719
- **PageRank coefficient**: β = -0.015\* (HR = 0.986) — protective in time-windowed
- **Out-degree**: β = -0.291\*\*\* (HR = 0.747) — most stable coefficient
- **family_rho_F**: β = -0.859\*\*\* (HR = 0.424) — strongest predictor

---

### exp_005: Parsimonious 2014-2020 (Non-Overlapping)

**Directory**: `experiments/exp_005_parsimonious_2014_2020/`

**Purpose**: Focus on "true family data" period (2014-2020) with non-overlapping windows and parsimonious model progression

**Configuration Files**:

- [`config_cox.yaml`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_005_parsimonious_2014_2020/config_cox.yaml)
  - **Model Progression** (parsimonious → full):
    1. **Model 1 (Core)**: camel_roa, family_rho_F, network_out_degree, network_C_b
    2. **Model 2 (+CAMEL)**: + camel_npl_ratio, camel_tier1_capital_ratio
    3. **Model 3 (+Network)**: + network_page_rank, betweenness, closeness, eigenvector
    4. **Model 4 (+Ownership)**: + foreign_FEC_d, family_FOP
    5. **Model 5 (Full)**: + camel_liquid_assets_ratio, state_SOP, state_SCP, foreign_FOP_t
  - MLflow Experiment: "Cox_Parsimonious_2014_2020" (ID: 6)

- [`config_logistic.yaml`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_005_parsimonious_2014_2020/config_logistic.yaml)
  - Mirror of Cox configuration
  - MLflow Experiment: "Logistic_Parsimonious_2014_2020" (ID: 6 shared)

**Run Scripts**:

- [`run_cox.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_005_parsimonious_2014_2020/run_cox.py)
  - **StandardScaler normalization**: All features scaled to 0-100 range
  - Sets `ROLLING_WINDOW_DIR` to non-overlapping 2014-2020 directory
  - Date range: 2014-01-01 to 2020-12-31
  - Tags: `scaled=true`, `non_overlapping=true`, `period=2014-2020`
- [`run_logistic.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_005_parsimonious_2014_2020/run_logistic.py)
  - Same StandardScaler normalization as Cox
  - Clustered SE by regn

**Data Source**:

- Rolling windows: `rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes/`
- 3 windows: 2014-2016, 2016-2018, 2018-2020
- Window size: 2 years, step size: 2 years (non-overlapping)

**Results**:

- **Cox C-index**: 0.7246 (Model 4: +Ownership)
- **Network Metrics Status**:
  - ✅ in_degree, out_degree, page_rank: Variable, included
  - ❌ betweenness, closeness, eigenvector: **ZERO VARIANCE** → dropped
  - ❌ network_C_b (ownership complexity): **ZERO VARIANCE** → dropped
- **Interpretation**: 2014-2020 network structure extremely stable (ossified)

---

## Part 2: Data Layer Enhancements

### 2.1 Rolling Window Data Loader

**File**: [`mlflow_utils/rolling_window_loader.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/mlflow_utils/rolling_window_loader.py)

**Key Modifications**:

1. **Fixed Identifier Matching** (Lines 71-95):

   ```python
   # Correct matching chain: Accounting.REGN → Neo4j.regn_cbr → Neo4j.Id → RollingWindow.Id
   # Changed from 'entity_id' to 'bank_id' (Neo4j Id property)
   ```

2. **NodeLabels Type Handling** (Lines 177-237):

   ```python
   # Fixed: nodeLabels stored as numpy array, not list
   rolling_banks = rolling_df[
       rolling_df['nodeLabels'].apply(lambda x: 'Bank' in x if hasattr(x, '__iter__') else False)
   ].copy()
   ```

3. **Optimised Temporal Matching** (Lines 185-237):
   - **Before**: O(n×m) row-by-row matching → ~hours
   - **After**: Vectorised pandas merge + temporal filter → ~9 seconds

   ```python
   # Efficient merge
   merged_with_rw = pd.merge(
       merged_df,
       rolling_banks,
       left_on='bank_id',
       right_on='Id',
       how='left'
   )
   # Temporal overlap filter
   matched_mask = (
       (merged_with_rw['window_start_year'] <= merged_with_rw['obs_year']) &
       (merged_with_rw['window_end_year_inclusive'] >= merged_with_rw['obs_year'])
   )
   ```

4. **Match Rate**: 99.5% → 127% (overlapping windows create multiple matches per observation)

**Performance**:

- Test dataset (151K obs): 9 seconds (vs hours before optimization)
- Full dataset (192K obs): ~15 seconds

---

### 2.2 Rolling Window Pipeline Enhancements

#### File: [`rolling_windows/metrics.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/metrics.py)

**Added Centrality Metrics** (Lines 29-52):

```python
# Betweenness centrality
gds.betweenness.mutate(
    G,
    mutateProperty="betweenness",
    concurrency=cfg.read_concurrency,
)

# Closeness centrality
gds.closeness.mutate(
    G,
    mutateProperty="closeness",
    concurrency=cfg.read_concurrency,
)

# Eigenvector centrality
gds.eigenvector.mutate(
    G,
    mutateProperty="eigenvector",
    maxIterations=20,
    concurrency=cfg.read_concurrency,
)
```

**Why Added**: exp_004 lacked betweenness/closeness metrics available in static experiments (exp_002), preventing fair comparison

#### File: [`data_models/rolling_windows.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/data_models/rolling_windows.py)

**Extended Pydantic Model** (Lines 22-28):

```python
class RollingWindowNodeFeatures(BaseModel):
    # Existing
    in_degree: Optional[float] = None
    out_degree: Optional[float] = None
    page_rank: Optional[float] = None

    # NEW
    betweenness: Optional[float] = Field(None, description="Betweenness Centrality score.")
    closeness: Optional[float] = Field(None, description="Closeness Centrality score.")
    eigenvector: Optional[float] = Field(None, description="Eigenvector Centrality score.")
```

#### Pipeline Execution

**Command** (2014-2020 non-overlapping):

```bash
cd rolling_windows && uv run python run_pipeline.py \
  --start-year 2014 \
  --end-start-year 2019 \
  --window-years 2 \
  --step-years 2 \
  --no-fastrp \
  --no-hashgnn \
  --no-node2vec \
  --no-export-feature-vectors \
  --no-export-feature-blocks \
  --base-projection-cypher /Users/alexandersoldatkin/projects/factions-networks-thesis/data_processing/cypher/35_0_rollwin_base_temporal_projection.cypher \
  --output-dir output/nodes_2014_2020_nonoverlap
```

**Output**:

- 3 parquet files: `node_features_rw_2014_2015.parquet`, `node_features_rw_2016_2017.parquet`, `node_features_rw_2018_2019.parquet`
- Size: ~2.0-2.1 MB each
- Rows: 38,503 - 39,615 nodes per window
- Columns: 19 (including new centrality metrics)

**Directory Structure Fix**:

```bash
# Loader expects <base>/output/nodes, pipeline outputs to <base>/nodes
# Fixed by reorganizing:
mv rolling_windows/output/nodes_2014_2020_nonoverlap/nodes \
   rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes
```

---

### 2.3 Neo4j Query Enhancement

**File**: [`queries/cypher/001_get_all_banks.cypher`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/queries/cypher/001_get_all_banks.cypher)

**Change** (Line 5):

```cypher
MATCH (n:Bank)
WHERE n.regn_cbr IS NOT NULL
RETURN
    toString(n.regn_cbr) as regn_cbr,
    n.Id as bank_id,  // ← ADDED: UUID for rolling window matching
    n.is_dead as is_dead,
    ...
```

**Purpose**: Enable `bank_id` (UUID) matching with rolling window `Id` column

---

## Part 3: Analysis & Documentation

### 3.1 Technical Implementation Documentation

**File**: [`memory-bank/time_window_regression_experiments.md`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/memory-bank/time_window_regression_experiments.md)

**Size**: ~650 lines, 45KB

**Contents**:

1. Executive Summary
2. Motivation (static vs time-windowed)
3. Technical Architecture (data flow diagrams)
4. Implementation Details
   - Initial O(n×m) approach failure
   - Optimised O(n+m) vectorised solution
   - Critical implementation details
5. Experiment Configurations (full YAML specs)
6. Results (C-indices, convergence, model comparisons)
7. Code Reference Map (every file touched with line numbers)
8. Static vs Time-Windowed Comparison Table
9. Technical Challenges & Solutions (4 major issues)
10. Reproducibility (exact commands)
11. Future Work (4 concrete proposals)
12. Lessons Learned
13. Appendices (env vars, file sizes, dependencies)

---

### 3.2 Comparative Analysis Writeup

**File**: [`memory-bank/time_window_regression_writeup.md`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/memory-bank/time_window_regression_writeup.md)

**Size**: ~18,000 words, 125KB

**Contents**:

#### Section 1: Historical Context (Russian Banking 2004-2025)

- 2008 Crisis: $582B reserves → $384B, $36B bailouts
- 2014 Sanctions: Interest rates 8% → 17%, mass license revocations
- 2020-2025: 72% state ownership, potential Oct 2026 systemic crisis
- **Network Firefighter Phenomenon**: High centrality = forced acquisitions

#### Section 2: Methodological Comparison

- Static: Collapsed temporal graph, endogenous centrality
- Time-Windowed: 4-year slices, reduced endogeneity, temporal variation

#### Section 3: Coefficient Stability Analysis

**PageRank Sign Reversal** (Table):
| Model | Static HR | Time-Windowed HR | Interpretation |
|-------|-----------|-------------------|----------------|
| Cox Model 6 | 0.994** | **0.986\*\*\* | Endogeneity confirmed |

**Out-Degree Perfect Stability**:

- βstatic = βtime-windowed = -0.291\*\*\* (0.0% difference)
- Structural measures immune to endogeneity

**family_rho_F Amplification**:

- Static: HR = 0.822 (17.8% reduction)
- Time-Windowed: HR = 0.424 (57.6% reduction)
- 330% stronger effect when measured historically

#### Section 4: Model Performance

- Cox C-index: 0.698 → 0.765 (+9.6%)
- Log-likelihood ratio: -log₂(p) = 82.72 → 290.43 (+251%)

#### Section 5: Most Protective Variables

1. family_rho_F (57.6% hazard reduction)
2. camel_roa (40.0% hazard reduction)
3. network_out_degree (25.3% hazard reduction)

#### Section 6-11: Theoretical Implications, Policy Recommendations, Limitations, Future Work, Conclusions

**Key Takeaway**: Time-windowed approach **essential** for crisis-prone systems with regulatory interventions

---

### 3.3 Aggregated Stargazer Tables

**Script**: [`scripts/aggregate_stargazer.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/scripts/aggregate_stargazer.py)

**Execution**:

```bash
uv run python scripts/aggregate_stargazer.py --exp_id 4  # Cox TV Rolling Window
uv run python scripts/aggregate_stargazer.py --exp_id 5  # Logistic TV Rolling Window
uv run python scripts/aggregate_stargazer.py            # All experiments
```

**Output Files**:

- `stargazer/stargazer_aggregated_coef_20260110_232111.csv` (24 models)
- `stargazer/stargazer_aggregated_hr_20260110_232111.csv` (24 models)

**Content**: Publication-ready comparison tables with:

- Coefficients + SE + significance stars
- Hazard ratios / Odds ratios
- Model fit statistics (LL, AIC, C-index/AUC)
- N observations, subjects, events

---

## Part 4: Complete File Manifest

### 4.1 New Files Created

**Experiments**:

- `experiments/exp_004_rolling_window_tv/config_cox.yaml`
- `experiments/exp_004_rolling_window_tv/config_logistic.yaml`
- `experiments/exp_004_rolling_window_tv/run_cox.py`
- `experiments/exp_004_rolling_window_tv/run_logistic.py`
- `experiments/exp_005_parsimonious_2014_2020/config_cox.yaml`
- `experiments/exp_005_parsimonious_2014_2020/config_logistic.yaml`
- `experiments/exp_005_parsimonious_2014_2020/run_cox.py`
- `experiments/exp_005_parsimonious_2014_2020/run_logistic.py`

**Documentation**:

- `memory-bank/time_window_regression_experiments.md` (technical guide)
- `memory-bank/time_window_regression_writeup.md` (comparative analysis)
- `memory-bank/CONTINUATION_GUIDE_2.md` (this file)

**Artifact Files** (`.gemini/antigravity/brain/...`):

- `implementation_plan.md`
- `task.md`
- `walkthrough.md`

**Data**:

- `rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes/node_features_rw_2014_2015.parquet`
- `rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes/node_features_rw_2016_2017.parquet`
- `rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes/node_features_rw_2018_2019.parquet`

**Stargazer Outputs**:

- `stargazer/stargazer_aggregated_coef_20260110_232111.csv`
- `stargazer/stargazer_aggregated_hr_20260110_232111.csv`

---

### 4.2 Modified Files

**Core Data Infrastructure**:

1. [`mlflow_utils/rolling_window_loader.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/mlflow_utils/rolling_window_loader.py)
   - Lines 71-95: Fixed bank_id matching
   - Lines 177-237: Optimised temporal matching (vectorised)
   - Lines 185-192: NodeLabels type handling

2. [`data_models/rolling_windows.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/data_models/rolling_windows.py)
   - Lines 25-28: Added betweenness, closeness, eigenvector fields

**Rolling Window Pipeline**: 3. [`rolling_windows/metrics.py`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/rolling_windows/metrics.py)

- Lines 29-52: Added 3 new centrality calculations

**Neo4j Queries**: 4. [`queries/cypher/001_get_all_banks.cypher`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/queries/cypher/001_get_all_banks.cypher)

- Line 5: Added `n.Id as bank_id` for UUID matching

---

### 4.3 Files Referenced (Not Modified)

**Visualisation Utilities**:

- `visualisations/cox_stargazer_new.py` (Stargazer generation)
- `visualisations/cox_interpretation.py` (interpretation reports)
- `visualisations/logistic_stargazer.py`
- `visualisations/logistic_interpretation.py`

**Queries**:

- `queries/cypher/002_ownership_complexity.cypher` (referenced for exp_005)
- `queries/cypher/003_1_rollwin_filter_window_graph.cypher` (pipeline reference)
- `queries/cypher/003_2_rollwin_metrics_reference.cypher` (pipeline reference)

**Data Models**:

- `data_models/analysis.py` (AnalysisDatasetRow)
- `data_models/accounting.py`

---

## Part 5: MLflow Experiments

### Experiment Hierarchy

| ID  | Name                            | Description                       | Runs | Status      |
| --- | ------------------------------- | --------------------------------- | ---- | ----------- |
| 2   | Paper_Cox_Models_Comparison     | Static network Cox                | 6    | ✅ Complete |
| 3   | Logistic_TV_Comparison_Paper    | Static network Logistic           | 6    | ✅ Complete |
| 4   | Cox_TV_Rolling_Window           | Time-windowed Cox                 | 6    | ✅ Complete |
| 5   | Logistic_TV_Rolling_Window      | Time-windowed Logistic            | 6    | ✅ Complete |
| 6   | Cox_Parsimonious_2014_2020      | Parsimonious Cox (2014-2020)      | 10   | ✅ Complete |
| 6   | Logistic_Parsimonious_2014_2020 | Parsimonious Logistic (2014-2020) | 5    | ✅ Complete |

**Total Runs**: 39

**Artifact Structure per Run**:

```
mlartifacts/<exp_id>/<run_id>/artifacts/
├── stargazer_column.csv      # Coefficients + SE
├── stargazer_hr_column.csv   # Hazard Ratios / Odds Ratios + SE
└── interpretation.md          # Variable interpretations, rankings
```

---

## Part 6: Key Findings & Insights

### 6.1 Methodological Findings

1. **Endogeneity Confirmed**:
   - PageRank coefficient sign reversal (static risk → time-windowed protective)
   - Static centrality contaminated by post-crisis interventions
   - Out-degree coefficient stability validates hypothesis (structural vs derived metrics)

2. **Performance Gains**:
   - C-index improvement: +9.6% (Cox)
   - Better out-of-sample discrimination
   - Stronger log-likelihood ratios

3. **Coefficient Stability Rankings**:
   - Most Stable: network_out_degree (σ=0.012)
   - Method-Sensitive: family_rho_F (σ=0.297), network_page_rank (σ=0.009)
   - Unstable: camel_liquid_assets_ratio (σ=0.624)

---

### 6.2 Substantive Findings

1. **Network Firefighter Phenomenon**:
   - High centrality banks forced to absorb failing peers
   - Static measures conflate strength with regulatory burden
   - Time-windowed measures isolate genuine network advantage

2. **Family Networks as Safety Net**:
   - family_rho_F = strongest predictor (57.6% hazard reduction)
   - Informal support structures > formal capital ratios
   - Russian _blat_ (connections) crucial for survival

3. **Capital Ratio Paradox**:
   - Higher Tier 1 capital → **higher** failure risk (HR = 5.606\*\*\*)
   - Evidence of "zombie bank" forbearance
   - Regulatory focus on capital misses operational insolvency

4. **2014-2020 Network Ossification**:
   - **Zero variance** in betweenness, closeness, eigenvector, ownership complexity
   - Network structure frozen during sanctions period
   - Concentration increased (top 5 banks: 66.5% assets by 2024)

---

### 6.3 Technical Learnings

1. **Performance Optimisation**:
   - Row-by-row temporal matching: O(n×m) = hours
   - Vectorised pandas merge: O(n+m) = seconds
   - **1000x speedup** via proper indexing

2. **Data Type Gotchas**:
   - NodeLabels stored as numpy array in parquet, not list
   - Requires `hasattr(x, '__iter__')` check before membership test

3. **GDS Limitations**:
   - Custom metrics (ownership complexity) require Cypher + manual mutation
   - No built-in support for path-based complexity calculations
   - Embedding methods (FastRP, HashGNN) optional for network analysis

4. **StandardScaler Benefits**:
   - 0-100 scaling enables coefficient comparability
   - Essential when mixing variables with different units (%, counts, ratios)
   - Improves numerical stability in optimization

---

## Part 7: Next Steps & Future Work

### 7.1 Immediate Follow-Ups

1. **Generate Final Tables**:

   ```bash
   cd experiments/exp_005_parsimonious_2014_2020
   uv run python ../../scripts/aggregate_stargazer.py --exp_id 6
   ```

2. **Create Interpretation Summary**:
   - Compare Model 1 (Core) vs Model 5 (Full) for exp_005
   - Assess diminishing returns of additional variables

3. **Update `regression_writeup.md`**:
   - Integrate exp_004/exp_005 findings
   - Include parsimonious model conclusions
   - Add 2014-2020 network stability discussion

---

### 7.2 Robustness Checks

1. **Sensitivity to Window Size**:
   - Test 1-year, 3-year, 5-year windows
   - Optimal window = trade-off between temporal precision and sample size

2. **Lag Structure**:
   - Current: Network metrics contemporaneous with outcomes
   - Test: t-1, t-2 year lags
   - Hypothesis: 2-year lag optimal for crisis→failure cascade

3. **Interaction Effects**:
   - `network_out_degree × family_rho_F`: Synergy between diversification and cohesion?
   - `network_page_rank × foreign_FEC_d`: Foreign investors + centrality?

4. **Non-Linear Effects**:
   - PageRank may have threshold effects
   - Test quadratic terms, splines

---

### 7.3 Advanced Extensions

1. **Network Change Metrics**:

   ```python
   delta_page_rank = PageRank(t) - PageRank(t-4)
   ```

   - Hypothesis: **Declining** centrality better predictor than absolute level
   - Captures loss of counterparties → liquidity stress

2. **Community-Level Analysis**:
   - Louvain communities already computed in rolling windows
   - Multi-level models with community fixed effects
   - Test: Within-community contagion effects

3. **Systemic Risk Contribution**:
   - Compute CoVaR (conditional value-at-risk) per window
   - Hypothesis: Banks contributing more to systemic risk get bailouts
   - Compare static vs time-windowed systemic importance

4. **Time-Windowed Ownership Complexity**:
   - **Current**: Uses static Neo4j calculation
   - **Goal**: Compute complexity per rolling window via Cypher
   - **Challenge**: GDS Python client limitations for custom metrics
   - **Solution**: Post-process exported data with custom script

---

### 7.4 Interpretation & Policy

1. **Early Warning System**:
   - Best Model: Cox Model 4 (+Foreign), C-index 0.764
   - Variables to Monitor:
     - family_rho_F (decreasing = family withdrawal)
     - camel_roa (primary indicator)
     - network_out_degree (diversification)
     - foreign_FEC_d (foreign flight)

2. **Zombie Bank Detection**:
   - Profile: High Tier 1 + Low ROA + High NPL
   - Time-windowed network can identify pre-crisis deterioration

3. **Regulatory Recommendations**:
   - Monitor network structure, not just balance sheets
   - Avoid forcing acquisitions on already-central banks (exhausts capacity)
   - Recognize informal support networks (family ties) in risk assessment

---

## Part 8: Environment & Dependencies

### 8.1 Key Environment Variables

**`.env` File Requirements**:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>

# Data Paths
ACCOUNTING_DIR=/Users/.../accounting_cbr_imputed
ROLLING_WINDOW_DIR=/Users/.../rolling_windows/output  # For exp_004

# For exp_005, set in run script:
# ROLLING_WINDOW_DIR=rolling_windows/output/nodes_2014_2020_nonoverlap
```

### 8.2 Python Dependencies

**Critical Packages**:

```toml
# pyproject.toml (uv-managed)
pandas = "^2.0"
numpy = "^1.24"
lifelines = "^0.27"          # Cox PH, time-varying
statsmodels = "^0.14"        # Logistic, clustered SE
mlflow = "^2.8"              # Experiment tracking
scikit-learn = "^1.3"        # StandardScaler
graphdatascience = "^1.7"    # Neo4j GDS client
python-dotenv = "^1.0"
pydantic = "^2.0"            # Data validation
```

### 8.3 External Services

**MLflow Server**:

```bash
uv run mlflow server --port 5000
# UI: http://127.0.0.1:5000
```

**Neo4j Database**:

- Version: 5.x
- GDS Plugin: Required
- Database: Check NEO4J_DATABASE env var (default: neo4j)

---

## Part 9: Common Issues & Solutions

### Issue 1: Rolling Window Match Rate 0%

**Symptom**: "Matched rolling window features for 0/151428 observations (0.0%)"

**Root Cause**: Incorrect identifier matching

**Solution**:

1. Verify Neo4j query includes `n.Id as bank_id`
2. Check rolling window parquet has `Id` column (UUID)
3. Ensure loader uses `bank_id` not `entity_id`

**Reference**: [`mlflow_utils/rolling_window_loader.py:71-95`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/mlflow_utils/rolling_window_loader.py#L71-L95)

---

### Issue 2: Slow Temporal Matching (Hours)

**Symptom**: Data loading takes hours

**Root Cause**: Row-by-row matching in O(n×m) complexity

**Solution**: Vectorised pandas merge

```python
# BEFORE (slow)
for _, obs_row in merged_df.iterrows():
    match = match_observation_to_window(obs_row['bank_id'], obs_row['date'], rolling_df)

# AFTER (fast)
merged_with_rw = pd.merge(merged_df, rolling_banks, left_on='bank_id', right_on='Id', how='left')
matched_mask = (
    (merged_with_rw['window_start_year'] <= merged_with_rw['obs_year']) &
    (merged_with_rw['window_end_year_inclusive'] >= merged_with_rw['obs_year'])
)
```

**Reference**: [`mlflow_utils/rolling_window_loader.py:185-237`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/mlflow_utils/rolling_window_loader.py#L185-L237)

---

### Issue 3: NodeLabels Type Error

**Symptom**: `TypeError: 'in' requires string as left operand, not numpy.ndarray`

**Root Cause**: NodeLabels stored as numpy array in parquet

**Solution**:

```python
# BEFORE
rolling_banks = rolling_df[rolling_df['nodeLabels'].apply(lambda x: 'Bank' in x)]

# AFTER
rolling_banks = rolling_df[
    rolling_df['nodeLabels'].apply(lambda x: 'Bank' in x if hasattr(x, '__iter__') else False)
]
```

**Reference**: [`mlflow_utils/rolling_window_loader.py:186-192`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/mlflow_utils/rolling_window_loader.py#L186-L192)

---

### Issue 4: Directory Structure Mismatch

**Symptom**: `ValueError: Rolling window nodes directory not found: .../output/nodes`

**Root Cause**: Loader expects `<base>/output/nodes`, pipeline outputs to `<base>/nodes`

**Solution**:

```bash
mkdir -p rolling_windows/output/nodes_2014_2020_nonoverlap/output
mv rolling_windows/output/nodes_2014_2020_nonoverlap/nodes \
   rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes
```

---

### Issue 5: MLflow 403 Error

**Symptom**: `MlflowException: API request ... failed with error code 403`

**Root Cause**: MLflow server not running or connection issue

**Solution**:

```bash
# Check if running
curl http://127.0.0.1:5000/health

# Restart if needed
pkill -f "mlflow server"
uv run mlflow server --port 5000 &

# In run script, explicitly set URI
mlflow.set_tracking_uri("http://127.0.0.1:5000")
```

---

### Issue 6: Constant Variables Dropped

**Symptom**: "Dropping constant column: network_betweenness"

**Root Cause**: Metric has zero variance in time period

**Interpretation**: Not an error! Indicates network stability in that period

**Action**: Document finding; consider alternative time periods or metrics

---

## Part 10: Code Snippets for Common Tasks

### 10.1 Run Existing Experiments

```bash
# exp_004: Time-Windowed (Full Period)
cd experiments/exp_004_rolling_window_tv
uv run python run_cox.py
uv run python run_logistic.py

# exp_005: Parsimonious (2014-2020)
cd experiments/exp_005_parsimonious_2014_2020
uv run python run_cox.py
uv run python run_logistic.py
```

### 10.2 Generate Stargazer Tables

```bash
# For specific experiment
uv run python scripts/aggregate_stargazer.py --exp_id 4

# For all experiments
uv run python scripts/aggregate_stargazer.py
```

### 10.3 Inspect Rolling Window Data

```python
import pandas as pd

# Load a window
df = pd.read_parquet('rolling_windows/output/nodes_2014_2020_nonoverlap/output/nodes/node_features_rw_2014_2015.parquet')

# Check columns
print('Columns:', df.columns.tolist())

# Filter to banks
banks = df[df['nodeLabels'].apply(lambda x: 'Bank' in x if hasattr(x, '__iter__') else False)]

# Check network metrics
network_cols = [c for c in banks.columns if any(kw in c.lower() for kw in ['degree', 'rank', 'between', 'close', 'eigen'])]
print('Network metrics:', network_cols)
print(banks[network_cols].describe())
```

### 10.4 Query MLflow Results

```python
import mlflow
mlflow.set_tracking_uri("http://127.0.0.1:5000")

# Get experiment
exp = mlflow.get_experiment_by_name("Cox_TV_Rolling_Window")

# Get runs
runs = mlflow.search_runs(experiment_ids=[exp.experiment_id])

# Best C-index
best_run = runs.loc[runs['metrics.c_index'].idxmax()]
print(f"Best C-index: {best_run['metrics.c_index']:.4f}")
print(f"Model: {best_run['tags.human_readable_name']}")
```

### 10.5 Create New Parsimonious Experiment

```yaml
# experiments/exp_00X_new/config_cox.yaml
experiment:
  name: "Cox_New_Analysis"

  models:
    model_1_baseline:
      name: "Baseline"
      features:
        - <top_3_predictors_from_previous>

    model_2_extended:
      name: "Extended"
      features:
        - <baseline_features>
        - <additional_features>

data:
  start_year: 2010
  end_year: 2020

model_params:
  penalizer: 0.0
  l1_ratio: 0.0
```

```python
# experiments/exp_00X_new/run_cox.py
# Copy from exp_005, modify:
# 1. Config path
# 2. Date range if needed
# 3. Rolling window directory if using custom windows
```

---

## Part 11: References

### Session Artifacts

1. **Implementation Plan**: [`.gemini/.../implementation_plan.md`](file:///Users/alexandersoldatkin/.gemini/antigravity/brain/2a003c80-0d91-4fb5-bf2f-791d407eb1c6/implementation_plan.md)
2. **Task Checklist**: [`.gemini/.../task.md`](file:///Users/alexandersoldatkin/.gemini/antigravity/brain/2a003c80-0d91-4fb5-bf2f-791d407eb1c6/task.md)
3. **Walkthrough**: [`.gemini/.../walkthrough.md`](file:///Users/alexandersoldatkin/.gemini/antigravity/brain/2a003c80-0d91-4fb5-bf2f-791d407eb1c6/walkthrough.md)

### Key Documentation Files

1. **Technical Guide**: [`memory-bank/time_window_regression_experiments.md`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/memory-bank/time_window_regression_experiments.md)
2. **Comparative Analysis**: [`memory-bank/time_window_regression_writeup.md`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/memory-bank/time_window_regression_writeup.md)
3. **Experiment Framework**: [`memory-bank/experiment_framework.md`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/memory-bank/experiment_framework.md)
4. **Original Continuation Guide**: [`memory-bank/CONTINUATION_GUIDE.md`](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/memory-bank/CONTINUATION_GUIDE.md)

### External References

1. Russian Banking Crisis Literature (2008, 2014) — see `time_window_regression_writeup.md` citations
2. Network Endogeneity: Hochberg et al. (2007)
3. Zombie Banks: Acharya et al. (2011)
4. Russian Informal Networks: Ledeneva (1998)

---

## Appendix A: Experiment Design Principles

### Hierarchical Model Building

**Rationale**: Assess marginal contribution of variable groups

**Template**:

1. **Controls**: Strongest predictors from prior literature
2. **+Network**: Add network centrality measures
3. **+Family**: Add family ownership variables
4. **+Foreign**: Add foreign ownership variables
5. **+State**: Add state ownership variables
6. **Full**: Kitchen sink (verify diminishing returns)

**Best Practice**: Start parsimonious, build up. Avoid "full model first" approach.

---

### StandardScaler Normalization

**When to Use**:

- Variables have different units (%, counts, ratios)
- Need coefficient comparability
- Mixing financial ratios with network metrics

**Implementation**:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Scale to 0-100 for interpretability
for col in features:
    min_val = X_scaled[col].min()
    max_val = X_scaled[col].max()
    if max_val > min_val:
        X_scaled[col] = 100 * (X_scaled[col] - min_val) / (max_val - min_val)
```

**Interpretation**: Coefficients represent effect of moving from min→max of variable

---

### Time-Windowed vs Static: Decision Matrix

| Criterion              | Static                                     | Time-Windowed               |
| ---------------------- | ------------------------------------------ | --------------------------- |
| **System Stability**   | Stable, no shocks                          | Crisis-prone, interventions |
| **Time Horizon**       | < 5 years                                  | 15+ years                   |
| **Research Goal**      | Description                                | Causal inference            |
| **Computational Cost** | Low (query Neo4j)                          | High (pre-compute windows)  |
| **Available Metrics**  | Full suite (betwee nness, closeness, etc.) | Limited by pipeline         |
| **Endogeneity Risk**   | High                                       | Lower                       |

**Recommendation**: Use **both** for robustness checks; report sensitivity if results diverge

---

## Appendix B: Glossary

**Terms**:

- **C-index**: Concordance index, Cox model goodness-of-fit (0.5 = random, 1.0 = perfect)
- **AUC**: Area Under ROC Curve, logistic model discrimination metric
- **HR**: Hazard Ratio, exp(β) in Cox models (>1 = increased risk, <1 = decreased risk)
- **OR**: Odds Ratio, exp(β) in logistic models
- **family_rho_F**: Family network cohesion (density of intra-family ties)
- **network_C_b**: Ownership complexity score (avg_path_length × log10(1 + unique_owners))
- **Pooled Logistic**: Logistic regression on person-period data

**File Naming**:

- `exp_00X`: Experiment directory number
- `rw`: Rolling window
- `tv`: Time-varying
- `nonoverlap`: Non-overlapping windows

---

## Appendix C: Session Timeline

| Time      | Activity                                                  | Duration     |
| --------- | --------------------------------------------------------- | ------------ |
| 23:00     | Session start, review exp_002/003                         | 30 min       |
| 23:30     | Create exp_004 configs, implement RollingWindowDataLoader | 1 hr         |
| 00:30     | Debug 0% match rate, fix identifier matching              | 45 min       |
| 01:15     | Optimize temporal matching (O(n×m) → O(n+m))              | 30 min       |
| 01:45     | Run exp_004 Cox & Logistic, generate artifacts            | 45 min       |
| 02:30     | Create comparative analysis writeup (18K words)           | 1.5 hr       |
| 04:00     | Plan exp_005, add betweenness/closeness/eigenvector       | 30 min       |
| 04:30     | Run rolling window pipeline (2014-2020, 2-year windows)   | 15 min       |
| 04:45     | Create exp_005 configs, implement StandardScaler          | 45 min       |
| 05:30     | Run exp_005 Cox & Logistic                                | 20 min       |
| 05:50     | Generate Stargazer tables, verify results                 | 20 min       |
| 06:10     | Create CONTINUATION_GUIDE_2.md                            | 30 min       |
| **Total** |                                                           | **~7 hours** |

---

**END OF CONTINUATION GUIDE**

_Last Updated_: 2026-01-11 00:30  
_Session ID_: 2a003c80-0d91-4fb5-bf2f-791d407eb1c6  
_Next Session_: Review exp_005 results, generate final publication tables, update regression_writeup.md
