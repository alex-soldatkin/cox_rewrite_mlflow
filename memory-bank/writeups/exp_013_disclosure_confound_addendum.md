# CRITICAL ADDENDUM: Disclosure Mandate Confound (exp_013)

**Date**: 2026-01-12  
**Priority**: HIGHEST - Must address before accepting exp_013 findings

---

## The Problem: Measurement Artifact Hypothesis

### Disclosure Mandate Timing Coincidence

**Observation**: Russia may have implemented stricter beneficial ownership disclosure rules ~2013-2014, **exactly coinciding** with Nabiullina's cleanup campaign.

**Confound**: The observed "reverse causality" pattern in exp_013 could be a **measurement artifact**:

- **Not**: Survivors truly build family connections
- **Instead**: Better disclosure reveals pre-existing connections that were always there
- **Spurious peak 2016**: Maximum disclosure compliance, not maximum connection accumulation

### Evidence for Disclosure Artifact

1. **Timing**: FCR increase coincides exactly with Nabiullina appointment
2. **Static FCR**: 99.8% of banks have constant FCR → Unlikely if actively building
3. **Cleanup incentives**: Stricter oversight → Better disclosure compliance
4. **International pressure**: Post-sanctions transparency requirements

---

## Proposed Solution: Link Prediction Model (Extension 1A)

### Objective

Impute missing/undisclosed family ties using:

1. **String matching**: Levenshtein distance on Russian surnames + patronymics
2. **Network embeddings**: FastRP or HashGNN to capture latent family structures
3. **Logistic regression**: Train on observed ties, predict missing ties

### Implementation Plan

#### Step 1: Feature Engineering

```python
# 1. Name similarity features
def compute_name_similarity(person1, person2):
    surname_sim = 1 - levenshtein_distance(person1.surname, person2.surname) / max(len(...))
    patronymic_sim = 1 - levenshtein_distance(person1.patronymic, person2.patronymic) / max(len(...))

    # Russian naming conventions: shared patronymic = same father
    same_patronymic = (person1.patronymic == person2.patronymic)

    return {
        'surname_similarity': surname_sim,
        'patronymic_similarity': patronymic_sim,
        'same_patronymic': same_patronymic
    }

# 2. Network embedding features (Neo4j GDS)
CALL gds.graph.project('ownership_graph',
    ['Person', 'Bank'],
    'OWNS')

CALL gds.fastRP.stream('ownership_graph', {
    embeddingDimension: 128,
    iterationWeights: [1.0, 1.0, 1.0]
})
YIELD nodeId, embedding
RETURN nodeId, embedding

# 3. Shared ownership patterns
def shared_ownership_features(person1, person2):
    banks_p1 = set(person1.owned_banks)
    banks_p2 = set(person2.owned_banks)

    return {
        'jaccard_banks': len(banks_p1 & banks_p2) / len(banks_p1 | banks_p2),
        'num_shared_banks': len(banks_p1 & banks_p2),
        'co_investment_strength': sum(ownership_overlap(b) for b in banks_p1 & banks_p2)
    }
```

#### Step 2: Train Link Prediction Model

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# Training data: observed family ties
X_train = [
    {
        **compute_name_similarity(p1, p2),
        'embedding_cosine': cosine_similarity(emb1, emb2),
        **shared_ownership_features(p1, p2)
    }
    for (p1, p2) in observed_family_pairs
]

X_negative = [
    # Sample negative edges (non-family pairs)
    ...
]

y_train = [1] * len(X_train) + [0] * len(X_negative)

# Fit model
model = LogisticRegression(class_weight='balanced')
model.fit(X_combined, y_train)

# Evaluate
print(f"Precision: {precision_score(y_test, y_pred)}")
print(f"Recall: {recall_score(y_test, y_pred)}")
print(f"F1: {f1_score(y_test, y_pred)}")
```

#### Step 3: Impute Missing Family Ties

```python
# For all person pairs NOT in observed family graph
candidate_pairs = get_all_person_pairs_not_in_family_graph()

for (p1, p2) in candidate_pairs:
    features = extract_features(p1, p2)
    prob_family = model.predict_proba(features)[1]

    if prob_family > threshold:  # e.g., 0.7 for precision, 0.5 for recall
        # Add inferred family tie to Neo4j
        CREATE (p1)-[:FAMILY_INFERRED {probability: prob_family}]->(p2)

# Recompute FCR with imputed ties
for bank in banks:
    fcr_imputed = compute_fcr(bank, include_inferred=True)
    bank.family_connection_ratio_imputed = fcr_imputed
```

#### Step 4: Re-run exp_007-013 Suite

**Critical validation**: Run all experiments with `family_connection_ratio_imputed`

| Experiment  | Original FCR                | Imputed FCR            | Expected if Disclosure Artifact        |
| ----------- | --------------------------- | ---------------------- | -------------------------------------- |
| exp_007     | HR=0.988\*\*\*              | HR=?                   | Similar (pre-disclosure period)        |
| exp_008     | HR=0.988\*\*\*              | HR=?                   | Similar (community control robust)     |
| exp_009     | Crisis × FCR null           | Crisis × FCR?          | Similar (crisis not disclosure-driven) |
| exp_011     | FCR declines 2004→2020      | FCR stable?            | **Decline disappears** (measurement)   |
| exp_012     | FCR × Nabiullina negative   | FCR × Nabiullina null? | **Interaction disappears** (spurious)  |
| **exp_013** | **2016 peak (+0.25\***)\*\* | **No peak?**           | **Peak disappears** (CRITICAL TEST)    |

### Expected Outcomes

**Scenario A: Disclosure Artifact Confirmed**

- FCR_imputed **removes 2014-2018 peak** in exp_013
- exp_011 temporal decline **disappears** (FCR stable after imputation)
- exp_012 governor interaction **null** (no regime difference)
- **Conclusion**: Observed reverse causality was measurement artifact

**Scenario B: Genuine Reverse Causality Confirmed**

- FCR_imputed **preserves 2016 peak** in exp_013 (may reduce magnitude but pattern persists)
- exp_011 temporal pattern **remains** (genuine compositional change)
- exp_012 governor interaction **persists** (genuine selection effect)
- **Conclusion**: Reverse causality is real, disclosure is minor confounder

**Scenario C: Partial (Most Likely)**

- FCR_imputed **reduces but doesn't eliminate** 2016 peak
- Peak magnitude drops from +0.25 to ~+0.15
- **Conclusion**: Both disclosure improvement AND genuine accumulation

---

## Implementation Priority

**Phase 1 (1-2 weeks)**: Link prediction model development

- Extract person-pair features from Neo4j
- Train/validate logistic regression
- Sensitivity analysis on threshold selection

**Phase 2 (1 week)**: Imputation and validation

- Generate FCR_imputed for all banks/quarters
- Validate against known family ties (hold-out set)
- Compare FCR vs FCR_imputed distributions

**Phase 3 (2-3 weeks)**: Re-run experiment suite

- exp_007 through exp_013 with FCR_imputed
- Compare coefficients, significance, C-indices
- Document changes in interpretation

**Total**: 4-6 weeks

---

## Alternative: Robustness Check Without Full Imputation

**Quick test** (if full imputation infeasible):

1. **Subsample analysis**: Re-run exp_013 on **pre-2013 data only** (before disclosure mandate)
   - If reverse causality absent pre-2013 → Supports disclosure artifact
   - If reverse causality present pre-2013 → Genuine effect

2. **Disclosure quality proxy**: Code disclosure completeness per bank-quarter
   - If high correlation between disclosure quality and FCR_observed → Artifact
   - If low correlation → Genuine FCR

3. **Cross-sectional vs panel variation**:
   - If FCR increases **within-bank** during cleanup → Accumulation
   - If FCR increases **between-bank** only → Selection/disclosure

---

## References and Related Work

**Link prediction in ownership networks**:

- Lü & Zhou (2011): Link prediction in complex networks (survey)
- Peixoto (2012): Inferring missing links in large-scale networks
- Zhang & Chen (2018): Link prediction based on graph neural networks

**Name matching for family ties**:

- Christen (2012): Data matching approaches for family reconstruction
- Bilenko et al. (2003): Adaptive name matching in information integration

**Russian naming conventions**:

- Patronymics as family indicators (father's name + suffix)
- Surname inheritance patterns

---

**Status**: Proposal requiring implementation  
**Next Step**: Create exp_014 for link prediction model development
