# Experiment Plan: Testing Transaction Cost Mechanisms of Family Influence

**Experiment ID**: `exp_010_mechanism_testing`  
**Date**: 2026-01-11  
**Author**: Based on mechanisms from `family_survival_revised.md` §"Mechanisms of Family Influence: A Transaction Cost Perspective"

---

## Executive Summary

This experiment plan operationalises and tests the three **Transaction Cost Economics (TCE)** mechanisms proposed in the theoretical paper to explain _how_ family ownership enhances bank survival in Russia's institutional environment. Following Coasean institutional analysis, we test:

1. **Political Embeddedness** → Reducing "political transaction costs" through local information networks
2. **Tax Optimization** → Strategic firm boundary manipulation via ownership stake dilution
3. **Internal Capital Markets** → "Make vs. Buy" decision for capital through related-party lending

Each mechanism translates into testable hypotheses with specific proxies derived from existing Neo4j graph data and CBR accounting reports.

---

## 1. Theoretical Background

### 1.1 Transaction Cost Economics Framework

From Coase (1937) and North (1990), transaction costs include:

- **Search costs**: Finding trading partners
- **Bargaining costs**: Negotiating terms
- **Enforcement costs**: Ensuring compliance

In Russia's "suspension of law" environment post-2004 (Sodbiznesbank crisis), these costs are existential threats rather than economic frictions.

### 1.2 Three Mechanisms from Paper

| Mechanism                    | Transaction Cost Addressed            | Family Network Function                                                                  | Expected Effect on Survival                                          |
| ---------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Political Embeddedness**   | Information asymmetry with regulators | Family members placed near regional/municipal officials → advance warning of inspections | **Positive** (higher survival for geographically embedded families)  |
| **Tax Optimization**         | State appropriation via taxation      | Stake dilution across family members to avoid disclosure thresholds (20%, 50%)           | **Positive** (higher survival for fragmented family ownership)       |
| **Internal Capital Markets** | External credit market failures       | Related-party lending ("propping") prioritises family wealth preservation                | **Positive** (higher survival for banks with family-owned borrowers) |

**Key insight**: Family networks substitute for missing or predatory state institutions.

---

## 2. Mechanism 1: Political Embeddedness

### 2.1 Hypothesis

**H1**: Banks whose family owners/managers have **geographically proximate connections to regional government officials** exhibit higher survival probability, especially during periods of regulatory uncertainty (2004, 2014-2017).

**Logic**: Family members embedded in local political structures reduce information costs by:

- Gathering advance intelligence on regulatory inspections
- Buying time to "cook the books" or restructure assets
- Acting as informal enforcement structure lowering political transaction costs

### 2.2 Operationalisation

#### Proxies for Political Embeddedness

| Variable                         | Source                                        | Construction                                                                            | Prediction                                                                       |
| -------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `regional_family_density`        | Neo4j `:FAMILY` + `:MANAGEMENT`               | Count family members in bank's regional offices (not Moscow HQ) / total family members  | **Positive** coef                                                                |
| `family_municipal_overlap`       | Neo4j person addresses + municipal boundaries | Binary: 1 if ≥2 family members reside in bank's operational region                      | **Positive** coef                                                                |
| `regional_enforcement_intensity` | CBR regional inspection data (if available)   | Count of licence revocations per region per year (proxy for regulatory pressure)        | **Interaction**: family embeddedness more protective in high-enforcement regions |
| `political_connection_proxy`     | Neo4j person attributes                       | Family members with prior government employment (source: Reputation.ru compliance data) | **Positive** coef                                                                |

#### Data Requirements

**Existing**:

- ✅ Neo4j `:Person` nodes with family relationships
- ✅ Bank regional office locations (if in `:Bank` node properties)
- ✅ Family member names/patronymics for matching

**New** (requires extension):

- ❌ Person residential addresses (may need web scraping or Reputation.ru extension)
- ❌ Municipal/regional boundaries (GeoJSON shapefiles)
- ⚠️ CBR regional inspection data (request from user or proxy via regional licence revocation rates)

#### Model Specification

**Cox Time-Varying** with regional stratification:

```python
# Base model
formula = """
    family_connection_ratio +
    regional_family_density +          # NEW: Embeddedness proxy
    family_municipal_overlap +         # NEW: Binary geographic co-location
    political_connection_proxy +       # NEW: Government employment history
    camel_roa + camel_npl_ratio + camel_tier1_capital_ratio +
    rw_out_degree_4q_lag +
    state_ownership_pct + foreign_ownership_total_pct
"""

# Interaction with enforcement intensity
formula_interaction = """
    family_connection_ratio +
    regional_family_density * regional_enforcement_intensity +  # Mechanism test
    family_municipal_overlap +
    camel_roa + ...
"""

# Stratify by region to control for regional heterogeneity
ctv = CoxTimeVaryingFitter(strata=['region'])
ctv.fit(df, formula=formula_interaction, ...)
```

**Expected Results**:

- `regional_family_density`: β > 0, p < 0.05 (embedded families survive better)
- `regional_family_density × regional_enforcement_intensity`: β > 0 (embeddedness more valuable under regulatory pressure)

### 2.3 Temporal Heterogeneity Test

**Hypothesis H1.1**: Political embeddedness effect **strongest** during:

- 2004 banking crisis (Sodbiznesbank shock → regulatory uncertainty)
- 2014-2017 cleanup era (Central Bank sanitization campaigns)

**Test**: Re-run with crisis×embeddedness interactions:

```python
formula_crisis = """
    regional_family_density +
    regional_family_density * crisis_2004 +
    regional_family_density * crisis_2014 +
    ...
"""
```

**Expected**: Interaction coefficients > 0 (embeddedness premium during crises).

---

## 3. Mechanism 2: Tax Optimization via Stake Dilution

### 3.1 Hypothesis

**H2**: Banks with **fragmented family ownership** (many small stakes vs. few large stakes) exhibit higher survival probability, as dilution avoids regulatory disclosure thresholds (20%, 50%) and tax liabilities.

**Logic**: From paper:

> "Family members are frequently present in the ownership structure solely to dilute the stakes of the main beneficiary... This prevents any single entity from crossing ownership thresholds that trigger higher tax liabilities, mandatory disclosure, or stricter regulatory reporting."

### 3.2 Operationalisation

#### Proxies for Tax Optimization

| Variable                         | Source                            | Construction                                                                                                   | Prediction                                     |
| -------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `family_stake_fragmentation`     | Neo4j `:OWNERSHIP`                | Herfindahl index of family ownership stakes: `1 - Σ(stake_i / total_family_stake)²` (higher = more fragmented) | **Positive** coef                              |
| `family_members_below_threshold` | Neo4j `:OWNERSHIP`                | Count family members with stakes 5-19% (just below 20% disclosure threshold)                                   | **Positive** coef                              |
| `largest_family_stake`           | Neo4j `:OWNERSHIP`                | Max family ownership % (should be **negative** if dilution is protective)                                      | **Negative** coef                              |
| `family_shell_companies`         | Neo4j `:OWNERSHIP` via `:Company` | Count family-controlled `:Company` nodes owning bank (proxy for intermediary complexity)                       | **Positive** coef                              |
| `threshold_proximity`            | Neo4j `:OWNERSHIP`                | Binary: 1 if any family stake within 2pp of 20% or 50% threshold (18-22%, 48-52%)                              | **Negative** coef (risky to be near threshold) |

#### Data Requirements

**Existing**:

- ✅ Neo4j ownership relationships with `Size` property (% stake)
- ✅ Family connections (`:FAMILY` relationships)

**New**:

- ⚠️ Need to identify `:Company` nodes that are family-controlled (query: companies where majority owners are family members)

#### Model Specification

**Cross-sectional logistic** (since dilution is structural property):

```python
formula = """
    family_connection_ratio +
    family_stake_fragmentation +           # NEW: Herfindahl of family stakes
    family_members_below_threshold +       # NEW: Count near 20% threshold
    largest_family_stake +                 # NEW: Max stake (should be negative)
    family_shell_companies +               # NEW: Ownership complexity
    threshold_proximity +                  # NEW: Binary proximity to threshold
    camel_roa + bank_age + ...
"""

logit_model = sm.Logit(df['survived'], X)
results = logit_model.fit()
```

**Expected Results**:

- `family_stake_fragmentation`: β > 0 (more fragmented = higher survival)
- `largest_family_stake`: β < 0 (concentrated ownership = lower survival, contradicting naive family ownership effects)
- `family_members_below_threshold`: β > 0 (strategic positioning below disclosure threshold)

### 3.3 Falsification Test

**Hypothesis H2.1**: If tax optimization is the mechanism, effect should be **strongest** after:

- 2004: Introduction of stricter beneficial ownership disclosure rules
- 2013: Nabiullina cleanup era (enhanced regulatory scrutiny)

**Test**: Subperiod analysis:

```python
# Pre-regulation (2004-2007) vs Post-regulation (2014-2020)
df_pre = df[df['year'] <= 2007]
df_post = df[df['year'] >= 2014]

# Run same model on both subsets
# Expect fragmentation effect stronger post-2014
```

**Expected**: `family_stake_fragmentation` coefficient larger post-2014 (mechanism activated by regulation).

---

## 4. Mechanism 3: Internal Capital Markets (Related-Party Lending)

### 4.1 Hypothesis

**H3**: Banks engaged in **related-party lending** to family-owned businesses exhibit higher survival probability during crises, as internal capital markets provide "soft budget constraints" when external credit markets fail.

**Logic**: From paper:

> "Family banking groups create 'internal capital markets,' choosing to 'make' rather than 'buy' capital. By lending to their own family-owned businesses, the bank decreases the likelihood of bankruptcy for the broader family conglomerate... This acts as an insurance mechanism."

### 4.2 Operationalisation

#### Proxies for Internal Capital Markets

| Variable                    | Source                                      | Construction                                                                          | Prediction                                                                        |
| --------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `related_party_loan_ratio`  | CBR Form 101 (if available)                 | Related-party loans / total loans (some banks report this)                            | **Positive** coef (but **negative** in non-crisis periods if viewed as tunneling) |
| `family_borrower_count`     | Neo4j `:BORROWER` relationships (if exists) | Count family-owned companies receiving loans from bank                                | **Positive** coef                                                                 |
| `family_network_loan_flow`  | Neo4j graph paths                           | Sum of loan amounts where borrower is `:Company` owned by family member               | **Positive** coef                                                                 |
| `intra_group_lending_dummy` | Neo4j `:OWNERSHIP` + `:BORROWER`            | Binary: 1 if bank lends to companies owned by its own shareholders (circular lending) | **Interaction**: positive during crises, negative during normal times             |

#### Data Requirements

**Existing**:

- ⚠️ CBR Form 101 may not have related-party breakdown (needs verification)
- ❌ Neo4j `:BORROWER` relationships NOT currently in database (major limitation)

**New** (requires data extension):

- ❌ Borrower data: Corporate loan book with company identifiers (could scrape from CBR corporate reporting if banks disclose major borrowers)
- ❌ Family-company linkages: Match borrowing companies to family ownership via name/patronymic heuristics

**Alternative proxy** (without borrower data):

- `family_owned_company_assets`: Total assets of `:Company` nodes owned by family members (proxy for family conglomerate size)
- **Logic**: Larger family conglomerate → more internal capital market opportunities

#### Model Specification

**Cox Time-Varying with crisis interactions**:

```python
# Base model (may show negative coef if "tunneling" dominates)
formula_base = """
    family_connection_ratio +
    related_party_loan_ratio +          # NEW: RPL (if available)
    family_owned_company_assets +       # NEW: Proxy for internal market size
    camel_roa + ...
"""

# Crisis interaction model (mechanism test)
formula_crisis = """
    family_connection_ratio +
    related_party_loan_ratio +
    related_party_loan_ratio * crisis_2008 +    # Propping during GFC
    related_party_loan_ratio * crisis_2014 +    # Propping during sanctions
    camel_roa + ...
"""

ctv = CoxTimeVaryingFitter()
ctv.fit(df, formula=formula_crisis, ...)
```

**Expected Results**:

- `related_party_loan_ratio`: β < 0 (tunneling/expropriation during normal times)
- `related_party_loan_ratio × crisis_2008`: β > 0 (propping/insurance during crisis, reversing sign)
- Total effect during crisis: β_base + β_interaction > 0 (net positive survival effect)

### 4.3 Endogeneity Concern

**Problem**: Related-party lending may be **endogenous**—failing banks engage in desperate tunneling (reverse causality).

**Mitigation**:

1. **Use lagged RPL** (t-4 quarters): `related_party_loan_ratio_4q_lag` (re-use `QuarterlyWindowDataLoader` from exp_007)
2. **Placebo test**: If RPL*t predicts survival but RPL*{t-4} does not → endogeneity
3. **Subgroup analysis**: Restrict to banks with RPL ratios < 10% (below excessive tunneling threshold)

---

## 5. Combined Mechanisms Model

### 5.1 Full Specification

**Test all three mechanisms simultaneously**:

```python
formula_full = """
    # Baseline family effects
    family_connection_ratio +
    family_ownership_pct +

    # Mechanism 1: Political Embeddedness
    regional_family_density +
    regional_family_density * regional_enforcement_intensity +

    # Mechanism 2: Tax Optimization
    family_stake_fragmentation +
    largest_family_stake +
    family_members_below_threshold +

    # Mechanism 3: Internal Capital Markets
    related_party_loan_ratio_4q_lag +
    related_party_loan_ratio_4q_lag * crisis_2008 +
    related_party_loan_ratio_4q_lag * crisis_2014 +

    # Controls
    camel_roa + camel_npl_ratio + camel_tier1_capital_ratio +
    rw_out_degree_4q_lag + rw_page_rank_4q_lag +
    state_ownership_pct + foreign_ownership_total_pct
"""

ctv = CoxTimeVaryingFitter(strata=['community_collapsed'])
ctv.fit(df, formula=formula_full, ...)
```

### 5.2 Mechanism Importance Comparison

**Variance decomposition**: Run stepwise models to compare incremental R² / C-index improvements:

| Model | Features Added                | Incremental C-index | Interpretation            |
| ----- | ----------------------------- | ------------------- | ------------------------- |
| M0    | CAMEL + network only          | Baseline            | Fundamentals              |
| M1    | M0 + political embeddedness   | +0.01               | Embeddedness contribution |
| M2    | M0 + tax optimization         | +0.02               | Tax dilution contribution |
| M3    | M0 + internal capital markets | +0.03               | RPL contribution          |
| M4    | M0 + all three mechanisms     | +0.04               | Full model                |

**Interpretation**: Largest incremental C-index indicates dominant mechanism.

---

## 6. Data Loader Reuse Strategy

### 6.1 Existing Loaders

From `mlflow_utils/`:

- ✅ `quarterly_window_loader.py`: Loads quarterly accounting + 4Q lagged network (exp_007)
- ✅ `rolling_window_loader.py`: Loads 2-year window network metrics (exp_006)

### 6.2 Required Extensions

**File**: `mlflow_utils/mechanism_data_loader.py`

```python
from quarterly_window_loader import QuarterlyWindowDataLoader
import pandas as pd
from neo4j import GraphDatabase

class MechanismDataLoader(QuarterlyWindowDataLoader):
    """
    Extends QuarterlyWindowDataLoader with mechanism-specific features.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gds = self._init_neo4j()  # Reuse Neo4j connection pattern

    # ========== MECHANISM 1: Political Embeddedness ==========
    def compute_regional_family_density(self, df):
        """
        Query Neo4j for family members per region.
        Returns: family_members_in_region / total_family_members
        """
        query = """
        MATCH (b:Bank {regn_cbr: $regn})-[:MANAGEMENT]->(p:Person)
        OPTIONAL MATCH (p)-[:FAMILY_RELATION]-(f:Person)
        WHERE p.region_office <> 'Moscow'  // Regional, not HQ
        RETURN b.regn_cbr AS regn,
               count(DISTINCT f) AS regional_family,
               count(DISTINCT p) AS total_family
        """
        # Execute for each bank, merge back to df
        ...
        return df

    def compute_municipal_overlap(self, df):
        """
        Binary indicator for family geographic co-location.
        Requires person addresses (may not exist).
        """
        ...
        return df

    # ========== MECHANISM 2: Tax Optimization ==========
    def compute_family_stake_fragmentation(self, df):
        """
        Herfindahl index: 1 - Σ(stake_i / total_family_stake)²
        """
        query = """
        MATCH (b:Bank {regn_cbr: $regn})<-[r:OWNERSHIP]-(p:Person)
        OPTIONAL MATCH (p)-[:FAMILY_RELATION]-(f:Person)
        WHERE f.regn_cbr = $regn OR p.regn_cbr = $regn
        WITH b, collect(r.Size) AS stakes
        RETURN b.regn_cbr AS regn,
               reduce(hhi = 0.0, s IN stakes | hhi + (s / sum(stakes))^2) AS hhi,
               1 - hhi AS fragmentation
        """
        ...
        return df

    def count_family_near_threshold(self, df, threshold=20.0, window=2.0):
        """
        Count family stakes in (threshold - window, threshold + window).
        """
        query = """
        MATCH (b:Bank {regn_cbr: $regn})<-[r:OWNERSHIP]-(p:Person)
        OPTIONAL MATCH (p)-[:FAMILY_RELATION]-(f:Person)
        WHERE r.Size >= $threshold - $window
          AND r.Size <= $threshold + $window
        RETURN b.regn_cbr AS regn, count(*) AS near_threshold
        """
        ...
        return df

    # ========== MECHANISM 3: Internal Capital Markets ==========
    def compute_related_party_loans(self, df):
        """
        Requires :BORROWER relationships (NOT IN CURRENT DB).
        Fallback: Use family_owned_company_assets as proxy.
        """
        # Ideal query (if :BORROWER exists):
        query_ideal = """
        MATCH (b:Bank {regn_cbr: $regn})-[l:LOANS_TO]->(c:Company)
        OPTIONAL MATCH (c)<-[:OWNERSHIP]-(p:Person)-[:FAMILY_RELATION]-(f:Person)
        WHERE f owns b (via ownership chain)
        RETURN sum(l.amount) AS rpl_total
        """

        # Fallback query (family company assets):
        query_fallback = """
        MATCH (b:Bank {regn_cbr: $regn})<-[:OWNERSHIP]-(p:Person)
        OPTIONAL MATCH (p)-[:FAMILY_RELATION]-(f:Person)
        OPTIONAL MATCH (f)-[:OWNERSHIP]->(c:Company)
        RETURN sum(c.total_assets) AS family_company_assets
        """
        ...
        return df

    def load_mechanism_data(self, lag_quarters=4):
        """
        Main method: Load quarterly base + mechanism features.
        """
        # Start with base quarterly loader
        df = super().load_with_lags(lag_quarters=lag_quarters)

        # Add mechanism features
        df = self.compute_regional_family_density(df)
        df = self.compute_family_stake_fragmentation(df)
        df = self.count_family_near_threshold(df, threshold=20.0)
        df = self.count_family_near_threshold(df, threshold=50.0)  # Both thresholds
        df = self.compute_related_party_loans(df)  # Proxy only if no borrower data

        return df
```

---

## 7. Implementation Roadmap

### Phase 1: Data Preparation (3-5 days)

**Day 1**: Extend Neo4j schema (if needed)

- Check if person regional office data exists
- Add `:BORROWER` relationships IF corporate loan data available (ASK USER)

**Day 2**: Implement `MechanismDataLoader`

- Write Cypher queries for each mechanism proxy
- Test queries on subset of banks (validate output)

**Day 3**: Generate quarterly snapshots with mechanism features

- Reuse exp_007 quarterly snapshot pipeline
- Add mechanism features to parquet files

**Day 4-5**: Data validation

- Check for missing values
- Verify distributions (e.g., fragmentation index in [0,1])
- Document data quality issues

### Phase 2: Model Implementation (4-6 days)

**Day 1**: Set up experiment directory

```bash
cp -r experiments/exp_009_crisis_interactions experiments/exp_010_mechanism_testing
```

**Day 2-3**: Configure models

- `config_mechanisms.yaml`: Specify M1 (embeddedness), M2 (tax), M3 (internal capital), M4 (full)
- Adapt `run_cox.py` to use `MechanismDataLoader`

**Day 4**: Implement interaction models

- Crisis×embeddedness
- Crisis×related_party_lending

**Day 5**: Run all model specifications

- 6 core models + robustness checks

**Day 6**: Debug convergence issues

- Check for multicollinearity (VIF)
- Penalisation if needed

### Phase 3: Analysis & Robustness (3-4 days)

**Day 1**: Mechanism comparison

- Variance decomposition table
- Incremental C-index plot

**Day 2**: Temporal heterogeneity

- Subperiod analysis (2004-2007, 2014-2020)
- Crisis interaction tests

**Day 3**: Falsification tests

- Placebo test for RPL endogeneity
- Forward-lag test for embeddedness

**Day 4**: Stargazer aggregation

- Generate comparison tables
- Interpretation writeup

### Phase 4: Documentation (2 days)

**Day 1**: Create mechanism writeup

- `memory-bank/writeups/mechanism_testing_writeup.md`
- Interpret findings vis-à-vis theory

**Day 2**: Update paper draft

- Integrate empirical findings into mechanisms section
- Revise abstract/conclusion

**Total**: ~15 days (part-time)

---

## 8. Expected Results & Interpretation

### 8.1 Successful Mechanism Validation

| Mechanism                    | Key Variable                            | Expected Sign                                | If Confirmed                                           | If Rejected                                   |
| ---------------------------- | --------------------------------------- | -------------------------------------------- | ------------------------------------------------------ | --------------------------------------------- |
| **Political Embeddedness**   | `regional_family_density`               | **Positive**                                 | Family networks provide local informational advantages | Family connections national, not local        |
|                              | `regional_family_density × enforcement` | **Positive**                                 | Embeddedness more valuable under regulatory pressure   | Embeddedness ineffective or captured by state |
| **Tax Optimization**         | `family_stake_fragmentation`            | **Positive**                                 | Dilution shields from disclosure/tax                   | Concentration optimal (contradicts mechanism) |
|                              | `largest_family_stake`                  | **Negative**                                 | Large concentrated stakes risky                        | Concentration provides control benefits       |
| **Internal Capital Markets** | `related_party_loan_ratio_4q_lag`       | **Negative** (normal), **Positive** (crisis) | Internal markets insurance during crises               | RPL is tunneling (always harmful)             |
|                              | `RPL × crisis_2008`                     | **Positive** (reversal)                      | Propping activates during stress                       | No crisis-contingent mechanism                |

### 8.2 Interpretation Scenarios

**Scenario A: All three mechanisms validated**

- **Conclusion**: Family ownership operates through multiple reinforcing channels (embeddedness + tax shield + internal finance)
- **Policy implication**: Family networks are sophisticated institutional substitutes, not simple nepotism
- **Theoretical contribution**: Empirical validation of TCE framework in banking

**Scenario B: Only one mechanism significant**

- **E.g., embeddedness yes, tax/RPL no**
- **Conclusion**: Dominant mechanism is informational (political connections), not financial engineering
- **Implication**: Focus regulatory policy on geographic monitoring, not ownership structure complexity

**Scenario C: None confirmed**

- **Conclusion**: Family effects operate through unmeasured channels (reputation, long-term orientation)
- **Implication**: Need alternative theoretical frameworks (socioemotional wealth, trust-based governance)

### 8.3 Mechanism Interaction Hypothesis

**H4**: Mechanisms are **complementary**, not substitutes.

**Test**: Interaction term `embeddedness × fragmentation`

- If **positive**: Banks using both strategies survive best (snowball effect)
- If **zero**: Mechanisms independent (additive)
- If **negative**: Trade-off between strategies

---

## 9. Limitations & Mitigations

### L1: Missing Borrower Data

**Problem**: Neo4j lacks `:BORROWER` relationships → cannot directly measure related-party loans

**Mitigation**:

1. **Use CBR Form 101** (if available): Some banks report RPL ratio
2. **Proxy via family company assets**: Assumes lending proportional to family firm size
3. **Request user guidance**: ASK if corporate borrower data can be added to DB

### L2: Person Geographic Data Sparse

**Problem**: May not have regional office assignments or residential addresses for all persons

**Mitigation**:

1. **Use available subset**: Report coverage % transparently
2. **Binary indicator**: If ANY family member regional (vs. none) instead of continuous density
3. **Infer from bank regional operations**: If bank has regional branches, assume family present there

### L3: Endogeneity of Fragmentation

**Problem**: Fragmented ownership may be _consequence_ of distress (shareholders flee), not protective strategy

**Mitigation**:

1. **Use T-4 lagged fragmentation** (pre-determined)
2. **Restrict to stable banks**: Exclude banks with recent ownership volatility
3. **First-difference model**: Test if changes in fragmentation predict survival changes

### L4: Threshold Proximity Measurement Error

**Problem**: 20% and 50% thresholds are regulatory, but banks may use different accounting standards

**Mitigation**:

1. **Sensitivity analysis**: Test thresholds at 15%, 20%, 25% (window around statutory threshold)
2. **Industry expert validation**: Confirm thresholds with Russian banking specialists

---

## 10. Success Criteria

### Minimum Viable

✅ `MechanismDataLoader` successfully computes:

- Political embeddedness proxy (even if partial coverage)
- Fragmentation index for all banks with family ownership
- Internal capital proxy (company assets, not loans)

✅ At least **one mechanism** shows significant coefficient (p < 0.05) in predicted direction

✅ C-index improvement over baseline family model (exp_008/exp_009)

### Strong Result

✅ **Two or more mechanisms** significant
✅ Crisis interactions validated (embeddedness stronger during 2014, RPL reverses sign during 2008)
✅ Variance decomposition shows mechanisms explain ≥40% of family ownership effect
✅ Robustness across subperiods and lag specifications

### Publishable

✅ All three mechanisms validated with expected signs
✅ Complementarity test shows positive interaction (mechanisms compound)
✅ Falsification tests passed (placebo, forward-lag non-significant)
✅ External validity: Compare Russia mechanism strengths to similar emerging markets (literature synthesis)

---

## 11. Connection to Existing Experiments

| Prior Experiment | Relevance to exp_010                                                            | Reuse Components                                     |
| ---------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **exp_007**      | Lagged network → Adapt for lagged fragmentation/RPL                             | ✅ `QuarterlyWindowDataLoader`, 4Q lag logic         |
| **exp_008**      | Family connection ratio → Baseline for mechanism comparison                     | ✅ Model specification templates                     |
| **exp_009**      | Crisis interactions → Test embeddedness/RPL×crisis                              | ✅ Crisis dummy variables, interaction term approach |
| **exp_006**      | Community stratification → Control for community confounding in mechanism tests | ✅ Community aggregation logic, stratified Cox       |

**Synergy**: exp_010 **decomposes** the family effect found in exp_007-009 into **specific causal channels** (embeddedness, tax, capital markets).

---

## 12. Next Steps After exp_010

### If Mechanisms Validated

1. **Policy brief**: Translate findings for Central Bank audience (which mechanisms regulators can/should target)
2. **Paper revision**: Replace theoretical speculation with empirical evidence in mechanisms section
3. **Extension**: Test mechanisms in other institutional contexts (China, India, MENA family banks)

### If Mechanisms Not Found

1. **Alternative theories**: Socioemotional wealth (non-financial utility), reputational capital, dynastic succession concerns
2. **Qualitative investigation**: Interviews with family bank owners to identify unmeasured mechanisms
3. **Refocus on baseline result**: Family effects robust but mechanism unclear → treat as "black box" protective factor

---

## 13. Conclusion

This experiment plan operationalises the three TCE mechanisms from the theoretical paper into testable hypotheses with novel proxies derived from Neo4j graph data. By reusing data loaders from exp_007-009 and extending them with mechanism-specific features, we can efficiently test whether family survival benefits operate through:

1. **Information networks** (political embeddedness)
2. **Financial engineering** (tax optimisation via stake dilution)
3. **Crisis insurance** (internal capital markets via related-party lending)

The modular design allows each mechanism to be tested independently before combining in a full specification, enabling clear identification of dominant channels and informing both theory development and regulatory policy.

**Recommendation**: Proceed with exp_010 contingent on **user confirming availability of**:

- ✅ Person regional office data (likely exists)
- ⚠️ Borrower/corporate loan data (likely **not** exists → use proxy)
- ⚠️ CBR Form 101 with related-party disclosure (ASK USER)

**Estimated effort**: 15 days (part-time) if borrower data unavailable, 20 days if requires new data collection.
