# exp_011 Subperiod Analysis: Manual Results Summary

**Generated**: 2026-01-11  
**Source**: exp_011_run_success.log output

---

## Model Performance Summary (C-index)

### 2004-2007 Period (Early Crisis Era)

- M1 Baseline: 0.6608
- M2 Crisis 2004: 0.6610
- M3 Family × Crisis 2004: 0.6604
- M4 State × Crisis 2004: 0.6610
- M5 Foreign × Crisis 2004: 0.6603
- M6 Full Interactions: 0.6612

**Best**: M6 Full Interactions (C-index = 0.6612)

### 2007-2013 Period (GFC & Recovery)

- M1 Baseline: 0.6370
- M2 Crisis 2008: 0.6373
- M3 Family × Crisis 2008: 0.6372
- M4 State × Crisis 2008: 0.6373
- M5 Foreign × Crisis 2008: 0.6377
- M6 Full Interactions: 0.6370

**Best**: M5 Foreign × Crisis 2008 (C-index = 0.6377)

### 2013-2020 Period (Sanctions Era)

- M1 Baseline: 0.6386
- M2 Crisis 2014: 0.6262
- M3 Family × Crisis 2014: 0.6184
- M4 State × Crisis 2014: 0.6266
- M5 Foreign × Crisis 2014: 0.6285
- M6 Full Interactions: 0.6211

**Best**: M1 Baseline (C-index = 0.6386)

---

## Key Observations

### Predictive Power Across Periods

1. **2004-2007** had highest C-index (0.66) - best model fit
2. **2007-2013** had moderate C-index (0.64)
3. **2013-2020** had moderate C-index (0.64)

### Interaction Term Value

- **2004-2007**: Full interactions (+0.0004 over baseline) - minimal improvement
- **2007-2013**: Foreign×Crisis best (+0.0007) - slight improvement
- **2013-2020**: Baseline best (interactions HURT performance) - suggests complex non-linear effects

### Period-Specific Patterns

- Early period (2004-2007): Models perform similarly regardless of crisis interactions
- GFC period (2007-2013): Foreign ownership interactions most informative
- Sanctions era (2013-2020): Adding crisis interactions reduces model fit (overfitting or wrong functional form)

---

## Convergence Warnings

### Complete Separation Indicators (Low Variance)

**2004 Crisis**:

- `family_connection_ratio_x_crisis_2004`
- `state_ownership_pct_x_crisis_2004`
- `foreign_ownership_total_pct_x_crisis_2004`

**Interpretation**: These features have extremely strong predictive power during the 2004 crisis (coefficients very large in magnitude, approaching complete separation in logistic sense).

**2008 Crisis**:

- `state_ownership_pct_x_crisis_2008`

---

## Next Steps for Full Analysis

1. **Extract Baseline Coefficients**: Compare `family_connection_ratio` HR across M1 for all three periods
2. **Interaction Magnitude**: Extract crisis interaction coefficients from M3-M6
3. **Structural Break Test**: Formal Chow test at 2013 boundary
4. **M6 Detailed Comparison**: Side-by-side all ownership × crisis terms

---

## Data Quality Metrics

| Period    | Observations | Banks | Events | Crisis Obs | Crisis % |
| --------- | ------------ | ----- | ------ | ---------- | -------- |
| 2004-2007 | 33,966       | 944   | 669    | 1,314      | 3.9%     |
| 2007-2013 | 70,243       | 1,001 | 688    | 12,839     | 18.3%    |
| 2013-2020 | 53,957       | 829   | 508    | 15,617     | 28.7%    |

**Note**: 2007-2013 has most observations and highest event count (688 deaths)
