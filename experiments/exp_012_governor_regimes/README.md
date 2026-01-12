# exp_012: Central Bank Governor Regime Effects

**Research Question**: Do ownership effects on bank survival vary systematically between Central Bank governor regimes (Ignatyev vs Nabiullina)?

**Hypothesis**: Regulatory philosophy differences between governors create regime-specific ownership advantages:

- **Ignatyev era (2004-2013)**: Laissez-faire approach, light regulation, family connections more valuable
- **Nabiullina era (2013-2020)**: Aggressive cleanup, license revocations, state/transparent ownership favored

## Motivation

### Previous Findings

**exp_009**: Found crisis-specific ownership effects but assumed stable coefficients within crisis periods  
**exp_011**: Found declining family effects over time (FCR: -0.018 → -0.011 from 2004 to 2020) but couldn't isolate regime vs crisis effects

### Governor Transition (2013)

**Sergey Ignatyev (2002-2013)**:

- Governed during 2004 banking crisis, 2008 GFC
- Known for accommodative stance toward systemically important banks
- Limited license revocations

**Elvira Nabiullina (2013-present)**:

- Appointed June 2013
- Implemented aggressive cleanup campaign (2013-2016)
- Revoked 300+ banking licenses
- Stricter capital requirements
- Enhanced transparency requirements

### Confounding: Regime vs Crisis

**Problem**: 2013 transition coincides with:

- Crimea sanctions (2014)
- Oil price collapse
- Cleanup campaign intensity

**Cannot distinguish**:

- Nabiullina **regime effect** (tougher regulation)
- **Crisis effect** (2014 sanctions)
- **Selection effect** (cleanup removed weakest banks)

### exp_012 Approach

Test governor regime effects **controlling for crises**:

```
Model: ownership_effects ~ governor_dummy + crisis_dummies + governor × ownership
```

If significant governor × ownership interactions → **regime matters** beyond crisis timing

## Data

**Same as exp_009**:

- Period: 2004-2020 (quarterly snapshots, 4Q lag)
- Sample: ~140K observations, ~1,100 banks, ~770 events
- Features: Ownership, network (lagged), CAMEL, crisis indicators

**New variables**:

- `governor_nabiullina`: Binary (1 if period ≥ 2013Q3, else 0)
- Interaction terms: `ownership × governor_nabiullina`

## Model Specifications

### M1: Baseline (No Governor Effects)

```yaml
features:
  - family_connection_ratio
  - family_ownership_pct
  - state_ownership_pct
  - foreign_ownership_total_pct
  - rw_page_rank_4q_lag
  - rw_out_degree_4q_lag
  - camel_roa
  - camel_npl_ratio
  - camel_tier1_capital_ratio
```

### M2: Governor Dummy

```yaml
features: [M1 features]
  + governor_nabiullina
```

**Test**: Does Nabiullina period have different baseline hazard?

### M3: Family × Governor

```yaml
features: [M2 features]
  + family_connection_ratio_x_governor
  + family_ownership_pct_x_governor
```

**Hypothesis**: Family effects **weaker** under Nabiullina (stricter affiliated lending rules)

### M4: State × Governor

```yaml
features: [M2 features]
  + state_ownership_pct_x_governor
```

**Hypothesis**: State effects **stronger** under Nabiullina (bailout expectations, policy bank role)

### M5: Foreign × Governor

```yaml
features: [M2 features]
  + foreign_ownership_total_pct_x_governor
```

**Hypothesis**: Foreign effects **weaker** under Nabiullina (sanctions, geopolitical stress)

### M6: Full Interactions

```yaml
features: [M2 features]
  + family_connection_ratio_x_governor
  + family_ownership_pct_x_governor
  + state_ownership_pct_x_governor
  + foreign_ownership_total_pct_x_governor
```

## Expected Results

**If regime matters**:

- Significant `governor_nabiullina` main effect
- Significant ownership × governor interactions
- Different magnitudes than crisis × ownership from exp_009

**If regime doesn't matter** (just crisis timing):

- Non-significant governor interactions
- exp_011 subperiod differences driven entirely by crisis exposure

## Comparison to exp_011

| Aspect             | exp_011                            | exp_012                              |
| ------------------ | ---------------------------------- | ------------------------------------ |
| **Approach**       | Separate models per period         | Single model with regime dummy       |
| **Advantage**      | Full coefficient flexibility       | Tests regime hypothesis directly     |
| **Disadvantage**   | Can't test formal structural break | Assumes regime = discrete shift      |
| **Crisis control** | Implicit (period-specific crises)  | Explicit (crisis dummies + governor) |

**Complementary**: exp_011 shows patterns, exp_012 tests mechanisms

## Files

- Configuration: `config_cox.yaml`
- Runner: `run_cox.py` (modified from exp_009)
- Output: MLflow experiment `exp_012_governor_regimes`

## Implementation Notes

**Governor dummy creation**:

```python
# Nabiullina appointed June 2013
df['governor_nabiullina'] = (df['date'] >= pd.Timestamp('2013-07-01')).astype(int)
```

**Interaction generation**:

```python
for ownership_var in ['family_connection_ratio', 'family_ownership_pct',
                       'state_ownership_pct', 'foreign_ownership_total_pct']:
    df[f'{ownership_var}_x_governor'] = df[ownership_var] * df['governor_nabiullina']
```

**Crisis controls**: Include all 3 crisis dummies from exp_009 to isolate governor effect from crisis timing
