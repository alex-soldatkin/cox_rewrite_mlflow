# exp_013: Reverse Causality Test - Does Survival Predict Family Connections?

**Research Question**: Do survivors build stronger family connections over time, or do family connections cause survival?

**Hypothesis**: If family connections are **endogenous** to survival (reverse causality), then survival status should predict family_connection_ratio.

## Motivation

### The Endogeneity Problem

**Previous experiments (exp_007-012)**: Found family connection ratio (FCR) protective (HR≈0.988-0.990)

**Endogeneity concern**:

- **Forward causality**: Family connections → Lower failure risk
- **Reverse causality**: Survival → Builds more family connections (network expansion)
- **Omitted confounding**: Both driven by quality/political power

**Cannot distinguish** with Cox PH alone (predicts survival from FCR)

### Why Reverse Causality Matters

**Scenario 1: Exogenous family connections**

- Family ties determined by historical relationships, business group membership
- Connections **cause** survival via liquidity sharing, information networks
- **Policy**: Encourage family business groups

**Scenario 2: Endogenous family connections**

- Survivors **build connections** as they grow (M&A, cross-ownership)
- Connections are **outcome**, not cause
- **Policy**: Family ties are marker of success, not driver

**exp_013 approach**: Test whether **survival predicts FCR growth**

---

## Experimental Design

### Approach: Panel Regression (Reversed Equation)

**Standard equation** (exp_007-012):

```
survival ~ family_connection_ratio + controls
```

**Reversed equation** (exp_013):

```
family_connection_ratio ~ survived_to_t + controls
```

### Model Specifications

**M1: Cross-sectional (2015)**

```python
# OLS at single time point (mid-sample)
fcr_2015 ~ survived_to_2015 + camel + network_2011 + ownership
```

**Purpose**: Test whether banks alive in 2015 have higher FCR than those that died before 2015

**M2: Cross-sectional (2020)**

```python
# OLS at end of sample
fcr_2020 ~ survived_to_2020 + camel + network_2016 + ownership
```

**Purpose**: Test longer-run reverse causality (full sample)

**M3: Panel with Bank Fixed Effects**

```python
# Panel regression with entity FE
fcr_it ~ survived_status_it + camel_it + network_it-4 + alpha_i + epsilon_it
```

**Purpose**: Test within-bank FCR changes as survival likelihood evolves

**M4: First Differences**

```python
# Change-in-change specification
Δfcr_it ~ Δsurvived_prob_it + Δcamel_it + Δnetwork_it-4
```

**Purpose**: Eliminate time-invariant confounders

---

## Data Construction

### Outcome Variable: family_connection_ratio

**Source**: Neo4j graph database (bank node property)  
**Observation**: Quarterly (2010-2020)
**Range**: Continuous [0, 1]

### Key Predictor: survived_to_t

**Construction**:

```python
# Binary indicator
survived_to_2015 = 1 if death_date > 2015-12-31 or death_date is None
survived_to_2020 = 1 if death_date > 2020-12-31 or death_date is None

# Panel version: "still alive at quarter t"
survived_status_t = 1 if alive at t, 0 if died before t
```

### Controls (Same as exp_008)

**CAMEL ratios**:

- camel_roa
- camel_npl_ratio
- camel_tier1_capital_ratio

**Lagged network** (4Q lag to avoid simultaneity):

- rw_page_rank_4q_lag
- rw_out_degree_4q_lag

**Other ownership**:

- state_ownership_pct
- foreign_ownership_total_pct

---

## Expected Results

### If Family Connections are Exogenous (Forward Causality Only)

**M1-M2 (Cross-sectional)**: survived_to_t coefficient **not significant**

- Reason: FCR determined pre-sample, doesn't change with survival

**M3 (Panel FE)**: survived_status coefficient **not significant**

- Reason: Within-bank FCR variation unrelated to survival status

**M4 (First diffs)**: Δsurvived_prob coefficient **not significant**

- Reason: Changes in survival likelihood don't cause FCR changes

### If Family Connections are Endogenous (Reverse Causality)

**M1-M2**: survived_to_t coefficient **positive and significant**

- Survivors have **higher FCR** than dead banks
- Magnitude: ≈0.05-0.10 higher FCR for survivors

**M3**: survived_status coefficient **positive**

- Banks build connections as they remain alive

**M4**: Δsurvived_prob coefficient **positive**

- Improving survival odds → FCR growth

### If Both Directions Apply (Bidirectional)

**M1-M2**: Positive effect (selection)
**M3-M4**: Positive but smaller (within-bank growth)

**Interpretation**: FCR both **causes survival** AND **results from survival**

---

## Implementation Details

### Software

**Regression**: `statsmodels`

- `OLS` for M1-M2
- `PanelOLS` (linearmodels) for M3
- First differences via pandas for M4

**Data loading**: `QuarterlyWindowDataLoader` (from exp_008)

**Sample**: 2010-2020 (quarterly), ~44K bank-quarter observations

### Specifications

**M1 (2015 Cross-section)**:

```yaml
data:
  year: 2015
  quarter: Q4
regression:
  outcome: family_connection_ratio
  predictors:
    - survived_to_2015
    - camel_roa
    - camel_npl_ratio
    - camel_tier1_capital_ratio
    - state_ownership_pct
    - foreign_ownership_total_pct
    - rw_page_rank_2014q4  # 4Q lag
    - rw_out_degree_2014q4
```

**M3 (Panel FE)**:

```yaml
data:
  start_year: 2010
  end_year: 2020
  frequency: quarterly
regression:
  outcome: family_connection_ratio
  entity_effects: true  # Bank fixed effects
  time_effects: false
  predictors:
    - survived_status
    - camel_roa
    - ... (same as M1)
```

---

## Interpretation Guide

### Strong Evidence Against Reverse Causality

survived_to_t coefficient **< 0.01 and p > 0.10** in all models

**Interpretation**: Family connections **genuinely exogenous**

- Determined by historical business relationships
- exp_007-012 Cox results are **causal**
- No endogeneity bias

### Strong Evidence For Reverse Causality

survived_to_t coefficient **> 0.05 and p < 0.01** in M1-M2

**Interpretation**: Survivorsselectively build connections

- exp_007-012 Cox results **biased upward**
- True causal effect smaller than estimated
- Requires instrumental variable approach

### Mixed Evidence (Most Likely)

- **Cross-sectional** (M1-M2): Positive (selection effect)
- **Panel FE** (M3): Small positive (within-bank growth)
- **First diff** (M4): Near zero (no short-run causality)

**Interpretation**:

- **Long-run**: Some reverse causality (survivors accumulate connections)
- **Short-run**: Forward causality dominates (connections → survival)
- **exp_007-012 Cox valid** for policy (short-run protective effect real)
- **But**: Long-run equilibrium more complex

---

## Policy Implications

### If No Reverse Causality

**Promote family business groups** as stabilizing force

- Connections **cause** stability
- Regulatory barriers to affiliated lending counterproductive

### If Strong Reverse Causality

**Family ties are outcome marker**, not policy lever

- Focus on **fundamentals** (CAMEL) that allow connection-building
- Family connections indicate quality, don't create it

### If Bidirectional (Expected)

**Nuanced approach**:

- **Short-run**: Family connections genuinely protective (keep them)
- **Long-run**: Survivors build more connections (concentration concern)
- **Policy**: Allow family ties but **monitor accumulation** (antitrust)

---

## Files

- Configuration: `config_ols.yaml`
- Runner: `run_regression.py`
- MLflow experiment: `exp_013_reverse_causality`
