# Experiment 010 Implementation Log: Mechanism Testing

**Experiment ID:** `exp_010_mechanism_testing`
**Objective:** Operationalise and test the three Transaction Cost Economics (TCE) mechanisms: Political Embeddedness, Tax Optimization, and Internal Capital Markets.

## 📅 Status Log

- **2026-02-12**: Initial log creation. Experiment directory initialized.

## 🧪 Implementation Plan

### Phase 1: Data Preparation & Feasibility Check
- [ ] **Data Audit**:
    - [x] Check availability of `person.region_office` property in Neo4j (Missing, using Bank Region).
    - [x] Check availability of RPL ratio in CBR Form 101 data (Missing, using Group Assets).
    - [x] Check availability of corporate borrower data (Missing, using Company ownership).
- [x] Implement `MechanismDataLoader` (including stakeholders fragmentation index) <!-- id: 19 -->
    - [x] `mlflow_utils/mechanism_data_loader.py` inheriting from `QuarterlyWindowDataLoader`.
    - [x] **Political Embeddedness**: Regional stratification proxy.
    - [x] **Tax Optimization**: Stake fragmentation index (HHI).
    - [x] **Internal Capital Markets**: Family group company count.
- [x] **Hypothesis Testing**:
    - [x] Create [config_cox.yaml](file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/experiments/exp_010_mechanism_testing/config_cox.yaml) for model specifications.
    - [x] **Theoretical Refinement**: Expound on `stake_fragmentation_index` and Russian tax "splitting" strategies.
    - [x] MLflow logging of all mechanism proxies.
    - [x] Analysis of coefficients and H-race results. <!-- id: 20 -->
    - [x] **EPU Resilience**: Interaction effects with Economic Policy Uncertainty.
- [x] Experiment 014: Temporal FCR (1990-2022) <!-- id: 10 -->
- [ ] **Neo4j Extensions** (if needed):
    - [ ] Add `:BORROWER` relationships if data available.
    - [ ] Identify family-controlled `:Company` nodes for asset proxy.
- [x] Implement `MechanismDataLoader` (including stakeholders fragmentation index) <!-- id: 19 -->
    - [ ] `mlflow_utils/mechanism_data_loader.py` inheriting from `QuarterlyWindowDataLoader`.
    - [ ] **Political Embeddedness**:
        - [ ] `compute_regional_family_density`: Count family in regional offices.
        - [ ] `compute_municipal_overlap`: Binary co-location (if address data exists).
    - [ ] **Tax Optimization**:
        - [ ] `compute_family_stake_fragmentation`: Herfindahl index (1 - HHI).
        - [ ] `count_family_near_threshold`: Count stakes in [18%, 22%] and [48%, 52%].
    - [ ] **Internal Capital Markets**:
        - [ ] `compute_related_party_loans`: RPL ratio (if available) OR family company assets proxy.

### Phase 2: Model Configuration
- [ ] **Create Experiment Structure**:
    - [ ] `experiments/exp_010_mechanism_testing/config_mechanisms.yaml`
    - [ ] `experiments/exp_010_mechanism_testing/run_cox_mechanisms.py`
- [ ] **Define Models (Hypotheses)**:
    - **M1: Political Embeddedness (H1)**
        - Feature: `regional_family_density`
        - Interaction: `regional_family_density * regional_enforcement_intensity` (if available)
        - Interaction: `regional_family_density * crisis_2004/2014`
    - **M2: Tax Optimization (H2)**
        - Feature: `family_stake_fragmentation` (Expect +)
        - Feature: `largest_family_stake` (Expect -)
        - Feature: `family_members_below_threshold`
    - **M3: Internal Capital Markets (H3)**
        - Feature: `related_party_loan_ratio_4q_lag`
        - Interaction: `RPL_lag * crisis_2008/2014` (Expect + during crisis, - otherwise)
    - **M4: Full Combined Model**
        - All above + Controls + Community Stratification

### Phase 3: Execution & Analysis
- [ ] **Run Models**:
    - [ ] Execute `run_cox_mechanisms.py` for M1-M4.
    - [ ] Verify convergence (use StandardScaler).
- [ ] **Robustness Checks**:
    - [ ] Subperiod analysis (Pre-2008 vs Post-2014).
    - [ ] Placebo tests for RPL endogeneity.
- [ ] **Artifact Generation**:
    - [ ] `stargazer_mechanisms.csv`
    - [ ] Interpretation report.

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Borrower Data** | Cannot measure RPL directly | Use `family_owned_company_assets` as proxy for internal market potential. |
| **Missing Person Regions** | Cannot measure embeddedness | Use bank's regional branch presence as proxy for family reach. |
| **Endogeneity (RPL)** | Tunneling vs Propping | Use 4-quarter lagged RPL and crisis interactions to distinguish. |

## 📝 Detailed Log

### 1. Data Audit (Completed 2026-02-12)
*   [x] **Person Region**: `region_office` property missing/sparse in Neo4j (Count: 0).
    *   **Decision**: Use `Bank.region` as fallback. If a family controls a bank in Region X, we assume they are embedded there.
*   [x] **RPL Data**: Not found in accounting parquet files (no `related_party` columns).
    *   **Decision**: Must use **Internal Capital Markets Proxy** (`family_owned_company_assets`).
*   [x] **Borrower Data**: `:BORROWER` relationships count is 0.
    *   **Decision**: Confirmed need for asset-based proxy.
*   [x] **Company Assets**: `Company` nodes exist (verified). Will use `total_assets` if available, or just count of family-owned companies.

### 2. Loader Implementation (Completed 2026-02-12)
*   [x] Draft `MechanismDataLoader`.
*   [x] Verify fragmentation index (mean 0.35, max 0.94).
*   [x] Verify family company count proxy.

### 3. Hypothesis Testing (Completed 2026-02-12)
*   [x] **H1 (Political)**: `family_connection_ratio` protective within regional strata (p < 0.001).
*   [x] **H2 (Tax)**: `stake_fragmentation_index` protective (p = 0.001).
*   [x] **H3 (Internal Capital)**: `family_company_count` highly protective (p < 0.001).

## Aggregated Results
The horse race results have been aggregated into unified stargazer tables:
- **Coefficients**: `stargazer/stargazer_aggregated_coef_20260212_173552.csv`
- **Hazard Ratios**: `stargazer/stargazer_aggregated_hr_20260212_173552.csv`

The Internal Capital Market mechanism remains the dominant protective factor in the full horse race (M4).

### 4. Experiment 010 Expansion (H3++, Community, & 2004-2020) (Completed 2026-02-12)
*   **Timestamp**: 2026-02-12 19:05 UTC
*   **Objective**: Scaled Experiment 010 from 2010-2020 to 2004-2020. Integrated "Deep Proxies" (H3++) and Community-based stratification (Louvain).

#### Issues Encountered & Solutions:

1.  **Observation Count Discrepancy**:
    *   **Problem**: Initial runs yielded ~44,000 observations instead of the theoretical ~192,000.
    *   **Solution**: Identified that the frequency was **quarterly** (factor of 3 reduction) and the network snapshots were restricted to 2010-2020. Expanded the analysis to 2004-2020 by decoupling the data loader and pointing it to the full production dataset.
    ```python
    # mlruns_utils/mechanism_data_loader.py
    def load_mechanism_data(self, lag_quarters: int = 4, start_year: int = 2004, ...):
        # Now yields 139,038 observations (95% network match rate)
    ```

2.  **Hardcoded Temporal Boundaries**:
    *   **Problem**: `QuarterlyWindowDataLoader` was limited to `quarterly_2010_2020`.
    *   **Solution**: Updated class defaults to point to the local 2004-2020 production directory and reset the default `start_year` to 2004.

3.  **Community Stratification & Convergence**:
    *   **Problem**: Louvain communities with very few banks caused model non-convergence when used as strata.
    *   **Solution**: Implemented a collapsing threshold in `run_cox_mechanisms.py` to bucket small clusters into an 'other' group.
    ```python
    community_counts = df['network_community'].value_counts()
    df['community_id'] = df['network_community'].apply(
        lambda x: str(int(x)) if community_counts[x] >= 5 else 'other'
    )
    ```

#### Files Modified (Full Relative Paths):
- `mlflow_utils/mechanism_data_loader.py`: Added deep proxies (`PaidTax`, `Vehicles`) and full-period support.
- `mlflow_utils/quarterly_window_loader.py`: Decoupled legacy 2010-2020 paths.
- `experiments/exp_010_mechanism_testing/run_cox_mechanisms.py`: Integrated `M9` (Community) and `M10` (H3++) models.
- `experiments/exp_010_mechanism_testing/REPORT.md`: Centralised results write-up.
- `experiments/exp_010_mechanism_testing/compare_survival.py`: survival time unit set to months.

